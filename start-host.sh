#!/bin/bash

# 印忆 (YinYi) 宿主机方案启动脚本
# 使用本机 Ollama + Qwen3-VL-4B（支持 Apple Metal 加速）

echo "🚀 启动印忆服务 (宿主机方案)..."
echo ""

# 检查是否为 Apple Silicon
if [[ $(uname -m) == "arm64" ]]; then
    echo "✅ 检测到 Apple Silicon Mac"
    echo "💡 此方案将使用本机 Ollama + Qwen3-VL-4B"
    echo "   支持 Metal GPU 加速"
    echo ""
fi

# 检查 Ollama 是否安装
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama 未安装"
    echo ""
    echo "📥 请安装 Ollama："
    echo "   方法1: 运行以下命令"
    echo "   curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "   方法2: 从官网下载"
    echo "   https://ollama.com/download"
    echo ""
    exit 1
fi

echo "✅ Ollama 已安装"

# 检查 Ollama 版本（Qwen3-VL 需要 0.12.7+）
OLLAMA_VERSION=$(ollama --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
echo "   版本: $OLLAMA_VERSION"

# 检查 Ollama 是否运行
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "🔄 启动 Ollama 服务..."
    ollama serve &
    OLLAMA_PID=$!
    
    # 等待 Ollama 启动
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            echo "✅ Ollama 已启动"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        echo ""
        echo "❌ Ollama 启动失败"
        exit 1
    fi
else
    echo "✅ Ollama 正在运行"
fi

# 检查模型
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3-vl:4b}"
if ! ollama list | grep -q "qwen3-vl:4b"; then
    echo "📥 下载 Qwen3-VL-4B 模型（约 3.3GB）..."
    echo "   这可能需要 10-30 分钟，请耐心等待..."
    ollama pull qwen3-vl:4b
else
    echo "✅ Qwen3-VL-4B 模型已存在"
fi

# 检查目录
if [ ! -d "photos" ]; then
    echo "创建 photos 目录..."
    mkdir -p photos
fi

if [ ! -d "exports" ]; then
    echo "创建 exports 目录..."
    mkdir -p exports
fi

# 检查前端是否构建
if [ ! -d "frontend/dist" ]; then
    echo "⚠️  前端未构建，正在构建..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install
    fi
    npm run build
    cd ..
fi

# 显示配置信息
echo ""
echo "📂 当前配置："
echo "   照片目录: ${PHOTOS_DIR:-./photos (默认)}"
echo "   导出目录: ./exports"
echo "   字体目录: ./fonts"
echo "   AI 服务: 本机 Ollama"
echo "   模型: Qwen3-VL-4B"
echo "   加速: Metal GPU (M1/M2/M3)"
echo ""

# 启动 Docker 服务（仅后端和前端）
echo "🐳 启动 Docker 服务..."
docker compose -f docker-compose.host.yml up -d

echo ""
echo "✅ 印忆服务已全部启动！"
echo ""
echo "📱 访问地址："
echo "   Web 界面: http://localhost:8080"
echo "   API 文档: http://localhost:8765/docs"
echo ""
echo "⚡ 性能预期（M2 Mac + Qwen3-VL-4B）："
echo "   分析速度: 1-3 秒/张"
echo "   Metal 加速: ✅ 启用"
echo "   模型质量: ⭐⭐⭐⭐⭐"
echo ""
echo "📝 使用说明："
echo "   1. 打开 http://localhost:8080"
echo "   2. 点击'开始扫描'导入照片"
echo "   3. 等待 AI 分析完成"
echo "   4. 选择照片生成拍立得"
echo ""
echo "⚙️  常用命令："
echo "   查看日志: docker logs -f yinyi-backend"
echo "   停止服务: docker compose -f docker-compose.host.yml down"
echo "   重启后端: docker restart yinyi-backend"
echo ""

# 保持脚本运行，捕获 Ctrl+C
trap 'echo ""; echo "👋 正在停止服务..."; docker compose -f docker-compose.host.yml down; exit 0' INT

# 显示实时日志
echo "📊 实时日志（按 Ctrl+C 停止）："
docker logs -f yinyi-backend
