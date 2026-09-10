@echo off
REM =============================================
REM STARTUP SCRIPT FOR WINDOWS (TradeProject Futures)
REM =============================================
REM Usage: double-click start_wds.bat or run in CMD
REM
REM This script sets up the environment and starts
REM the trading engine on Windows.
REM =============================================

echo =============================================
echo   TradeProject Futures Trading Engine
echo   Starting...
echo =============================================
echo.

REM Check for .env_wds
if not exist ".env_wds" (
    echo [WARNING] .env_wds not found. Copying .env_wds.example...
    copy .env_wds.example .env_wds
    echo [INFO] Please edit .env_wds with your Binance API credentials!
    echo.
    pause
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.11+.
    echo [ERROR] Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check ccxt
python -c "import ccxt" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    pip install -r requirements_wds.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM Check for placeholder API keys
findstr /i "your_api_key_here" .env_wds >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] .env_wds still has placeholder API keys!
    echo [WARNING] Please edit .env_wds and add your real Binance API keys.
    echo.
    pause
)

echo.
echo =============================================
echo   Starting Trading Engine...
echo =============================================
echo.

REM Run the scheduler
python run_scheduler_wds.py

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo [ERROR] Trading engine crashed. Check logs above.
    pause
)
