@echo off
chcp 65001 >nul
title 印忆 (YinYi) - Windows 启动器
setlocal EnableDelayedExpansion

echo ==========================================
echo    印忆 (YinYi) - 照片记忆打印助手
echo    Windows 原生部署版
echo ==========================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

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
    (
        echo PHOTOS_DIR=Z:\Photos
        echo EXPORTS_DIR=.\exports
        echo AI_BACKEND=iflow
        echo IFLOW_API_KEY=your-api-key-here
        echo IFLOW_MODEL=qwen3-vl-plus
        echo IFLOW_API_URL=https://api.iflow.cn/v1/chat/completions
    ) > .env
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

REM 启动后端服务
echo [1/2] 启动后端服务...
echo     正在打开新窗口启动后端...

REM 创建后端启动脚本
echo @echo off > "%TEMP%\yinyi_backend.bat"
echo chcp 65001 ^>nul >> "%TEMP%\yinyi_backend.bat"
echo title 印忆后端 >> "%TEMP%\yinyi_backend.bat"
echo cd /d "%SCRIPT_DIR%backend" >> "%TEMP%\yinyi_backend.bat"
echo. >> "%TEMP%\yinyi_backend.bat"
echo if not exist venv ( >> "%TEMP%\yinyi_backend.bat"
echo     echo 正在创建虚拟环境... >> "%TEMP%\yinyi_backend.bat"
echo     python -m venv venv >> "%TEMP%\yinyi_backend.bat"
echo ) >> "%TEMP%\yinyi_backend.bat"
echo. >> "%TEMP%\yinyi_backend.bat"
echo echo 正在激活虚拟环境... >> "%TEMP%\yinyi_backend.bat"
echo call venv\Scripts\activate.bat >> "%TEMP%\yinyi_backend.bat"
echo. >> "%TEMP%\yinyi_backend.bat"
echo echo 正在安装依赖... >> "%TEMP%\yinyi_backend.bat"
echo pip install -q -r requirements.txt >> "%TEMP%\yinyi_backend.bat"
echo. >> "%TEMP%\yinyi_backend.bat"
echo echo 正在启动后端服务... >> "%TEMP%\yinyi_backend.bat"
echo python main.py >> "%TEMP%\yinyi_backend.bat"
echo pause >> "%TEMP%\yinyi_backend.bat"

start "印忆后端" cmd /k "%TEMP%\yinyi_backend.bat"

REM 等待后端启动
echo     等待后端启动...
ping -n 4 127.0.0.1 >nul 2>&1

REM 检查后端是否启动
curl -s http://localhost:8765/health >nul 2>&1
if errorlevel 1 (
    echo     后端启动中，再等待 5 秒...
    ping -n 6 127.0.0.1 >nul 2>&1
)

REM 启动前端服务
echo [2/2] 启动前端服务...
echo     正在打开新窗口启动前端...

REM 创建前端启动脚本
echo @echo off > "%TEMP%\yinyi_frontend.bat"
echo chcp 65001 ^>nul >> "%TEMP%\yinyi_frontend.bat"
echo title 印忆前端 >> "%TEMP%\yinyi_frontend.bat"
echo cd /d "%SCRIPT_DIR%frontend" >> "%TEMP%\yinyi_frontend.bat"
echo. >> "%TEMP%\yinyi_frontend.bat"
echo echo 正在安装前端依赖... >> "%TEMP%\yinyi_frontend.bat"
echo call npm install >> "%TEMP%\yinyi_frontend.bat"
echo. >> "%TEMP%\yinyi_frontend.bat"
echo echo 正在启动前端服务... >> "%TEMP%\yinyi_frontend.bat"
echo npm run dev >> "%TEMP%\yinyi_frontend.bat"
echo pause >> "%TEMP%\yinyi_frontend.bat"

start "印忆前端" cmd /k "%TEMP%\yinyi_frontend.bat"

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

REM 尝试打开浏览器
start http://localhost:8080
