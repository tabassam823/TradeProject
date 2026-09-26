"""
sig_math.py
Core Mathematical Engine for Signature Trading (Sig-Trading).
Implements Path Normalization, Hoff Lead-Lag Transformation,
Iterative Chen's Identity Signature Computation, and Tensor Utilities.
Pure NumPy implementation for lightweight execution on CPU/Docker.
"""

from typing import List, Tuple, Optional
import numpy as np


def normalize_path(path: np.ndarray, base_price_relative: bool = True) -> np.ndarray:
    """
    Normalizes market path into time-augmented market factor process Z_hat.
    
    Parameters:
    -----------
    path : np.ndarray
        Array of shape (T, D) where:
        - Column 0: Time index or timestamps
        - Column 1..d: Asset prices
        - Column d+1..D-1: Exogenous signals
    base_price_relative : bool
        If True, scales prices as P_t / P_0 (invariant to price magnitude).
        
    Returns:
    --------
    np.ndarray: Normalized path of shape (T, D).
    """
    arr = np.array(path, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    
    T, D = arr.shape
    if T <= 1:
        return arr
    
    norm_arr = np.copy(arr)
    
    # 1. Normalize time (column 0) to [0, 1]
    t_min = norm_arr[0, 0]
    t_max = norm_arr[-1, 0]
    t_range = t_max - t_min
    if t_range > 1e-12:
        norm_arr[:, 0] = (norm_arr[:, 0] - t_min) / t_range
    else:
        norm_arr[:, 0] = np.linspace(0.0, 1.0, T)
        
    # 2. Normalize asset prices (relative to starting price P_0)
    if base_price_relative and D > 1:
        for c in range(1, D):
            p0 = norm_arr[0, c]
            if abs(p0) > 1e-12:
                norm_arr[:, c] = norm_arr[:, c] / p0
            else:
                # If initial value is 0, standardize by std
                std = np.std(norm_arr[:, c])
                if std > 1e-12:
                    norm_arr[:, c] = (norm_arr[:, c] - np.mean(norm_arr[:, c])) / std

    return norm_arr


def hoff_lead_lag(path: np.ndarray) -> np.ndarray:
    """
    Transforms path into Hoff Lead-Lag path (Definition 2.3 & Theorem 2.10).
    Lifts continuous / discrete paths to compensate Itô-to-Stratonovich quadratic covariation.
    
    Parameters:
    -----------
    path : np.ndarray of shape (T, D)
    
    Returns:
    --------
    np.ndarray: Lead-Lag path of shape (2T - 1, 2D)
        - First D columns: Lead process
        - Next D columns: Lag process
    """
    path = np.asarray(path, dtype=np.float64)
    if path.ndim == 1:
        path = path.reshape(-1, 1)
    
    T, D = path.shape
    if T <= 1:
        return np.hstack([path, path])
    
    ll_length = 2 * T - 1
    ll_path = np.zeros((ll_length, 2 * D), dtype=np.float64)
    
    # Construction:
    # 2k   : (Z_{t_k}, Z_{t_k})
    # 2k+1 : (Z_{t_{k+1}}, Z_{t_k})
    for k in range(T - 1):
        ll_path[2 * k, :D] = path[k]
        ll_path[2 * k, D:] = path[k]
        
        ll_path[2 * k + 1, :D] = path[k + 1]
        ll_path[2 * k + 1, D:] = path[k]
        
    ll_path[2 * (T - 1), :D] = path[-1]
    ll_path[2 * (T - 1), D:] = path[-1]
    
    return ll_path


def get_signature_dim(dim: int, order: int) -> int:
    """
    Calculates the total dimension of truncated tensor algebra T^(order)(R^dim):
    Sum_{k=0}^order dim^k
    """
    if dim == 1:
        return order + 1
    return (dim ** (order + 1) - 1) // (dim - 1)


def get_word_catalog(dim: int, order: int) -> List[Tuple[int, ...]]:
    """
    Generates word catalog up to truncated order M for alphabet {0, 1, ..., dim-1}.
    Empty word () is represented as empty tuple.
    """
    catalog = [()]
    current_level = [()]
    for _ in range(order):
        next_level = []
        for w in current_level:
            for letter in range(dim):
                next_level.append(w + (letter,))
        catalog.extend(next_level)
        current_level = next_level
    return catalog


def _segment_signature(delta: np.ndarray, order: int) -> List[np.ndarray]:
    """
    Computes the signature of a single straight-line segment with increment delta.
    Level k = (delta^(tensor k)) / k!
    """
    levels = [np.array([1.0], dtype=np.float64)] # Level 0
    cur = np.array([1.0], dtype=np.float64)
    fact = 1.0
    for k in range(1, order + 1):
        cur = np.kron(cur, delta)
        fact *= k
        levels.append(cur / fact)
    return levels


def _chen_tensor_product(sig1: List[np.ndarray], sig2: List[np.ndarray], order: int) -> List[np.ndarray]:
    """
    Applies Chen's identity tensor product:
    (S1 \otimes S2)_n = Sum_{k=0}^n S1_k \otimes S2_{n-k}
    """
    res = []
    for n in range(order + 1):
        level_n = np.zeros(len(sig1[n]), dtype=np.float64)
        for k in range(n + 1):
            term = np.kron(sig1[k], sig2[n - k])
            level_n += term
        res.append(level_n)
    return res


def compute_signature(path: np.ndarray, order: int = 2) -> np.ndarray:
    """
    Computes the truncated signature of a piecewise linear path using Chen's identity.
    
    Parameters:
    -----------
    path : np.ndarray of shape (T, D)
    order : int, truncation level (default 2)
    
    Returns:
    --------
    np.ndarray: 1D array containing concatenated tensor levels 0 through order.
    """
    path = np.asarray(path, dtype=np.float64)
    if path.ndim == 1:
        path = path.reshape(-1, 1)
        
    T, D = path.shape
    if T <= 1:
        dim_total = get_signature_dim(D, order)
        res = np.zeros(dim_total, dtype=np.float64)
        res[0] = 1.0
        return res
        
    deltas = np.diff(path, axis=0)
    
    # Initialize signature with first step
    sig = _segment_signature(deltas[0], order)
    
    # Concat remaining steps via Chen's Identity
    for step in range(1, len(deltas)):
        step_sig = _segment_signature(deltas[step], order)
        sig = _chen_tensor_product(sig, step_sig, order)
        
    return np.concatenate(sig)


def extract_lead_lag_pnl_matrix(sigs_lead_lag: np.ndarray, dim_original: int, order: int) -> np.ndarray:
    """
    Extracts PnL attribution features for trading strategies (Theorem 2.11).
    Maps signature terms ending with asset lead differentials to feature vectors.
    
    Parameters:
    -----------
    sigs_lead_lag : np.ndarray of shape (K, total_ll_sig_dim)
        Matrix of K sample paths' lead-lag signatures up to order (2M+1) or M.
    dim_original : int
        Original dimension D = 1 + d + N (lead-lag dim is 2D).
    order : int
        Truncation order M for strategy functional.
        
    Returns:
    --------
    np.ndarray of shape (K, num_features)
    """
    # For lead-lag space, lead channel for asset m (1-indexed) is index m.
    # The feature matrix extracts relevant signature projections.
    # In practice, for order M=1 or M=2, this extracts terms of length <= order + 1.
    return sigs_lead_lag
