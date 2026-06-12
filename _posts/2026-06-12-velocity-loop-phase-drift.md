---
layout: post
title: "速度环闭得很好，相位为什么还是乱？——多电机同步与级联控制"
date: 2026-06-12 21:00:00 +0800
categories: [控制理论]
tags: [级联控制, 速度环, 锁相, 电机控制, 机器人]
author: "Dragonking"
excerpt: "每台电机的速度环都闭得漂亮，可几台电机一起转，不到一分钟相位就岔开了。这不是参数没调好，而是结构上就管不住：对相位来说，速度环是开环的。"
---

## 一台都没坏，但整体乱了

做多电机系统的人多半撞见过这个怪现象：单独看每一台电机，速度环响应干脆、稳态误差极小，示波器上挑不出毛病；可是让四台电机按固定相位关系一起转——比如驱动四条腿走步态——走上几十秒，腿和腿之间的相对相位就悄悄岔开了，转个弯乱得更快。

第一反应通常是"PID 没调好，再调调"。调完发现没用。因为这不是参数问题，是**结构问题**：速度环这个东西，从设计上就不负责相位。这篇文章把这件事讲透，再讲清楚解法——级联控制（Cascade Control）里的相位外环。

## 直觉：定速巡航的两辆车

先不上公式。想象两辆车并排出发，都开定速巡航（Cruise Control），都设 100 km/h。巡航系统工作得很好：一辆车实际跑 99.5，另一辆跑 100.3，误差都不到 1%。

但你盯着两车的**车距**看：每小时拉开 800 米。更要命的是，巡航系统永远不会去追回这个差距——它的任务清单里只有"把车速保持在 100"，**根本没有"和旁边那辆车保持并排"这一项**。车距对它来说是不存在的量。

多电机的相位问题一模一样：

- 车速 ↔ 电机转速 $\omega$
- 车距 ↔ 电机之间的相对相位 $\Delta\theta$
- 巡航系统 ↔ 每台驱动器里各自的速度环

每台驱动器只看自己的转速，互相不知道对方的存在。"左前腿和右后腿应该差 180°"这条约束，**不存在于任何一个控制环里**——它是个完全无人看管的状态。

<svg viewBox="0 0 560 310" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <defs>
    <marker id="arrow-axis" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 z" fill="var(--text-secondary)"/>
    </marker>
    <marker id="arrow-gap" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 z" fill="var(--primary-color)"/>
    </marker>
  </defs>
  <!-- 坐标轴 -->
  <path d="M 70 260 L 530 260" stroke="var(--text-secondary)" stroke-width="1.5" marker-end="url(#arrow-axis)"/>
  <path d="M 70 260 L 70 40" stroke="var(--text-secondary)" stroke-width="1.5" marker-end="url(#arrow-axis)"/>
  <text x="520" y="285" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="13">时间 t</text>
  <text x="40" y="50" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="13">转角 θ</text>
  <!-- 电机 A -->
  <path d="M 70 260 L 500 75" stroke="var(--primary-color)" stroke-width="2.5"/>
  <text x="380" y="120" fill="var(--primary-color)" font-family="Inter, sans-serif" font-size="13">电机 A</text>
  <!-- 电机 B -->
  <path d="M 70 260 L 500 135" stroke="var(--text-secondary)" stroke-width="2.5"/>
  <text x="380" y="208" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="13">电机 B</text>
  <!-- 相位差标注 -->
  <path d="M 508 82 L 508 128" stroke="var(--primary-color)" stroke-width="1.5"
        marker-start="url(#arrow-gap)" marker-end="url(#arrow-gap)"/>
  <text x="500" y="68" fill="var(--text-primary)" font-family="Inter, sans-serif" font-size="13" text-anchor="end">Δθ(t) 越拉越大</text>
  <!-- 注释 -->
  <text x="180" y="245" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">两条线斜率几乎相同：速度都“闭好了”</text>
</svg>

## 相位是速度的积分

把直觉翻译成数学。转角（相位）$\theta$ 就是角速度 $\omega$ 对时间的积分：

$$\theta(t) = \theta(0) + \int_0^t \omega(\tau)\, d\tau$$

逐个符号解释：$\theta(t)$ 是 $t$ 时刻的转角（rad），$\theta(0)$ 是初始转角（rad），$\omega(\tau)$ 是 $\tau$ 时刻的角速度（rad/s）。

> **代入数字**：电机以恒定 $\omega = 6.28\ \mathrm{rad/s}$（正好每秒一圈）转 10 s，初始角为 0：
> $$\theta = 0 + 6.28 \times 10 = 62.8\ \mathrm{rad} = 10\ \text{圈}$$

速度环保证的是 $\omega_{\text{实际}} \approx \omega_{\text{命令}}$，但"$\approx$"永远有残差。定义速度残差 $\varepsilon(t) = \omega_{\text{实际}}(t) - \omega_{\text{命令}}(t)$，那么相位误差就是残差的积分：

$$\Delta\theta(t) = \int_0^t \varepsilon(\tau)\, d\tau$$

如果残差有一个不为零的均值 $\bar\varepsilon$（rad/s），相位误差就**随时间线性增长**：$\Delta\theta(t) \approx \bar\varepsilon\, t$。

> **代入数字**：两台电机收到相同命令 $6.28\ \mathrm{rad/s}$。由于增益标定差异，A 实际快了 0.2%（$+0.0126\ \mathrm{rad/s}$），B 慢了 0.8%（$-0.0502\ \mathrm{rad/s}$）。两者的相对残差 $\bar\varepsilon = 0.0628\ \mathrm{rad/s}$。从同相漂到反相（差 $\pi$ rad）需要：
> $$t = \frac{\pi}{0.0628} \approx 50\ \mathrm{s}$$
> 每台电机的速度误差都不到 1%——完全在"调得很好"的范围内——但不到一分钟，步态就从同相变成了反相。这就是"走一会儿就乱"的基本速率。

这就是问题的核心：**有界的速度误差，积分出无界的相位误差**。速度环里没有任何一项在看"角度欠了多少"，所以对相位这个量来说，整个系统是开环的。

## 进阶：三种漂移机制

实际系统里，相位岔开通常是三种机制叠加的结果，漂移的"形状"各不相同。

### 机制一：恒定偏差 → 线性漂移

上面算过的情况。来源是增益标定差异、电流传感器偏置、机械摩擦不对称等。特点是漂移方向固定、速率恒定，最容易被察觉，也最致命。

### 机制二：零均值噪声 → 随机游走

就算把标定做到极致、残差均值严格为零，相位也不会停在原地——它会做随机游走（Random Walk）。设残差是标准差为 $\sigma_\varepsilon$、相关时间为 $\tau_c$ 的零均值噪声，相位误差的标准差近似按 $\sqrt{t}$ 增长：

$$\sigma_{\Delta\theta}(t) \approx \sigma_\varepsilon \sqrt{2\,\tau_c\, t}$$

符号含义：$\sigma_\varepsilon$ 是速度残差的标准差（rad/s），$\tau_c$ 是噪声的相关时间（s），即扰动"自我相似"的典型时长。

> **代入数字**：取 $\sigma_\varepsilon = 0.05\ \mathrm{rad/s}$、$\tau_c = 0.1\ \mathrm{s}$，运行 $t = 100\ \mathrm{s}$：
> $$\sigma_{\Delta\theta} \approx 0.05 \times \sqrt{2 \times 0.1 \times 100} = 0.05 \times 4.47 \approx 0.22\ \mathrm{rad} \approx 12.8°$$
> 而且这个数随 $\sqrt{t}$ 继续涨，没有上限。

### 机制三：瞬态冲击 → 单向欠账

足式机器人每次触地、负载每次突变，都会把转子顿一下。速度环要经过反馈链路的死区时间（Dead Time）加上自身的响应时间才能把速度拉回来——但它**只恢复"速度对"，顿那一下丢掉的角度永久欠账**。每一步欠一点，而且冲击方向往往一致（总是减速），欠账单向累积。

> **代入数字**：假设每次触地冲击平均丢 0.02 rad，步频 2 步/秒，等效漂移率 $0.04\ \mathrm{rad/s}$——比机制一里那个 1% 增益差造成的漂移还要快。

这也解释了**为什么转向时乱得更快**：差速转向下左右负载严重不对称，冲击更猛（机制三放大），负载相关的估计偏差也更大（机制一放大）。而且左右两侧本来就是不同的速度命令，跨侧相对相位理应连续滑动——根本不存在"锁住"一说，能控的只有同速度命令组内部的相位关系。

## 解法：把相位也闭起来——级联控制

既然速度环管不了相位，那就在它外面再套一个环，专门看相位。这个结构叫级联控制（Cascade Control）：外环的输出不直接拧电机，而是作为内环的**命令修正量**。

<svg viewBox="0 0 660 300" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <defs>
    <marker id="arrow-fwd" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L9,3 L0,6 z" fill="var(--primary-color)"/>
    </marker>
    <marker id="arrow-fb" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L9,3 L0,6 z" fill="var(--text-secondary)"/>
    </marker>
  </defs>
  <!-- 控制器方框 -->
  <rect x="60" y="60" width="104" height="48" rx="6" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
  <text x="112" y="80" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">相位控制器</text>
  <text x="112" y="98" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">~10 Hz</text>
  <rect x="200" y="60" width="104" height="48" rx="6" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
  <text x="252" y="80" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">速度控制器</text>
  <text x="252" y="98" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">~10² Hz</text>
  <rect x="340" y="60" width="104" height="48" rx="6" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
  <text x="392" y="80" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">电流控制器</text>
  <text x="392" y="98" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="11">~10³ Hz</text>
  <rect x="480" y="60" width="80" height="48" rx="6" fill="var(--bg-secondary)" stroke="var(--text-secondary)" stroke-width="2"/>
  <text x="520" y="89" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">电机</text>
  <!-- 前向通路 -->
  <path d="M 8 84 L 56 84" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arrow-fwd)"/>
  <text x="28" y="74" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">θ*</text>
  <path d="M 164 84 L 196 84" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arrow-fwd)"/>
  <text x="172" y="74" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">ω*</text>
  <path d="M 304 84 L 336 84" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arrow-fwd)"/>
  <text x="316" y="74" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">i*</text>
  <path d="M 444 84 L 476 84" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arrow-fwd)"/>
  <text x="454" y="74" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">u</text>
  <path d="M 560 84 L 640 84" stroke="var(--primary-color)" stroke-width="2" marker-end="url(#arrow-fwd)"/>
  <text x="630" y="74" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">θ</text>
  <!-- 反馈通路：电流 -->
  <circle cx="576" cy="84" r="3" fill="var(--text-secondary)"/>
  <path d="M 576 84 L 576 150 L 392 150 L 392 112" stroke="var(--text-secondary)" stroke-width="1.5" fill="none" marker-end="url(#arrow-fb)"/>
  <text x="470" y="144" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">电流 i</text>
  <!-- 反馈通路：转速 -->
  <circle cx="596" cy="84" r="3" fill="var(--text-secondary)"/>
  <path d="M 596 84 L 596 190 L 252 190 L 252 112" stroke="var(--text-secondary)" stroke-width="1.5" fill="none" marker-end="url(#arrow-fb)"/>
  <text x="400" y="184" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">转速 ω</text>
  <!-- 反馈通路：转角 -->
  <circle cx="616" cy="84" r="3" fill="var(--text-secondary)"/>
  <path d="M 616 84 L 616 230 L 112 230 L 112 112" stroke="var(--text-secondary)" stroke-width="1.5" fill="none" marker-end="url(#arrow-fb)"/>
  <text x="340" y="224" fill="var(--text-secondary)" font-family="Inter, sans-serif" font-size="12">转角 θ（编码器）</text>
  <!-- 图注 -->
  <text x="330" y="275" fill="var(--text-secondary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">级联结构：外环输出是内环的命令，越往内越快</text>
</svg>

三个环各管一个物理量，频率逐层拉开：

| 环 | 反馈量 | 典型更新率 | 负责的事 |
|------|--------|-----------|----------|
| 电流环 | 相电流 $i$ | kHz 级 | 转矩跟得上 |
| 速度环 | 转速 $\omega$ | 百 Hz 级 | 转得够快 |
| 相位环 | 转角 $\theta$ | 几十 Hz | 转到了**该在的角度** |

最简单的相位外环就是一个带限幅（Saturation）的比例修正：

$$\omega_{\text{cmd}} = \omega_{\text{base}} + \mathrm{sat}\big(K_p\, e_\theta,\ \pm u_{\max}\big)$$

逐个符号解释：$\omega_{\text{base}}$ 是基础速度命令（rad/s）；$e_\theta = \theta_{\text{ref}} - \theta$ 是相位误差（rad），其中参考相位 $\theta_{\text{ref}}$ 通常是一个匀速旋转的虚拟主轴；$K_p$ 是外环比例增益（s⁻¹）；$u_{\max}$ 是修正量限幅（rad/s），防止外环猛拽内环。

> **代入数字**：取 $K_p = 1.5\ \mathrm{s^{-1}}$、$u_{\max} = 0.6\ \mathrm{rad/s}$。当前相位落后 $e_\theta = 0.10\ \mathrm{rad}$（约 5.7°）：
> $$\Delta\omega = 1.5 \times 0.10 = 0.15\ \mathrm{rad/s}$$
> 未触发限幅，速度命令在基础值上加 0.15 rad/s，把欠的角度**主动追回来**。

控制理论的说法是：外环给系统补上了**对积分状态（相位）的反馈**。从此有界扰动只产生有界相位误差。对于恒定残差 $\bar\varepsilon$，比例外环的稳态误差是：

$$e_{\theta,\infty} = \frac{\bar\varepsilon}{K_p}$$

> **代入数字**：还是那个 $\bar\varepsilon = 0.0628\ \mathrm{rad/s}$ 的增益差，$K_p = 1.5\ \mathrm{s^{-1}}$：
> $$e_{\theta,\infty} = \frac{0.0628}{1.5} \approx 0.042\ \mathrm{rad} \approx 2.4°$$
> 对比开环：同样的扰动，100 s 后漂掉 6.28 rad——整整一圈。闭相位环后误差**钉死在 2.4°**，不再随时间增长。

### "更高级"是严格的包含关系

闭相位是不是比闭速度更高级？是，而且在数学上是单向包含：

- **锁住相位 ⟹ 平均速度自动正确**。相位参考本身就在匀速旋转，跟住它，平均速度必然等于参考速度。
- **闭住速度 ⇏ 相位正确**。前面整篇都在说这件事。

所以相位环不是速度环的"补丁"，而是包住它的更外一层。这和锁相环（Phase-Locked Loop, PLL）能同时锁频锁相、而锁频环只能锁频，是同一个道理。

## 进阶：外环不是免费的

加了外环，问题没有全部消失，而是换了两种形式。

### 限制一：外环带宽被内环封顶

级联控制有条经验法则：外环带宽要比内环慢 3~5 倍，否则两个环互相打架、系统振荡。

$$f_{\text{外}} \lesssim \frac{f_{\text{内}}}{3 \sim 5}$$

> **代入数字**：内环（速度环）带宽 4 Hz，外环带宽就只能做到约 $4/5 \sim 4/3 \approx 0.8 \sim 1.3\ \mathrm{Hz}$。意思是：相位扰动里变化快于 1 Hz 的成分，外环根本追不上，只能靠内环硬扛。

反馈链路的死区时间还会进一步压低这个上限。死区 $T_d$ 在穿越频率 $\omega_c$ 处吃掉的相位裕度是：

$$\varphi_{\text{loss}} = \omega_c\, T_d$$

符号含义：$\omega_c$ 是外环的穿越角频率（rad/s），$T_d$ 是通信加采样的总死区时间（s）。

> **代入数字**：链路死区 $T_d = 60\ \mathrm{ms}$，外环穿越频率 1 Hz（$\omega_c = 6.28\ \mathrm{rad/s}$）：
> $$\varphi_{\text{loss}} = 6.28 \times 0.06 \approx 0.38\ \mathrm{rad} \approx 21.6°$$
> 一条普通的串口/总线链路，就吃掉了 20 多度相位裕度。这直接限制了 $K_p$ 能开多大——也解释了为什么转速越高、锁相精度越差：扰动频率随转速上升，迟早越过外环带宽。

### 限制二：修正量本身就是扰动

外环不停地给速度命令加减 $K_p e_\theta$，对速度环来说这就是一个持续抖动的输入。结果是：相位确定性提高了，**速度平滑性变差了**——体现在机器人上可能是偏航纹波增大、振动加剧。$K_p$ 和 $u_{\max}$ 的整定本质上是在"相位锁多紧"和"运行多平顺"之间买卖。

## 应用案例

**印刷机套准与电子虚拟主轴。** 多色印刷要求各色辊的角度严格对齐，差 0.1 mm 就糊版。老式印刷机用一根物理长轴把所有辊硬连在一起；现代方案是电子虚拟主轴（Electronic Line Shafting, ELS）：软件里跑一个匀速旋转的虚拟参考轴，每个电机各自闭相位环去跟它。这是相位级联控制最经典的工业落地。

**足式机器人步态同步。** 曲柄连杆驱动的多足机器人里，"步态"本质上就是腿与腿之间的相对相位关系（对角步态 = 对角腿差 0°、同侧腿差 180°）。只闭速度环的机器人会经历本文描述的全部漂移机制；给每条腿加一个以虚拟步态时钟为参考的相位外环，步态才能长期保持。

**学习策略作为自适应相位外环。** 用强化学习（Reinforcement Learning, RL）训练运动策略时，有一个看似平常的细节：把关节角度喂进策略网络的观测里。从级联控制的视角看，这等于让神经网络坐在相位外环的位置上——而且它比固定增益的锁相更进一步：不是死锁某个预设相位，而是根据速度命令和姿态**自己决定每条腿该处于什么相位、要不要补**。训出来的策略本质上是一个学出来的自适应相位控制器，速度环只是它手里的执行器。这也是为什么观测里少了关节角，sim2real 往往就过不去——你把外环的反馈量掐了。

## 术语表

| 术语 | 英文 | 含义 |
|------|------|------|
| 带宽 | Bandwidth | 控制环能有效跟踪的扰动频率上限 |
| 级联控制 | Cascade Control | 外环输出作为内环命令的多层嵌套控制结构 |
| 定速巡航 | Cruise Control | 汽车自动保持车速的速度闭环系统 |
| 死区时间 | Dead Time | 信号从产生到生效的纯延迟，吃相位裕度 |
| 电子虚拟主轴 | Electronic Line Shafting, ELS | 用软件参考轴替代物理长轴的多机同步方案 |
| 锁相环 | Phase-Locked Loop, PLL | 同时锁定频率与相位的闭环结构 |
| 随机游走 | Random Walk | 零均值随机增量的累积过程，方差随时间线性增长 |
| 强化学习 | Reinforcement Learning, RL | 通过试错与奖励信号学习策略的机器学习范式 |
| 限幅 | Saturation | 将控制量钳制在上下限内的非线性环节 |
| 稳态误差 | Steady-State Error | 系统进入稳态后残留的恒定误差 |
