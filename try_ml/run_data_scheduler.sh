#!/usr/bin/env bash
# Script to run periodic data ingestion in background daemon mode
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRY_ML_DIR="$CURRENT_DIR"
TRADE_PROJECT_DIR="$(dirname "$TRY_ML_DIR")"

# Cari Python Virtual Environment secara otomatis
PYTHON_EXEC=""
if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    PYTHON_EXEC="$VIRTUAL_ENV/bin/python"
elif [ -x "$TRADE_PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON_EXEC="$TRADE_PROJECT_DIR/.venv/bin/python"
elif [ -x "$TRADE_PROJECT_DIR/.venv/bin/python3" ]; then
    PYTHON_EXEC="$TRADE_PROJECT_DIR/.venv/bin/python3"
elif [ -x "$TRY_ML_DIR/.venv/bin/python" ]; then
    PYTHON_EXEC="$TRY_ML_DIR/.venv/bin/python"
elif [ -x "$TRY_ML_DIR/.venv/bin/python3" ]; then
    PYTHON_EXEC="$TRY_ML_DIR/.venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXEC="$(command -v python3)"
else
    echo "❌ Error: Python executable tidak ditemukan!"
    exit 1
fi

LOG_FILE="$CURRENT_DIR/data_pipeline.log"
PID_FILE="$CURRENT_DIR/data_pipeline.pid"

INTERVAL_MINUTES=${1:-30}

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[WARNING] Periodic data pipeline is ALREADY RUNNING (PID: $PID)."
        echo "Logs: tail -f $LOG_FILE"
        exit 0
    else
        rm "$PID_FILE"
    fi
fi

echo "=========================================================="
echo "🚀 STARTING PERIODIC DATA INGESTION SCHEDULER"
echo "=========================================================="
echo "Interval: Every $INTERVAL_MINUTES minutes"
echo "Log file: $LOG_FILE"

nohup "$PYTHON_EXEC" "$CURRENT_DIR/periodic_data_pipeline.py" --loop "$INTERVAL_MINUTES" > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"

echo "[SUCCESS] Data ingestion daemon started with PID: $NEW_PID"
echo "To monitor logs: tail -f $LOG_FILE"
echo "To stop: bash $CURRENT_DIR/stop_data_scheduler.sh"
