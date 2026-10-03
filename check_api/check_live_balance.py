import os
from binance.client import Client
from dotenv import load_dotenv

# 1. Muat kredensial dari .env
load_dotenv()
API_KEY = os.getenv("BINANCE_LIVE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_LIVE_SECRET_KEY")

# 2. Inisialisasi Client TANPA testnet=True (default adalah Live/Production)
client = Client(API_KEY, SECRET_KEY)

def check_live_futures_balance():
    try:
        balances = client.futures_account_balance()
        print("=== SALDO DOMPET BINANCE FUTURES (LIVE) ===")
        
        found_active_balance = False
        for item in balances:
            asset = item.get("asset")
            wallet_balance = float(item.get("balance", 0.0))
            cross_wallet = float(item.get("crossWalletBalance", 0.0))
            unrealized_pnl = float(item.get("crossUnPnl", 0.0))
            available = float(
                item.get("availableBalance")
                or item.get("maxWithdrawAmount")
                or 0.0
            )

            # Tampilkan USDT atau aset lain yang saldonya lebih dari 0
            if asset == "USDT" or wallet_balance > 0:
                found_active_balance = True
                print(f"\n[{asset}]")
                print(f"  Total Saldo (Wallet)    : {wallet_balance:,.4f} {asset}")
                print(f"  Saldo Tersedia (Margin) : {available:,.4f} {asset}")
                print(f"  Saldo Cross Wallet      : {cross_wallet:,.4f} {asset}")
                print(f"  Unrealized PnL          : {unrealized_pnl:+,.4f} {asset}")

        if not found_active_balance:
            print("Semua saldo aset di dompet Futures saat ini bernilai 0.")

    except Exception as e:
        print(f"\n[ERROR] Gagal membaca saldo Live: {e}")

if __name__ == "__main__":
    check_live_futures_balance()