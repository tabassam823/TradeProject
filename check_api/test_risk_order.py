"""
Script untuk membuka posisi LONG uji coba dengan resiko SL tepat $1 USD di Binance Futures Testnet.
"""
import os
import math
from decimal import Decimal
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *

load_dotenv()
API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
SECRET_KEY = os.getenv("BINANCE_TESTNET_SECRET_KEY") or os.getenv("BINANCE_TESTNET_API_SECRET")

client = Client(API_KEY, SECRET_KEY, testnet=True)

def open_test_risk_position(symbol="SOLUSDT", risk_dollars=1.0, leverage=10, reward_ratio=2.0):
    print("=" * 65)
    print(f"🎯 MEMBUKA ORDER UJI COBA DENGAN RISIKO TEPAT ${risk_dollars:.2f} USD")
    print("=" * 65)
    
    # 1. Ambil aturan simbol & harga pasar
    info = client.futures_exchange_info()
    rules = {"min_qty": 0.01, "step_size": "0.01", "tick_size": "0.01", "min_notional": 5.0}
    for s in info["symbols"]:
        if s["symbol"] == symbol:
            for f in s["filters"]:
                if f.get("filterType") == "LOT_SIZE":
                    rules["min_qty"] = float(f.get("minQty", 0.01))
                    rules["step_size"] = f.get("stepSize", "0.01")
                elif f.get("filterType") == "PRICE_FILTER":
                    rules["tick_size"] = f.get("tickSize", "0.01")
                elif f.get("filterType") == "MIN_NOTIONAL":
                    notional_val = f.get("notional") or f.get("minNotional") or 5.0
                    rules["min_notional"] = float(notional_val)

    ticker = client.futures_symbol_ticker(symbol=symbol)
    current_price = float(ticker["price"])
    
    # 2. Tentukan ukuran quantity yang aman di atas min_notional
    # Untuk SOL (~$109), 0.1 SOL = ~$10.9 notional (memenuhi syarat min_notional $5)
    target_qty = 0.1
    min_qty_by_notional = (rules["min_notional"] * 1.10) / current_price
    raw_qty = max(rules["min_qty"], min_qty_by_notional, target_qty)
    
    step = Decimal(str(rules["step_size"]))
    quantity = float((Decimal(str(raw_qty)) // step) * step)
    
    # 3. Hitung SL Distance agar Loss = risk_dollars
    # Risk = quantity * sl_distance => sl_distance = risk_dollars / quantity
    sl_dist = risk_dollars / quantity
    tp_dist = sl_dist * reward_ratio
    
    tick = Decimal(str(rules["tick_size"]))
    sl_price = float((Decimal(str(current_price - sl_dist)) // tick) * tick)
    tp_price = float((Decimal(str(current_price + tp_dist)) // tick) * tick)
    
    notional_val = quantity * current_price
    required_margin = notional_val / leverage
    
    print(f"Simbol           : {symbol}")
    print(f"Harga Entry Saat : ${current_price:,.2f}")
    print(f"Ukuran Posisi    : {quantity} SOL (Nilai Kontrak: ${notional_val:,.2f} USDT)")
    print(f"Leverage         : {leverage}x (Margin Terpakai: ${required_margin:,.2f} USDT)")
    print(f"Harga Stop Loss  : ${sl_price:,.2f} (Jarak: -${sl_dist:.2f} | Maksimum Rugi: -${risk_dollars:.2f} USD)")
    print(f"Harga Take Profit: ${tp_price:,.2f} (Jarak: +${tp_dist:.2f} | Potensi Untung: +${risk_dollars * reward_ratio:.2f} USD)")
    print("-" * 65)
    
    # 4. Set Leverage & Bersihkan algo lama
    client.futures_change_leverage(symbol=symbol, leverage=leverage)
    try:
        client.futures_cancel_all_algo_open_orders(symbol=symbol)
    except Exception:
        pass
        
    # 5. Order 1: Market Entry BUY
    print("\n[1/3] Mengirim Market Order (BUY)...")
    entry_order = client.futures_create_order(
        symbol=symbol,
        side=SIDE_BUY,
        type=FUTURE_ORDER_TYPE_MARKET,
        quantity=quantity
    )
    entry_id = entry_order.get('orderId')
    print(f"  -> ✅ Sukses Masuk Posisi! Order ID: {entry_id} | Status: {entry_order.get('status')}")
    
    # 6. Order 2: Take Profit Market (closePosition=True)
    print(f"[2/3] Memasang Take Profit di ${tp_price:,.2f}...")
    tp_order = client.futures_create_order(
        symbol=symbol,
        side=SIDE_SELL,
        type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
        stopPrice=tp_price,
        closePosition=True,
        workingType="MARK_PRICE"
    )
    tp_id = tp_order.get('algoId') or tp_order.get('orderId')
    print(f"  -> ✅ TP Terpasang di Bursa! ID: {tp_id}")
    
    # 7. Order 3: Stop Loss Market (closePosition=True)
    print(f"[3/3] Memasang Stop Loss di ${sl_price:,.2f}...")
    sl_order = client.futures_create_order(
        symbol=symbol,
        side=SIDE_SELL,
        type=FUTURE_ORDER_TYPE_STOP_MARKET,
        stopPrice=sl_price,
        closePosition=True,
        workingType="MARK_PRICE"
    )
    sl_id = sl_order.get('algoId') or sl_order.get('orderId')
    print(f"  -> ✅ SL Terpasang di Bursa! ID: {sl_id}")
    
    print("\n" + "=" * 65)
    print("🎉 SEMUA ORDER SUDAH AKTIF DI BINANCE FUTURES TESTNET!")
    print("Silakan buka Binance Futures Testnet UI di browser untuk melihat:")
    print("1. Tab 'Positions': Posisi SOLUSDT 0.10 Long")
    print("2. Tab 'Open Orders' / 'TP/SL': Order Take Profit & Stop Loss aktif")
    print("=" * 65)
    
    return entry_order, tp_order, sl_order

if __name__ == "__main__":
    open_test_risk_position(symbol="SOLUSDT", risk_dollars=1.0, leverage=10, reward_ratio=2.0)
