#!/usr/bin/env bash
# Script untuk menjalankan Forward Test Daemon di background secara nonstop

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRY_ML_DIR="$(dirname "$SCRIPT_DIR")"
TRADE_PROJECT_DIR="$(dirname "$TRY_ML_DIR")"

# Cari Python Virtual Environment
VENV_PYTHON=""
if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    VENV_PYTHON="$VIRTUAL_ENV/bin/python"
elif [ -x "$TRADE_PROJECT_DIR/.venv/bin/python" ]; then
    VENV_PYTHON="$TRADE_PROJECT_DIR/.venv/bin/python"
elif [ -x "$TRADE_PROJECT_DIR/.venv/bin/python3" ]; then
    VENV_PYTHON="$TRADE_PROJECT_DIR/.venv/bin/python3"
elif [ -x "$TRY_ML_DIR/.venv/bin/python" ]; then
    VENV_PYTHON="$TRY_ML_DIR/.venv/bin/python"
elif [ -x "$TRY_ML_DIR/.venv/bin/python3" ]; then
    VENV_PYTHON="$TRY_ML_DIR/.venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    VENV_PYTHON="$(command -v python3)"
else
    echo "❌ Error: Python executable tidak ditemukan!"
    exit 1
fi

LOG_FILE="$SCRIPT_DIR/output/live_daemon.log"
PID_FILE="$SCRIPT_DIR/output/daemon.pid"

# Cek apakah daemon sudah berjalan
EXISTING_PID=$(pgrep -f "forward_test.py --loop" | head -n 1)
if [ -n "$EXISTING_PID" ]; then
    echo "$EXISTING_PID" > "$PID_FILE"
    echo "⚠️  Forward Test Daemon SUDAH BERJALAN di latar belakang dengan PID $EXISTING_PID."
    echo "📄 File Log : $LOG_FILE"
    echo "🔍 Cek Log  : tail -f crypto_ml_trading/output/live_daemon.log"
    echo "🛑 Stop Bot : bash crypto_ml_trading/stop_daemon.sh"
    exit 0
fi

mkdir -p "$SCRIPT_DIR/output"
echo "Menggunakan Python: $VENV_PYTHON"
echo "🚀 Memulai Forward Test Binance Testnet Daemon di background (setsid)..."

# Jalankan dengan setsid agar proses independen dari sesi terminal
setsid "$VENV_PYTHON" -u "$SCRIPT_DIR/forward_test.py" --loop --live-testnet > "$LOG_FILE" 2>&1 < /dev/null &
sleep 2

NEW_PID=$(pgrep -f "forward_test.py --loop" | head -n 1)
if [ -n "$NEW_PID" ]; then
    echo "$NEW_PID" > "$PID_FILE"
    echo "✅ Daemon berhasil AKTIF dan BERJALAN dengan PID $NEW_PID!"
    echo "📄 File Log : $LOG_FILE"
    echo "🔍 Cek Log  : tail -f crypto_ml_trading/output/live_daemon.log"
    echo "🛑 Stop Bot : bash crypto_ml_trading/stop_daemon.sh"
else
    echo "❌ Gagal memulai daemon! Periksa isi log:"
    cat "$LOG_FILE"
    exit 1
fi
