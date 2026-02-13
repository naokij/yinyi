@echo off
chcp 65001 >nul
title 印忆 (YinYi) - 停止服务
setlocal EnableDelayedExpansion

echo ==========================================
echo    印忆 (YinYi) - 停止所有服务
echo ==========================================
echo.

set "BACKEND_PID="
set "FRONTEND_PID="

REM 查找后端进程 (port 8765)
echo [*] 正在查找后端服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    set "BACKEND_PID=%%a"
    echo [✓] 找到后端进程 (PID: %%a)
)

if defined BACKEND_PID (
    echo [*] 正在停止后端服务...
    taskkill /F /PID %BACKEND_PID% >nul 2>&1
    if errorlevel 1 (
        echo [!] 无法停止后端进程
    ) else (
        echo [✓] 后端服务已停止
    )
) else (
    echo [!] 未找到运行中的后端服务
)

REM 查找前端进程 (port 3000)
echo [*] 正在查找前端服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    set "FRONTEND_PID=%%a"
    echo [✓] 找到前端进程 (PID: %%a)
)

if defined FRONTEND_PID (
    echo [*] 正在停止前端服务...
    taskkill /F /PID %FRONTEND_PID% >nul 2>&1
    if errorlevel 1 (
        echo [!] 无法停止前端进程
    ) else (
        echo [✓] 前端服务已停止
    )
) else (
    echo [!] 未找到运行中的前端服务
)

REM 尝试关闭印忆命令窗口
echo [*] 正在关闭印忆窗口...
taskkill /F /FI "WINDOWTITLE eq 印忆后端*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq 印忆前端*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq 印忆 (YinYi)*" >nul 2>&1

echo.
echo ==========================================
echo    服务停止完成
echo ==========================================
echo.

pause
