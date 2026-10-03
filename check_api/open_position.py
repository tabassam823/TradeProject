import os
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv

# 1. Muat kredensial Testnet
load_dotenv()
API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
SECRET_KEY = os.getenv("BINANCE_TESTNET_SECRET_KEY")

client = Client(API_KEY, SECRET_KEY, testnet=True)

def open_long_with_tpsl(symbol="SOLUSDT", quantity=0.002, leverage=10, tp_percent=2.0, sl_percent=1.0):
    try:
        # 2. Atur Leverage
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        print(f"[INFO] Leverage untuk {symbol} diatur ke {leverage}x")

        # 3. Batalkan semua Algo Order (TP/SL) lama yang masih menggantung agar tidak error -4130
        print(f"[INFO] Membersihkan antrean TP/SL lama pada {symbol}...")
        client.futures_cancel_all_algo_open_orders(symbol=symbol)

        # 4. Ambil harga pasar saat ini
        ticker = client.futures_symbol_ticker(symbol=symbol)
        current_price = float(ticker["price"])
        print(f"[INFO] Harga {symbol} saat ini: ${current_price:,.2f}")

        # 5. Hitung harga Take Profit dan Stop Loss (1 desimal untuk BTCUSDT)
        tp_price = round(current_price * (1 + tp_percent / 100), 1)
        sl_price = round(current_price * (1 - sl_percent / 100), 1)

        # 6. ORDER 1: Buka Posisi Long dengan Market Order
        print("\n[1/3] Mengirim Market Order (Long)...")
        entry_order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=FUTURE_ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f" -> Berhasil masuk posisi! Order ID: {entry_order.get('orderId')}")

        # 7. ORDER 2: Pasang Take Profit
        print(f"[2/3] Memasang Take Profit di harga ${tp_price:,.1f}...")
        tp_order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
            stopPrice=tp_price,
            closePosition=True,
            workingType="MARK_PRICE"
        )
        tp_id = tp_order.get("algoId") or tp_order.get("orderId")
        print(f" -> TP terpasang! Algo ID: {tp_id}")

        # 8. ORDER 3: Pasang Stop Loss
        print(f"[3/3] Memasang Stop Loss di harga ${sl_price:,.1f}...")
        sl_order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,
            stopPrice=sl_price,
            closePosition=True,
            workingType="MARK_PRICE"
        )
        sl_id = sl_order.get("algoId") or sl_order.get("orderId")
        print(f" -> SL terpasang! Algo ID: {sl_id}")

    except Exception as e:
        print(f"\n[ERROR] Gagal mengeksekusi order: {e}")

if __name__ == "__main__":
    open_long_with_tpsl(
        symbol="ETHUSDT",
        quantity=20,
        leverage=10,
        tp_percent=2.0,
        sl_percent=1.0
    )