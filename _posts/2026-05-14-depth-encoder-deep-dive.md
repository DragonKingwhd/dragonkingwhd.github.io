---
layout: post
title: "DepthEncoder 深度解析：CNN + MLP + GRU 到底在干什么"
date: 2026-05-14
categories: [计算机科学, 学习]
tags: [深度学习, CNN, GRU, 强化学习, 机器人感知, 表征学习]
author: "Dragonking"
excerpt: "逐层拆解一个把深度图压缩成 32 维隐向量的编码器：CNN 找局部 pattern、MLP 全局融合、GRU 时序记忆，并用人类视觉皮层做类比。"
kb: true
kb_cat: rl
---

<div class="de-doc">

<div class="container">



<nav class="toc">
  <h3>目录</h3>
  <ol>
    <li><a href="#overview">完整流水线</a></li>
    <li><a href="#input">输入：一张深度图</a></li>
    <li><a href="#conv1">第 1 层 Conv2d：找局部 pattern</a></li>
    <li><a href="#pool">第 2 层 MaxPool：缩小图</a></li>
    <li><a href="#conv2">第 3 层 Conv2d：组合 pattern</a></li>
    <li><a href="#flatten">第 4 层 Flatten：摊平</a></li>
    <li><a href="#mlp">第 5/6 层 Linear：全局压缩</a></li>
    <li><a href="#gru">RecurrentDepthBackbone：时序融合</a></li>
    <li><a href="#paramcount">参数量对比：为什么不能纯 MLP</a></li>
    <li><a href="#analogy">类比：人类视觉皮层</a></li>
  </ol>
</nav>

<!-- ============== 1 ============== -->
<h2 id="overview">1. 完整流水线总览</h2>

<p>核心任务：把一张 <code>87 × 58</code> 像素的深度图编码成一个 <code>32D</code> 的隐向量 <code>depth_latent</code>，让下游策略网络能直接用这个紧凑表征来理解前方地形，而不必处理原始的几千个像素。</p>

<div class="svg-wrap">
<svg viewBox="0 0 1000 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ov-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#475569"/>
    </marker>
  </defs>
  <!-- Input depth -->
  <rect x="20" y="60" width="100" height="100" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="70" y="50" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">输入</text>
  <text x="70" y="100" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">depth</text>
  <text x="70" y="120" font-size="11" fill="#475569" text-anchor="middle">87 × 58</text>
  <text x="70" y="138" font-size="11" fill="#475569" text-anchor="middle">5046 像素</text>

  <line x1="120" y1="110" x2="160" y2="110" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- CNN block -->
  <rect x="160" y="40" width="200" height="140" rx="8" fill="#d1fae5" stroke="#059669" stroke-width="2"/>
  <text x="260" y="32" font-size="12" font-weight="700" fill="#059669" text-anchor="middle">CNN（卷积）</text>
  <text x="260" y="64" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Conv2d(1→32, k=5)</text>
  <text x="260" y="84" font-size="11" fill="#475569" text-anchor="middle">↓</text>
  <text x="260" y="102" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">MaxPool2d(2)</text>
  <text x="260" y="120" font-size="11" fill="#475569" text-anchor="middle">↓</text>
  <text x="260" y="138" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Conv2d(32→64, k=3)</text>
  <text x="260" y="160" font-size="11" fill="#475569" text-anchor="middle">作用: 局部 pattern 提取</text>

  <line x1="360" y1="110" x2="400" y2="110" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- MLP block 1 -->
  <rect x="400" y="40" width="200" height="140" rx="8" fill="#fed7aa" stroke="#d97706" stroke-width="2"/>
  <text x="500" y="32" font-size="12" font-weight="700" fill="#d97706" text-anchor="middle">MLP（全连接）</text>
  <text x="500" y="68" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Flatten</text>
  <text x="500" y="88" font-size="11" fill="#475569" text-anchor="middle">↓ 62400D</text>
  <text x="500" y="108" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Linear(→128)</text>
  <text x="500" y="128" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Linear(→32)</text>
  <text x="500" y="160" font-size="11" fill="#475569" text-anchor="middle">作用: 全局信息压缩</text>

  <line x1="600" y1="110" x2="640" y2="110" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- GRU block -->
  <rect x="640" y="40" width="200" height="140" rx="8" fill="#fce7f3" stroke="#be185d" stroke-width="2"/>
  <text x="740" y="32" font-size="12" font-weight="700" fill="#be185d" text-anchor="middle">GRU + MLP（时序）</text>
  <text x="740" y="68" font-size="11" fill="#475569" text-anchor="middle">+ prop(31D)</text>
  <text x="740" y="86" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">combine_mlp</text>
  <text x="740" y="106" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">GRU(32→512)</text>
  <text x="740" y="126" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">output_mlp</text>
  <text x="740" y="160" font-size="11" fill="#475569" text-anchor="middle">作用: 多帧时序平滑</text>

  <line x1="840" y1="110" x2="880" y2="110" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- Output -->
  <rect x="880" y="60" width="100" height="100" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
  <text x="930" y="50" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">输出</text>
  <text x="930" y="105" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">depth_latent</text>
  <text x="930" y="123" font-size="11" fill="#475569" text-anchor="middle">32D</text>
  <text x="930" y="141" font-size="10" fill="#dc2626" text-anchor="middle">→ Actor</text>

  <!-- Bottom annotation -->
  <text x="500" y="205" font-size="12" fill="#475569" text-anchor="middle">三种网络层<strong>串联</strong>，每段做不同的事 — 不是单一的"MLP"</text>
</svg>
</div>

<div class="callout">
  <strong>核心观点</strong>
  <p>把 5046 像素压成 32D 不是"单一网络在算"，而是<strong>三段流水线协作</strong>：</p>
  <ol style="margin: 6px 0 0 20px;">
    <li><span style="color:var(--cnn);font-weight:700">CNN</span> 段：从原始像素中找"局部视觉概念"（边缘、角、平地……）</li>
    <li><span style="color:var(--mlp);font-weight:700">MLP</span> 段：把分散在各位置的局部信息融合压缩成全局表征</li>
    <li><span style="color:var(--gru);font-weight:700">GRU</span> 段：累积过去多步深度信息，时序平滑</li>
  </ol>
</div>

<!-- ============== 2 ============== -->
<h2 id="input">2. 输入：一张深度图是什么</h2>

<p>机器人前方的相机看到了下面这样一片场景。每个像素的值 = 那条光线击中障碍物的距离（米）。</p>

<div class="svg-wrap">
<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg">
  <text x="350" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">87 × 58 = 5046 个数字（每个数字 = 距离值，单位 m）</text>

  <!-- Depth image grid - simplified visualization -->
  <g transform="translate(150,40)">
    <!-- Background (远) -->
    <rect x="0" y="0" width="400" height="260" fill="#cbd5e1"/>
    <text x="200" y="20" font-size="11" fill="#1e293b" text-anchor="middle">远处 (~2.5m)</text>

    <!-- Obstacle (近) -->
    <rect x="120" y="80" width="160" height="120" fill="#1e3a8a"/>
    <text x="200" y="145" font-size="13" fill="#ffffff" text-anchor="middle" font-weight="700">障碍物</text>
    <text x="200" y="165" font-size="11" fill="#dbeafe" text-anchor="middle">~0.5m（近）</text>

    <!-- Ground (中) -->
    <rect x="0" y="200" width="400" height="60" fill="#64748b"/>
    <text x="200" y="235" font-size="11" fill="#ffffff" text-anchor="middle">地面（中等距离 ~1.5m）</text>

    <!-- Pixel grid lines -->
    <g stroke="#94a3b8" stroke-width="0.3" opacity="0.5">
      <line x1="50" y1="0" x2="50" y2="260"/>
      <line x1="100" y1="0" x2="100" y2="260"/>
      <line x1="150" y1="0" x2="150" y2="260"/>
      <line x1="200" y1="0" x2="200" y2="260"/>
      <line x1="250" y1="0" x2="250" y2="260"/>
      <line x1="300" y1="0" x2="300" y2="260"/>
      <line x1="350" y1="0" x2="350" y2="260"/>
      <line x1="0" y1="50" x2="400" y2="50"/>
      <line x1="0" y1="100" x2="400" y2="100"/>
      <line x1="0" y1="150" x2="400" y2="150"/>
    </g>

    <!-- Frame -->
    <rect x="0" y="0" width="400" height="260" fill="none" stroke="#1e293b" stroke-width="2"/>
  </g>

  <!-- Side labels -->
  <text x="40" y="80" font-size="11" fill="#475569" text-anchor="start">深色 = 近</text>
  <text x="40" y="100" font-size="11" fill="#475569" text-anchor="start">浅色 = 远</text>
  <text x="40" y="170" font-size="11" fill="#475569" text-anchor="start">机器人要</text>
  <text x="40" y="186" font-size="11" fill="#475569" text-anchor="start">从这堆数</text>
  <text x="40" y="202" font-size="11" fill="#475569" text-anchor="start">字"看出"</text>
  <text x="40" y="218" font-size="11" fill="#475569" text-anchor="start">前方有障</text>
  <text x="40" y="234" font-size="11" fill="#475569" text-anchor="start">碍物</text>
</svg>
<div class="caption">机器人前方的深度图（示意）— 每个像素是个距离数值</div>
</div>

<div class="callout">
  <strong>关键挑战</strong>：网络拿到的不是这张<em>图片</em>，而是 5046 个<em>原始数字</em>。它必须自己学会"哪些数字组合在一起意味着'有障碍'"。这就是 CNN 要解决的事。
</div>

<!-- ============== 3 ============== -->
<h2 id="conv1">3. 第 1 层 Conv2d(1→32, k=5)：找 32 种局部 pattern</h2>

<p>Conv2d 卷积层就像<strong>一组 32 个放大镜</strong>。每个放大镜是一个 <code>5×5</code> 的小窗口，里面存着一个"我要找的 pattern"。这个放大镜会在整张图上从左到右、从上到下滑动一遍，<strong>每滑到一个位置就检查"这块区域是不是匹配我要找的 pattern"</strong>。</p>

<h3>3.1 单个放大镜在干什么</h3>

<div class="svg-wrap">
<svg viewBox="0 0 900 380" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">放大镜 #1：5×5 窗口，专门找"水平边缘"（上面远、下面近）</text>

  <!-- Filter content -->
  <g transform="translate(50,50)">
    <text x="100" y="-8" font-size="12" font-weight="700" fill="#059669" text-anchor="middle">这个放大镜里的数值：</text>
    <rect x="0" y="0" width="200" height="200" fill="#d1fae5" stroke="#059669" stroke-width="2"/>
    <g font-size="13" text-anchor="middle" fill="#1e293b" font-family="monospace">
      <text x="20" y="25">-1</text>  <text x="60" y="25">-1</text> <text x="100" y="25">-1</text> <text x="140" y="25">-1</text> <text x="180" y="25">-1</text>
      <text x="20" y="65">-1</text>  <text x="60" y="65">-1</text> <text x="100" y="65">-1</text> <text x="140" y="65">-1</text> <text x="180" y="65">-1</text>
      <text x="20" y="105">0</text>  <text x="60" y="105">0</text> <text x="100" y="105">0</text> <text x="140" y="105">0</text> <text x="180" y="105">0</text>
      <text x="20" y="145">+1</text>  <text x="60" y="145">+1</text> <text x="100" y="145">+1</text> <text x="140" y="145">+1</text> <text x="180" y="145">+1</text>
      <text x="20" y="185">+1</text>  <text x="60" y="185">+1</text> <text x="100" y="185">+1</text> <text x="140" y="185">+1</text> <text x="180" y="185">+1</text>
    </g>
    <!-- Grid -->
    <g stroke="#059669" stroke-width="0.5" opacity="0.5">
      <line x1="40" y1="0" x2="40" y2="200"/>
      <line x1="80" y1="0" x2="80" y2="200"/>
      <line x1="120" y1="0" x2="120" y2="200"/>
      <line x1="160" y1="0" x2="160" y2="200"/>
      <line x1="0" y1="40" x2="200" y2="40"/>
      <line x1="0" y1="80" x2="200" y2="80"/>
      <line x1="0" y1="120" x2="200" y2="120"/>
      <line x1="0" y1="160" x2="200" y2="160"/>
    </g>
  </g>

  <!-- Arrow -->
  <text x="320" y="155" font-size="14" fill="#475569" font-family="monospace">滑动 × 检查</text>
  <line x1="290" y1="170" x2="370" y2="170" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- Original image with sliding window -->
  <g transform="translate(420,50)">
    <text x="200" y="-8" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">深度图上滑动</text>

    <!-- Background -->
    <rect x="0" y="0" width="400" height="220" fill="#cbd5e1"/>
    <rect x="120" y="60" width="160" height="120" fill="#1e3a8a"/>
    <rect x="0" y="180" width="400" height="40" fill="#64748b"/>

    <!-- Sliding window (highlighted) -->
    <rect x="100" y="50" width="40" height="40" fill="none" stroke="#dc2626" stroke-width="3"/>
    <text x="120" y="105" font-size="10" fill="#dc2626" text-anchor="middle">这块亮</text>
    <text x="120" y="120" font-size="10" fill="#dc2626" text-anchor="middle">（上远下近 ✓）</text>

    <rect x="320" y="90" width="40" height="40" fill="none" stroke="#0891b2" stroke-width="3"/>
    <text x="340" y="155" font-size="10" fill="#0891b2" text-anchor="middle">这块暗</text>
    <text x="340" y="170" font-size="10" fill="#0891b2" text-anchor="middle">（全远 ✗）</text>

    <rect x="0" y="0" width="400" height="220" fill="none" stroke="#1e293b" stroke-width="2"/>
  </g>

  <!-- Bottom explanation -->
  <text x="450" y="320" font-size="13" fill="#1e293b" text-anchor="middle">
    每个位置算: 5×5 区域里 25 个像素值 × 5×5 放大镜里 25 个权重 → 求和 → 得到一个激活强度
  </text>
  <text x="450" y="345" font-size="12" fill="#475569" text-anchor="middle">
    匹配的位置激活强度高，不匹配的位置激活强度低
  </text>
</svg>
<div class="caption">放大镜定义"上方有负权重、下方有正权重" → 在"上远下近"的位置激活强</div>
</div>

<h3>3.2 32 个放大镜并行扫一遍，产生 32 张激活图</h3>

<div class="svg-wrap">
<svg viewBox="0 0 900 420" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">32 个放大镜各扫一遍 → 32 张激活图</text>

  <!-- Input -->
  <rect x="20" y="160" width="120" height="100" fill="#cbd5e1" stroke="#1e293b" stroke-width="2"/>
  <rect x="50" y="190" width="60" height="40" fill="#1e3a8a"/>
  <text x="80" y="282" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">depth (1, 58, 87)</text>

  <line x1="140" y1="210" x2="200" y2="210" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <text x="170" y="200" font-size="10" fill="#475569" text-anchor="middle">扫描</text>

  <!-- Filter bank (3 shown, "..." indicates more) -->
  <g transform="translate(200,40)">
    <text x="100" y="-5" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">32 个放大镜</text>
    <rect x="0" y="0" width="60" height="60" fill="#d1fae5" stroke="#059669"/>
    <text x="30" y="35" font-size="11" fill="#1e293b" text-anchor="middle">#1 水平边缘</text>
    <rect x="70" y="0" width="60" height="60" fill="#d1fae5" stroke="#059669"/>
    <text x="100" y="35" font-size="11" fill="#1e293b" text-anchor="middle">#2 垂直边缘</text>
    <rect x="140" y="0" width="60" height="60" fill="#d1fae5" stroke="#059669"/>
    <text x="170" y="35" font-size="11" fill="#1e293b" text-anchor="middle">#3 平地</text>
    <text x="220" y="35" font-size="14" fill="#475569" text-anchor="middle">⋯</text>
    <text x="220" y="55" font-size="11" fill="#475569" text-anchor="middle">共 32 个</text>

    <text x="100" y="80" font-size="10" fill="#475569" text-anchor="middle">每个 5×5、互不相同（网络学出来的）</text>
  </g>

  <line x1="430" y1="210" x2="490" y2="210" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- Output: 32 activation maps -->
  <g transform="translate(490,60)">
    <text x="180" y="-5" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">32 张激活图 (32, 54, 83)</text>

    <!-- Map 1 -->
    <rect x="0" y="0" width="100" height="60" fill="#fef9c3" stroke="#a16207"/>
    <rect x="20" y="10" width="60" height="6" fill="#a16207"/>
    <rect x="20" y="42" width="60" height="6" fill="#a16207"/>
    <text x="50" y="78" font-size="10" fill="#475569" text-anchor="middle">#1: 水平边缘亮</text>

    <!-- Map 2 -->
    <rect x="120" y="0" width="100" height="60" fill="#fef9c3" stroke="#a16207"/>
    <rect x="142" y="10" width="6" height="40" fill="#a16207"/>
    <rect x="192" y="10" width="6" height="40" fill="#a16207"/>
    <text x="170" y="78" font-size="10" fill="#475569" text-anchor="middle">#2: 垂直边缘亮</text>

    <!-- Map 3 -->
    <rect x="240" y="0" width="100" height="60" fill="#fef9c3" stroke="#a16207"/>
    <rect x="240" y="45" width="100" height="15" fill="#a16207" opacity="0.5"/>
    <text x="290" y="78" font-size="10" fill="#475569" text-anchor="middle">#3: 地面平地亮</text>

    <!-- More maps -->
    <text x="180" y="120" font-size="14" fill="#475569" text-anchor="middle">⋮ 共 32 张</text>
    <text x="180" y="140" font-size="11" fill="#475569" text-anchor="middle">每张图 54×83 像素</text>
    <text x="180" y="160" font-size="11" fill="#475569" text-anchor="middle">每张显示"该 pattern 在哪些位置匹配"</text>
  </g>

  <!-- Bottom: parameter count -->
  <rect x="20" y="350" width="860" height="55" rx="6" fill="#f1f5f9" stroke="#94a3b8"/>
  <text x="450" y="370" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">参数量 = 32 个放大镜 × 5×5 个权重 + 32 个 bias</text>
  <text x="450" y="390" font-size="12" fill="#475569" text-anchor="middle">= 832 个 — 因为<strong>同一个放大镜在所有位置共享权重</strong>，这是 CNN 高效的根本原因</text>
</svg>
<div class="caption">每个放大镜在整张图扫一遍，产生一张激活图。32 个放大镜 = 32 张激活图。</div>
</div>

<div class="callout callout-cnn">
  <strong>Conv2d 这一层做了什么</strong>
  <p>把"5046 个原始距离数字"翻译成"32 种基础视觉概念，在图中哪里出现"。这一步是 <strong>"原始像素 → 局部 pattern 检测"</strong>。</p>
  <p style="margin-top: 6px;">放大镜里的具体数值（权重）是网络<strong>训出来的</strong> —— 没人告诉它"放大镜 #1 该长成水平边缘检测器"，是 PPO/DAgger 的梯度自动塑造出来的。</p>
</div>

<!-- ============== 4 ============== -->
<h2 id="pool">4. 第 2 层 MaxPool2d(2)：缩小图，保留最强信号</h2>

<p>MaxPool 比 Conv 简单得多 —— 它<strong>没有任何参数</strong>，纯粹是个"取最大值"的操作。每 <code>2×2</code> 块只保留最大值，于是图<strong>缩小一半</strong>。</p>

<div class="svg-wrap">
<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg">
  <text x="350" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">MaxPool2d(kernel=2)：每个 2×2 块取最大值</text>

  <!-- Before -->
  <g transform="translate(50,60)">
    <text x="120" y="-5" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">激活图（4×4 示意）</text>
    <!-- 4x4 grid with values -->
    <rect x="0" y="0" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="30" y="36" font-size="14" text-anchor="middle" fill="#1e293b">1</text>
    <rect x="60" y="0" width="60" height="60" fill="#fde047" stroke="#a16207"/>
    <text x="90" y="36" font-size="14" text-anchor="middle" fill="#1e293b">3</text>
    <rect x="120" y="0" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="150" y="36" font-size="14" text-anchor="middle" fill="#1e293b">2</text>
    <rect x="180" y="0" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="210" y="36" font-size="14" text-anchor="middle" fill="#1e293b">1</text>

    <rect x="0" y="60" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="30" y="96" font-size="14" text-anchor="middle" fill="#1e293b">0</text>
    <rect x="60" y="60" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="90" y="96" font-size="14" text-anchor="middle" fill="#1e293b">2</text>
    <rect x="120" y="60" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="150" y="96" font-size="14" text-anchor="middle" fill="#1e293b">1</text>
    <rect x="180" y="60" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="210" y="96" font-size="14" text-anchor="middle" fill="#1e293b">0</text>

    <rect x="0" y="120" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="30" y="156" font-size="14" text-anchor="middle" fill="#1e293b">4</text>
    <rect x="60" y="120" width="60" height="60" fill="#facc15" stroke="#a16207"/>
    <text x="90" y="156" font-size="14" text-anchor="middle" fill="#1e293b">5</text>
    <rect x="120" y="120" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="150" y="156" font-size="14" text-anchor="middle" fill="#1e293b">0</text>
    <rect x="180" y="120" width="60" height="60" fill="#fde047" stroke="#a16207"/>
    <text x="210" y="156" font-size="14" text-anchor="middle" fill="#1e293b">4</text>

    <rect x="0" y="180" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="30" y="216" font-size="14" text-anchor="middle" fill="#1e293b">1</text>
    <rect x="60" y="180" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="90" y="216" font-size="14" text-anchor="middle" fill="#1e293b">2</text>
    <rect x="120" y="180" width="60" height="60" fill="#fde047" stroke="#a16207"/>
    <text x="150" y="216" font-size="14" text-anchor="middle" fill="#1e293b">3</text>
    <rect x="180" y="180" width="60" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="210" y="216" font-size="14" text-anchor="middle" fill="#1e293b">1</text>

    <!-- 2x2 group highlights -->
    <rect x="0" y="0" width="120" height="120" fill="none" stroke="#dc2626" stroke-width="2.5" stroke-dasharray="4,2"/>
    <rect x="120" y="0" width="120" height="120" fill="none" stroke="#0891b2" stroke-width="2.5" stroke-dasharray="4,2"/>
    <rect x="0" y="120" width="120" height="120" fill="none" stroke="#16a34a" stroke-width="2.5" stroke-dasharray="4,2"/>
    <rect x="120" y="120" width="120" height="120" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-dasharray="4,2"/>
  </g>

  <!-- Arrow -->
  <line x1="320" y1="180" x2="400" y2="180" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <text x="360" y="170" font-size="11" fill="#475569" text-anchor="middle">每块取 max</text>

  <!-- After -->
  <g transform="translate(430,120)">
    <text x="60" y="-5" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">缩小后 (2×2)</text>
    <rect x="0" y="0" width="60" height="60" fill="#fde047" stroke="#dc2626" stroke-width="2.5"/>
    <text x="30" y="36" font-size="16" text-anchor="middle" font-weight="700" fill="#1e293b">3</text>
    <rect x="60" y="0" width="60" height="60" fill="#fef9c3" stroke="#0891b2" stroke-width="2.5"/>
    <text x="90" y="36" font-size="16" text-anchor="middle" font-weight="700" fill="#1e293b">2</text>
    <rect x="0" y="60" width="60" height="60" fill="#facc15" stroke="#16a34a" stroke-width="2.5"/>
    <text x="30" y="96" font-size="16" text-anchor="middle" font-weight="700" fill="#1e293b">5</text>
    <rect x="60" y="60" width="60" height="60" fill="#fde047" stroke="#7c3aed" stroke-width="2.5"/>
    <text x="90" y="96" font-size="16" text-anchor="middle" font-weight="700" fill="#1e293b">4</text>
  </g>

  <!-- Bottom -->
  <text x="350" y="285" font-size="12" fill="#475569" text-anchor="middle">实际网络中：尺寸高宽各除以 2</text>
  <text x="350" y="305" font-size="11" fill="#94a3b8" text-anchor="middle">没有参数 · 不学习 · 纯下采样</text>
</svg>
</div>

<div class="callout callout-cnn">
  <strong>MaxPool 这一层做了什么</strong>
  <ul style="margin: 6px 0 0 20px;">
    <li><strong>省计算</strong>：图变小一半，后续运算量也减半</li>
    <li><strong>平移容忍</strong>：障碍偏一两个像素，下采样后激活图几乎不变</li>
    <li><strong>保留强信号</strong>："只要 2×2 内有匹配点，就算这块匹配了"</li>
  </ul>
</div>

<!-- ============== 5 ============== -->
<h2 id="conv2">5. 第 3 层 Conv2d(32→64, k=3)：组合 pattern 找更复杂的概念</h2>

<p>这一层和第 1 层<strong>结构一样</strong>，但<strong>作用对象不同</strong>：它不是在原始深度图上找 pattern，而是<strong>在前面 32 张激活图的组合上找更高级的 pattern</strong>。</p>

<div class="svg-wrap">
<svg viewBox="0 0 900 340" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">CNN 第 2 层：在 32 张激活图上找"组合 pattern"</text>

  <!-- Input: 32 activation maps -->
  <g transform="translate(30,60)">
    <text x="70" y="-5" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">输入: 32 张激活图</text>
    <rect x="0" y="0" width="120" height="60" fill="#fde047" stroke="#a16207" opacity="0.7"/>
    <rect x="10" y="10" width="120" height="60" fill="#fef9c3" stroke="#a16207" opacity="0.8"/>
    <rect x="20" y="20" width="120" height="60" fill="#fde68a" stroke="#a16207" opacity="0.9"/>
    <rect x="30" y="30" width="120" height="60" fill="#fef9c3" stroke="#a16207"/>
    <text x="90" y="65" font-size="10" fill="#1e293b" text-anchor="middle">水平边缘</text>
    <text x="90" y="78" font-size="9" fill="#475569" text-anchor="middle">⋯</text>
    <text x="90" y="91" font-size="9" fill="#475569" text-anchor="middle">⋯共 32 张</text>
  </g>

  <line x1="200" y1="120" x2="250" y2="120" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- Filter -->
  <g transform="translate(260,60)">
    <text x="60" y="-5" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">64 个新放大镜</text>
    <rect x="0" y="0" width="120" height="80" fill="#d1fae5" stroke="#059669"/>
    <text x="60" y="20" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">每个 3×3×32</text>
    <text x="60" y="40" font-size="10" fill="#475569" text-anchor="middle">(高 × 宽 × 输入通道数)</text>
    <text x="60" y="60" font-size="10" fill="#475569" text-anchor="middle">"看遍 32 张激活图的</text>
    <text x="60" y="73" font-size="10" fill="#475569" text-anchor="middle">同一个 3×3 区域"</text>
  </g>

  <line x1="395" y1="120" x2="445" y2="120" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>

  <!-- Output -->
  <g transform="translate(460,60)">
    <text x="100" y="-5" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">输出: 64 张激活图</text>
    <rect x="0" y="0" width="120" height="60" fill="#bae6fd" stroke="#0891b2" opacity="0.7"/>
    <rect x="10" y="10" width="120" height="60" fill="#bae6fd" stroke="#0891b2" opacity="0.8"/>
    <rect x="20" y="20" width="120" height="60" fill="#bae6fd" stroke="#0891b2" opacity="0.9"/>
    <rect x="30" y="30" width="120" height="60" fill="#bae6fd" stroke="#0891b2"/>
    <text x="90" y="65" font-size="10" fill="#1e293b" text-anchor="middle">更高级概念</text>
    <text x="90" y="78" font-size="9" fill="#475569" text-anchor="middle">⋯</text>
    <text x="90" y="91" font-size="9" fill="#475569" text-anchor="middle">⋯共 64 张</text>
  </g>

  <!-- Example -->
  <g transform="translate(640,40)">
    <text x="120" y="0" font-size="11" font-weight="700" fill="#0891b2" text-anchor="middle">举例：可能学到的</text>
    <text x="120" y="14" font-size="11" font-weight="700" fill="#0891b2" text-anchor="middle">新放大镜代表的概念</text>
    <rect x="0" y="24" width="240" height="100" fill="#ecfeff" stroke="#0891b2"/>
    <text x="10" y="44" font-size="10" fill="#1e293b">• "障碍物角"</text>
    <text x="10" y="60" font-size="9" fill="#475569">  = 水平边缘 + 垂直边缘 同位置</text>
    <text x="10" y="80" font-size="10" fill="#1e293b">• "完整障碍物"</text>
    <text x="10" y="96" font-size="9" fill="#475569">  = 上下都有水平边缘 + 中间近</text>
    <text x="10" y="116" font-size="10" fill="#1e293b">• "前方台阶"</text>
    <text x="10" y="132" font-size="9" fill="#475569">  = 下半平地 + 上半近距离</text>
  </g>

  <!-- Bottom note -->
  <rect x="30" y="225" width="840" height="100" rx="8" fill="#f1f5f9" stroke="#94a3b8"/>
  <text x="450" y="248" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">CNN 的"层级抽象"特点</text>
  <text x="450" y="270" font-size="12" fill="#475569" text-anchor="middle">第 1 层 = 边缘 / 角 / 平地 等<strong>低级视觉特征</strong></text>
  <text x="450" y="288" font-size="12" fill="#475569" text-anchor="middle">第 2 层 = 障碍角 / 完整物体 / 台阶 等<strong>组合的高级概念</strong></text>
  <text x="450" y="306" font-size="12" fill="#475569" text-anchor="middle">层越深 → 表达越抽象（这是 CNN 之于视觉任务的本质优势）</text>
</svg>
</div>

<div class="callout callout-cnn">
  <strong>第 2 层 Conv2d 做了什么</strong>
  <p>把"32 种基础视觉概念的空间分布"组合成"64 种更高级的概念"。CNN 越深的层 = 越抽象的语义。这就像人类视觉皮层的层级处理：V1 找边缘 → V2 找形状 → V4 找物体。</p>
  <p style="margin-top: 6px;">输出 shape: <code>(64, 25, 39)</code> —— 64 个通道，每个通道是 25×39 的激活图。</p>
</div>

<h3>5.1 25 和 39 是怎么算出来的</h3>

<div class="svg-wrap">
<svg viewBox="0 0 900 280" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">尺寸演化追踪</text>

  <!-- Stages -->
  <g font-family="monospace" font-size="13">
    <!-- 0 -->
    <rect x="40" y="50" width="140" height="60" rx="6" fill="#dbeafe" stroke="#2563eb"/>
    <text x="110" y="70" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">输入</text>
    <text x="110" y="92" text-anchor="middle" fill="#1e293b">(1, 58, 87)</text>

    <line x1="180" y1="80" x2="220" y2="80" stroke="#475569" marker-end="url(#ov-arr)"/>
    <text x="200" y="72" font-size="10" fill="#475569" text-anchor="middle">Conv k=5</text>
    <text x="200" y="92" font-size="10" fill="#475569" text-anchor="middle">H−5+1, W−5+1</text>

    <!-- 1 -->
    <rect x="220" y="50" width="140" height="60" rx="6" fill="#d1fae5" stroke="#059669"/>
    <text x="290" y="70" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Conv1 后</text>
    <text x="290" y="92" text-anchor="middle" fill="#1e293b">(32, 54, 83)</text>

    <line x1="360" y1="80" x2="400" y2="80" stroke="#475569" marker-end="url(#ov-arr)"/>
    <text x="380" y="72" font-size="10" fill="#475569" text-anchor="middle">MaxPool</text>
    <text x="380" y="92" font-size="10" fill="#475569" text-anchor="middle">÷ 2</text>

    <!-- 2 -->
    <rect x="400" y="50" width="140" height="60" rx="6" fill="#d1fae5" stroke="#059669"/>
    <text x="470" y="70" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Pool 后</text>
    <text x="470" y="92" text-anchor="middle" fill="#1e293b">(32, 27, 41)</text>

    <line x1="540" y1="80" x2="580" y2="80" stroke="#475569" marker-end="url(#ov-arr)"/>
    <text x="560" y="72" font-size="10" fill="#475569" text-anchor="middle">Conv k=3</text>
    <text x="560" y="92" font-size="10" fill="#475569" text-anchor="middle">H−3+1, W−3+1</text>

    <!-- 3 -->
    <rect x="580" y="50" width="140" height="60" rx="6" fill="#d1fae5" stroke="#059669"/>
    <text x="650" y="70" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Conv2 后</text>
    <text x="650" y="92" text-anchor="middle" font-weight="700" fill="#dc2626">(64, 25, 39) ★</text>

    <line x1="720" y1="80" x2="760" y2="80" stroke="#475569" marker-end="url(#ov-arr)"/>
    <text x="740" y="72" font-size="10" fill="#475569" text-anchor="middle">Flatten</text>

    <!-- 4 -->
    <rect x="760" y="50" width="100" height="60" rx="6" fill="#fed7aa" stroke="#d97706"/>
    <text x="810" y="70" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">摊平</text>
    <text x="810" y="92" text-anchor="middle" fill="#1e293b">(62400,)</text>
  </g>

  <!-- Formula box -->
  <rect x="40" y="150" width="820" height="100" rx="6" fill="#fef9c3" stroke="#a16207"/>
  <text x="450" y="172" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">关键公式（无 padding，stride=1 的 Conv）</text>
  <text x="450" y="195" font-size="12" font-family="monospace" fill="#1e293b" text-anchor="middle">H_out = H_in − kernel + 1     W_out = W_in − kernel + 1</text>
  <text x="450" y="220" font-size="12" fill="#475569" text-anchor="middle">高: 58 → 54 → 27 → 25     宽: 87 → 83 → 41 → 39</text>
  <text x="450" y="240" font-size="12" fill="#475569" text-anchor="middle">最后 <strong>Flatten</strong>: 64 × 25 × 39 = <strong>62,400</strong> 个数字一字排开</text>
</svg>
</div>

<!-- ============== 6 ============== -->
<h2 id="flatten">6. 第 4 层 Flatten：从图像 → 一维向量</h2>

<p>Flatten 是个<strong>纯 reshape 操作</strong>，没有参数、不学习。它把 <code>(64, 25, 39)</code> 的 3D 张量按顺序排成一根 62400 维的长向量。</p>

<div class="svg-wrap">
<svg viewBox="0 0 900 260" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">Flatten: 3D 张量 → 1D 向量</text>

  <!-- 3D cube representation -->
  <g transform="translate(50,60)">
    <text x="100" y="-10" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">(64, 25, 39) 3D 张量</text>
    <!-- Stack of feature maps -->
    <g>
      <rect x="0" y="0" width="180" height="120" fill="#dbeafe" stroke="#2563eb" opacity="0.4"/>
      <rect x="8" y="8" width="180" height="120" fill="#dbeafe" stroke="#2563eb" opacity="0.5"/>
      <rect x="16" y="16" width="180" height="120" fill="#dbeafe" stroke="#2563eb" opacity="0.6"/>
      <rect x="24" y="24" width="180" height="120" fill="#dbeafe" stroke="#2563eb" opacity="0.7"/>
      <rect x="32" y="32" width="180" height="120" fill="#dbeafe" stroke="#2563eb" opacity="0.85"/>
      <rect x="40" y="40" width="180" height="120" fill="#dbeafe" stroke="#2563eb"/>
      <text x="130" y="100" font-size="13" fill="#1e293b" text-anchor="middle">25 × 39 的</text>
      <text x="130" y="118" font-size="13" fill="#1e293b" text-anchor="middle">激活图</text>
      <text x="130" y="138" font-size="12" fill="#475569" text-anchor="middle">叠 64 层</text>
    </g>
  </g>

  <!-- Arrow -->
  <line x1="280" y1="130" x2="380" y2="130" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <text x="330" y="120" font-size="12" fill="#475569" text-anchor="middle">按顺序串起来</text>
  <text x="330" y="148" font-size="11" fill="#475569" text-anchor="middle">不做任何运算</text>

  <!-- 1D vector -->
  <g transform="translate(400,100)">
    <text x="240" y="-10" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">(62400,) 1D 向量</text>
    <!-- Vector visualization - just a long thin bar with divisions -->
    <rect x="0" y="0" width="460" height="40" fill="#fed7aa" stroke="#d97706" stroke-width="2"/>
    <g stroke="#d97706" stroke-width="0.5" opacity="0.5">
      <line x1="23" y1="0" x2="23" y2="40"/>
      <line x1="46" y1="0" x2="46" y2="40"/>
      <line x1="69" y1="0" x2="69" y2="40"/>
      <line x1="92" y1="0" x2="92" y2="40"/>
      <line x1="115" y1="0" x2="115" y2="40"/>
      <line x1="138" y1="0" x2="138" y2="40"/>
      <line x1="161" y1="0" x2="161" y2="40"/>
    </g>
    <text x="60" y="65" font-size="10" fill="#475569" text-anchor="middle">第1张图 25×39 个数</text>
    <text x="60" y="78" font-size="10" fill="#475569" text-anchor="middle">= 前 975 个</text>
    <text x="240" y="65" font-size="10" fill="#475569" text-anchor="middle">第2张图</text>
    <text x="240" y="78" font-size="10" fill="#475569" text-anchor="middle">975~1950</text>
    <text x="430" y="65" font-size="10" fill="#475569" text-anchor="middle">⋯共 64 段</text>
    <text x="430" y="78" font-size="10" fill="#475569" text-anchor="middle">总 62400 个</text>
  </g>

  <!-- Bottom -->
  <rect x="40" y="220" width="820" height="30" rx="6" fill="#f1f5f9" stroke="#94a3b8"/>
  <text x="450" y="240" font-size="12" fill="#475569" text-anchor="middle">Flatten 是"接口转换器"：CNN 输出图像状（3D），Linear 要向量状（1D），中间得有 Flatten 衔接</text>
</svg>
</div>

<!-- ============== 7 ============== -->
<h2 id="mlp">7. 第 5/6 层 Linear：全局信息压缩</h2>

<p>到了 Linear 层，数据已经是 62400 维向量，**包含了所有空间位置上 64 种高级概念的激活强度**。Linear 做的事是<strong>把这些散布在各位置的信息融合成一个全局摘要</strong>。</p>

<h3>7.1 Linear(62400 → 128) 在干什么</h3>

<div class="svg-wrap">
<svg viewBox="0 0 900 360" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">Linear(62400 → 128): 把所有空间信息融合成 128 个全局特征</text>

  <!-- Input vector -->
  <g transform="translate(40,60)">
    <text x="100" y="-5" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">输入 62400D</text>
    <rect x="0" y="0" width="200" height="220" fill="#fed7aa" stroke="#d97706"/>
    <!-- Visualize as vertical bar with markers -->
    <g font-size="9" fill="#475569" text-anchor="end">
      <text x="-5" y="20">x[0]</text>
      <text x="-5" y="40">x[1]</text>
      <text x="-5" y="60">x[2]</text>
      <text x="-5" y="115">⋮</text>
      <text x="-5" y="200">x[62399]</text>
    </g>
    <g stroke="#d97706" opacity="0.4">
      <line x1="0" y1="20" x2="200" y2="20"/>
      <line x1="0" y1="40" x2="200" y2="40"/>
      <line x1="0" y1="60" x2="200" y2="60"/>
      <line x1="0" y1="200" x2="200" y2="200"/>
    </g>
  </g>

  <!-- Multiplication symbol -->
  <text x="280" y="180" font-size="30" font-family="monospace" fill="#1e293b" text-anchor="middle">×</text>

  <!-- Weight matrix -->
  <g transform="translate(310,60)">
    <text x="80" y="-5" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">权重矩阵 W</text>
    <text x="80" y="10" font-size="11" fill="#475569" text-anchor="middle">128 × 62400</text>
    <rect x="0" y="20" width="160" height="200" fill="#bae6fd" stroke="#0891b2"/>
    <!-- Grid -->
    <g stroke="#0891b2" stroke-width="0.5" opacity="0.3">
      <line x1="40" y1="20" x2="40" y2="220"/>
      <line x1="80" y1="20" x2="80" y2="220"/>
      <line x1="120" y1="20" x2="120" y2="220"/>
      <line x1="0" y1="60" x2="160" y2="60"/>
      <line x1="0" y1="100" x2="160" y2="100"/>
      <line x1="0" y1="140" x2="160" y2="140"/>
      <line x1="0" y1="180" x2="160" y2="180"/>
    </g>
    <text x="80" y="125" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">~800 万个</text>
    <text x="80" y="145" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">权重</text>
  </g>

  <!-- Equal sign -->
  <text x="510" y="180" font-size="30" font-family="monospace" fill="#1e293b" text-anchor="middle">=</text>

  <!-- Output -->
  <g transform="translate(540,90)">
    <text x="60" y="-5" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">输出 128D</text>
    <rect x="0" y="0" width="120" height="160" fill="#fef9c3" stroke="#a16207" stroke-width="2"/>
    <g font-size="9" fill="#475569" text-anchor="end">
      <text x="-5" y="20">y[0]</text>
      <text x="-5" y="40">y[1]</text>
      <text x="-5" y="80">⋮</text>
      <text x="-5" y="148">y[127]</text>
    </g>
    <g stroke="#a16207" opacity="0.4">
      <line x1="0" y1="20" x2="120" y2="20"/>
      <line x1="0" y1="40" x2="120" y2="40"/>
      <line x1="0" y1="148" x2="120" y2="148"/>
    </g>
  </g>

  <!-- Annotation -->
  <g transform="translate(700,90)">
    <text x="0" y="0" font-size="12" font-weight="700" fill="#dc2626">每个 y[i] 的含义：</text>
    <text x="0" y="22" font-size="11" fill="#1e293b">y[i] = W[i,0]·x[0]</text>
    <text x="0" y="38" font-size="11" fill="#1e293b">    + W[i,1]·x[1]</text>
    <text x="0" y="54" font-size="11" fill="#1e293b">    + ⋯</text>
    <text x="0" y="70" font-size="11" fill="#1e293b">    + W[i,62399]·x[62399]</text>
    <text x="0" y="86" font-size="11" fill="#1e293b">    + bias</text>
    <text x="0" y="115" font-size="11" fill="#475569">= 62400 个输入的</text>
    <text x="0" y="131" font-size="11" fill="#475569">  加权组合</text>
  </g>

  <!-- Bottom note -->
  <rect x="40" y="305" width="820" height="40" rx="6" fill="#f1f5f9" stroke="#94a3b8"/>
  <text x="450" y="330" font-size="12" fill="#475569" text-anchor="middle">
    每个 y[i] = "这 62400 个数应该按某种权重组合起来，代表某种全局意义" — 网络自己学这些权重
  </text>
</svg>
</div>

<h3>7.2 Linear(128 → 32) 最终压缩</h3>

<p>再来一次 Linear，把 128 维压成 32 维。这一步是最后的"语义提炼"：</p>

<div class="svg-wrap">
<svg viewBox="0 0 900 240" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">Linear(128 → 32): 最终对接 Actor 的格式</text>

  <!-- 128D -->
  <g transform="translate(80,50)">
    <text x="60" y="-5" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">128D 抽象表征</text>
    <rect x="0" y="0" width="120" height="140" fill="#fef9c3" stroke="#a16207"/>
    <text x="60" y="78" font-size="13" fill="#1e293b" text-anchor="middle">128 个抽象</text>
    <text x="60" y="96" font-size="13" fill="#1e293b" text-anchor="middle">高级特征</text>
  </g>

  <line x1="220" y1="120" x2="320" y2="120" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <text x="270" y="110" font-size="11" fill="#475569" text-anchor="middle">Linear(128→32)</text>
  <text x="270" y="138" font-size="11" fill="#475569" text-anchor="middle">~4k 参数</text>

  <!-- 32D -->
  <g transform="translate(360,50)">
    <text x="60" y="-5" font-size="12" font-weight="700" fill="#dc2626" text-anchor="middle">32D depth_feat ★</text>
    <rect x="0" y="0" width="120" height="140" fill="#fed7aa" stroke="#d97706" stroke-width="2.5"/>
    <text x="60" y="78" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">32 个数字</text>
    <text x="60" y="96" font-size="11" fill="#475569" text-anchor="middle">分布式编码</text>
    <text x="60" y="112" font-size="11" fill="#475569" text-anchor="middle">地形语义</text>
  </g>

  <!-- Annotation -->
  <g transform="translate(540,60)">
    <text x="0" y="0" font-size="12" font-weight="700" fill="#0891b2">每个 32D 维度可能编码（举例）：</text>
    <text x="0" y="22" font-size="11" fill="#1e293b">• 维度 1 ≈ 前方障碍物的高度</text>
    <text x="0" y="40" font-size="11" fill="#1e293b">• 维度 2 ≈ 距离障碍物多远</text>
    <text x="0" y="58" font-size="11" fill="#1e293b">• 维度 3 ≈ 左侧通路宽度</text>
    <text x="0" y="76" font-size="11" fill="#1e293b">• 维度 4 ≈ 右侧通路宽度</text>
    <text x="0" y="94" font-size="11" fill="#1e293b">• ⋮</text>
    <text x="0" y="116" font-size="11" fill="#475569">（网络自定义的语义，</text>
    <text x="0" y="132" font-size="11" fill="#475569">  未必有这么清晰的人类可读含义）</text>
  </g>
</svg>
</div>

<div class="callout callout-mlp">
  <strong>MLP 这两层做了什么</strong>
  <p>把 CNN 提取出的"分布在各空间位置的高级视觉特征"（62400 维）<strong>融合压缩</strong>成对决策有用的紧凑表征（32 维）。这一步是从"视觉感知"过渡到"决策准备"的桥梁。</p>
  <p style="margin-top: 6px;">参数量主要集中在 <code>Linear(62400→128)</code> 这一层（~800 万），是整个 DepthEncoder 最重的部分。</p>
</div>

<!-- ============== 8 ============== -->
<h2 id="gru">8. RecurrentDepthBackbone：时序融合</h2>

<p>到目前为止我们处理的都是<strong>单帧深度图</strong>。但机器人是连续运动的，<strong>多帧深度图含有时序信息</strong>（比如障碍物接近的速度），单帧丢失这部分。所以最后加一段 GRU 做时序融合。</p>

<h3>8.1 RecurrentDepthBackbone 的内部结构</h3>

<div class="svg-wrap">
<svg viewBox="0 0 900 360" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">RecurrentDepthBackbone：CNN 输出 + 本体观测 → 时序融合 → 最终 latent</text>

  <!-- Inputs -->
  <rect x="30" y="60" width="140" height="40" rx="6" fill="#fed7aa" stroke="#d97706"/>
  <text x="100" y="84" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">depth_feat (32D)</text>
  <text x="100" y="118" font-size="10" fill="#475569" text-anchor="middle">CNN 模块的输出</text>

  <rect x="30" y="160" width="140" height="40" rx="6" fill="#dbeafe" stroke="#2563eb"/>
  <text x="100" y="184" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">prop (31D)</text>
  <text x="100" y="218" font-size="10" fill="#475569" text-anchor="middle">本体观测</text>

  <!-- Concat -->
  <line x1="170" y1="80" x2="220" y2="120" stroke="#475569" stroke-width="1.5"/>
  <line x1="170" y1="180" x2="220" y2="140" stroke="#475569" stroke-width="1.5"/>
  <rect x="220" y="110" width="100" height="40" rx="6" fill="#f1f5f9" stroke="#475569"/>
  <text x="270" y="135" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">concat (63D)</text>

  <!-- combination MLP -->
  <line x1="320" y1="130" x2="350" y2="130" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <rect x="350" y="100" width="160" height="60" rx="6" fill="#fed7aa" stroke="#d97706"/>
  <text x="430" y="122" font-size="12" font-weight="700" fill="#d97706" text-anchor="middle">combination_mlp</text>
  <text x="430" y="140" font-size="11" fill="#475569" text-anchor="middle">Linear(63→128)</text>
  <text x="430" y="155" font-size="11" fill="#475569" text-anchor="middle">→ Linear(→32)</text>

  <!-- GRU -->
  <line x1="510" y1="130" x2="540" y2="130" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <rect x="540" y="80" width="160" height="100" rx="6" fill="#fce7f3" stroke="#be185d" stroke-width="2"/>
  <text x="620" y="105" font-size="12" font-weight="700" fill="#be185d" text-anchor="middle">GRU</text>
  <text x="620" y="125" font-size="11" fill="#475569" text-anchor="middle">输入: 32D</text>
  <text x="620" y="142" font-size="11" fill="#475569" text-anchor="middle">hidden state: 512D</text>
  <text x="620" y="160" font-size="11" fill="#475569" text-anchor="middle">输出: 512D</text>

  <!-- Hidden state loop -->
  <path d="M 700 100 Q 730 70 720 50 Q 690 30 580 30 Q 540 30 540 80" stroke="#dc2626" stroke-width="2" fill="none" stroke-dasharray="4,3" marker-end="url(#ov-arr)"/>
  <text x="620" y="22" font-size="10" font-weight="700" fill="#dc2626" text-anchor="middle">hidden state 自循环（记忆上一时刻）</text>

  <!-- Output MLP -->
  <line x1="700" y1="130" x2="730" y2="130" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <rect x="730" y="100" width="140" height="60" rx="6" fill="#fed7aa" stroke="#d97706"/>
  <text x="800" y="122" font-size="12" font-weight="700" fill="#d97706" text-anchor="middle">output_mlp</text>
  <text x="800" y="140" font-size="11" fill="#475569" text-anchor="middle">Linear(512→34)</text>
  <text x="800" y="155" font-size="11" fill="#475569" text-anchor="middle">+ Tanh</text>

  <!-- Final output -->
  <line x1="800" y1="160" x2="800" y2="200" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
  <rect x="720" y="200" width="160" height="50" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2.5"/>
  <text x="800" y="222" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">depth_latent (32D)</text>
  <text x="800" y="240" font-size="10" fill="#dc2626" text-anchor="middle">★ 取前 32 维注入 Actor</text>

  <!-- Bottom annotation -->
  <rect x="30" y="280" width="840" height="65" rx="6" fill="#f1f5f9" stroke="#94a3b8"/>
  <text x="450" y="300" font-size="13" font-weight="700" fill="#1e293b" text-anchor="middle">三段协作</text>
  <text x="450" y="318" font-size="11" fill="#475569" text-anchor="middle">① combination_mlp 把视觉特征 + 本体观测<strong>融合</strong>（机器人既看到障碍，也知道自己当前姿态）</text>
  <text x="450" y="335" font-size="11" fill="#475569" text-anchor="middle">② GRU 把当前帧和<strong>历史多帧</strong>的融合特征整合，得到平滑的时序表征；③ output_mlp 压回 32D</text>
</svg>
</div>

<h3>8.2 GRU 的核心思想：一个会记忆的盒子</h3>

<div class="svg-wrap">
<svg viewBox="0 0 900 340" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">GRU 在多帧上展开：每个时间步它"看一眼新输入 + 参考之前的记忆"</text>

  <!-- Time axis -->
  <line x1="60" y1="240" x2="850" y2="240" stroke="#94a3b8" stroke-width="1"/>
  <text x="60" y="265" font-size="11" fill="#475569">t=0</text>
  <text x="220" y="265" font-size="11" fill="#475569">t=1</text>
  <text x="380" y="265" font-size="11" fill="#475569">t=2</text>
  <text x="540" y="265" font-size="11" fill="#475569">t=3</text>
  <text x="700" y="265" font-size="11" fill="#475569">t=4 (当前)</text>

  <!-- GRU cells at each time step -->
  <g>
    <!-- t=0 -->
    <rect x="40" y="120" width="80" height="80" rx="8" fill="#fce7f3" stroke="#be185d" stroke-width="2"/>
    <text x="80" y="155" font-size="12" font-weight="700" fill="#be185d" text-anchor="middle">GRU</text>
    <text x="80" y="175" font-size="10" fill="#1e293b" text-anchor="middle">h_0</text>

    <!-- input arrow -->
    <line x1="80" y1="220" x2="80" y2="200" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
    <text x="80" y="234" font-size="10" fill="#475569" text-anchor="middle">depth_t0</text>

    <!-- t=1 -->
    <rect x="200" y="120" width="80" height="80" rx="8" fill="#fce7f3" stroke="#be185d" stroke-width="2"/>
    <text x="240" y="155" font-size="12" font-weight="700" fill="#be185d" text-anchor="middle">GRU</text>
    <text x="240" y="175" font-size="10" fill="#1e293b" text-anchor="middle">h_1</text>
    <line x1="240" y1="220" x2="240" y2="200" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
    <text x="240" y="234" font-size="10" fill="#475569" text-anchor="middle">depth_t1</text>

    <!-- t=2 -->
    <rect x="360" y="120" width="80" height="80" rx="8" fill="#fce7f3" stroke="#be185d" stroke-width="2"/>
    <text x="400" y="155" font-size="12" font-weight="700" fill="#be185d" text-anchor="middle">GRU</text>
    <text x="400" y="175" font-size="10" fill="#1e293b" text-anchor="middle">h_2</text>
    <line x1="400" y1="220" x2="400" y2="200" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
    <text x="400" y="234" font-size="10" fill="#475569" text-anchor="middle">depth_t2</text>

    <!-- t=3 -->
    <rect x="520" y="120" width="80" height="80" rx="8" fill="#fce7f3" stroke="#be185d" stroke-width="2"/>
    <text x="560" y="155" font-size="12" font-weight="700" fill="#be185d" text-anchor="middle">GRU</text>
    <text x="560" y="175" font-size="10" fill="#1e293b" text-anchor="middle">h_3</text>
    <line x1="560" y1="220" x2="560" y2="200" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
    <text x="560" y="234" font-size="10" fill="#475569" text-anchor="middle">depth_t3</text>

    <!-- t=4 (current) -->
    <rect x="680" y="120" width="80" height="80" rx="8" fill="#fce7f3" stroke="#be185d" stroke-width="3"/>
    <text x="720" y="155" font-size="12" font-weight="700" fill="#be185d" text-anchor="middle">GRU</text>
    <text x="720" y="175" font-size="10" font-weight="700" fill="#dc2626" text-anchor="middle">h_4 ★</text>
    <line x1="720" y1="220" x2="720" y2="200" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
    <text x="720" y="234" font-size="10" fill="#475569" text-anchor="middle">depth_t4</text>

    <!-- Hidden state passing -->
    <line x1="120" y1="160" x2="200" y2="160" stroke="#dc2626" stroke-width="2" marker-end="url(#ov-arr)"/>
    <line x1="280" y1="160" x2="360" y2="160" stroke="#dc2626" stroke-width="2" marker-end="url(#ov-arr)"/>
    <line x1="440" y1="160" x2="520" y2="160" stroke="#dc2626" stroke-width="2" marker-end="url(#ov-arr)"/>
    <line x1="600" y1="160" x2="680" y2="160" stroke="#dc2626" stroke-width="2" marker-end="url(#ov-arr)"/>

    <!-- Output -->
    <line x1="720" y1="120" x2="720" y2="80" stroke="#475569" stroke-width="1.5" marker-end="url(#ov-arr)"/>
    <rect x="660" y="50" width="120" height="30" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
    <text x="720" y="71" font-size="11" font-weight="700" fill="#1e293b" text-anchor="middle">输出 depth_latent</text>
  </g>

  <!-- Annotation -->
  <text x="270" y="115" font-size="11" font-weight="700" fill="#dc2626" text-anchor="middle">"记忆" h 传给下一步</text>
  <text x="270" y="100" font-size="10" fill="#475569" text-anchor="middle">每步的 hidden state 包含"截至目前所有看过的信息"</text>

  <text x="450" y="290" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">h_t = f(h_{t-1}, depth_t)</text>
  <text x="450" y="310" font-size="11" fill="#475569" text-anchor="middle">当前 hidden = 上一步 hidden + 当前输入 的非线性融合</text>
  <text x="450" y="328" font-size="11" fill="#475569" text-anchor="middle">这就是 GRU 实现"时序记忆"的本质 — 隐状态在时间上滚动累积</text>
</svg>
</div>

<div class="callout callout-gru">
  <strong>GRU 这一段做了什么</strong>
  <ul style="margin: 6px 0 0 20px;">
    <li><strong>时序平滑</strong>：单帧深度的瞬态噪声（某像素跳一下）被多帧融合后平均掉</li>
    <li><strong>运动感知</strong>：通过对比当前 vs 上一帧，隐含编码出"障碍物接近速度"</li>
    <li><strong>记忆持续</strong>：即便某一帧深度严重受干扰，GRU hidden state 还保存着前几帧的"理解"，行为不会跳变</li>
  </ul>
  <p style="margin-top: 6px;">实战中：你训练完后跑 play，机器人在某些复杂地形下能展示出"提前预判"的行为 —— 这就是 GRU 时序记忆的功劳。</p>
</div>

<!-- ============== 9 ============== -->
<h2 id="paramcount">9. 参数量对比：为什么不能用纯 MLP 处理深度图</h2>

<p>有人会问：MLP 理论上能逼近任何函数，为什么处理深度图不直接用 MLP？答案是<strong>参数量爆炸 + 没有空间归纳偏置</strong>。</p>

<div class="svg-wrap">
<svg viewBox="0 0 900 380" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">参数量对比（log 尺度）</text>

  <!-- Bars -->
  <g transform="translate(80,60)">
    <!-- Pure MLP first layer -->
    <text x="80" y="22" font-size="12" font-weight="700" fill="#1e293b">纯 MLP 第一层 Linear(5046→128)</text>
    <rect x="0" y="30" width="450" height="35" fill="#dc2626"/>
    <text x="240" y="53" font-size="13" font-weight="700" fill="#ffffff" text-anchor="middle">645,888 个参数</text>

    <!-- CNN Conv1 -->
    <text x="80" y="105" font-size="12" font-weight="700" fill="#1e293b">CNN 第 1 层 Conv2d(1→32, k=5)</text>
    <rect x="0" y="113" width="3" height="35" fill="#059669"/>
    <text x="100" y="135" font-size="12" font-weight="700" fill="#1e293b">832 个参数</text>
    <text x="100" y="150" font-size="10" fill="#475569">(32 个 5×5 放大镜 + 32 bias)</text>

    <!-- CNN Conv2 -->
    <text x="80" y="185" font-size="12" font-weight="700" fill="#1e293b">CNN 第 2 层 Conv2d(32→64, k=3)</text>
    <rect x="0" y="193" width="13" height="35" fill="#059669"/>
    <text x="100" y="215" font-size="12" font-weight="700" fill="#1e293b">18,496 个参数</text>
    <text x="100" y="230" font-size="10" fill="#475569">(64 个 3×3×32 放大镜 + 64 bias)</text>

    <!-- Linear 62400 (in actual pipeline) -->
    <text x="80" y="265" font-size="12" font-weight="700" fill="#1e293b">实际 Linear(62400→128)</text>
    <rect x="0" y="273" width="600" height="35" fill="#d97706"/>
    <text x="300" y="296" font-size="13" font-weight="700" fill="#ffffff" text-anchor="middle">7,987,328 个参数</text>
  </g>

  <!-- Conclusion box -->
  <rect x="30" y="335" width="840" height="40" rx="6" fill="#f1f5f9" stroke="#94a3b8"/>
  <text x="450" y="360" font-size="12" fill="#475569" text-anchor="middle">
    <strong>关键观察</strong>: CNN 用 ~20k 参数学到 64 种空间特征，纯 MLP 用 ~645k 参数才把 5046 像素压成 128D — 而且后者效果通常更差
  </text>
</svg>
</div>

<h3>9.1 为什么 CNN 参数少还更有效</h3>

<table>
  <tr><th>纯 MLP 的问题</th><th>CNN 的优势</th></tr>
  <tr>
    <td>每个像素位置都有独立权重，<strong>不共享</strong></td>
    <td>同一个 5×5 放大镜<strong>在所有位置共享</strong>权重</td>
  </tr>
  <tr>
    <td>把 5046 个像素当 5046 个独立数字处理，<strong>不知道哪两个像素是邻居</strong></td>
    <td>卷积只看局部 5×5 邻域，<strong>天然利用空间结构</strong></td>
  </tr>
  <tr>
    <td>图像稍微平移，激活模式完全不同，必须重新学</td>
    <td>权重共享 + 局部感受野 → <strong>translation invariance</strong>，平移后输出几乎不变</td>
  </tr>
  <tr>
    <td>需要海量数据才能学到"边缘"这种基本概念</td>
    <td>归纳偏置自带"局部 pattern 假设"，少量数据就能学好</td>
  </tr>
</table>

<!-- ============== 10 ============== -->
<h2 id="analogy">10. 类比：人类视觉皮层的层级处理</h2>

<p>DepthEncoder 的"CNN + MLP + GRU"架构和人类视觉系统的处理方式<strong>高度同构</strong>。这不是巧合 —— CNN 本身就是从视觉皮层研究里得到灵感。</p>

<div class="svg-wrap">
<svg viewBox="0 0 900 380" xmlns="http://www.w3.org/2000/svg">
  <text x="450" y="22" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">人类视觉系统 vs DepthEncoder 架构对照</text>

  <!-- Human side -->
  <g transform="translate(50,60)">
    <text x="180" y="-5" font-size="13" font-weight="700" fill="#0891b2" text-anchor="middle">人类视觉处理流程</text>

    <rect x="0" y="0" width="360" height="50" rx="6" fill="#cffafe" stroke="#0891b2"/>
    <text x="180" y="22" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">视网膜 / 光感受器</text>
    <text x="180" y="38" font-size="11" fill="#475569" text-anchor="middle">接收光信号，输出像素级强度</text>

    <line x1="180" y1="50" x2="180" y2="70" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="70" width="360" height="50" rx="6" fill="#cffafe" stroke="#0891b2"/>
    <text x="180" y="92" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">V1（初级视觉皮层）</text>
    <text x="180" y="108" font-size="11" fill="#475569" text-anchor="middle">检测边缘、朝向、对比度</text>

    <line x1="180" y1="120" x2="180" y2="140" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="140" width="360" height="50" rx="6" fill="#cffafe" stroke="#0891b2"/>
    <text x="180" y="162" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">V2 / V4</text>
    <text x="180" y="178" font-size="11" fill="#475569" text-anchor="middle">把边缘组合成形状、纹理、物体</text>

    <line x1="180" y1="190" x2="180" y2="210" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="210" width="360" height="50" rx="6" fill="#cffafe" stroke="#0891b2"/>
    <text x="180" y="232" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">下颞叶 IT</text>
    <text x="180" y="248" font-size="11" fill="#475569" text-anchor="middle">物体识别 + 场景理解</text>

    <line x1="180" y1="260" x2="180" y2="280" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="280" width="360" height="50" rx="6" fill="#cffafe" stroke="#0891b2"/>
    <text x="180" y="302" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">海马 / 工作记忆</text>
    <text x="180" y="318" font-size="11" fill="#475569" text-anchor="middle">结合短时记忆，整合"刚才看到的"</text>
  </g>

  <!-- Arrows mapping -->
  <g stroke="#7c3aed" stroke-width="2" stroke-dasharray="4,3">
    <line x1="420" y1="85" x2="480" y2="85" marker-end="url(#ov-arr)"/>
    <line x1="420" y1="155" x2="480" y2="155" marker-end="url(#ov-arr)"/>
    <line x1="420" y1="225" x2="480" y2="225" marker-end="url(#ov-arr)"/>
    <line x1="420" y1="295" x2="480" y2="345" marker-end="url(#ov-arr)"/>
  </g>

  <!-- Robot side -->
  <g transform="translate(490,60)">
    <text x="180" y="-5" font-size="13" font-weight="700" fill="#d97706" text-anchor="middle">DepthEncoder 流程</text>

    <rect x="0" y="0" width="360" height="50" rx="6" fill="#dbeafe" stroke="#2563eb"/>
    <text x="180" y="22" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">RayCasterCamera / Depth 传感器</text>
    <text x="180" y="38" font-size="11" fill="#475569" text-anchor="middle">输出 87×58 像素的距离值</text>

    <line x1="180" y1="50" x2="180" y2="70" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="70" width="360" height="50" rx="6" fill="#d1fae5" stroke="#059669"/>
    <text x="180" y="92" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Conv2d 第 1 层</text>
    <text x="180" y="108" font-size="11" fill="#475569" text-anchor="middle">检测水平 / 垂直边缘、平地</text>

    <line x1="180" y1="120" x2="180" y2="140" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="140" width="360" height="50" rx="6" fill="#d1fae5" stroke="#059669"/>
    <text x="180" y="162" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">MaxPool + Conv2d 第 2 层</text>
    <text x="180" y="178" font-size="11" fill="#475569" text-anchor="middle">组合成障碍角、台阶、整体形状</text>

    <line x1="180" y1="190" x2="180" y2="210" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="210" width="360" height="50" rx="6" fill="#fed7aa" stroke="#d97706"/>
    <text x="180" y="232" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">Flatten + Linear 层</text>
    <text x="180" y="248" font-size="11" fill="#475569" text-anchor="middle">融合全局信息成 32D 决策表征</text>

    <line x1="180" y1="260" x2="180" y2="280" stroke="#475569" marker-end="url(#ov-arr)"/>

    <rect x="0" y="280" width="360" height="50" rx="6" fill="#fce7f3" stroke="#be185d"/>
    <text x="180" y="302" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">GRU 时序融合</text>
    <text x="180" y="318" font-size="11" fill="#475569" text-anchor="middle">累积多帧记忆，输出最终 latent</text>
  </g>
</svg>
</div>

<div class="callout">
  <strong>设计哲学的同构</strong>
  <p>无论是人脑还是机器学习网络，处理高维感知信号的最有效方式都是<strong>"低级特征 → 局部组合 → 全局抽象 → 时序整合"</strong>这条流水线。这是一个被生物进化和机器学习研究<strong>双重验证</strong>的好结构。</p>
</div>

<hr>

<!-- ============== 12 ============== -->
<h2>12. 一句话回顾</h2>

<table>
  <tr><th>层</th><th>做的事</th><th>类比</th></tr>
  <tr><td><code>Conv2d(1→32, k=5)</code></td><td>在原始深度图上扫 32 种局部 pattern</td><td>V1 检测边缘</td></tr>
  <tr><td><code>MaxPool2d(2)</code></td><td>缩小图，保留强信号</td><td>视觉信息粗略化</td></tr>
  <tr><td><code>Conv2d(32→64, k=3)</code></td><td>组合低级 pattern 成 64 种高级概念</td><td>V2/V4 组合形状</td></tr>
  <tr><td><code>Flatten</code></td><td>把 3D 张量摊平成 1D 向量</td><td>接口转换</td></tr>
  <tr><td><code>Linear(62400→128)</code></td><td>全局信息融合压缩</td><td>高级皮层抽象</td></tr>
  <tr><td><code>Linear(128→32)</code></td><td>最终对接 Actor 期待格式</td><td>决策准备</td></tr>
  <tr><td><code>combination_mlp + GRU + output_mlp</code></td><td>融合本体观测 + 时序累积 → 32D depth_latent</td><td>短时记忆 + 决策</td></tr>
</table>

<p style="text-align: center; margin-top: 40px; color: var(--muted); font-size: 13px;">
  本文聚焦 DepthEncoder 的内部机制
</p>

</div>

</div>

<style>
.de-doc {
    --de-accent: #c2410c;
    --de-accent-soft: #fff7ed;
    --de-cnn: #047857;  --de-cnn-soft: #d1fae5;
    --de-mlp: #b45309;  --de-mlp-soft: #fef3c7;
    --de-gru: #9d174d;  --de-gru-soft: #fce7f3;
    --de-border: var(--border, #e7e5e4);
    --de-code-bg: var(--bg-code, #f5f5f4);
    --de-muted: var(--text-soft, #525252);
    font-size: 15.5px;
    line-height: 1.8;
    color: var(--text);
}
.de-doc h2 {
    color: var(--de-accent);
    border-top: none;
    border-left: 3px solid var(--de-accent);
    padding: 0 0 0 0.75rem;
    margin: 3rem 0 1rem;
    font-size: 1.35rem;
}
.de-doc h3 { margin: 2rem 0 0.6rem; font-size: 1.1rem; }
.de-doc h4 { margin: 1.5rem 0 0.5rem; font-size: 0.95rem; color: var(--de-muted); }
.de-doc p { margin: 0 0 0.9rem; }
.de-doc code {
    background: var(--de-code-bg);
    padding: 1px 6px;
    border-radius: 4px;
    border: 1px solid var(--border-soft, #f0efed);
    font-family: var(--font-mono);
    font-size: 0.88em;
    color: var(--accent-hover, #9a3412);
}
.de-doc table {
    width: 100%; border-collapse: collapse; margin: 1.25rem 0;
    background: #fff; border-radius: 6px; overflow: hidden;
    display: block; overflow-x: auto; font-size: 0.88rem;
}
.de-doc th, .de-doc td {
    padding: 0.6rem 0.85rem; text-align: left;
    border-bottom: 1px solid var(--de-border); vertical-align: top;
}
.de-doc th { background: var(--de-code-bg); font-weight: 600; }
.de-doc td code { background: #fff; border: 1px solid var(--de-border); }
.de-doc .callout {
    background: var(--de-accent-soft); border-left: 4px solid var(--de-accent);
    padding: 0.75rem 1rem; border-radius: 4px; margin: 1rem 0; font-size: 0.92rem;
}
.de-doc .callout strong { color: var(--de-accent); }
.de-doc .callout-cnn { background: var(--de-cnn-soft); border-left-color: var(--de-cnn); }
.de-doc .callout-cnn strong { color: var(--de-cnn); }
.de-doc .callout-mlp { background: var(--de-mlp-soft); border-left-color: var(--de-mlp); }
.de-doc .callout-mlp strong { color: var(--de-mlp); }
.de-doc .callout-gru { background: var(--de-gru-soft); border-left-color: var(--de-gru); }
.de-doc .callout-gru strong { color: var(--de-gru); }
.de-doc svg { display: block; margin: 1rem auto; max-width: 100%; height: auto; }
.de-doc .svg-wrap {
    background: #fff; border: 1px solid var(--de-border); border-radius: 8px;
    padding: 0.75rem; margin: 1.25rem auto;
}
.de-doc .caption { text-align: center; color: var(--de-muted); font-size: 0.82rem; margin-top: 0.25rem; }
.de-doc hr { border: none; border-top: 1px dashed var(--de-border); margin: 2.5rem 0; }
.de-doc ul li { margin-bottom: 0.3rem; }
.de-doc .toc {
    background: var(--bg-soft); border: 1px solid var(--de-border); border-radius: 8px;
    padding: 1rem 1.5rem; margin-bottom: 2rem;
}
.de-doc .toc h3 {
    margin: 0 0 0.6rem; font-size: 0.72rem; color: var(--de-muted);
    text-transform: uppercase; letter-spacing: 0.12em; font-family: var(--font-mono);
}
.de-doc .toc ol { margin: 0; padding-left: 1.25rem; columns: 2; column-gap: 2rem; }
.de-doc .toc a { color: var(--text); text-decoration: none; }
.de-doc .toc a:hover { color: var(--de-accent); }
@media (max-width: 600px) {
    .de-doc .toc ol { columns: 1; }
}
</style>
