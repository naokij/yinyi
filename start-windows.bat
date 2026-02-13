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

REM 检查 .env 配置
if not exist ".env" (
    echo.
    echo [!] .env 配置文件不存在，正在创建默认配置...
    echo PHOTOS_DIR=Z:\Photos > .env
    echo EXPORTS_DIR=.\exports >> .env
    echo AI_BACKEND=iflow >> .env
    echo IFLOW_API_KEY=your-api-key-here >> .env
    echo IFLOW_MODEL=qwen3-vl-plus >> .env
    echo IFLOW_API_URL=https://api.iflow.cn/v1/chat/completions >> .env
    echo.
    echo [!] 请编辑 .env 文件，填入您的心流 API Key
    echo 获取 API Key: https://platform.iflow.cn
    notepad .env
    pause
)
echo [✓] .env 配置文件已就绪

REM 创建必要目录
if not exist "backend\data" mkdir "backend\data"
if not exist "backend\data\cache\heic" mkdir "backend\data\cache\heic"
if not exist "backend\exports" mkdir "backend\exports"
if not exist "frontend\public" mkdir "frontend\public"
echo [✓] 目录结构已创建

echo.
echo ==========================================
echo    启动服务
echo ==========================================
echo.

REM 启动后端
echo [1/2] 启动后端服务...
start "印忆后端" cmd /k "cd backend && python -m venv venv 2>nul && venv\Scripts\activate.bat && pip install -q -r requirements.txt && python main.py"

echo     等待后端启动...
ping 127.0.0.1 -n 4 >nul

REM 检查后端是否启动
curl -s http://localhost:8765/health >nul 2>&1
if errorlevel 1 (
    echo     后端启动中，再等待 5 秒...
    ping 127.0.0.1 -n 6 >nul
)

REM 启动前端
echo [2/2] 启动前端服务...
start "印忆前端" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo ==========================================
echo    服务启动中...
echo ==========================================
echo.
echo 访问地址：
echo   Web 界面: http://localhost:8080
echo   API 文档: http://localhost:8765/docs
echo.
echo 后端日志: 查看 "印忆后端" 窗口
echo 前端日志: 查看 "印忆前端" 窗口
echo.
echo AI 模式: 心流 API (iflow)
echo 如需使用本地 Ollama，请修改 .env 文件：
echo   AI_BACKEND=ollama
echo.
echo 按任意键打开浏览器... (或关闭此窗口)
pause >nul
start http://localhost:8080
