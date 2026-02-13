@echo off
chcp 65001 >nul
title 印忆 (YinYi) - 停止服务

echo ==========================================
echo    印忆 (YinYi) - 停止所有服务
echo ==========================================
echo.

REM 查找并终止后端进程
echo [*] 正在停止后端服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    set BACKEND_PID=%%a
)

if defined BACKEND_PID (
    taskkill /F /PID %BACKEND_PID% >nul 2>&1
    if errorlevel 1 (
        echo [!] 无法停止后端进程 (PID: %BACKEND_PID%)
    ) else (
        echo [✓] 后端服务已停止 (PID: %BACKEND_PID%)
    )
) else (
    echo [!] 未找到运行中的后端服务
)

REM 查找并终止前端进程 (Node.js on port 3000)
echo [*] 正在停止前端服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    set FRONTEND_PID=%%a
)

if defined FRONTEND_PID (
    taskkill /F /PID %FRONTEND_PID% >nul 2>&1
    if errorlevel 1 (
        echo [!] 无法停止前端进程 (PID: %FRONTEND_PID%)
    ) else (
        echo [✓] 前端服务已停止 (PID: %FRONTEND_PID%)
    )
) else (
    echo [!] 未找到运行中的前端服务
)

REM 终止所有相关命令窗口
echo [*] 正在关闭印忆窗口...
taskkill /F /FI "WINDOWTITLE eq 印忆后端*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq 印忆前端*" >nul 2>&1

echo.
echo ==========================================
echo    服务已全部停止
echo ==========================================
echo.

REM 可选：按任意键退出
pause >nul
