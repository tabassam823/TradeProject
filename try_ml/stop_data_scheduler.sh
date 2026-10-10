#!/usr/bin/env bash
# Script to safely stop periodic data ingestion daemon
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$CURRENT_DIR/data_pipeline.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[STOPPING] Killing data pipeline process PID: $PID..."
        kill "$PID"
        sleep 1
        if ps -p "$PID" > /dev/null 2>&1; then
            kill -9 "$PID"
        fi
        echo "[STOPPED] Data ingestion scheduler halted."
    else
        echo "[INFO] Process $PID is not running."
    fi
    rm -f "$PID_FILE"
else
    echo "[INFO] No running data ingestion daemon found (pid file does not exist)."
fi
