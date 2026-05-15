#!/bin/bash

echo "🚀 博客网站快速部署脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git未安装，请先安装Git${NC}"
    exit 1
fi

echo -e "${BLUE}📝 请输入您的信息：${NC}"

# 获取用户输入
read -p "GitHub用户名: " GITHUB_USERNAME
read -p "您的邮箱: " USER_EMAIL
read -p "您的姓名: " USER_NAME
read -p "博客标题: " BLOG_TITLE
read -p "博客描述: " BLOG_DESCRIPTION

# 验证输入
if [ -z "$GITHUB_USERNAME" ]; then
    echo -e "${RED}❌ GitHub用户名不能为空${NC}"
    exit 1
fi

REPO_NAME="${GITHUB_USERNAME}.github.io"
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo ""
echo -e "${YELLOW}🔧 配置网站信息...${NC}"

# 更新_config.yml
sed -i.bak "s/your-email@example.com/${USER_EMAIL}/g" _config.yml
sed -i.bak "s/your_username/${GITHUB_USERNAME}/g" _config.yml
sed -i.bak "s/Your Name/${USER_NAME}/g" _config.yml

if [ ! -z "$BLOG_TITLE" ]; then
    sed -i.bak "s/我的技术博客/${BLOG_TITLE}/g" _config.yml
fi

if [ ! -z "$BLOG_DESCRIPTION" ]; then
    sed -i.bak "s/分享技术知识、项目经验和学习心得的个人博客/${BLOG_DESCRIPTION}/g" _config.yml
fi

# 清理备份文件
rm -f _config.yml.bak

# 更新示例文章中的邮箱
if [ -f "_posts/2024-12-27-welcome-to-my-blog.md" ]; then
    sed -i.bak "s/{{ site.email }}/${USER_EMAIL}/g" _posts/2024-12-27-welcome-to-my-blog.md
    rm -f _posts/2024-12-27-welcome-to-my-blog.md.bak
fi

echo -e "${GREEN}✅ 网站信息配置完成${NC}"

# Git配置
echo -e "${YELLOW}🔧 配置Git...${NC}"

# 检查是否已经是Git仓库
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✅ Git仓库初始化完成${NC}"
fi

# 设置Git用户信息（仅用于当前仓库）
git config user.name "$USER_NAME"
git config user.email "$USER_EMAIL"

echo -e "${YELLOW}📦 添加文件到Git...${NC}"

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: 创建个人博客网站

- 添加基础网站结构
- 集成数据可视化工具
- 配置响应式设计
- 设置SEO优化

Generated with automated setup script"

echo -e "${GREEN}✅ 文件提交完成${NC}"

# 设置远程仓库
echo -e "${YELLOW}🌐 配置远程仓库...${NC}"

# 检查是否已经有origin
if git remote get-url origin &> /dev/null; then
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi

echo -e "${GREEN}✅ 远程仓库配置完成${NC}"

# 推送到GitHub
echo -e "${YELLOW}⬆️  推送到GitHub...${NC}"
echo -e "${BLUE}请输入您的GitHub密码或访问令牌${NC}"

# 设置主分支
git branch -M main

# 推送
if git push -u origin main; then
    echo -e "${GREEN}🎉 部署成功！${NC}"
    echo ""
    echo -e "${BLUE}📍 您的网站将在几分钟后可以访问：${NC}"
    echo -e "${GREEN}🌍 https://${GITHUB_USERNAME}.github.io${NC}"
    echo ""
    echo -e "${YELLOW}📝 后续步骤：${NC}"
    echo "1. 访问 https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/settings/pages"
    echo "2. 确认 GitHub Pages 已启用"
    echo "3. 等待几分钟让部署完成"
    echo "4. 访问您的网站！"
    echo ""
    echo -e "${BLUE}📖 更多信息请查看 README.md 文件${NC}"
else
    echo -e "${RED}❌ 推送失败${NC}"
    echo -e "${YELLOW}💡 可能的原因：${NC}"
    echo "1. 仓库不存在 - 请先在GitHub创建仓库: ${REPO_NAME}"
    echo "2. 认证失败 - 请检查用户名和密码/令牌"
    echo "3. 网络问题 - 请检查网络连接"
    echo ""
    echo -e "${BLUE}🔧 手动步骤：${NC}"
    echo "1. 访问 https://github.com/new"
    echo "2. 创建名为 '${REPO_NAME}' 的公开仓库"
    echo "3. 重新运行此脚本"
fi

echo ""
echo -e "${BLUE}🎯 享受您的新博客！${NC}"