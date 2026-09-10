#!/bin/bash
# =============================================
# STARTUP SCRIPT FOR WINDOWS/LINUX (TradeProject Futures)
# =============================================
# Usage (Linux):   ./start_wds.sh
# Usage (Windows): start_wds.bat
#
# This script sets up the environment and starts the trading engine.
# =============================================

echo "============================================="
echo "  TradeProject Futures Trading Engine"
echo "  Starting..."
echo "============================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "[OS] Windows detected"
    PYTHON=python3
    ACTIVATE=""
    SCHEDULER="run_scheduler_wds.py"
else
    echo "[OS] Linux/Mac detected"
    PYTHON=python3
    ACTIVATE=""
    SCHEDULER="run_scheduler_wds.py"
fi

# Check if .env_wds exists, if not copy .env.example
if [ ! -f ".env_wds" ]; then
    echo "[WARNING] .env_wds not found. Copying .env_wds.example..."
    cp .env_wds.example .env_wds
    echo "[INFO] Please edit .env_wds with your Binance API credentials!"
    echo ""
    read -p "Press Enter after editing .env_wds..."
fi

# Install dependencies if needed
if ! python3 -c "import ccxt" 2>/dev/null; then
    echo "[SETUP] Installing dependencies..."
    pip install -r requirements_wds.txt
fi

# Verify API credentials
if grep -q "your_api_key_here" .env_wds 2>/dev/null; then
    echo "[WARNING] .env_wds still has placeholder API keys!"
    echo "[WARNING] Please edit .env_wds and add your real Binance API keys."
    echo ""
fi

echo ""
echo "============================================="
echo "  Starting Trading Engine..."
echo "============================================="
echo ""

# Run the scheduler
$PYTHON $SCHEDULER
