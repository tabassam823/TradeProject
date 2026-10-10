#!/usr/bin/env bash
# ==============================================================================
# Script untuk Menghentikan Forward Testing & Live Scalping Daemon
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/output/scalping_daemon.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "ℹ️  Tidak ada PID file ditemukan. Scalping Daemon tampaknya tidak sedang berjalan."
    exit 0
fi

PID=$(cat "$PID_FILE")
if ps -p "$PID" > /dev/null 2>&1; then
    echo "🛑 Menghentikan Scalping Daemon (PID: $PID)..."
    kill "$PID"
    sleep 2
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  Proses belum berhenti, mengirim sinyal SIGKILL..."
        kill -9 "$PID"
    fi
    echo "✅ Scalping Daemon berhasil dihentikan."
else
    echo "ℹ️  Proses dengan PID $PID sudah tidak aktif."
fi

rm -f "$PID_FILE"
