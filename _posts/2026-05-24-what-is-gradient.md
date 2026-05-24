---
layout: post
title: "梯度是什么，又该怎么算：从一条切线到梯度下降"
date: 2026-05-24 12:00:00 +0800
categories: [机器人学, 强化学习]
tags: [梯度, 梯度下降, 优化, 学习率, 导数]
author: "Dragonking"
excerpt: "系统辨识、策略训练、轨迹优化，表面上是三件事，骨子里都是同一句话：对能调的变量算梯度，然后往下坡走一步。本文从一条切线讲起，把梯度的概念和它到底怎么算，一步步算给你看。"
kb: true
kb_cat: rl
---

机器人学习里有三件听起来毫不相干的事：**系统辨识（System Identification, SI）** 是调仿真参数去贴近真机，**策略训练（Policy Training）** 是让机器人学会动作，**轨迹优化（Trajectory Optimization, TO）** 是规划一条最省力的运动。但在可微仿真的语境下，它们其实是同一个动作：

$$\text{变量} \leftarrow \text{变量} - \alpha\cdot\frac{\partial L}{\partial\,\text{变量}}$$

> 三者只是"变量"和"目标 $L$"的名字不同：辨识调的是仿真参数、训练调的是策略参数、优化调的是控制序列。更新公式一模一样。

这行公式的主角就是**梯度（gradient）** $\partial L/\partial\,\text{变量}$。看懂它怎么来、怎么算，上面三件事就一通百通。本文不碰可微仿真的工程细节，只把梯度这个概念和它的计算，从最朴素的一条切线讲到能手算的梯度下降。

## 直觉：梯度就是"哪边是下坡"

想象你站在一座山的某个位置，蒙着眼，只想尽快走到谷底。你能做的只有一件事：用脚感受**脚下哪个方向最陡、是往上还是往下**，然后朝下坡方向迈一小步，再重新感受，再迈一步。

梯度就是"脚下的坡度"这件事的数学版本。它同时告诉你两个信息：**坡有多陡**（数值大小）和**朝哪个方向上升最快**（正负 / 方向）。既然梯度指的是"上坡最快"的方向，那想下山，往它的**反方向**走就对了——这就是更新公式里那个**减号**的来历。

整个过程不需要你看见整座山的全貌，只靠脚下这一点的局部坡度，一步步挪。这既是梯度下降的强大之处（不用知道函数长什么样），也是它的软肋（容易掉进近处的小坑出不来，后面会讲）。

## 导数：一条切线的斜率

先从只有一个变量的情况说起。函数 $y=f(x)$ 在某点的**导数（derivative）**，就是它在那一点切线的斜率，定义是"$x$ 动一点点，$y$ 跟着动多少"的比值：

$$f'(x) = \lim_{\Delta x\to 0}\frac{f(x+\Delta x)-f(x)}{\Delta x}$$

> 拿 $f(x)=x^2$ 在 $x=3$ 处算：取一个很小的 $\Delta x=0.001$，
> $$\frac{f(3.001)-f(3)}{0.001} = \frac{9.006001-9}{0.001} = 6.001 \approx 6$$
> 这正好等于公式 $f'(x)=2x$ 在 $x=3$ 的值 $2\times3=6$。导数 6 的意思是：在 $x=3$ 附近，$x$ 每增加 1，$y$ 大约增加 6。

<svg viewBox="0 0 340 220" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <!-- 坐标轴 -->
  <line x1="30" y1="195" x2="320" y2="195" stroke="var(--text-mute)" stroke-width="1.5"/>
  <line x1="170" y1="20" x2="170" y2="195" stroke="var(--text-mute)" stroke-width="1.5"/>
  <text x="312" y="190" fill="var(--text-soft)" font-family="Inter, sans-serif" font-size="12">x</text>
  <text x="176" y="30" fill="var(--text-soft)" font-family="Inter, sans-serif" font-size="12">y</text>
  <!-- 抛物线 y=x^2 -->
  <path d="M 50 40 Q 170 350 290 40" fill="none" stroke="var(--primary-color)" stroke-width="2.5"/>
  <!-- 切点 P -->
  <circle cx="245" cy="100" r="5" fill="var(--accent-color)"/>
  <text x="252" y="98" fill="var(--accent-color)" font-family="Inter, sans-serif" font-size="12">P</text>
  <!-- 切线（正斜率） -->
  <line x1="200" y1="148" x2="295" y2="58" stroke="var(--accent-color)" stroke-width="2" stroke-dasharray="5 3"/>
  <text x="210" y="140" fill="var(--accent-color)" font-family="Inter, sans-serif" font-size="11">导数 &gt; 0（切线上扬）</text>
  <!-- 下坡箭头：朝左（负梯度方向） -->
  <path d="M 235 118 L 200 150" stroke="var(--secondary-color)" stroke-width="2.5" marker-end="url(#arrowd)"/>
  <text x="120" y="172" fill="var(--secondary-color)" font-family="Inter, sans-serif" font-size="12">−梯度方向 = 下坡</text>
  <defs>
    <marker id="arrowd" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 z" fill="var(--secondary-color)"/>
    </marker>
  </defs>
</svg>

## 怎么读导数的正负号

记住一句话就够用：

- 导数 $f'(x) > 0$：$x$ 增大时 $y$ 也增大（**同向**），所以这一点处于"上坡"，想下坡得让 $x$ **减小**。
- 导数 $f'(x) < 0$：$x$ 增大时 $y$ 反而减小（**反向**），这一点是"下坡朝右"，想下坡得让 $x$ **增大**。

梯度下降的更新公式靠那个**减号**，自动把这两种情况都处理对：

$$x_{\text{new}} = x_{\text{old}} - \alpha\cdot f'(x)$$

> 设 $f(x)=x^2$（最小值在 $x=0$），学习率 $\alpha=0.3$：
> - 在 $x=3$（导数 $=6>0$）：$x_{\text{new}} = 3 - 0.3\times6 = 1.2$，$x$ 变小了，朝 0 靠近 ✓
> - 在 $x=-3$（导数 $=-6<0$）：$x_{\text{new}} = -3 - 0.3\times(-6) = -1.2$，负负得正，$x$ 变大了，也朝 0 靠近 ✓
>
> 无论起点在左在右，减号都把它推向谷底。这里 $\alpha$ 是**学习率（Learning Rate）**，控制一步走多远。

## 手算一遍：完整的梯度下降迭代

把上面的规则连起来跑五步，对 $f(x)=x^2$、起点 $x=3$、学习率 $\alpha=0.3$，导数为 $f'(x)=2x$：

| 步 | $x$ | $y=x^2$ | 导数 $2x$ | 更新量 $\alpha\cdot$导数 | 下一步 $x$ |
|---|------|---------|----------|------------------------|-----------|
| 0 | 3.000 | 9.000 | 6.000 | 1.800 | 1.200 |
| 1 | 1.200 | 1.440 | 2.400 | 0.720 | 0.480 |
| 2 | 0.480 | 0.230 | 0.960 | 0.288 | 0.192 |
| 3 | 0.192 | 0.037 | 0.384 | 0.115 | 0.077 |
| 4 | 0.077 | 0.006 | 0.154 | 0.046 | 0.031 |

> 验证第 1 步：$x=1.2$，导数 $=2\times1.2=2.4$，更新量 $=0.3\times2.4=0.72$，下一步 $x=1.2-0.72=0.48$，与表中一致。$y$ 从 9 一路掉到 0.006，正在逼近谷底 $x=0$。

两个值得注意的现象：

- **自带刹车**：越接近谷底 $x=0$，导数（坡度）越小，更新量自动变小，步子越迈越小，不会冲过头。
- **学习率决定成败**：上面 $\alpha=0.3$ 平稳收敛；若 $\alpha=1.1$，更新会在 0 两侧来回**震荡甚至发散**；若 $\alpha=0.01$，方向没错但步子太碎，要几百步才到。

## 推广：多个变量时，梯度是一个向量

真实问题里要调的往往不止一个变量。这时"导数"升级成**梯度**：对每个变量各求一次**偏导数（partial derivative）**，拼成一个向量。

$$\nabla f = \left(\frac{\partial f}{\partial x_1},\ \frac{\partial f}{\partial x_2},\ \dots,\ \frac{\partial f}{\partial x_n}\right)$$

> 拿 $f(x,y)=x^2+y^2$（一个碗形面，最低点在原点）在 $(3,4)$ 处算：
> $$\nabla f = (2x,\ 2y) = (2\times3,\ 2\times4) = (6,\ 8)$$
> 这个向量 $(6,8)$ 指向"上坡最快"的方向。想下坡，取它的反方向，用 $\alpha=0.1$ 更新：
> $$(x,y)_{\text{new}} = (3,4) - 0.1\times(6,8) = (2.4,\ 3.2)$$
> 离原点更近了。多变量的更新公式和一维一模一样，只是"减一个数"变成"减一个向量"。

关键认知：**梯度的每个分量，衡量的是"只动这一个变量、其余不变时，目标变化多快"**。把所有方向的敏感度打包成一个向量，就知道整体该往哪挪。

## 软肋：局部最优

梯度下降只看脚下的坡，所以它只能保证走到**局部最优（local optimum）**——附近的一个谷底，不保证是全局最深的那个。遇到下面这种"W 形"双谷函数就会暴露问题：

<svg viewBox="0 0 360 200" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <line x1="20" y1="180" x2="345" y2="180" stroke="var(--text-mute)" stroke-width="1.5"/>
  <!-- W 形曲线：浅谷在左，深谷在右，中间隔着一个山包 -->
  <path d="M 25 45 Q 70 140 110 118 Q 150 96 180 65 Q 215 38 255 158 Q 295 188 340 50"
        fill="none" stroke="var(--primary-color)" stroke-width="2.5"/>
  <!-- 小球停在浅谷 -->
  <circle cx="110" cy="108" r="7" fill="var(--accent-color)"/>
  <!-- 标注 -->
  <text x="60" y="150" fill="var(--text-soft)" font-family="Inter, sans-serif" font-size="11">局部最优（浅谷）</text>
  <text x="240" y="178" fill="var(--secondary-color)" font-family="Inter, sans-serif" font-size="11">全局最优（深谷）</text>
  <!-- 山包标注 -->
  <text x="150" y="55" fill="var(--text-mute)" font-family="Inter, sans-serif" font-size="11">跨不过的山包</text>
</svg>

> 例如 $f(x)$ 有两个谷：深谷在 $x=2.0$（$f=-1.0$），浅谷在 $x=-1.5$（$f=-0.3$）。若从浅谷一侧出发，梯度只会把球推进**浅谷**就停住，因为它"看不到"中间山包另一侧还有更深的谷——爬不过去。

工程上常用几招配合脱困：

- **多起点（Multi-start）**：撒多个随机初值各跑一遍，取最好结果。
- **加噪声 / 退火（Simulated Annealing）**：让更新带随机扰动，有机会跳出小坑。
- **温启动（Warm Start）**：先用粗糙方法求个大致解，再用梯度精修——工程最常用。
- **采样优化兜底（CEM / MPPI）**：先用全局视角的采样法找粗解，再交给梯度做局部精修。

> 核心认知：没有任何方法能 100% 保证找到全局最优（一般是 NP-hard 难题）。实践套路是"**探索机制找全局 + 梯度做局部精修**"两条腿走路。

## 应用：一个公式，三件事

回到开头那张统一视角的表。一旦仿真器可微，机器人学习的三大任务在数学上就没有边界，全都退化成"对能调的变量算梯度、往下坡走一步"：

| 任务 | 优化变量 | 优化目标 $L$ | 梯度 |
|------|---------|------------|------|
| 系统辨识 | 仿真参数 $\theta\_{\text{sim}}$ | 仿真—真机轨迹误差 | $\partial L/\partial\theta\_{\text{sim}}$ |
| 策略训练 | 策略参数 $\theta\_\pi$ | 累积奖励的负值 $-R$ | $\partial(-R)/\partial\theta\_\pi$ |
| 轨迹优化 | 控制序列 $a\_0\dots a\_T$ | 轨迹总代价 $J$ | $\partial J/\partial a$ |

> 三行的更新动作都是 $\text{变量}\leftarrow\text{变量}-\alpha\cdot\text{梯度}$。差别只在"梯度由谁来算"：可微仿真把整条轨迹变成一张透明的计算图，用链式法则**精确**地把梯度一路传回去；而像 PPO 这种把环境当黑箱的方法，只能靠大量采样去**估计**梯度方向，方差大、要的样本多。这就是"梯度穿透物理层级，实现端到端优化"那句话的实际含义。

实践中你几乎不用手动选学习率 $\alpha$——**Adam、RMSprop** 这类自适应优化器（adaptive optimizer）会根据历史梯度自动调步长，省去人工调参的麻烦。但它们调的仍是同一个量：你已经手算过的那个梯度。

## 术语表

- **Adam**：一种自适应学习率优化器，按历史梯度自动调整每个参数的步长。
- **CEM（Cross-Entropy Method）**：基于采样的优化方法，常用于求全局粗解。
- **导数（Derivative）**：单变量函数在某点切线的斜率，衡量"$x$ 动一点 $y$ 动多少"。
- **梯度（Gradient, $\nabla f$）**：多变量函数各偏导数组成的向量，指向上升最快的方向。
- **梯度下降（Gradient Descent, GD）**：沿梯度反方向迭代更新变量以最小化目标的优化方法。
- **学习率（Learning Rate, $\alpha$）**：梯度下降每步的步长系数，太大发散、太小过慢。
- **局部最优 / 全局最优（Local / Global Optimum）**：附近最小点 / 整个定义域上的最小点。
- **MPPI（Model Predictive Path Integral）**：基于采样的模型预测控制方法。
- **偏导数（Partial Derivative）**：只让一个变量变化、其余固定时，目标对该变量的变化率。
- **PPO（Proximal Policy Optimization）**：主流无模型强化学习算法，靠采样估计梯度。
- **策略训练（Policy Training）**：学习一个从状态到动作的映射。
- **系统辨识（System Identification, SI）**：用真机数据估计仿真模型参数。
- **温启动（Warm Start）**：用粗糙可行解初始化精细优化，缓解局部最优。
- **轨迹优化（Trajectory Optimization, TO）**：规划一条最优的控制序列。
