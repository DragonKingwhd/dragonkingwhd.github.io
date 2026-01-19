# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

这是一个使用 **Jekyll** 构建、托管在 **GitHub Pages** 上的个人技术博客和作品集网站。网站采用现代深色主题，具有响应式设计，包含博客文章、工具集、日记部分和集成 Gitalk 评论系统的留言板。

**在线网站：** https://dragonkingwhd.github.io

## 构建与开发命令

### 前置要求
- Ruby 2.7+ 和 Bundler
- Git

### 常用命令

**安装依赖：**
```bash
bundle install
```

**本地构建网站：**
```bash
bundle exec jekyll build
```

**本地开发服务器（带实时重载）：**
```bash
bundle exec jekyll serve
```
网站将在 `http://localhost:4000` 可访问

**部署到 GitHub Pages：**
```bash
git add .
git commit -m "你的提交信息"
git push origin main
```
GitHub Pages 会在推送到 main 分支时自动构建和部署。

## 项目结构

### 核心目录

- **`_posts/`** - 博客文章，使用 Markdown 格式。文件命名规范：`YYYY-MM-DD-title.md`
- **`_diary_posts/`** - 日记条目（与博客文章分离的独立集合）
- **`_layouts/`** - Jekyll 布局模板（default、post、diary、project、home）
- **`_includes/`** - 可复用的 HTML 组件（导航、页脚、主题切换器、Gitalk 评论）
- **`_data/`** - YAML 数据文件（外部资源配置）
- **`assets/`** - 静态资源（CSS、JavaScript、图片、PDF）
  - `css/style.css` - 主样式表，包含用于主题的 CSS 变量
  - `js/main.js` - 客户端 JavaScript（导航、平滑滚动、返回顶部按钮）

### 关键页面

- **`index.html`** - 首页，采用卡片式导航
- **`blog.html`** - 博客列表页面，支持搜索和分类筛选
- **`floating-diary.html`** - 日记条目显示
- **`guestbook.html`** - 留言板，集成 Gitalk 评论
- **`tools.html`** - 工具集合页面
- **`material-properties.html`** - 材料属性工具
- **`sim2sim-guide.html`** - Sim2Sim 部署指南

### 配置文件

- **`_config.yml`** - Jekyll 配置，包含网站元数据、导航菜单、Gitalk 设置和主题颜色
- **`Gemfile`** - Ruby 依赖（Jekyll 4.3.0、jekyll-feed、jekyll-sitemap、jekyll-seo-tag）

## 架构与关键模式

### Jekyll 集合

网站使用三种主要内容类型，配置为集合：

1. **文章** (`_posts/`) - 博客文章，布局：`post`
2. **日记** (`_diary_posts/`) - 个人日记条目，布局：`diary`
3. **技能** 和 **文档** - 用于未来扩展的额外集合

每个集合在 `_config.yml` 中都有默认的前置元数据设置。

### 主题系统

网站实现了**深色/浅色主题切换器**，使用：
- `style.css` 中的 CSS 自定义属性（变量），如 `--primary-color`、`--bg-primary`、`--text-primary` 等
- `[data-theme="light"]` 属性选择器用于浅色模式覆盖
- `theme-switcher.html` 组件，用于切换主题并持久化用户偏好

### 评论系统

**Gitalk** 集成用于文章评论：
- 在 `_config.yml` 中配置 GitHub OAuth 凭证
- 通过 `_includes/gitalk.html` 在文章布局中包含
- 需要设置 GitHub OAuth App 以启用评论功能

### 导航与布局

- **`_layouts/default.html`** - 基础布局，包含导航栏、主内容区、页脚和主题切换器
- **`_layouts/post.html`** - 扩展默认布局，添加文章元数据（日期、作者、分类、标签）、文章导航和分享按钮
- **`_layouts/diary.html`** - 类似文章布局，用于日记条目
- 导航菜单项在 `_config.yml` 的 `navigation` 数组中配置

### 样式方法

- **CSS 变量** 用于在深色/浅色模式间保持一致的主题
- **响应式设计** 采用移动优先方法，使用媒体查询
- **字体栈**：Inter（无衬线）、JetBrains Mono（等宽）、Noto Sans SC（中文）
- **图标**：Font Awesome 6.4.0 通过 CDN 加载
- **配色方案**：青色主色（#00d4ff）、紫色强调色（#7c3aed）、红色辅助色（#ff6b6b）

## 内容管理

### 创建博客文章

1. 在 `_posts/` 中创建新文件，命名规范：`YYYY-MM-DD-title.md`
2. 添加前置元数据：
```yaml
---
layout: post
title: "你的标题"
date: YYYY-MM-DD HH:MM:SS +0800
categories: [分类1, 分类2]
tags: [标签1, 标签2]
author: "作者名"
excerpt: "简短描述"
---
```
3. 使用 Markdown 编写内容（支持 kramdown 语法）

### 创建日记条目

1. 在 `_diary_posts/` 中创建新文件，命名规范：`YYYY-MM-DD-title.md`
2. 添加前置元数据（类似文章，布局将为 `diary`）
3. 日记条目使用相同的 Markdown 格式

### 前置元数据字段

- `layout` - 使用的模板（post、diary、default 等）
- `title` - 页面/文章标题
- `date` - 发布日期（用于排序和永久链接）
- `categories` - 分类数组（用于 blog.html 中的筛选）
- `tags` - 标签数组（显示为井号标签）
- `author` - 作者名
- `excerpt` - 简短描述（用于元标签和列表）

## 重要实现细节

### 永久链接结构

在 `_config.yml` 中配置：
- 文章：`/:categories/:year/:month/:day/:title:output_ext`
- 日记：`/diary/:year/:month/:day/:title/`

### 排除文件

以下文件在 Jekyll 构建中被排除（在 `_config.yml` 中）：
- Gemfile、Gemfile.lock
- README.md
- vendor/ 目录

### 插件

- `jekyll-feed` - 生成 RSS 源
- `jekyll-sitemap` - 生成 sitemap.xml
- `jekyll-seo-tag` - SEO 元标签（可用但当前布局中未主动使用）

### 外部服务

- **Gitalk 评论** - 需要在 `_config.yml` 中配置 GitHub OAuth App 凭证
- **不蒜子分析** - 在文章布局中加载的访客计数脚本
- **Dify 聊天机器人** - 嵌入在首页的聊天机器人（令牌在 index.html 中）
- **Google Fonts** - Inter、JetBrains Mono、Noto Sans SC 通过 CDN 加载

## 常见开发任务

### 添加新博客文章

```bash
# 在 _posts/ 中创建文件
# 添加前置元数据，layout: post
# 使用 Markdown 编写内容
# 本地测试：bundle exec jekyll serve
# 推送到 main 分支
```

### 修改样式

- 编辑 `assets/css/style.css`
- 使用 CSS 变量设置颜色，以保持主题一致性
- 测试深色和浅色两种主题

### 更新导航

编辑 `_config.yml` 中的 `navigation` 数组：
```yaml
navigation:
  - title: 页面标题
    url: /page-url/
    icon: "fas fa-icon-name"
```

### 添加新页面

1. 在根目录或子目录中创建 `.html` 文件
2. 添加前置元数据，`layout: default` 或自定义布局
3. 使用 Jekyll Liquid 模板语言处理动态内容

### 更新网站配置

编辑 `_config.yml` 以修改：
- 网站标题、描述、作者信息
- 导航菜单
- 主题颜色
- Gitalk 设置
- 集合定义

## 未来开发注意事项

- 网站使用 **kramdown** markdown 处理器和 **rouge** 语法高亮
- 所有外部资源（字体、图标、库）通过 CDN 加载以确保可靠性
- 主题切换器在 localStorage 中持久化用户偏好
- 移动导航使用汉堡菜单，点击链接后自动关闭
- 文章导航（上一篇/下一篇）由 Jekyll 自动生成
- 网站针对 GitHub Pages 部署进行了优化（无服务器端处理）
