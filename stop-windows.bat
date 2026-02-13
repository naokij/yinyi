@echo off
chcp 65001 >nul
title 印忆 (YinYi) - 停止服务

echo ==========================================
echo    印忆 (YinYi) - 停止所有服务
echo ==========================================
echo.

echo [*] 正在查找并停止服务...

REM 查找并停止后端进程 (port 8765)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    echo [+] 找到后端进程 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [-] 无法停止后端进程
    ) else (
        echo [+] 后端服务已停止
    )
)

REM 查找并停止前端进程 (port 3000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo [+] 找到前端进程 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [-] 无法停止前端进程
    ) else (
        echo [+] 前端服务已停止
    )
)

REM 关闭相关窗口
taskkill /F /FI "WINDOWTITLE eq 印忆后端*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq 印忆前端*" >nul 2>&1

echo.
echo ==========================================
echo    服务停止完成
echo ==========================================
echo.
pause
