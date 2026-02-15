@echo off
chcp 65001 >nul
title YinYi - Windows Launcher

echo ==========================================
echo    YinYi - Photo Memory Printer
echo    Windows Native Deployment
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed or not in PATH
    echo Please install Python 3.11+ and check "Add to PATH"
    pause
    exit /b 1
)
echo [OK] Python installed

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not installed
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js installed

REM Check .env config
if not exist ".env" (
    echo.
    echo [!] .env file not found, creating default config...
    echo PHOTOS_DIR=Z:\Photos > .env
    echo EXPORTS_DIR=.\exports >> .env
    echo AI_BACKEND=iflow >> .env
    echo IFLOW_API_KEY=your-api-key-here >> .env
    echo IFLOW_MODEL=qwen3-vl-plus >> .env
    echo IFLOW_API_URL=https://api.iflow.cn/v1/chat/completions >> .env
    echo.
    echo [!] Please edit .env file and add your API Key
    echo Get API Key: https://platform.iflow.cn
    notepad .env
    pause
)
echo [OK] .env config ready

REM Create directories
if not exist "backend\data" mkdir "backend\data"
if not exist "backend\data\cache\heic" mkdir "backend\data\cache\heic"
if not exist "backend\exports" mkdir "backend\exports"
if not exist "frontend\public" mkdir "frontend\public"
echo [OK] Directories created

echo.
echo ==========================================
echo    Starting Services
echo ==========================================
echo.

REM Start Backend
echo [1/2] Starting Backend Service...
start "YinYi Backend" cmd /k "cd backend && python -m venv venv 2>nul && venv\Scripts\activate.bat && pip install -q -r requirements.txt && python main.py"

echo     Waiting for backend...
ping 127.0.0.1 -n 4 >nul

REM Check backend
curl -s http://localhost:8765/health >nul 2>&1
if errorlevel 1 (
    echo     Backend starting, wait 5 more seconds...
    ping 127.0.0.1 -n 6 >nul
)

REM Start Frontend
echo [2/2] Starting Frontend Service...
start "YinYi Frontend" cmd /k "cd frontend && npm install && npm run dev -- --host 0.0.0.0"

echo.
echo ==========================================
echo    Services Started!
echo ==========================================
echo.
echo Access URLs:
echo   Local:   http://localhost:3000
echo   LAN:     http://%COMPUTERNAME%:3000  (replace %%COMPUTERNAME%% with your PC's IP)
echo   API:     http://localhost:8765/docs
echo.
echo To access from other devices in LAN:
echo   1. Check your PC's IP: ipconfig
echo   2. Use http://[YOUR_IP]:3000
echo.
echo Backend Log: Check 'YinYi Backend' window
echo Frontend Log: Check 'YinYi Frontend' window
echo.
echo AI Mode: Iflow API
echo For local Ollama, edit .env: AI_BACKEND=ollama
echo.
echo Press any key to open browser... (or close this window)
pause >nul
start http://localhost:3000
