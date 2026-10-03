import os
from binance.client import Client
from dotenv import load_dotenv

# Muat kredensial dari .env
load_dotenv()
API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
SECRET_KEY = os.getenv("BINANCE_TESTNET_SECRET_KEY")

# Inisialisasi client dengan opsi testnet=True
client = Client(API_KEY, SECRET_KEY, testnet=True)

def get_futures_balance(target_asset="USDT"):
    try:
        # Mengambil seluruh data saldo di wallet USDT-M Futures
        balances = client.futures_account_balance()
        
        for item in balances:
            if item["asset"] == target_asset:
                print(f"--- Saldo Akun Futures ({target_asset}) ---")
                print(f"Total Saldo (Wallet Balance)   : {float(item['balance']):,.4f} {target_asset}")
                print(f"Saldo Tersedia (Cross Wallet)  : {float(item['crossWalletBalance']):,.4f} {target_asset}")
                print(f"P/L Belum Terealisasi          : {float(item['crossUnPnl']):,.4f} {target_asset}")
                print(f"Batas Penarikan Maksimal       : {float(item['withdrawAvailable']):,.4f} {target_asset}")
                return item
        
        print(f"Aset {target_asset} tidak ditemukan di dompet Futures.")
        return None

    except Exception as e:
        print(f"Terjadi kesalahan saat memanggil API: {e}")

if __name__ == "__main__":
    get_futures_balance("USDT")