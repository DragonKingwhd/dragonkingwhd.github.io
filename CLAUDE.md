# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal tech blog and portfolio website built with **Jekyll** and hosted on **GitHub Pages**. The site features a modern dark theme with responsive design, blog posts, tools, a diary section, and a guestbook with Gitalk comments integration.

**Live site:** https://dragonkingwhd.github.io

## Build & Development Commands

### Prerequisites
- Ruby 2.7+ with Bundler
- Git

### Common Commands

**Install dependencies:**
```bash
bundle install
```

**Build the site locally:**
```bash
bundle exec jekyll build
```

**Serve locally with live reload (development):**
```bash
bundle exec jekyll serve
```
The site will be available at `http://localhost:4000`

**Deploy to GitHub Pages:**
```bash
git add .
git commit -m "Your commit message"
git push origin main
```
GitHub Pages automatically builds and deploys on push to the main branch.

## Project Structure

### Core Directories

- **`_posts/`** - Blog articles in Markdown format. Files follow naming convention: `YYYY-MM-DD-title.md`
- **`_diary_posts/`** - Diary entries (separate collection from blog posts)
- **`_layouts/`** - Jekyll layout templates (default, post, diary, project, home)
- **`_includes/`** - Reusable HTML components (navigation, footer, theme-switcher, gitalk comments)
- **`_data/`** - YAML data files (external resources configuration)
- **`assets/`** - Static assets (CSS, JavaScript, images, PDFs)
  - `css/style.css` - Main stylesheet with CSS variables for theming
  - `js/main.js` - Client-side JavaScript (navigation, smooth scroll, back-to-top button)

### Key Pages

- **`index.html`** - Homepage with card-based navigation
- **`blog.html`** - Blog listing page with search and category filtering
- **`floating-diary.html`** - Diary entries display
- **`guestbook.html`** - Guestbook with Gitalk comments
- **`tools.html`** - Tools collection page
- **`material-properties.html`** - Material properties tool
- **`sim2sim-guide.html`** - Sim2Sim deployment guide

### Configuration

- **`_config.yml`** - Jekyll configuration with site metadata, navigation menu, Gitalk settings, and theme colors
- **`Gemfile`** - Ruby dependencies (Jekyll 4.3.0, jekyll-feed, jekyll-sitemap, jekyll-seo-tag)

## Architecture & Key Patterns

### Jekyll Collections

The site uses three main content types configured as collections:

1. **Posts** (`_posts/`) - Blog articles with layout: `post`
2. **Diary Posts** (`_diary_posts/`) - Personal diary entries with layout: `diary`
3. **Skills** & **Docs** - Additional collections for future expansion

Each collection has default front matter settings in `_config.yml`.

### Theming System

The site implements a **dark/light theme switcher** using:
- CSS custom properties (variables) in `style.css` with `--primary-color`, `--bg-primary`, `--text-primary`, etc.
- `[data-theme="light"]` attribute selector for light mode overrides
- `theme-switcher.html` component that toggles theme and persists preference

### Comments System

**Gitalk** is integrated for post comments:
- Configuration in `_config.yml` with GitHub OAuth credentials
- Included via `_includes/gitalk.html` in post layout
- Requires GitHub OAuth App setup for comment functionality

### Navigation & Layout

- **`_layouts/default.html`** - Base layout with navbar, main content area, footer, and theme switcher
- **`_layouts/post.html`** - Extends default, adds post metadata (date, author, categories, tags), post navigation, and share buttons
- **`_layouts/diary.html`** - Similar to post layout for diary entries
- Navigation menu items configured in `_config.yml` under `navigation` array

### Styling Approach

- **CSS Variables** for consistent theming across light/dark modes
- **Responsive Design** with mobile-first approach using media queries
- **Font Stack**: Inter (sans-serif), JetBrains Mono (monospace), Noto Sans SC (Chinese)
- **Icons**: Font Awesome 6.4.0 via CDN
- **Color Scheme**: Cyan primary (#00d4ff), purple accent (#7c3aed), red secondary (#ff6b6b)

## Content Management

### Creating Blog Posts

1. Create a new file in `_posts/` with naming: `YYYY-MM-DD-title.md`
2. Add front matter:
```yaml
---
layout: post
title: "Your Title"
date: YYYY-MM-DD HH:MM:SS +0800
categories: [Category1, Category2]
tags: [tag1, tag2]
author: "Author Name"
excerpt: "Brief description"
---
```
3. Write content in Markdown (supports kramdown syntax)

### Creating Diary Entries

1. Create a new file in `_diary_posts/` with naming: `YYYY-MM-DD-title.md`
2. Add front matter (similar to posts, layout will be `diary`)
3. Diary entries use the same Markdown format

### Front Matter Fields

- `layout` - Template to use (post, diary, default, etc.)
- `title` - Page/post title
- `date` - Publication date (used for sorting and permalinks)
- `categories` - Array of categories (used for filtering in blog.html)
- `tags` - Array of tags (displayed as hashtags)
- `author` - Author name
- `excerpt` - Short description (used in meta tags and listings)

## Important Implementation Details

### Permalink Structure

Configured in `_config.yml`:
- Posts: `/:categories/:year/:month/:day/:title:output_ext`
- Diary: `/diary/:year/:month/:day/:title/`

### Excluded Files

The following are excluded from Jekyll build (in `_config.yml`):
- Gemfile, Gemfile.lock
- README.md
- vendor/ directory

### Plugins

- `jekyll-feed` - Generates RSS feed
- `jekyll-sitemap` - Generates sitemap.xml
- `jekyll-seo-tag` - SEO meta tags (available but not actively used in current layouts)

### External Services

- **Gitalk Comments** - Requires GitHub OAuth App credentials in `_config.yml`
- **Busuanzi Analytics** - Visitor counter script loaded in post layout
- **Dify Chatbot** - Embedded chatbot on homepage (token in index.html)
- **Google Fonts** - Inter, JetBrains Mono, Noto Sans SC loaded via CDN

## Common Development Tasks

### Adding a New Blog Post

```bash
# Create file in _posts/
# Add front matter with layout: post
# Write content in Markdown
# Test locally: bundle exec jekyll serve
# Push to main branch
```

### Modifying Styles

- Edit `assets/css/style.css`
- Use CSS variables for colors to maintain theme consistency
- Test both light and dark themes

### Updating Navigation

Edit `_config.yml` under `navigation` array:
```yaml
navigation:
  - title: Page Title
    url: /page-url/
    icon: "fas fa-icon-name"
```

### Adding New Pages

1. Create `.html` file in root or subdirectory
2. Add front matter with `layout: default` or custom layout
3. Use Jekyll Liquid templating for dynamic content

### Updating Site Configuration

Edit `_config.yml` for:
- Site title, description, author info
- Navigation menu
- Theme colors
- Gitalk settings
- Collection definitions

## Notes for Future Development

- The site uses **kramdown** markdown processor with **rouge** syntax highlighting
- All external resources (fonts, icons, libraries) are loaded via CDN for reliability
- The theme switcher persists user preference in localStorage
- Mobile navigation uses a hamburger menu that closes when a link is clicked
- Post navigation (previous/next) is automatically generated by Jekyll
- The site is optimized for GitHub Pages deployment (no server-side processing)
