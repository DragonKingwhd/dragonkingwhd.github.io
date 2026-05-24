---
layout: post
title: "从单摆到浮动基座：机器人动力学方程的演进"
date: 2026-05-24 10:00:00 +0800
categories: [机器人学, 控制系统]
tags: [动力学, 浮动基座, 全身控制, 拉格朗日方程, 接触力]
author: "Dragonking"
excerpt: "一根棍子的运动方程，和一台人形机器人的运动方程，长得其实是同一个样子。本文从单摆出发，一项一项把标量推广成矩阵，看懂机器人动力学方程里每个符号的来历。"
kb: true
kb_cat: control
---

第一次翻开人形机器人的动力学方程，多半会被一行符号劝退：

$$M(q)\ddot q + C(q,\dot q)\dot q + g(q) = S^\top \tau + \sum_i J_{c,i}^\top f_c^{(i)}$$

矩阵、雅可比、选择矩阵、接触力，全堆在一起。但如果你学过高中物理里的单摆，那么这行方程你其实**已经认识一大半了**——它只是单摆方程的"加宽版"。本文的目标，就是从一根棍子开始，一项一项把它推广成上面这一行，让每个符号都有来历。

## 直觉：运动方程在说一件什么事

抛开所有符号，任何一个机械系统的运动方程都在讲同一句话：

> **「让它动起来一共要花的力」 = 「你的电机出的力」 + 「环境帮你出的力」**

这里有一个容易混淆的地方先说清楚：方程其实做了**两次不同方向的拆分**。

- **等号左边是"需求侧"**——让它动起来一共要花多少力，又分两块：一块用来对抗惯性（越重、转得越快越费力），一块用来对抗重力和各种"假想力"（比如旋转时甩出去的离心效应）。
- **等号右边是"供给侧"**——这些力从哪来，分两块：你的电机力矩，加上环境（地面）的接触力。

所以**不是**"对抗惯性 = 电机出力、对抗重力 = 环境出力"那样一一对应。等号真正的意思是：左边两笔"要花的钱"加起来，正好由右边两个"出钱方"凑齐。电机和地面是出钱的两方，惯性和重力是要花的两笔账。

单摆只有一个角度要管，所以这些"力"都是一个个数字（标量）；人形机器人有几十个关节要同时管，于是同样的话得用**向量和矩阵**来说。结构没变，只是从"一根水管"变成了"一捆水管"。下面先看那根水管。

## 起点：单摆（1 自由度）

考虑一个质量 $m$、杆长 $l$ 的理想单摆，$\theta$ 是杆与竖直方向的夹角。它的运动方程是：

<svg viewBox="0 0 320 200" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;">
  <!-- 天花板 -->
  <line x1="40" y1="30" x2="200" y2="30" stroke="var(--text-mute)" stroke-width="2"/>
  <line x1="120" y1="30" x2="120" y2="38" stroke="var(--text-mute)" stroke-width="1.5"/>
  <!-- 竖直参考虚线 -->
  <line x1="120" y1="30" x2="120" y2="170" stroke="var(--border-strong)" stroke-width="1.5" stroke-dasharray="4 4"/>
  <!-- 摆杆 -->
  <line x1="120" y1="30" x2="200" y2="150" stroke="var(--primary-color)" stroke-width="3"/>
  <!-- 摆球 -->
  <circle cx="200" cy="150" r="14" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2.5"/>
  <text x="200" y="155" fill="var(--text-primary)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">m</text>
  <!-- 角度标注 -->
  <path d="M 120 90 A 60 60 0 0 1 145 84" fill="none" stroke="var(--accent-color)" stroke-width="1.5"/>
  <text x="138" y="78" fill="var(--accent-color)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">θ</text>
  <!-- 杆长标注 -->
  <text x="150" y="98" fill="var(--text-soft)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">l</text>
  <!-- 重力箭头 -->
  <line x1="200" y1="170" x2="200" y2="195" stroke="var(--secondary-color)" stroke-width="2" marker-end="url(#arrowg)"/>
  <text x="218" y="190" fill="var(--secondary-color)" text-anchor="middle" font-family="Inter, sans-serif" font-size="12">mg</text>
  <!-- 关节力矩 -->
  <path d="M 100 40 A 22 22 0 0 1 138 48" fill="none" stroke="var(--text-soft)" stroke-width="2" marker-end="url(#arrowt)"/>
  <text x="92" y="55" fill="var(--text-soft)" text-anchor="middle" font-family="Inter, sans-serif" font-size="13">τ</text>
  <defs>
    <marker id="arrowg" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 z" fill="var(--secondary-color)"/>
    </marker>
    <marker id="arrowt" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 z" fill="var(--text-soft)"/>
    </marker>
  </defs>
</svg>

$$\underbrace{ml^2\,\ddot\theta}_{\text{惯量}\,\cdot\,\text{角加速度}} + \underbrace{mgl\sin\theta}_{\text{重力项}} = \underbrace{\tau}_{\text{关节力矩}}$$

三个符号的含义：

- $ml^2$：摆绕转轴的**转动惯量（moment of inertia）**，单位 $\text{kg}\cdot\text{m}^2$，相当于"转动版的质量"。
- $mgl\sin\theta$：重力对转轴产生的**回复力矩**，单位 $\text{N}\cdot\text{m}$（注意是力矩，不是力），角度越偏离竖直，它越大。
- $\tau$：电机施加在关节上的**力矩**，单位 $\text{N}\cdot\text{m}$，是我们唯一能主动控制的量。

这里要特别澄清 $mgl\sin\theta$ 的来历，因为很容易卡住。重力确实只有竖直向下的 $mg$、水平方向没有力——这都对。但能不能让摆**转起来**，看的不是力本身，而是**力矩 = 力 × 力臂**。力臂（lever arm）是转轴到"力作用线"的**垂直距离**：重力作用线是一条竖直线，转轴到它的垂直距离就是摆球的**水平偏移** $l\sin\theta$。于是：

$$\text{重力力矩} = \underbrace{mg}_{\text{竖直力}} \times \underbrace{l\sin\theta}_{\text{水平力臂}} = mgl\sin\theta$$

> 直觉验证：$\theta = 0$（竖直挂着）时 $l\sin 0 = 0$，力臂为零，重力使不上劲，力矩 = 0，摆不动——符合常识；$\theta = 90^\circ$（水平伸出）时力臂最大为 $l$，重力最"想"把它拽下来。
>
> 换个等价说法：把重力沿杆方向和垂直杆方向分解，沿杆那份被杆的张力顶住、不干活，垂直杆的那份 $mg\sin\theta$ 才是真正推动旋转的切向力，再乘力臂 $l$ 同样得到 $mgl\sin\theta$。

> 取贴近真实小臂的参数 $m = 1.5\ \text{kg}$、$l = 0.4\ \text{m}$、$g = 9.81\ \text{m/s}^2$，当前角度 $\theta = 30^\circ = 0.524\ \text{rad}$：
>
> 转动惯量 $ml^2 = 1.5 \times 0.4^2 = 0.24\ \text{kg}\cdot\text{m}^2$
>
> 重力力矩 $mgl\sin\theta = 1.5 \times 9.81 \times 0.4 \times \sin 30^\circ = 2.943\ \text{N}\cdot\text{m}$
>
> 若想让它**静止悬停**（$\ddot\theta = 0$），所需力矩就是 $\tau = 2.943\ \text{N}\cdot\text{m}$。

如果电机多给一点，比如 $\tau = 4\ \text{N}\cdot\text{m}$，剩下的力矩就用来加速：

$$\ddot\theta = \frac{\tau - mgl\sin\theta}{ml^2} = \frac{4 - 2.943}{0.24} = 4.40\ \text{rad/s}^2$$

> 代入验证：$0.24 \times 4.40 + 2.943 = 1.056 + 2.943 = 3.999 \approx 4\ \text{N}\cdot\text{m}$，与施加力矩一致。

这就是 1 自由度的全部故事：一个惯量项、一个重力项、一个控制项。

## 推广：浮动基座（$n_v$ 自由度）

现在把单摆换成一台**浮动基座（floating base）**机器人——所谓"浮动"，是指它的躯干不像机械臂那样被螺栓固定在地上，而是自由地飘在空间里，靠脚和地面的接触才站得住。

它有几十个关节要同时管，所以单个角度 $\theta$ 变成了**广义坐标（generalized coordinates）**向量 $q$，对应的广义速度 $\dot q \in \mathbb{R}^{n_v}$。运动方程长这样：

$$\underbrace{M(q)\,\ddot q}_{\text{惯量}\,\cdot\,\text{加速度}} + \underbrace{C(q,\dot q)\,\dot q + g(q)}_{\text{科氏} + \text{重力}} = \underbrace{S^\top \tau}_{\text{关节力矩}} + \underbrace{\sum_i J_{c,i}^\top f_c^{(i)}}_{\text{接触力}}$$

逐项和单摆对照，会发现它们是一一对应的：

| 单摆（1-DOF） | 浮动基座（$n_v$-DOF） | 物理意义 |
|------|------|------|
| $ml^2$ | $M(q) \in \mathbb{R}^{n_v \times n_v}$ | 质量矩阵 / 惯量 |
| $mgl\sin\theta$ | $C(q,\dot q)\dot q + g(q)$ | 非线性力项（科氏 + 重力） |
| $\tau$ | $S^\top \tau$ | 关节力矩 |
| —（固定基座没有） | $\sum_i J\_{c,i}^\top f_c^{(i)}$ | 接触力 |

把这四项拆开看：

**① 质量矩阵 $M(q)$**：单摆的 $ml^2$ 是一个数，机器人则是一个 $n_v \times n_v$ 的矩阵，因为推动一个关节会牵连其他关节一起动（耦合）。它还随姿态 $q$ 变化——手臂伸直和收拢时，整体惯量并不一样。

**② 非线性力项 $C\dot q + g$**：单摆的 $mgl\sin\theta$ 只有重力。机器人多出一个 $C(q,\dot q)\dot q$ 项，描述旋转带来的**科氏力与离心力（Coriolis & centrifugal）**——这里的 $\dot q$ 就是广义速度（各关节转动的快慢），而整个 $C\dot q$ 项跟速度的**平方**挂钩：转得越快，它越大。你伸直手臂原地快速转圈、手被甩向外张开，那股向外的力就是它。

至于"单摆这一项恰好为零"，意思是把单摆的数代进去，**整个 $C(q,\dot q)\dot q$ 算出来等于数字 0**，对方程毫无贡献，所以单摆方程里压根没有 $\dot\theta$ 这种速度项。为什么是 0?因为这种"被甩出去"的力，要么来自多个关节互相牵连，要么来自惯量随姿态变化；而单摆只有一个关节、惯量 $ml^2$ 又是常数，没有可甩的对象，这一项自然消失。机器人关节多、惯量随姿态变，它才冒出来。

**③ 关节力矩 $S^\top\tau$**：多出一个**选择矩阵（selection matrix）** $S$。原因是浮动基座的 6 个自由度（躯干的 3 个平移 + 3 个旋转）**没有电机**——没人能凭空给躯干一个推力。$S$ 的作用就是把电机力矩 $\tau$ 只"分发"给那些真正装了电机的关节。

**④ 接触力 $\sum_i J_{c,i}^\top f_c^{(i)}$**：这是单摆完全没有的新项。机器人靠脚踩地的反作用力站立和行走，$f_c^{(i)}$ 是第 $i$ 个接触点的力，**接触雅可比（contact Jacobian）** $J_{c,i}$ 负责把这个力从接触点"翻译"回每个关节坐标上。

### 数字示例 ①：让单摆方程从浮动基座方程里"长回来"

检验推广是否自洽，最好的办法是让它退化。设想机器人只剩一个关节、固定在地面（没有浮动基座、没有接触），那么：$n_v = 1$，$q = [\theta]$，$\dot q = [\dot\theta]$，且

$$M(q) = [\,ml^2\,] = [0.24],\quad C\dot q = [0],\quad g(q) = [\,mgl\sin\theta\,] = [2.943],\quad S = [1],\quad \textstyle\sum_i J_{c,i}^\top f_c^{(i)} = [0]$$

代回矩阵方程：

$$[0.24]\,\ddot\theta + [0] + [2.943] = [1]\cdot\tau + [0] \;\Longrightarrow\; 0.24\,\ddot\theta + 2.943 = \tau$$

> 这与前面单摆的 $ml^2\ddot\theta + mgl\sin\theta = \tau$ 完全相同。说明矩阵方程是单摆方程的真·超集——把维度压到 1、去掉接触，它自己就退化回那根棍子。

### 数字示例 ②：接触力项怎么算

考虑一台约 $60\ \text{kg}$ 的机器人**双脚站立**，体重 $W = 60 \times 9.81 = 588.6\ \text{N}$，两脚平均分担，每只脚的竖直支撑力：

$$f_c^{(\text{左})} = f_c^{(\text{右})} = \frac{W}{2} = \frac{588.6}{2} = 294.3\ \text{N}$$

假设某个膝关节的接触雅可比在竖直方向的分量为 $J_{c,z} = 0.35$（量纲为长度，单位 $\text{m}$，表示该脚竖直受力对膝关节产生的力臂效应），那么单只脚的接触力映射到这个膝关节上的等效力矩：

$$\tau_{\text{膝}}^{\text{接触}} = J_{c,z}\cdot f_c = 0.35 \times 294.3 = 103.0\ \text{N}\cdot\text{m}$$

这 $103.0\ \text{N}\cdot\text{m}$ 是地面通过接触力"无偿"帮膝关节扛住的力矩。要看清它的意义，把站立时的方程写成"静止版"（不动，故 $\ddot q = 0$、$\dot q = 0$）：

$$\underbrace{g(q)}_{\text{重力往下拽}} = \underbrace{S^\top \tau}_{\text{电机出力}} + \underbrace{J_c^\top f_c}_{\text{地面帮忙}} \;\Longrightarrow\; S^\top \tau = g(q) - J_c^\top f_c$$

> 重力在每个关节上制造"塌下去"的趋势 $g(q)$，地面反作用力通过 $J_c^\top f_c$ 顶住了一大部分（膝关节这里顶了 103 N·m），**电机只需补上两者的差额**。这个"差额"不是"让腿动起来的力"，而是维持平衡所需的净力矩——若地面顶的正好够，电机出力可接近 0，腿靠骨架就稳稳站住（想想你直腿站着并不觉得累）。等到要迈步、下蹲（$\ddot q \neq 0$），电机才额外再掏出 $M(q)\ddot q$ 那一份去产生加速度。
>
> 这也正是接触雅可比的现实意义：$f_c$ 是脚底那个真实的 3D 反作用力（牛顿），而 $J_c^\top$ 是个"翻译器"，负责回答**"脚底这一推，会在膝、髋、踝各关节分别产生多大力矩"**。没有它，你只知道脚底有 294 N，却不知道它替哪个关节分担了多少——$J_c^\top f_c$ 就是把"地面的帮忙"按关节摊派下去的账本。

## 应用：这行方程在机器人控制里干什么

理解了方程结构，就能看懂现代机器人控制里两个高频操作。

**正动力学（forward dynamics）——用于仿真**。在当前时刻 $t$，已知当前**状态** $(q,\dot q)$ 和当前**输入**（这一刻施加的力矩 $\tau$ 与接触力 $f_c$），分三步往前推一帧：

1. **反解加速度**：把方程整理成 $\ddot q = M(q)^{-1}\big[S^\top\tau + J_c^\top f_c - C\dot q - g\big]$，算出这一刻的 $\ddot q$。
2. **积分一步**（取小步长 $\Delta t$，如 $0.001\ \text{s}$）：加速度积分得速度，速度积分得位置：

$$\dot q(t+\Delta t) = \dot q(t) + \ddot q\,\Delta t,\qquad q(t+\Delta t) = q(t) + \dot q(t)\,\Delta t$$

3. 得到**下一时刻**的状态 $(q,\dot q)$，再拿它当新的"当前状态"重复。

> 数字示例：单摆当前 $\dot\theta = 0$、算得 $\ddot\theta = 4.40\ \text{rad/s}^2$，取 $\Delta t = 0.001\ \text{s}$，则下一步 $\dot\theta = 0 + 4.40 \times 0.001 = 0.0044\ \text{rad/s}$。一帧帧滚下去，就把摆的运动"放电影"般演出来了。

MuJoCo、Isaac Sim 这类物理引擎，本质就是每个时间步都在解这个方程。

**逆动力学（inverse dynamics）——用于控制**。反过来：先想好"我希望机器人产生什么加速度 $\ddot q$"（比如重心往左移、抬右脚），再用方程反算需要多大的关节力矩 $\tau$ 去实现它。**全身控制（Whole-Body Control, WBC）** 正是建立在这一步上——把"保持平衡""跟踪步态""不超关节限位"全写成对 $\ddot q$、$\tau$、$f_c$ 的约束，再求解满足这行方程的最优力矩。

> 换句话说：单摆方程教你"给定力矩，摆会怎么动"；而控制工程师每天在做的，是反过来回答"想让它这么动，该给多少力矩"。同一行方程，正着读是仿真，反着读是控制。

如果你想顺着"状态怎么表示"这条线继续看，可以接着读 [状态向量打包：X = F(X, U)](/state-vector/)，它和本文是同一套思路的两面——一个讲**状态怎么排**，一个讲**力怎么算**。

## 术语表

- **接触雅可比（Contact Jacobian, $J_c$）**：把接触点的力/速度映射到广义坐标的矩阵。
- **科氏力与离心力（Coriolis & Centrifugal）**：物体旋转时出现的速度相关惯性力，对应方程中的 $C(q,\dot q)\dot q$ 项。
- **浮动基座（Floating Base）**：躯干不固定在环境中、可在空间中自由运动的机器人模型，相对于固定基座（如工业机械臂）而言。
- **正动力学 / 逆动力学（Forward / Inverse Dynamics）**：由力矩求加速度 / 由期望加速度求力矩，互为反问题。
- **广义坐标（Generalized Coordinates, $q$）**：完整描述系统位形所需的一组独立变量。
- **转动惯量（Moment of Inertia）**：物体抵抗转动状态改变的度量，转动版的"质量"。
- **质量矩阵（Mass Matrix, $M(q)$）**：广义惯量，描述各自由度之间的惯性耦合。
- **选择矩阵（Selection Matrix, $S$）**：从全部自由度中挑出有电机驱动的那些关节的映射矩阵。
- **全身控制（Whole-Body Control, WBC）**：在满足完整动力学方程与多重任务约束下，统一求解全身关节力矩的控制框架。
- **自由度（Degree of Freedom, DOF）**：系统可独立运动的方向数，浮动基座机器人 $n_v = 6 + $ 关节数。
