"""Utility script to fetch and print Binance Futures USDT‑M account balance.
It respects the environment variables defined in `.env_wds` (overriding `.env`).
"""
import os, sys
from dotenv import load_dotenv

# Load .env then .env_wds (override) – same logic as the scheduler
load_dotenv()
load_dotenv('.env_wds', override=True)

# Ensure API keys are present
api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')
if not api_key or not secret_key:
    print('[ERROR] Binance API credentials not found in environment.')
    sys.exit(1)

# Add project root to sys.path for imports
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.core.binance_client_wds import BinanceFuturesClient

# Use mainnet if BINANCE_SANDBOX is set to false, otherwise testnet
sandbox_flag = os.getenv('BINANCE_SANDBOX', 'true').lower() in ('true', '1', 'yes')
client = BinanceFuturesClient(api_key=api_key, secret_key=secret_key, testnet=sandbox_flag)

balance = client.get_account_balance()
print('Futures USDT‑M Balance:', balance)
