---
layout: post
title: "Tailscale 异地组网踩坑记：打洞为什么失败，DERP 为什么慢，最后为什么掏钱了事"
date: 2026-06-13 00:30:00 +0800
categories: [网络]
tags: [Tailscale, NAT穿透, DERP, WireGuard, 异地组网]
author: "Dragonking"
excerpt: "折腾了两天 Tailscale：公网 IP 申请不到、打洞打不通、官方中继延迟三位数、自建 DERP 卡在域名证书，最后在淘宝花十几块钱买了个国内中继节点，瞬间通畅。这篇文章把这条决策链上每一步的原理和取舍讲清楚。"
---

## 两天的折腾，一条完整的决策链

需求很朴素：家里的台式机、随身的笔记本和手机，在不同城市、不同网络下能互相访问——远程开发、传文件、连家里的服务。装上 Tailscale 十分钟就"通"了，然后问题来了：ping 一下 200 多毫秒，SSH 打字一卡一卡，时不时还断流。

接下来两天，我把"多设备异地互联"这条技术栈从头到尾走了一遍：查公网 IP（申请不到）→ 研究打洞（打不通）→ 看官方中继（慢得没法用）→ 尝试自建中继（卡在域名和证书）→ 最后在淘宝买了个现成的国内中继节点，延迟从 200ms 掉到 40ms，十几块钱一个月，了事。

这篇文章把每一步"为什么会这样"讲清楚。如果你也在折腾异地组网，可以直接抄最后的决策表。

## 直觉：两个不让外人进门的小区

先把 NAT 穿透这件事讲成人话。

两台设备都躲在路由器后面，就像两个人各自住在**只许出、不许进**的封闭小区里：你可以随时出门找别人，但陌生人不能进小区找你。现在两个人想见面，有三种办法：

1. **有一方住在临街的房子**（公网 IP）——另一方直接上门，最简单，但现在临街房极其稀缺。
2. **约在各自小区门口碰头**（打洞）——两人同时出门，在门口"擦肩"的瞬间互相认识了，门卫以为对方是自己人放了进来。需要两边门卫的规则都比较宽松，时机也要掐准。
3. **找个咖啡馆中转**（中继）——双方都主动去同一家咖啡馆，让服务员传话。一定能见上，但咖啡馆离得远，传一句话要跑很远的路。

Tailscale 的策略就是按这个顺序来的：能直连就直连，能打洞就打洞，都不行就走中继——它管这个中继叫 DERP（Designated Encrypted Relay for Packets，指定加密包中继）。我那 200ms 的延迟，就是因为前两条路全堵死了，流量默默绕道了海外的"咖啡馆"。

<svg viewBox="0 0 640 320" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <defs>
    <marker id="arr-relay" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L9,3 L0,6 z" fill="var(--primary-color)"/>
    </marker>
  </defs>
  <!-- DERP 服务器 -->
  <rect x="265" y="30" width="110" height="50" rx="8" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
  <text x="320" y="51" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">DERP 中继</text>
  <text x="320" y="69" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">（公网服务器）</text>
  <!-- 设备 A -->
  <rect x="40" y="200" width="120" height="70" rx="8" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="100" y="228" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">设备 A</text>
  <text x="100" y="248" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">家宽 · CGNAT 后</text>
  <!-- 设备 B -->
  <rect x="480" y="200" width="120" height="70" rx="8" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="540" y="228" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">设备 B</text>
  <text x="540" y="248" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">手机热点 · CGNAT 后</text>
  <!-- 中继路径 -->
  <path d="M 110 196 L 282 86" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-relay)"/>
  <path d="M 358 86 L 530 196" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arr-relay)"/>
  <text x="160 " y="130" fill="var(--primary-color)" font-family="Inter, sans-serif" font-size="12">出站连接 ✓</text>
  <text x="430" y="130" fill="var(--primary-color)" font-family="Inter, sans-serif" font-size="12">出站连接 ✓</text>
  <!-- 直连失败路径 -->
  <path d="M 165 235 L 475 235" stroke="var(--text-secondary)" stroke-width="2" stroke-dasharray="7 5"/>
  <text x="320" y="225" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">打洞直连 ✗（双方都进不了对方的门）</text>
  <!-- 图注 -->
  <text x="320" y="305" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">两端都只能“往外打”，所以各自主动连向中继，由中继转发</text>
</svg>

## 为什么打洞在国内这么难

### NAT 与 CGNAT

网络地址转换（Network Address Translation, NAT）是路由器把内网地址翻译成公网地址的机制。家里一层 NAT 不算完——国内家宽现在普遍还套着一层运营商级 NAT（Carrier-Grade NAT, CGNAT）：你的"公网出口 IP"其实是运营商的，成千上万户共享，路由器 WAN 口拿到的是 `100.64.x.x` 这类地址。手机流量更是百分之百在 CGNAT 后面。

打洞（UDP Hole Punching）的原理是：双方先通过一个公网协调服务器（STUN，Session Traversal Utilities for NAT）各自探测出"我从外面看是什么地址和端口"，然后**同时**向对方的公网地址发包——各自的 NAT 看到出站流量，就给回程流量开了"洞"。

### 致命的对称 NAT

能不能打通，取决于 NAT 给出站连接分配端口的方式：

| NAT 组合 | 打洞结果 |
|----------|----------|
| 锥形 × 锥形 | 基本都能通 |
| 锥形 × 对称 | 受限锥可通，端口受限锥很难 |
| 对称 × 对称 | 基本必败 |

锥形 NAT（Cone NAT）对同一个内网端口复用同一个公网端口——你从 STUN 探到的端口，跟你去连对方时用的端口是同一个，对方照着打就行。而对称 NAT（Symmetric NAT）**对每个不同目的地都分配新端口**：STUN 探到的端口，在你真正连对方时已经换掉了，对方照着旧端口打，永远打不中。

对称 NAT 下唯一的指望是暴力猜端口。猜中的概率有多低，可以算一下。NAT 从约 $N$ 个端口里随机分配，一方发 $k$ 个探测包，命中概率近似为：

$$P \approx 1 - \left(1 - \frac{1}{N}\right)^{k}$$

符号含义：$N$ 是可用端口空间大小（个），$k$ 是发出的探测包数量（个）。

> **代入数字**：典型端口空间 $N = 64{,}512$（即 1024~65535），发 $k = 256$ 个探测包：
> $$P \approx 1 - \left(1 - \frac{1}{64512}\right)^{256} \approx 0.4\%$$
> 就算两边配合做生日攻击式的双向猜测，实际工程里对称×对称的打洞成功率也低到不值得指望。运营商 CGNAT 大多正是对称型——这就是"打了两天洞一个没通"的原因，不是你配置错了。

## 打不通就中继：延迟账怎么算

打洞失败后，Tailscale 自动回落到 DERP 中继。所有流量变成：A → 中继服务器 → B。延迟从"两点之间直线"变成"两点经第三点折线"，往返时延（Round-Trip Time, RTT）近似为两段 RTT 之和：

$$RTT_{\text{中继}} \approx RTT_{A \leftrightarrow R} + RTT_{R \leftrightarrow B}$$

符号含义：$RTT_{A \leftrightarrow R}$ 是设备 A 到中继 R 的往返时延（ms），$RTT_{R \leftrightarrow B}$ 是中继 R 到设备 B 的往返时延（ms）。中继本身的转发处理在 1 ms 量级，可忽略。

> **代入数字**：Tailscale 官方 DERP 节点全在海外，国内设备就近一般落到东京。杭州电信到东京 $RTT \approx 90\ \mathrm{ms}$，成都移动到东京 $RTT \approx 110\ \mathrm{ms}$：
> $$RTT_{\text{中继}} \approx 90 + 110 = 200\ \mathrm{ms}$$
> 换成国内 BGP 机房的中继：两端到上海机房分别约 $15\ \mathrm{ms}$ 和 $30\ \mathrm{ms}$：
> $$RTT_{\text{中继}} \approx 15 + 30 = 45\ \mathrm{ms}$$
> 同样是中继，换个位置，延迟差出 4 倍多。**中继不可怕，远的中继才可怕。**

### 比延迟更难受的是丢包

跨境链路真正折磨人的是丢包和抖动。WireGuard 本身是 UDP 不重传，丢包由上层的 TCP 或应用补——每丢一个包，就要多等至少一个 RTT。平均每个包需要的传输次数是：

$$E[n] = \frac{1}{1-p}$$

符号含义：$p$ 是单程丢包率（无量纲），$E[n]$ 是平均传输次数（次）。

> **代入数字**：跨境高峰期丢包率 $p = 8\%$，$RTT = 200\ \mathrm{ms}$：
> $$E[n] = \frac{1}{1-0.08} \approx 1.087$$
> 平均只多了 8.7% 的流量，看着不严重——但对交互式 SSH，意味着**每 100 次按键有 8 次要卡 200ms 以上**才显示出来。这就是"裸延迟 200ms 听着还行，用起来想砸键盘"的数学解释。体感由延迟分布的尾部决定，不由平均值决定。

## 进阶：DERP 到底是什么，自建卡在哪

### DERP 的协议本质

DERP 是 Tailscale 自己设计的中继协议，跑在 HTTPS（TCP 443）上——伪装成普通网站流量，几乎任何防火墙都放行，这是它"一定能通"的底气。代价是 TCP 承载 UDP 流量，遇到丢包还有队头阻塞，进一步放大尾延迟。

关键的安全性质：节点间流量是 WireGuard 端到端加密（End-to-End Encryption, E2EE）的，DERP **只转发密文，看不到内容**。中继方能看到的是元数据：哪些设备在通信、什么时候、流量多大。这是"敢用陌生人中继"的前提。

### 自建 derper 的完整账单

官方开源了中继服务端 `derper`，自建需要：

```bash
# file: 自建 derper 的最小部署
go install tailscale.com/cmd/derper@latest
derper --hostname=derp.example.com --certmode=letsencrypt
```

看着两行，实际要凑齐的东西不少：

- 一台国内有公网 IP 的 VPS（Virtual Private Server，虚拟专用服务器），轻量款每月 ¥20~50
- 一个域名，且 HTTPS 证书签发要求域名能正常解析——国内服务器还可能涉及备案
- 防火墙放行 TCP 443 与 STUN 的 UDP 3478
- 在 Tailscale 控制台的 ACL 里写入自定义 `derpMap`
- **别忘了 `--verify-clients`**：不开的话你的中继是裸奔的，任何知道地址的陌生 Tailscale 用户都能蹭用你的带宽

我就卡在域名证书这一环：新域名解析生效慢、证书签发反复失败，折腾半天后意识到——我要的是"能用"，不是"自营"。

### 淘宝 DERP 的本质

淘宝上十几块钱一个月的"DERP 加速"，本质就是商家批量部署好的国内 `derper` 节点，卖你一段 `derpMap` 配置，粘进自己的 ACL 即可。它不碰你的密钥、不入你的虚拟网络，只是个转发密文的哑管道。

要留意的两件事：一是问清楚有没有开 `verify-clients`（没开意味着节点超卖、被蹭，高峰期带宽不稳）；二是记住中继方看得到你的通信元数据，介意的话还是自建。

## 应用：方案决策表

两天踩坑浓缩成一张表：

| 方案 | 折腾量 | 月成本 | 典型 RTT | 适合谁 |
|------|--------|--------|----------|--------|
| 运营商开公网 IPv4 | 打客服电话碰运气 | 0~10 元 | 10~40 ms | 能开到的幸运儿 |
| IPv6 直连 | 两端开 v6 + 放行防火墙 | 0 | 10~40 ms | 两端都有 v6 的场景 |
| 打洞直连 | 0（Tailscale 自动） | 0 | 10~40 ms | 至少一端锥形 NAT |
| 官方 DERP | 0 | 0 | 150~300 ms，抖 | 临时凑合、低频使用 |
| 自建 DERP | VPS+域名+证书+部署 | 20~50 元 | 20~60 ms | 要完全可控、介意元数据 |
| 购买 DERP | 粘一段 ACL 配置 | 5~20 元 | 20~60 ms | 只想要"能用"的大多数人 |

我的最终形态：保留 Tailscale 默认的直连尝试（哪天运气好打通了自动走直连），中继回落到购买的国内 DERP 节点。日常 RTT 稳定在几十毫秒，SSH 不再卡键，手机热点下也能秒连家里的机器。

回头看,这两天最大的收获不是"通了"，而是把**直连、打洞、中继**这三层逻辑和各自的失败模式亲手摸了一遍——下次再遇到"为什么这么慢"，第一反应不再是重启大法，而是 `tailscale status` 看一眼到底走的哪条路。

> **延伸阅读**：Tailscale 官方博客 *How NAT traversal works*，把打洞讲得极透；以及 DERP 服务端源码 `tailscale.com/cmd/derper`。

## 术语表

| 术语 | 英文 | 含义 |
|------|------|------|
| 运营商级 NAT | Carrier-Grade NAT, CGNAT | 运营商在用户侧之上再套的一层共享 NAT |
| 锥形 NAT | Cone NAT | 同一内网端口复用同一公网端口的 NAT，可打洞 |
| 指定加密包中继 | Designated Encrypted Relay for Packets, DERP | Tailscale 的中继协议，跑在 HTTPS 上转发密文 |
| 端到端加密 | End-to-End Encryption, E2EE | 只有通信两端能解密，中间节点全程见不到明文 |
| 网络地址转换 | Network Address Translation, NAT | 内网地址与公网地址间的映射机制 |
| 往返时延 | Round-Trip Time, RTT | 数据包一来一回的总耗时 |
| 会话穿越工具 | Session Traversal Utilities for NAT, STUN | 帮设备探测自己公网地址和端口的协议 |
| 对称 NAT | Symmetric NAT | 每个目的地分配不同公网端口的 NAT，打洞基本必败 |
| UDP 打洞 | UDP Hole Punching | 双方同时向对方公网地址发包以建立直连的技术 |
| 虚拟专用服务器 | Virtual Private Server, VPS | 云上租用的独立服务器实例 |
| — | WireGuard | 现代轻量 VPN 隧道协议，Tailscale 的底层 |
