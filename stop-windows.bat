@echo off
chcp 65001 >nul
title YinYi - Stop Services

echo ==========================================
echo    YinYi - Stop All Services
echo ==========================================
echo.

REM Method 1: Find by port and kill
echo [*] Method 1: Stopping by port...

REM Stop backend (port 8765)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    echo [+] Found backend on port 8765 (PID: %%a)
    taskkill /F /T /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [-] Failed to stop PID %%a
    ) else (
        echo [+] Backend stopped
    )
)

REM Stop frontend (port 3000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo [+] Found frontend on port 3000 (PID: %%a)
    taskkill /F /T /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [-] Failed to stop PID %%a
    ) else (
        echo [+] Frontend stopped
    )
)

REM Method 2: Kill by window title
echo [*] Method 2: Stopping by window title...
taskkill /F /FI "WINDOWTITLE eq YinYi Backend*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq YinYi Frontend*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq YinYi*" /T >nul 2>&1

REM Method 3: Use PowerShell for more reliable termination
echo [*] Method 3: Using PowerShell...
powershell -Command "Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" 2>nul
powershell -Command "Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" 2>nul

REM Method 4: Kill Python and Node processes (last resort)
echo [*] Method 4: Checking for leftover processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *YinYi*" >nul 2>&1
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *YinYi*" >nul 2>&1

REM Verify services are stopped
echo [*] Verifying services stopped...
timeout /t 2 /nobreak >nul 2>&1

set BACKEND_RUNNING=0
set FRONTEND_RUNNING=0

netstat -ano | findstr ":8765" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 set BACKEND_RUNNING=1

netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 set FRONTEND_RUNNING=1

echo.
echo ==========================================
if %BACKEND_RUNNING%==0 (
    if %FRONTEND_RUNNING%==0 (
        echo    All Services Stopped Successfully
    ) else (
        echo    Backend stopped, Frontend still running
    )
) else (
    if %FRONTEND_RUNNING%==0 (
        echo    Backend still running, Frontend stopped
    ) else (
        echo    WARNING: Services may still be running
        echo    Try running as Administrator
    )
)
echo ==========================================
echo.
pause
