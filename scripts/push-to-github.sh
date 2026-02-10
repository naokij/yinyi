#!/bin/bash

# GitHub 推送辅助脚本
# 使用方式: ./scripts/push-to-github.sh

echo "🚀 推送到 GitHub"
echo ""

# 检查 Git 状态
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  有未提交的更改，请先提交:"
    git status
    exit 1
fi

# 检查是否已配置远程仓库
if git remote | grep -q "origin"; then
    echo "✅ 远程仓库已配置:"
    git remote -v
    echo ""
    read -p "是否要推送到现有远程仓库? [y/N]: " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo "📤 推送到 GitHub..."
        git push -u origin master
        echo ""
        echo "✅ 推送完成！"
        echo "访问: $(git remote get-url origin | sed 's/\.git$//' | sed 's/git@github\.com:/https:\/\/github\.com\//')"
    fi
else
    echo "🔗 尚未配置远程仓库"
    echo ""
    echo "请先在 GitHub 创建仓库:"
    echo "  1. 访问 https://github.com/new"
    echo "  2. Repository name: yinyi"
    echo "  3. 选择 Private 或 Public"
    echo "  4. 不要勾选 README"
    echo "  5. 点击 Create repository"
    echo ""
    read -p "输入你的 GitHub 用户名: " username
    read -p "选择仓库类型 [private/public]: " repo_type
    
    if [ "$repo_type" == "private" ]; then
        repo_url="https://github.com/${username}/yinyi.git"
    else
        repo_url="https://github.com/${username}/yinyi.git"
    fi
    
    echo ""
    echo "执行以下命令:"
    echo "  git remote add origin ${repo_url}"
    echo "  git branch -M main"
    echo "  git push -u origin main"
    echo ""
    read -p "是否执行? [y/N]: " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        git remote add origin ${repo_url}
        git branch -M main
        echo "📤 正在推送..."
        git push -u origin main
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ 推送成功！"
            echo "仓库地址: https://github.com/${username}/yinyi"
        else
            echo ""
            echo "❌ 推送失败"
            echo "请检查:"
            echo "  1. 是否已在 GitHub 创建仓库"
            echo "  2. 用户名是否正确"
            echo "  3. 是否有权限（私有仓库需要登录）"
        fi
    fi
fi
