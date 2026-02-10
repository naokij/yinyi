#!/bin/bash

# 初始化 Git 仓库并提交初始代码

echo "🚀 初始化印忆 Git 仓库..."

# 检查是否已在 Git 仓库中
if [ -d ".git" ]; then
    echo "✅ Git 仓库已存在"
else
    echo "📦 初始化 Git 仓库..."
    git init
fi

# 配置 Git（如果未配置）
if ! git config user.name > /dev/null; then
    echo ""
    read -p "请输入你的 Git 用户名: " git_name
    git config user.name "$git_name"
fi

if ! git config user.email > /dev/null; then
    echo ""
    read -p "请输入你的 Git 邮箱: " git_email
    git config user.email "$git_email"
fi

# 添加所有文件
echo "📁 添加文件到 Git..."
git add .

# 检查是否有更改要提交
if git diff --cached --quiet; then
    echo "⚠️  没有需要提交的更改"
else
    echo "💾 提交初始代码..."
    git commit -m "Initial commit: YinYi photo printing assistant

Features:
- FastAPI backend with SQLite
- Vue3 frontend
- Qwen3-VL AI analysis (Ollama)
- Polaroid template for Xiaomi Photo Printer 1S
- Windows native deployment support
- NAS photo integration via SMB

Tech Stack:
- Backend: Python 3.11, FastAPI, SQLAlchemy
- Frontend: Vue3, Vite, Pinia
- AI: Ollama with Qwen3-VL-4B
- Database: SQLite"
    
    echo ""
    echo "✅ 初始提交完成！"
fi

echo ""
echo "🔗 下一步：关联远程仓库"
echo ""
echo "选项 1: GitHub（推荐）"
echo "  1. 在 GitHub 创建新仓库（不要初始化 README）"
echo "  2. 运行以下命令："
echo ""
echo "     git remote add origin https://github.com/YOUR_USERNAME/yinyi.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo "选项 2: GitLab"
echo "     git remote add origin https://gitlab.com/YOUR_USERNAME/yinyi.git"
echo "     git branch -M main"  
echo "     git push -u origin main"
echo ""
echo "选项 3: 其他 Git 服务"
echo "     git remote add origin <YOUR_REPO_URL>"
echo "     git push -u origin main"
echo ""
