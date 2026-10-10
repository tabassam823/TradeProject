#!/usr/bin/env bash
# ==============================================================================
# Script untuk Menjalankan Forward Testing & Live Scalping Daemon (SOL Futures)
# ==============================================================================

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

PID_FILE="$SCRIPT_DIR/output/scalping_daemon.pid"
LOG_FILE="$SCRIPT_DIR/output/scalping_forward_test.log"

mkdir -p "$SCRIPT_DIR/output"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  Scalping Forward Test Daemon sudah aktif (PID: $PID)."
        echo "Gunakan './stop_scalping_daemon.sh' untuk menghentikan daemon terlebih dahulu."
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

echo "🚀 Memulai Forward Test Daemon 5m Futures Scalping (SOL-USD)..."
echo "Log file: $LOG_FILE"

nohup "$VENV_PYTHON" -u "$SCRIPT_DIR/forward_test.py" --mode loop --interval 60 --testnet > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"

echo "✅ Daemon BERHASIL dijalankan di background (PID: $NEW_PID)."
echo "Untuk melihat log aktivitas: tail -f $LOG_FILE"
echo "Untuk memeriksa status: ./check_scalping_status.sh"
