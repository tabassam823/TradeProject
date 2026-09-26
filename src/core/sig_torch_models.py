"""
sig_torch_models.py
PyTorch Deep Learning Architectures and Custom Portfolio Utility Loss Functions.
Implements:
1. SigNetMLP: Deep MLP operating on Signature features
2. TimeSeriesLSTM: Sequential LSTM operating on raw windowed paths
3. MeanVarianceUtilityLoss: Direct dynamic mean-variance portfolio loss
4. DirectSharpeLoss: Differentiable negative annualized Sharpe ratio
"""

from typing import List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class SigNetMLP(nn.Module):
    """
    Multi-Layer Perceptron that maps path signatures S^(<=M)(Z) directly
    to optimal continuous portfolio positions xi_t in [-1.0, +1.0].
    """
    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int] = [64, 32],
        dropout: float = 0.2,
        use_batchnorm: bool = True
    ):
        super().__init__()
        self.input_dim = input_dim
        layers = []
        in_dim = input_dim
        
        for h_dim in hidden_dims:
            layers.append(nn.Linear(in_dim, h_dim))
            if use_batchnorm:
                layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.GELU())
            if dropout > 0.0:
                layers.append(nn.Dropout(dropout))
            in_dim = h_dim
            
        # Final output layer mapping to 1 scalar position per asset
        layers.append(nn.Linear(in_dim, 1))
        layers.append(nn.Tanh()) # Constrains position to [-1.0, +1.0]
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        x: Tensor of shape (batch_size, input_dim)
        Returns: Tensor of shape (batch_size, 1) in [-1.0, 1.0]
        """
        return self.network(x)


class TimeSeriesLSTM(nn.Module):
    """
    Recurrent LSTM model processing raw normalized sequential market paths
    (batch_size, seq_len, num_features) to generate continuous dynamic position.
    """
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 48,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 24),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(24, 1),
            nn.Tanh()
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: Tensor of shape (batch_size, seq_len, input_size)
        Returns: Tensor of shape (batch_size, 1) in [-1.0, 1.0]
        """
        lstm_out, _ = self.lstm(x)
        # Take last time-step hidden state
        last_step = lstm_out[:, -1, :]
        return self.fc(last_step)


class MeanVarianceUtilityLoss(nn.Module):
    """
    Differentiable Mean-Variance Utility Loss:
    Loss = - ( E[R_p] - 0.5 * lambda * Var(R_p) )
    where R_p = position * forward_return
    """
    def __init__(self, risk_aversion_lambda: float = 1.0, eps: float = 1e-8):
        super().__init__()
        self.lambda_param = risk_aversion_lambda
        self.eps = eps
        
    def forward(self, positions: torch.Tensor, forward_returns: torch.Tensor) -> torch.Tensor:
        """
        positions: (batch_size, 1)
        forward_returns: (batch_size, 1)
        """
        # Portfolio returns
        portfolio_returns = positions.squeeze(-1) * forward_returns.squeeze(-1)
        
        expected_return = torch.mean(portfolio_returns)
        variance_return = torch.var(portfolio_returns, unbiased=True)
        
        utility = expected_return - 0.5 * self.lambda_param * variance_return
        return -utility # Minimize negative utility


class DirectSharpeLoss(nn.Module):
    """
    Direct Differentiable Negative Sharpe Ratio Loss:
    Loss = - ( Mean(R_p) / (Std(R_p) + eps) ) * sqrt(annualization_factor)
    """
    def __init__(self, annualization_factor: float = 8760.0, eps: float = 1e-6): # 8760 hours/year
        super().__init__()
        self.ann_factor = torch.sqrt(torch.tensor(annualization_factor, dtype=torch.float32))
        self.eps = eps
        
    def forward(self, positions: torch.Tensor, forward_returns: torch.Tensor) -> torch.Tensor:
        portfolio_returns = positions.squeeze(-1) * forward_returns.squeeze(-1)
        mean_ret = torch.mean(portfolio_returns)
        std_ret = torch.std(portfolio_returns, unbiased=True)
        
        sharpe = (mean_ret / (std_ret + self.eps)) * self.ann_factor
        return -sharpe


def create_model(model_name: str, input_dim: int, **kwargs) -> nn.Module:
    """Factory function for model creation."""
    name = model_name.lower().strip()
    if "signet" in name or "mlp" in name:
        hidden_dims = kwargs.get("hidden_dims", [64, 32])
        dropout = kwargs.get("dropout", 0.2)
        return SigNetMLP(input_dim=input_dim, hidden_dims=hidden_dims, dropout=dropout)
    elif "lstm" in name or "recurrent" in name:
        hidden_size = kwargs.get("hidden_size", 48)
        num_layers = kwargs.get("num_layers", 2)
        dropout = kwargs.get("dropout", 0.2)
        return TimeSeriesLSTM(input_size=input_dim, hidden_size=hidden_size, num_layers=num_layers, dropout=dropout)
    else:
        raise ValueError(f"Unknown model name: {model_name}. Supported: 'SigNetMLP', 'TimeSeriesLSTM'")
