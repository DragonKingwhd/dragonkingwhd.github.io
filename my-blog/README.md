# 我的技术博客

这是一个基于 Jekyll 和 GitHub Pages 的个人技术博客网站，具有现代化的设计和丰富的功能。

## ✨ 特性

- 📱 **响应式设计** - 完美适配桌面、平板和手机
- 🎨 **现代化UI** - 简洁美观的界面设计
- 📝 **博客系统** - 支持 Markdown 写作
- 🛠️ **项目展示** - 展示个人项目和作品
- 🔧 **实用工具** - 集成各种在线工具
- 🚀 **高性能** - 静态网站，加载速度快
- 🔍 **SEO友好** - 针对搜索引擎优化

## 🚀 快速部署到 GitHub Pages

### 1. 准备工作

确保您有 GitHub 账户，如果没有请先注册：https://github.com

### 2. 创建仓库

1. 登录 GitHub
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 仓库名称填写：`your-username.github.io`（将 your-username 替换为您的 GitHub 用户名）
4. 设置为 Public（公开）
5. 不要勾选 "Initialize this repository with a README"
6. 点击 "Create repository"

### 3. 上传网站文件

有两种方法上传文件：

#### 方法一：使用 Git 命令行（推荐）

```bash
# 在博客目录中初始化 Git 仓库
cd my-blog
git init

# 添加所有文件到暂存区
git add .

# 提交文件
git commit -m "Initial commit: 创建个人博客网站"

# 添加远程仓库（替换为您的仓库地址）
git remote add origin https://github.com/your-username/your-username.github.io.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

#### 方法二：使用 GitHub Web 界面

1. 在刚创建的仓库页面，点击 "uploading an existing file"
2. 将博客目录中的所有文件拖拽到页面中
3. 在页面底部填写提交信息："创建个人博客网站"
4. 点击 "Commit changes"

### 4. 启用 GitHub Pages

1. 在仓库页面，点击 "Settings" 选项卡
2. 在左侧菜单中找到 "Pages"
3. 在 "Source" 部分选择 "Deploy from a branch"
4. 选择 "main" 分支，文件夹选择 "/ (root)"
5. 点击 "Save"

### 5. 访问您的网站

几分钟后，您的网站将在以下地址可用：
```
https://your-username.github.io
```

## ⚙️ 个性化配置

### 修改网站信息

编辑 `_config.yml` 文件，修改以下内容：

```yaml
title: 您的博客标题
email: your-email@example.com
description: 您的博客描述
github_username: your_github_username
twitter_username: your_twitter_username

# 社交链接
social:
  github: your_username
  twitter: your_username
  email: your-email@example.com
```

### 添加头像

将您的头像图片重命名为 `avatar.jpg`，放置到 `assets/images/` 目录中。

### 修改关于页面

编辑 `about.md` 文件，填写您的个人信息。

## 📝 写博客

### 创建新文章

1. 在 `_posts` 目录中创建新文件
2. 文件名格式：`YYYY-MM-DD-title.md`
3. 文件开头添加 Front Matter：

```yaml
---
layout: post
title: "文章标题"
date: 2024-12-27
categories: [分类1, 分类2]
tags: [标签1, 标签2]
author: "您的名字"
---

文章内容使用 Markdown 格式...
```

### Front Matter 说明

- `layout`: 布局模板（通常使用 `post`）
- `title`: 文章标题
- `date`: 发布日期
- `categories`: 文章分类
- `tags`: 文章标签
- `author`: 作者
- `image`: 文章封面图片（可选）

## 🛠️ 添加项目

### 创建项目页面

1. 在 `_projects` 目录中创建 `.md` 文件
2. 添加项目信息：

```yaml
---
title: 项目名称
description: 项目描述
image: /assets/images/projects/project-image.png
demo_url: https://demo-url.com
github_url: https://github.com/username/project
tech_stack: ["HTML", "CSS", "JavaScript"]
status: 已完成
date: 2024-12-27
---

项目详细介绍...
```

## 🔧 添加工具

将您的 HTML 工具文件放置到 `tools` 目录中，然后在 `tools.html` 页面添加相应的卡片。

## 📁 项目结构

```
my-blog/
├── _config.yml          # Jekyll 配置文件
├── _layouts/             # 页面布局模板
│   ├── default.html      # 基础布局
│   ├── home.html         # 首页布局
│   ├── post.html         # 文章布局
│   └── project.html      # 项目布局
├── _includes/            # 可复用组件
│   ├── navigation.html   # 导航栏
│   └── footer.html       # 页脚
├── _posts/               # 博客文章
├── _projects/            # 项目页面
├── assets/               # 静态资源
│   ├── css/
│   ├── js/
│   └── images/
├── tools/                # 在线工具
├── index.md              # 首页
├── blog.html             # 博客列表页
├── projects.html         # 项目列表页
├── tools.html            # 工具页面
├── about.md              # 关于页面
└── README.md             # 说明文档
```

## 🎨 自定义样式

网站的样式定义在 `assets/css/style.css` 中，您可以：

- 修改颜色变量（`:root` 部分）
- 调整布局和间距
- 添加新的组件样式
- 实现暗色模式

## 📱 响应式设计

网站已经适配了各种设备：

- 桌面端（1200px+）
- 平板端（768px - 1199px）  
- 手机端（< 768px）

## 🔍 SEO 优化

网站包含了 SEO 优化功能：

- 自动生成 sitemap.xml
- 结构化数据
- Open Graph 标签
- Twitter Card 支持
- 语义化 HTML

## 🚀 性能优化

- 图片懒加载
- CSS/JS 压缩
- 静态文件缓存
- 响应式图片

## 🛠️ 本地开发

如果您想在本地预览网站：

### 安装 Jekyll

```bash
# 安装 Ruby（macOS/Linux）
# macOS: brew install ruby
# Ubuntu: sudo apt-get install ruby-full

# 安装 Jekyll 和 Bundler
gem install jekyll bundler

# 在项目目录中安装依赖
bundle install

# 启动本地服务器
bundle exec jekyll serve

# 访问 http://localhost:4000
```

### Windows 用户

建议使用 WSL (Windows Subsystem for Linux) 或 Docker 来运行 Jekyll。

## 📝 更新日志

- **v1.0.0** (2024-12-27)
  - 初始版本发布
  - 基础博客功能
  - 项目展示功能
  - 响应式设计
  - 集成数据可视化工具

## 🤝 贡献

欢迎提出建议和改进！您可以：

1. 提交 Issue 反馈问题
2. 提交 Pull Request 贡献代码
3. 完善文档和教程

## 📄 许可证

此项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ❓ 常见问题

### 网站没有显示怎么办？

1. 检查仓库名是否正确（必须是 `username.github.io`）
2. 确认 GitHub Pages 已启用
3. 等待几分钟让部署完成
4. 检查是否有构建错误

### 如何添加自定义域名？

1. 在仓库根目录创建 `CNAME` 文件
2. 文件中写入您的域名，如：`blog.example.com`
3. 在域名服务商处设置 DNS 记录指向 GitHub Pages

### 如何备份网站？

您的网站文件已经存储在 GitHub 上，这本身就是一个备份。建议定期：

1. 导出重要数据
2. 保存图片和媒体文件
3. 备份自定义配置

## 📞 支持

如果您在使用过程中遇到问题，可以：

1. 查看 [Jekyll 官方文档](https://jekyllrb.com/docs/)
2. 浏览 [GitHub Pages 文档](https://docs.github.com/en/pages)
3. 在本仓库提交 Issue

---

🎉 **恭喜！您现在拥有了一个专业的个人博客网站！**

开始分享您的技术心得和项目经验吧！