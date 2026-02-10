# 印忆 (YinYi) 依赖安装脚本 - 使用 winget
# 以管理员身份运行 PowerShell，然后执行此脚本

param(
    [switch]$SkipOllama
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  印忆 (YinYi) 依赖安装" -ForegroundColor Cyan
Write-Host "  使用 Windows Package Manager (winget)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 winget 是否安装
Write-Host "[1/6] 检查 winget..." -ForegroundColor Yellow
$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    Write-Host "❌ winget 未安装" -ForegroundColor Red
    Write-Host "请安装 App Installer：" -ForegroundColor Yellow
    Write-Host "https://apps.microsoft.com/detail/9NBLGGH4NNS1" -ForegroundColor Cyan
    exit 1
}
Write-Host "✅ winget 已安装" -ForegroundColor Green
Write-Host ""

# 更新 winget 源
Write-Host "[2/6] 更新 winget 源..." -ForegroundColor Yellow
winget source update
Write-Host "✅ 源已更新" -ForegroundColor Green
Write-Host ""

# 安装 Git
Write-Host "[3/6] 安装 Git..." -ForegroundColor Yellow
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    Write-Host "✅ Git 已安装：$(git --version)" -ForegroundColor Green
} else {
    winget install --id Git.Git --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Git 安装成功" -ForegroundColor Green
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "❌ Git 安装失败" -ForegroundColor Red
    }
}
Write-Host ""

# 安装 Python
Write-Host "[4/6] 安装 Python 3.11..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python 已安装：$pythonVersion" -ForegroundColor Green
    if ($pythonVersion -notmatch "3\.(11|12|13)") {
        Write-Host "⚠️  建议升级到 Python 3.11+" -ForegroundColor Yellow
    }
} else {
    winget install --id Python.Python.3.11 --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python 3.11 安装成功" -ForegroundColor Green
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "❌ Python 安装失败" -ForegroundColor Red
    }
}
Write-Host ""

# 安装 Node.js
Write-Host "[5/6] 安装 Node.js 20..." -ForegroundColor Yellow
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVersion = node --version
    Write-Host "✅ Node.js 已安装：$nodeVersion" -ForegroundColor Green
} else {
    winget install --id OpenJS.NodeJS --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Node.js 安装成功" -ForegroundColor Green
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "❌ Node.js 安装失败" -ForegroundColor Red
    }
}
Write-Host ""

# 安装 Ollama（可选）
if (-not $SkipOllama) {
    Write-Host "[6/6] 安装 Ollama..." -ForegroundColor Yellow
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollama) {
        Write-Host "✅ Ollama 已安装：$(ollama --version)" -ForegroundColor Green
    } else {
        # Ollama 可能不在 winget 官方源中，尝试安装
        try {
            winget install --id Ollama.Ollama --source winget --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Ollama 安装成功" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Ollama 可能不在 winget 中，请手动安装：" -ForegroundColor Yellow
                Write-Host "     https://ollama.com/download/windows" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "⚠️  Ollama 请手动安装：" -ForegroundColor Yellow
            Write-Host "     https://ollama.com/download/windows" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "[6/6] 跳过 Ollama 安装（使用 --SkipOllama 参数）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  依赖安装完成！" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请重启 PowerShell 以使用新安装的软件" -ForegroundColor Yellow
Write-Host ""
Write-Host "下一步：" -ForegroundColor Green
Write-Host "  1. 重启 PowerShell" -ForegroundColor White
Write-Host "  2. 克隆项目：git clone https://github.com/naokij/yinyi.git" -ForegroundColor White
Write-Host "  3. 下载模型：ollama pull qwen3-vl:4b" -ForegroundColor White
Write-Host "  4. 运行：.\start-windows.bat" -ForegroundColor White
Write-Host ""

# 验证安装
Write-Host "安装验证：" -ForegroundColor Green
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ Git: $(git --version)" -ForegroundColor White
}
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ Python: $(python --version)" -ForegroundColor White
}
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ Node.js: $(node --version)" -ForegroundColor White
}
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ Ollama: $(ollama --version)" -ForegroundColor White
}
Write-Host ""
