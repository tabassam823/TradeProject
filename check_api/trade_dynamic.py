import os
import math
from decimal import Decimal
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
SECRET_KEY = os.getenv("BINANCE_TESTNET_SECRET_KEY")

client = Client(API_KEY, SECRET_KEY, testnet=True)

def get_symbol_rules(symbol):
    """Mengambil aturan stepSize, tickSize, minQty, dan minNotional dari Binance"""
    info = client.futures_exchange_info()
    for s in info["symbols"]:
        if s["symbol"] == symbol:
            rules = {
                "min_qty": 0.001,
                "step_size": "0.001",
                "tick_size": "0.01",
                "min_notional": 5.0
            }
            for f in s["filters"]:
                f_type = f.get("filterType")
                if f_type == "LOT_SIZE":
                    rules["min_qty"] = float(f.get("minQty", 0.001))
                    rules["step_size"] = f.get("stepSize", "0.001")
                elif f_type == "PRICE_FILTER":
                    rules["tick_size"] = f.get("tickSize", "0.01")
                elif f_type == "MIN_NOTIONAL":
                    # Mengamankan pembacaan key 'notional' atau 'minNotional'
                    notional_val = f.get("notional") or f.get("minNotional") or 5.0
                    rules["min_notional"] = float(notional_val)
            return rules
    raise ValueError(f"Simbol {symbol} tidak ditemukan.")

def round_step_size(value, step_size_str):
    """Membulatkan angka ke bawah sesuai kelipatan stepSize / tickSize Binance"""
    step = Decimal(str(step_size_str))
    val = Decimal(str(value))
    rounded = (val // step) * step
    return float(rounded)

def round_up_step_size(value, step_size_str):
    """Membulatkan angka KE ATAS agar selalu memenuhi batas minimum notional"""
    step = float(step_size_str)
    precision = len(step_size_str.split(".")[1].rstrip("0")) if "." in step_size_str else 0
    val = math.ceil(value / step) * step
    return round(val, precision)

def get_available_usdt():
    """Mengecek saldo USDT yang siap dipakai untuk membuka posisi"""
    balances = client.futures_account_balance()
    for b in balances:
        if b.get("asset") == "USDT":
            # Mengambil availableBalance dengan fallback yang aman
            avail = (
                b.get("availableBalance")
                or b.get("maxWithdrawAmount")
                or b.get("withdrawAvailable")
                or b.get("crossWalletBalance")
                or b.get("balance")
                or 0.0
            )
            return float(avail)
    return 0.0

def open_dynamic_long(symbol="SOLUSDT", usdt_margin_to_use=None, leverage=10, tp_percent=2.0, sl_percent=1.0):
    try:
        # 1. Ambil aturan trading koin & harga saat ini
        rules = get_symbol_rules(symbol)
        ticker = client.futures_symbol_ticker(symbol=symbol)
        current_price = float(ticker["price"])

        # 2. Hitung batas minimum Quantity (buffer 5% di atas min_notional)
        min_qty_by_notional = (rules["min_notional"] * 1.05) / current_price
        raw_min_qty = max(rules["min_qty"], min_qty_by_notional)
        valid_min_qty = round_up_step_size(raw_min_qty, rules["step_size"])
        min_margin_required = (valid_min_qty * current_price) / leverage

        print(f"=== ATURAN TRADING {symbol} ===")
        print(f"Harga Saat Ini       : ${current_price:,.4f}")
        print(f"Min Notional (Order) : ${rules['min_notional']} USDT")
        print(f"Step Size (Qty)      : {rules['step_size']} | Tick Size (Harga): {rules['tick_size']}")
        print(f"Minimum Quantity     : {valid_min_qty} {symbol.replace('USDT', '')} (Butuh margin min. ~${min_margin_required:.2f} pada {leverage}x)")

        # 3. Tentukan Quantity yang akan dibeli
        if usdt_margin_to_use is None:
            quantity = valid_min_qty
        else:
            target_notional = usdt_margin_to_use * leverage
            quantity = round_step_size(target_notional / current_price, rules["step_size"])
            if quantity < valid_min_qty:
                print(f"[PERINGATAN] Margin ${usdt_margin_to_use} terlalu kecil. Menggunakan minimum quantity: {valid_min_qty}")
                quantity = valid_min_qty

        # 4. Cek Sufficient Margin (Kecukupan Saldo)
        available_usdt = get_available_usdt()
        notional_value = quantity * current_price
        required_margin = notional_value / leverage
        estimated_fee = notional_value * 0.001  # Estimasi buffer fee 0.1%
        total_needed = required_margin + estimated_fee

        print(f"\n=== CEK KECUKUPAN MARGIN ===")
        print(f"Saldo Tersedia       : ${available_usdt:,.2f} USDT")
        print(f"Ukuran Posisi        : {quantity} ({symbol}) senilai ${notional_value:,.2f} USDT")
        print(f"Margin Dibutuhkan    : ${total_needed:,.2f} USDT (Leverage {leverage}x)")

        if available_usdt < total_needed:
            print(f"[GAGAL] Margin tidak cukup! Kurang ${total_needed - available_usdt:,.2f} USDT.")
            return

        # 5. Atur Leverage & Bersihkan Algo Order TP/SL lama
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        client.futures_cancel_all_algo_open_orders(symbol=symbol)

        # 6. Hitung TP & SL sesuai Tick Size koin tersebut
        tp_price = round_step_size(current_price * (1 + tp_percent / 100), rules["tick_size"])
        sl_price = round_step_size(current_price * (1 - sl_percent / 100), rules["tick_size"])

        # 7. Eksekusi Market Order + TP + SL
        print(f"\n[1/3] Membuka Long {quantity} {symbol}...")
        entry = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=FUTURE_ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f" -> Berhasil! Order ID: {entry.get('orderId')}")

        print(f"[2/3] Memasang TP di ${tp_price}...")
        tp = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
            stopPrice=tp_price,
            closePosition=True,
            workingType="MARK_PRICE"
        )
        print(f" -> TP Terpasang! Algo ID: {tp.get('algoId') or tp.get('orderId')}")

        print(f"[3/3] Memasang SL di ${sl_price}...")
        sl = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,
            stopPrice=sl_price,
            closePosition=True,
            workingType="MARK_PRICE"
        )
        print(f" -> SL Terpasang! Algo ID: {sl.get('algoId') or sl.get('orderId')}")

    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    # Eksekusi SOLUSDT dengan ukuran paling minimum
    # open_dynamic_long(symbol="SOLUSDT", usdt_margin_to_use=None, leverage=10, tp_percent=2.0, sl_percent=1.0)

    # Contoh 2: Jika ingin trade ETHUSDT dengan modal margin $15 USDT (Uncomment untuk mencoba)
    open_dynamic_long(symbol="ETHUSDT", usdt_margin_to_use=15, leverage=10, tp_percent=2.0, sl_percent=1.0)