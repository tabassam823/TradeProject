#!/usr/bin/env bash
# ==============================================================================
# Script untuk Memeriksa Status Live Forward Testing Scalping
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/output/scalping_daemon.pid"
STATE_FILE="$SCRIPT_DIR/output/forward_test_state.json"
LOG_FILE="$SCRIPT_DIR/output/scalping_forward_test.log"
TRADES_FILE="$SCRIPT_DIR/output/forward_test_trades.csv"

echo "======================================================================"
echo "⚡ STATUS LIVE FORWARD TESTING: 5M FUTURES SCALPING (SOL-USD)"
echo "======================================================================"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🟢 Daemon Status : RUNNING (PID: $PID)"
    else
        echo "🔴 Daemon Status : STOPPED (Stale PID: $PID)"
    fi
else
    echo "⚪ Daemon Status : STOPPED (No Active PID)"
fi

if [ -f "$STATE_FILE" ]; then
    echo -e "\n📋 Current State Summary:"
    python3 -c "
import json
with open('$STATE_FILE') as f:
    s = json.load(f)
for k, v in s.items():
    if isinstance(v, float):
        print(f'   {k:<20}: {v:,.2f}')
    else:
        print(f'   {k:<20}: {v}')
"
fi

if [ -f "$TRADES_FILE" ]; then
    TRADES_COUNT=$(tail -n +2 "$TRADES_FILE" | wc -l)
    echo -e "\n📊 Total Closed Forward Trades: $TRADES_COUNT"
    if [ "$TRADES_COUNT" -gt 0 ]; then
        echo "Last 3 Trades:"
        head -n 1 "$TRADES_FILE"
        tail -n 3 "$TRADES_FILE"
    fi
fi

if [ -f "$LOG_FILE" ]; then
    echo -e "\n📜 Recent Activity Logs (Last 10 lines):"
    tail -n 10 "$LOG_FILE"
fi
echo "======================================================================"
