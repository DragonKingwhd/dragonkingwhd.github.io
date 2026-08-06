---
layout: post
title: "切分支为什么这么烦？——从分支的本质讲到 worktree 多工作区"
date: 2026-08-06 10:00:00 +0800
categories: [计算机科学, 工程技术]
tags: [Git, 分支管理, worktree, 版本控制, 开发流程]
author: "Dragonking"
excerpt: "改到一半线上出 bug，切个分支要先 stash、再等 IDE 重新索引、编译缓存全废。这不是操作不熟练，而是用错了工具：分支管的是历史，worktree 管的是现场。本文从 .git 目录的文件布局讲清楚两者的区别，给出决策表和一份 git branch / git worktree 命令速查。"
kb: true
kb_cat: misc
---

## 一个每天都在发生的场景

你正在 `feature/new-planner` 上改一个大功能，改了七八个文件，代码半通不通，编译刚跑完一轮增量构建。这时消息弹出来：线上有个空指针，急。

于是熟悉的流程开始了：

```bash
git stash push -m "planner WIP"
git switch main
git switch -c fix/npe
# ...改完、提交、推送...
git switch feature/new-planner
git stash pop
```

看起来很顺，代价却藏在中间：`git switch` 把工作区里几百个文件全部重写了一遍，**文件修改时间（mtime）全变**，于是增量编译缓存作废、IDE 触发全量重新索引、`node_modules` 或 Python 虚拟环境如果分支间依赖不同还得重装。改一行热修的实际成本，是两次全量重建。

更糟的情况是：你想**同时**看两个版本——比如对着 review 的分支和自己的实现逐行比对，或者一个分支上跑三小时的训练/测试，同时在另一个分支继续写代码。分支做不到这件事，因为一个仓库只有一张"书桌"。

这篇文章要讲清楚的就是这件事：**分支管理的是历史，工作区管理的是现场，它们是两个正交的维度。** 而 `git worktree` 正是那个被大多数人忽略、却能一次性解决上述所有问题的内置命令。

## 直觉：图书馆、书签和书桌

先建立一个能一直用下去的比喻。

一个 Git 仓库有三样东西：

- **对象库**（`.git/objects`）像一座**图书馆**。每一次提交、每一个文件版本，都作为一本不可变的书永久存放在里面，按内容哈希编号。它只增不减。
- **分支**（`.git/refs/heads/*`）像**书签**。书签本身没有内容，它只是写着"第 9f2b1c 号书"的一张小纸条。你可以随便加书签、挪书签、撕书签，图书馆的藏书一本都不会变。
- **工作区**（working tree）像一张**书桌**。你把某本书摊开在桌上，才能读它、改它。桌上是文件系统里真实存在、编辑器能打开的文件。

`git switch` 干的事情是：**把桌上的书收走，按另一个书签取一本新书摊开**。桌子只有一张，所以必须先收拾干净（stash 或 commit），换书也要花时间（重写文件）。

而 `git worktree` 干的事情是：**再搬一张书桌进来，共用同一座图书馆**。两张桌上可以同时摊着不同的书，互不干扰，图书馆也不用复制第二份。

<svg viewBox="0 0 660 350" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <defs>
    <marker id="arr-wt" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L9,3 L0,6 z" fill="var(--primary-color)"/>
    </marker>
  </defs>
  <!-- 共享对象库 -->
  <rect x="90" y="25" width="480" height="72" rx="8" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
  <text x="330" y="50" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="14">共享的 .git（一份，不复制）</text>
  <text x="330" y="72" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">objects 对象库 · refs 分支与标签 · config 配置 · hooks</text>
  <text x="330" y="89" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">— 图书馆 —</text>
  <!-- 连接线 -->
  <path d="M 170 100 L 110 175" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-wt)"/>
  <path d="M 330 100 L 330 175" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-wt)"/>
  <path d="M 490 100 L 550 175" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-wt)"/>
  <!-- 三个工作区 -->
  <rect x="30" y="180" width="160" height="96" rx="8" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="110" y="205" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">project/</text>
  <text x="110" y="226" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">主工作区</text>
  <text x="110" y="246" fill="var(--primary-color)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">feature/planner</text>
  <text x="110" y="265" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">改到一半，不用动</text>
  <rect x="250" y="180" width="160" height="96" rx="8" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="330" y="205" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">project-hotfix/</text>
  <text x="330" y="226" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">链接工作区</text>
  <text x="330" y="246" fill="var(--primary-color)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">fix/npe</text>
  <text x="330" y="265" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">干净的现场改热修</text>
  <rect x="470" y="180" width="160" height="96" rx="8" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="550" y="205" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">project-review/</text>
  <text x="550" y="226" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">链接工作区</text>
  <text x="550" y="246" fill="var(--primary-color)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">pr/1024</text>
  <text x="550" y="265" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">跑别人的测试</text>
  <!-- 图注 -->
  <text x="330" y="303" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">三张书桌，一座图书馆：各自有独立的 HEAD、暂存区和文件</text>
  <text x="330" y="325" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">磁盘上只多了工作区文件，历史记录一份都不重复</text>
</svg>

## 原理一：分支到底是什么

要理解为什么切分支"贵"，得先看清分支有多"轻"。

### 一个分支就是一行文本

```bash
$ cat .git/HEAD
ref: refs/heads/main

$ cat .git/refs/heads/main
9f2b1c4e7a08d3f5b6c1e2a9d4f8b0c3e5a7d9f1
```

就这样。一个分支 = 一个文件，里面是 40 个十六进制字符加一个换行，**41 字节**。（分支多了以后 Git 会把它们打包进 `.git/packed-refs`，本质不变。）

`HEAD` 则是一个指向"当前在哪个分支上"的指针。`HEAD → refs/heads/main → 9f2b1c…` 这条链，就是 Git 全部的"你在哪儿"的状态。

所以：

- **创建分支是 O(1) 的**，写一个 41 字节的文件而已，跟仓库多大、历史多长完全无关。
- **提交时**，Git 写入新的提交对象，然后把当前分支文件里的哈希改成新的。所谓"分支前进"，就是改这一行字。
- **删除分支不删任何代码**。撕掉书签，书还在图书馆里（直到 `git gc` 回收真正无人引用的对象）。

<svg viewBox="0 0 660 290" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <defs>
    <marker id="arr-ref" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 z" fill="var(--primary-color)"/>
    </marker>
  </defs>
  <!-- 主线提交 -->
  <line x1="100" y1="200" x2="150" y2="200" stroke="var(--text-secondary)" stroke-width="2"/>
  <line x1="190" y1="200" x2="240" y2="200" stroke="var(--text-secondary)" stroke-width="2"/>
  <line x1="280" y1="200" x2="330" y2="200" stroke="var(--text-secondary)" stroke-width="2"/>
  <circle cx="80" cy="200" r="20" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <circle cx="170" cy="200" r="20" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <circle cx="260" cy="200" r="20" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <circle cx="350" cy="200" r="20" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="80" y="205" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">A</text>
  <text x="170" y="205" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">B</text>
  <text x="260" y="205" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">C</text>
  <text x="350" y="205" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">D</text>
  <!-- 分叉 -->
  <line x1="185" y1="185" x2="248" y2="112" stroke="var(--text-secondary)" stroke-width="2"/>
  <line x1="285" y1="95" x2="330" y2="95" stroke="var(--text-secondary)" stroke-width="2"/>
  <circle cx="265" cy="95" r="20" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <circle cx="350" cy="95" r="20" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="265" y="100" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">E</text>
  <text x="350" y="100" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">F</text>
  <!-- 分支指针 -->
  <rect x="410" y="182" width="80" height="34" rx="6" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
  <text x="450" y="204" fill="var(--primary-color)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">main</text>
  <path d="M 408 199 L 375 199" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-ref)"/>
  <rect x="410" y="78" width="130" height="34" rx="6" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
  <text x="475" y="100" fill="var(--primary-color)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">feature/planner</text>
  <path d="M 408 95 L 375 95" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-ref)"/>
  <!-- HEAD -->
  <rect x="540" y="182" width="80" height="34" rx="6" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="580" y="204" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">HEAD</text>
  <path d="M 538 199 L 496 199" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-ref)"/>
  <!-- 图注 -->
  <text x="330" y="252" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">圆圈是不可变的提交对象，方框是可移动的指针</text>
  <text x="330" y="273" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">切换分支 = 改写 HEAD 里的那一行，外加把工作区文件刷成目标提交的内容</text>
</svg>

### 那"贵"在哪里

分支切换本身只改一行字，真正花钱的是第二步：**Git 必须让工作区和暂存区（index）与新的提交一致**。

它会对比当前提交和目标提交的文件树，删除、新增、覆写有差异的文件。差异越大写得越多——切一个改了半个仓库的分支，等价于重新解包半个项目。

而且下游工具并不知道"这些文件其实之前存在过"：

- **构建系统**看 mtime 和内容哈希，文件被重写就认为脏了，增量编译退化成全量。
- **IDE/LSP** 看到批量文件变更就重建索引，大型 C++/Rust 项目动辄数分钟。
- **依赖目录**（`node_modules/`、`target/`、`build/`）通常在 `.gitignore` 里，切分支时**不会被切换**——于是你带着 A 分支的依赖跑 B 分支的代码，出现玄学错误。

这三条，就是"切分支很烦"的全部来源。注意它们**没有一条是分支的锅**——分支只是改了一行字，是"共用一张书桌"这个约束造成的。

## 原理二：worktree 是怎么做到的

`git worktree` 的思路很直接：让一个仓库拥有多个工作区，每个工作区有自己的 `HEAD` 和 index，但共用同一份对象库和 refs。

```bash
# 从当前仓库派生一个新工作区，并在其中新建分支 fix/npe
git worktree add ../project-hotfix -b fix/npe main
```

执行后，磁盘上长这样：

```
project/                        # 主工作区
├── .git/                       # 真正的仓库目录
│   ├── objects/                # ← 共享
│   ├── refs/heads/             # ← 共享
│   ├── config                  # ← 共享
│   └── worktrees/
│       └── project-hotfix/     # 该链接工作区的私有状态
│           ├── HEAD            #   它自己的 HEAD
│           ├── index           #   它自己的暂存区
│           ├── gitdir          #   记录工作区路径
│           └── commondir       #   指回共享的 .git
├── src/
└── ...

project-hotfix/                 # 链接工作区（linked worktree）
├── .git                        # 注意：这是一个「文件」，不是目录
├── src/
└── ...
```

关键在那个 `.git` **文件**，内容只有一行：

```
gitdir: /Users/you/code/project/.git/worktrees/project-hotfix
```

Git 在任何目录里执行命令时，都会顺着这条线索找到私有状态目录，再顺着 `commondir` 找到共享的对象库。对你来说，`project-hotfix/` 用起来和一个独立仓库完全一样——`git log`、`git commit`、`git push` 全都正常，而且看得到全部历史。

### 什么共享，什么独立

这张表是理解 worktree 行为的核心，很多"怪现象"都能从这里解释：

| 内容 | 是否共享 | 说明 |
|------|----------|------|
| 对象库 `objects/` | ✅ 共享 | 所以新建工作区几乎不占额外磁盘（除了工作区文件本身） |
| 分支、标签 `refs/` | ✅ 共享 | 在 A 工作区提交，B 工作区立刻 `git log` 得到 |
| `config`、`hooks` | ✅ 共享 | 改一处，所有工作区生效 |
| **stash** `refs/stash` | ✅ **共享** | 常见误区：在 A 里 stash，B 里 `git stash list` 也看得到、也能 pop |
| `HEAD`（当前分支） | ❌ 独立 | 每个工作区各自在一个分支上 |
| `index`（暂存区） | ❌ 独立 | `git add` 互不干扰 |
| 工作区文件 | ❌ 独立 | 各自一份真实文件 |
| `refs/bisect/*` | ❌ 独立 | 所以可以在一个工作区里安心跑 `git bisect` |
| 未跟踪文件、构建产物 | ❌ 独立 | `node_modules/`、`.venv/`、`target/` 都要各自准备 |

**一条硬规则**：同一个分支不能同时在两个工作区里检出。

```bash
$ git worktree add ../tmp main
fatal: 'main' is already used by worktree at '/Users/you/code/project'
```

这不是限制，是保护——否则两个工作区同时提交到同一分支，会互相把对方的 HEAD 甩在身后。需要临时看同一分支的内容时，用 `--detach` 检出为游离 HEAD 即可。

### 和 `git clone` 的区别

有人会说：我再 clone 一份不就行了？可以，但代价不同：

| | 第二个 clone | worktree |
|---|---|---|
| 磁盘占用 | 历史 + 工作区各一份 | 只多一份工作区文件 |
| 新建速度 | 重新传输/复制整个历史 | 只写工作区文件 |
| 提交可见性 | 要 push/fetch 才能互通 | **立即互通**，同一份 refs |
| 分支状态 | 两套独立分支，容易分叉混乱 | 一套分支，全局一致 |
| 适合场景 | 真要隔离（改配置、试危险操作） | 同一项目的并行工作 |

日常并行开发，worktree 几乎全面优于第二个 clone。

## 应用：什么时候用哪个

这是全文最该记住的一张表。

| 需求 | 用什么 | 理由 |
|------|--------|------|
| 记录一条独立的开发线 | **分支** | 分支就是为这个存在的，成本近乎零 |
| 顺序地做完 A 再做 B | **分支** + `git switch` | 不需要同时存在，切换够用 |
| 临时打断几分钟，改动很小 | `git stash` | 最轻，但别囤积——stash 是共享的、无名字的、易遗忘的 |
| 改到一半要热修线上 | **worktree** | 保住现场，不毁编译缓存 |
| 一边跑长测试/训练，一边继续写 | **worktree** | 一张书桌做不到两件事 |
| 逐行对比两个版本的实际行为 | **worktree** | 两个目录可以同时用 diff 工具、同时运行 |
| review 别人的 PR 并跑起来 | **worktree** | 不污染自己的工作区和依赖 |
| `git bisect` 找回归 | **worktree** | bisect 状态是工作区私有的，主工作区不受影响 |
| 让多个 AI agent 并行改同一项目 | **worktree** | 天然隔离文件冲突，共享历史 |
| 需要不同的 Git 配置/远端/危险实验 | 第二个 **clone** | 这时候隔离才是目的 |

一句话版本：**要不要同时存在两份"正在编辑的现场"？要，就 worktree；不要，就分支。**

> 关于 `git stash` 的定位：它适合"我马上就回来"的中断，超过半小时的中断建议直接提交到分支上（`git commit -m "wip"`，回来后 `git reset --soft HEAD~1` 或 `git commit --amend`）。stash 没有名字、不带分支信息、还在所有工作区之间共享，攒到十几条以后没人分得清哪条是哪条。

## 实战：五个配方

### 配方 1：紧急热修，不动现场

```bash
# 主工作区继续放着改到一半的代码，碰都不用碰
git fetch origin
git worktree add ../proj-hotfix -b fix/npe origin/main

cd ../proj-hotfix
# 装依赖（这一份是独立的）→ 改 → 测 → 提交
git push -u origin fix/npe

# 合并后清理
cd ../project
git worktree remove ../proj-hotfix
git branch -d fix/npe
```

### 配方 2：跑长任务的同时继续开发

```bash
# 开一个专门用来跑训练/回归测试的工作区
git worktree add ../proj-bench feature/new-planner --detach
cd ../proj-bench && ./run_benchmark.sh   # 跑三小时，随它去

# 主工作区照常改代码、切分支、重编译，互不影响
```

注意这里用了 `--detach`：因为 `feature/new-planner` 已经在主工作区检出了，游离 HEAD 才能拿到同一份代码快照。

### 配方 3：review PR 并真的跑起来

```bash
git fetch origin pull/1024/head:pr-1024        # GitHub 的 PR 引用
git worktree add ../proj-pr1024 pr-1024
cd ../proj-pr1024
# 在这里随便改、随便试，脏了直接删
```

### 配方 4：二分查找回归

```bash
git worktree add ../proj-bisect --detach main
cd ../proj-bisect
git bisect start
git bisect bad HEAD
git bisect good v1.2.0
# 反复：跑测试 → git bisect good / bad
git bisect reset
cd ../project && git worktree remove ../proj-bisect
```

bisect 会疯狂切换提交、把工作区搅得天翻地覆——放在独立工作区里，主工作区一无所知。

### 配方 5：并行 AI agent

让多个 agent（Claude Code、Codex 之类）同时改同一个项目时，最大的问题是它们会互相覆盖文件。给每个 agent 一个 worktree，问题自然消失：

```bash
for task in refactor-api add-tests fix-lint; do
  git worktree add "../agents/$task" -b "agent/$task" main
done
```

每个 agent 在自己的目录里工作，提交进的是同一份对象库，最后统一 rebase 合并。跑完 `git worktree remove` 一键清场。

## 分支管理策略：给小团队的推荐

命令之外，还有个更重要的问题：分支该怎么组织。

### 推荐：主干开发 + 短命特性分支

除非你在做需要长期维护多个发布版本的产品（比如要同时支持 v1.x 和 v2.x），否则**别用 GitFlow**。那套 `develop` / `release/*` / `hotfix/*` 的五层结构是为"按季度发版的桌面软件"设计的，放到持续部署的项目上只会带来无穷无尽的合并冲突。

推荐这套：

1. **`main` 永远可发布**，受保护，只能通过 PR 合入。
2. **特性分支从 `main` 切出，寿命不超过 2~3 天**。这是最关键的一条——分支活得越久，合并时的冲突面积增长得越快（大致是"改动量 × 存活时间"）。功能大就拆成几个能独立合并的小步，用功能开关（feature flag）挡住半成品。
3. **合并前 rebase 到最新 `main`**，保持线性历史，`git log` 和 `git bisect` 才好用。合入用 squash merge 或 rebase merge，一个 PR 落成一个干净的提交。
4. **合并即删除分支**，本地远端都删。分支列表应该反映"正在进行的工作"，而不是"过去一年的考古现场"。

### 命名约定

统一前缀，让 `git branch --list 'fix/*'` 和 IDE 的分组显示能用起来：

| 前缀 | 用途 | 例子 |
|------|------|------|
| `feature/` | 新功能 | `feature/mpc-solver` |
| `fix/` | 缺陷修复 | `fix/npe-on-empty-traj` |
| `refactor/` | 不改行为的重构 | `refactor/split-controller` |
| `chore/` | 构建、依赖、杂务 | `chore/bump-torch` |
| `exp/` | 随时可能丢弃的实验 | `exp/try-diffusion-policy` |

多人协作时可以再加一层人名：`whd/feature/mpc-solver`，一眼看出归属。

### 一条实用配置

```bash
# 让 git pull 默认走 rebase，避免满屏 "Merge branch 'main' into 'main'"
git config --global pull.rebase true
# 让 git push 默认推同名分支
git config --global push.default current
# 自动清理远端已删除的分支引用
git config --global fetch.prune true
```

## 命令速查：`git branch` 全家桶

### 查看

```bash
git branch                       # 本地分支
git branch -a                    # 含远程跟踪分支
git branch -r                    # 只看远程跟踪分支
git branch -v                    # 附带每个分支最新提交的摘要
git branch -vv                   # 再加上游分支和 ahead/behind 计数 ★常用
git branch --show-current        # 只输出当前分支名（写脚本用）

git branch --list 'feature/*'    # 按通配符过滤
git branch --sort=-committerdate # 按最近提交时间排序 ★找"我上周在改啥"
git branch --sort=refname        # 按名字排序
```

自定义输出格式（`git branch` 底层就是 `git for-each-ref`）：

```bash
# 分支名 + 落后/领先状态 + 最后提交时间 + 作者
git branch --format='%(refname:short)|%(upstream:track)|%(committerdate:relative)|%(authorname)'
```

### 创建与切换

```bash
git branch feature/x             # 只建分支，不切过去
git switch -c feature/x          # 建并切换 ★推荐（Git 2.23+）
git switch -c feature/x main     # 从指定起点建
git switch -c feature/x origin/main --no-track   # 不设上游

git switch main                  # 切换
git switch -                     # 切回上一个分支 ★高频
git switch --detach v1.2.0       # 游离 HEAD 看某个历史点
```

`git checkout` 仍然能用，但它一个命令干了"切分支"和"恢复文件"两件毫不相干的事，是新手事故高发区。Git 2.23 把它拆成了 `git switch`（管分支）和 `git restore`（管文件），新代码建议用新命令。

### 上游关联

```bash
git branch -u origin/main             # 给当前分支设上游
git branch -u origin/dev feature/x    # 给指定分支设上游
git branch --unset-upstream           # 解除
git push -u origin feature/x          # 推送并同时设上游 ★最常用的方式
```

上游设对了，`git status` 才会告诉你"领先 3 个提交、落后 2 个"，`git pull` / `git push` 也才能不带参数直接用。

### 重命名与复制

```bash
git branch -m new-name                # 重命名当前分支
git branch -m old-name new-name       # 重命名指定分支
git branch -M main                    # 强制重命名（覆盖已存在的同名分支）
git branch -c old new                 # 复制分支（含 reflog 和配置）
```

远端没有"重命名"这回事，要手动推新删旧：

```bash
git branch -m old new
git push origin -u new
git push origin --delete old
```

### 删除

```bash
git branch -d feature/x          # 安全删除：未合并会拒绝 ★默认用这个
git branch -D feature/x          # 强制删除，不管有没有合并
git push origin --delete feature/x   # 删除远端分支
git fetch -p                     # 清理本地残留的远程跟踪引用
```

`-d` 的"已合并"判断是相对当前 HEAD 的。如果你用 squash merge，分支在 Git 看来**并未合并**（提交哈希全变了），`-d` 会拒绝——这种情况用 `-D` 是正常的。

### 筛选：找出该删的分支

```bash
git branch --merged main         # 已合并进 main 的分支（可以删了）
git branch --no-merged main      # 尚未合并的（还在进行中）
git branch --contains <commit>   # 哪些分支包含这个提交 ★排查"这个修复上线了吗"
git branch --no-contains <commit>
git branch --points-at <commit>  # 哪些分支正好指向这个提交
```

批量清理已合并的分支：

```bash
git branch --merged main | grep -vE '^\*|main|develop' | xargs -r git branch -d
```

清理"远端已经删了、本地还留着"的分支（squash merge 场景下最实用）：

```bash
git fetch -p
git for-each-ref --format '%(refname:short) %(upstream:track)' refs/heads \
  | awk '$2 == "[gone]" { print $1 }' \
  | xargs -r git branch -D
```

> 这两条都会真的删东西，第一次跑建议先把最后的 `xargs ...` 去掉，确认列表无误再执行。

## 命令速查：`git worktree`

```bash
# 创建
git worktree add ../path                 # 新建工作区，分支名取自目录名
git worktree add ../path <branch>        # 检出已有分支（该分支不能已被占用）
git worktree add ../path -b <new> <base> # 新建分支并检出 ★最常用
git worktree add --detach ../path <ref>  # 游离 HEAD，用于"同一分支再看一份"
git worktree add --track -b feat ../path origin/feat    # 建分支并设上游（路径在前，起点在后）

# 查看
git worktree list                        # 列出所有工作区、各自的分支和 HEAD
git worktree list --porcelain            # 机器可读格式，写脚本用

# 清理
git worktree remove ../path              # 删除（工作区必须干净）
git worktree remove --force ../path      # 有未提交改动也删
git worktree prune                       # 清理"目录被手工删了"留下的元数据
git worktree prune -n                    # 先看看会清理什么

# 其他
git worktree move ../old ../new          # 移动工作区（别用 mv，元数据会失联）
git worktree lock ../path --reason "在移动硬盘上"   # 防止被 prune 掉
git worktree unlock ../path
git worktree repair                      # 主仓库被移动后，修复所有链接
```

一个能记住的目录约定：

```
~/code/
├── project/            # 主工作区，永远停在 main
├── project-feat-a/
├── project-hotfix/
└── project-review/
```

主工作区始终留在 `main` 不动，所有实际工作都在派生的工作区里做。这样"当前在哪个分支"这个问题永远不会让你困惑，`cd` 到哪个目录就是在做哪件事。

## 常见坑

**1. 把 worktree 建在仓库目录里面。**
`git worktree add ./tmp` 会让新工作区的文件出现在主工作区的 `git status` 里，一不小心就提交进去了。**放到仓库外面**（`../project-x`），或者至少加进 `.gitignore`。

**2. 直接 `rm -rf` 删工作区目录。**
`.git/worktrees/` 里的元数据会残留，那个分支还会被标记为"已被检出"，别的地方检不出来。正确做法是 `git worktree remove`；已经手删了就补一句 `git worktree prune`。

**3. 忘了依赖目录不共享。**
`node_modules/`、`.venv/`、`target/`、`build/` 都不在版本控制里，新工作区是空的，要重新 `npm install` / `pip install -e .`。这既是代价也是好处——它顺带解决了"分支间依赖版本不一致"的玄学问题。真嫌慢的话可以软链接共享（`ln -s ../project/node_modules .`），但要确认两个分支的依赖确实一致。

**4. 以为 stash 是工作区私有的。**
不是。`refs/stash` 是共享 ref，在 A 工作区 `git stash`，B 工作区 `git stash pop` 会把改动弹到 B 的文件上——而且那些改动很可能属于另一个分支。用 worktree 之后，基本就不需要 stash 了。

**5. 子模块（submodule）支持不完整。**
含 submodule 的仓库用 worktree 有已知的边角问题，新工作区里通常要手动 `git submodule update --init --recursive`。重度依赖 submodule 的项目，谨慎评估。

**6. 长期不清理。**
worktree 很好用，一好用就容易攒下十几个。定期 `git worktree list` 看一眼，删掉已经合并的。

**7. IDE 需要按目录分别打开。**
每个 worktree 在 IDE 眼里是一个独立项目，索引、配置各一份。这正是它保住编译缓存的原因，但也意味着窗口会变多——这是这个方案的固有代价。

## 小结

把三句话记住就够了：

1. **分支是 41 字节的一行文本**，创建、删除、移动都几乎免费；它记录的是历史的岔路，不是磁盘上的文件夹。
2. **切分支贵在重写工作区**，代价由构建缓存、IDE 索引和依赖目录承担——这是"一个仓库一张书桌"这个约束的成本，不是分支的成本。
3. **`git worktree` 让一份对象库挂多张书桌**，几乎不占额外磁盘、提交实时互通、天然隔离现场。热修、跑长任务、review、bisect、并行 agent，全都归它。

如果读完只做一件事：现在就试一次 `git worktree add ../$(basename $PWD)-tmp -b tmp/try`，在里面随便改点东西，回主目录看一眼 `git status` ——什么都没变。那一刻的感觉，比这篇文章任何一段解释都管用。

## 术语表

| 术语 | 英文 | 含义 |
|------|------|------|
| 对象库 | Object Database | `.git/objects`，存放所有提交、树、文件内容的不可变仓库 |
| 游离 HEAD | Detached HEAD | HEAD 直接指向某个提交而非分支，此时提交不属于任何分支 |
| 快进合并 | Fast-forward | 目标分支只需把指针前移即可完成的合并，不产生合并提交 |
| 特性开关 | Feature Flag | 用运行时开关隐藏未完成功能，使其能安全合入主干 |
| 变基 | Rebase | 把一串提交搬到新基点上重放，产生线性历史 |
| 引用 | Reference, ref | 指向提交的可移动名字，分支和标签都是 ref |
| 引用日志 | Reflog | 记录 HEAD 和分支指针每次移动的本地日志，误删的救命稻草 |
| 压缩合并 | Squash Merge | 把分支上多个提交压成一个再合入主干 |
| 暂存区 | Staging Area, index | `git add` 后、`git commit` 前的中间区域，每个工作区独立 |
| 贮藏 | Stash | 临时保存工作区改动的栈，**在所有工作区之间共享** |
| 主干开发 | Trunk-Based Development | 所有人频繁合入单一主干，特性分支寿命极短的协作模式 |
| 上游分支 | Upstream Branch | 本地分支关联的远端分支，决定 pull/push 的默认目标 |
| 工作区 | Working Tree / Worktree | 文件系统上摊开的那份可编辑文件；一个仓库可以有多个 |
