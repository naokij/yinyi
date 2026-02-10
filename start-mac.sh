#!/bin/bash

# 印忆 (YinYi) Mac 专用启动脚本
# 针对 Apple Silicon 优化，使用 Ollama 获得更好性能

echo "🚀 启动印忆服务 (Mac 优化版)..."

# 检测是否为 Apple Silicon
if [[ $(uname -m) == "arm64" ]]; then
    echo "✅ 检测到 Apple Silicon Mac (M1/M2/M3)"
    echo "💡 提示：Docker Desktop for Mac 不支持 GPU 加速"
    echo "   使用 Ollama 替代 vLLM 可以获得更好的 CPU 性能"
    echo ""
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
echo "   AI 后端: Ollama (Mac 优化)"
echo ""

# 询问用户使用哪个配置
echo "请选择部署方式："
echo "1) Mac 优化版 (Ollama) - 推荐"
echo "2) 标准版 (vLLM)"
echo "3) 退出"
read -p "请输入选项 [1-3]: " choice

case $choice in
    1)
        echo "🐳 使用 Mac 优化配置启动..."
        docker compose -f docker-compose.mac.yml up -d
        
        echo ""
        echo "⏳ 等待 Ollama 启动..."
        sleep 5
        
        echo "📥 检查模型..."
        # 检查模型是否已下载
        if ! docker exec yinyi-ollama ollama list | grep -q "qwen"; then
            echo "📥 正在下载 Qwen2.5-VL 模型（约 4GB，请耐心等待）..."
            docker exec yinyi-ollama ollama pull qwen2.5-vl:7b
        fi
        
        echo ""
        echo "✅ 印忆服务已启动！"
        echo ""
        echo "📱 访问地址："
        echo "   Web 界面: http://localhost:8080"
        echo "   API 文档: http://localhost:8765/docs"
        echo ""
        echo "⚙️  查看日志："
        echo "   后端: docker logs -f yinyi-backend"
        echo "   AI 服务: docker logs -f yinyi-ollama"
        echo ""
        echo "📝 使用说明："
        echo "   1. 首次启动需要下载模型（约 4GB）"
        echo "   2. 在 Mac 上分析速度约 3-5 秒/张"
        echo "   3. 可以在后台持续运行"
        ;;
    2)
        echo "🐳 使用标准配置启动..."
        docker compose up -d
        
        echo ""
        echo "✅ 印忆服务已启动！"
        echo ""
        echo "📱 访问地址："
        echo "   Web 界面: http://localhost:8080"
        echo "   API 文档: http://localhost:8765/docs"
        echo ""
        echo "⚠️  注意：vLLM 在 Mac 上只能使用 CPU，性能较慢（约 10-20 秒/张）"
        ;;
    3)
        echo "已退出"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac
