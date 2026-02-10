@echo off
chcp 65001 >nul
title 印忆 (YinYi) - Windows 启动器

echo ==========================================
echo    印忆 (YinYi) - 照片记忆打印助手
echo    Windows 原生部署版
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或未添加到 PATH
    echo 请安装 Python 3.11+ 并确保勾选 "Add to PATH"
    pause
    exit /b 1
)

echo [✓] Python 已安装

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js 未安装
    echo 请安装 Node.js 18+ https://nodejs.org/
    pause
    exit /b 1
)

echo [✓] Node.js 已安装

REM 检查 Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] Ollama 未运行或未安装
    echo.
    echo 请按以下步骤操作：
    echo 1. 下载安装 Ollama: https://ollama.com/download/windows
    echo 2. 安装完成后，运行: ollama serve
    echo 3. 下载模型: ollama pull qwen3-vl:4b
    echo.
    echo 按任意键打开下载页面...
    pause >nul
    start https://ollama.com/download/windows
    exit /b 1
)

echo [✓] Ollama 正在运行

REM 检查模型
curl -s http://localhost:11434/api/tags | findstr "qwen3-vl" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] Qwen3-VL-4B 模型未找到
    echo 正在下载模型（约 3.3GB，请耐心等待）...
    echo.
    ollama pull qwen3-vl:4b
    if errorlevel 1 (
        echo [错误] 模型下载失败
        pause
        exit /b 1
    )
)

echo [✓] Qwen3-VL-4B 模型已就绪

REM 创建必要目录
if not exist "data" mkdir data
if not exist "exports" mkdir exports
if not exist "photos" mkdir photos

echo.
echo ==========================================
echo    启动服务
echo ==========================================
echo.

REM 启动后端
echo [1/2] 启动后端服务...
start "印忆后端" cmd /k "cd backend && python -m venv venv 2>nul && venv\Scripts\activate && pip install -q -r requirements.txt && python main.py"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 检查后端是否启动
curl -s http://localhost:8765/health >nul 2>&1
if errorlevel 1 (
    echo [!] 后端启动中，等待 5 秒...
    timeout /t 5 /nobreak >nul
)

REM 启动前端
echo [2/2] 启动前端服务...
start "印忆前端" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo ==========================================
echo    服务已启动！
echo ==========================================
echo.
echo 访问地址：
echo   Web 界面: http://localhost:8080
echo   API 文档: http://localhost:8765/docs
echo.
echo 后端日志: 查看 "印忆后端" 窗口
echo 前端日志: 查看 "印忆前端" 窗口
echo.
echo 按任意键打开浏览器...
pause >nul
start http://localhost:8080
