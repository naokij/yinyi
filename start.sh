#!/bin/bash

# 印忆 (YinYi) 启动脚本

echo "🚀 启动印忆服务..."

# 检查目录
if [ ! -d "photos" ]; then
    echo "创建 photos 目录..."
    mkdir -p photos
fi

if [ ! -d "exports" ]; then
    echo "创建 exports 目录..."
    mkdir -p exports
fi

if [ ! -d "fonts" ]; then
    echo "创建 fonts 目录..."
    mkdir -p fonts
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
echo ""

# 启动 Docker Compose
echo "🐳 启动 Docker 服务..."
docker compose up -d

echo ""
echo "✅ 印忆服务已启动！"
echo ""
echo "📱 访问地址："
echo "   Web 界面: http://localhost:8080"
echo "   API 文档: http://localhost:8765/docs"
echo ""
echo "⚙️  查看日志："
echo "   后端: docker logs -f yinyi-backend"
echo "   AI 服务: docker logs -f yinyi-vllm"
echo ""
echo "📝 修改照片目录："
echo "   PHOTOS_DIR=/path/to/photos ./start.sh"
echo ""
echo "⚠️  注意：首次启动需要下载 AI 模型（约 4GB），请耐心等待..."
echo "   查看模型下载进度: docker logs -f yinyi-vllm"
