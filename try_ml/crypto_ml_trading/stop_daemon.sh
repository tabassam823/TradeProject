#!/usr/bin/env bash
# Script untuk menghentikan Forward Test Daemon yang sedang berjalan

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/output/daemon.pid"

STOPPED=0
# Cek berdasarkan PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 Menghentikan Forward Test Daemon (PID $PID)..."
        kill "$PID"
        STOPPED=1
    fi
    rm -f "$PID_FILE"
fi

# Cek apakah masih ada proses forward_test.py --loop
REMAINING_PIDS=$(pgrep -f "forward_test.py --loop")
if [ -n "$REMAINING_PIDS" ]; then
    echo "🛑 Menghentikan sisa proses daemon ($REMAINING_PIDS)..."
    kill $REMAINING_PIDS 2>/dev/null
    STOPPED=1
fi

if [ $STOPPED -eq 1 ]; then
    echo "✅ Forward Test Daemon berhasil dihentikan."
else
    echo "ℹ️  Tidak ada Forward Test Daemon yang sedang berjalan."
fi
