@echo off
chcp 65001 >nul
title YinYi - Stop Services

echo ==========================================
echo    YinYi - Stop All Services
echo ==========================================
echo.

echo [*] Finding and stopping services...

REM Find and stop backend (port 8765)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    echo [+] Found backend process (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [-] Failed to stop backend
    ) else (
        echo [+] Backend stopped
    )
)

REM Find and stop frontend (port 3000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo [+] Found frontend process (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [-] Failed to stop frontend
    ) else (
        echo [+] Frontend stopped
    )
)

REM Close windows
taskkill /F /FI "WINDOWTITLE eq YinYi Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq YinYi Frontend*" >nul 2>&1

echo.
echo ==========================================
echo    Services Stopped
echo ==========================================
echo.
pause
