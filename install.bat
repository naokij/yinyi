@echo off
chcp 65001 >nul
echo ==========================================
echo    印忆 (YinYi) - Windows 一键安装
echo ==========================================
echo.

REM 检查 winget
winget --version >nul 2>&1
if errorlevel 1 (
    echo [X] 请先安装 winget
    echo     访问: https://apps.microsoft.com/detail/9NBLGGH4NNS1
    pause
    exit /b 1
)

echo [1/4] 安装 Git...
winget install Git.Git --accept-package-agreements --accept-source-agreements

echo [2/4] 安装 Python...
winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements

echo [3/4] 安装 Node.js...
winget install OpenJS.NodeJS --accept-package-agreements --accept-source-agreements

echo [4/4] 安装 Ollama...
winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements 2>nul || (
    echo     Ollama 需手动下载: https://ollama.com/download/windows
)

echo.
echo ==========================================
echo    安装完成！请重启电脑后运行项目
echo ==========================================
pause
