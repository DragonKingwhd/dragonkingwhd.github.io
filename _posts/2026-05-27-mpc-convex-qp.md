---
layout: post
title: "MPC 不是一条方程：从滚动优化到凸 QP"
date: 2026-05-27 10:00:00 +0800
categories: [机器人学, 控制系统]
tags: [MPC, 凸优化, QP, 模型预测控制, 四足机器人, 求解器]
author: "Dragonking"
excerpt: "看 Cheetah 3 论文时卡在 convex MPC：它到底是一种新方程，还是别的东西？本文把 MPC、动力学方程、QP、求解器四个层次彻底分开，再用一个能手算的小例子走通从滚动优化到凸 QP 的全过程。"
kb: true
kb_cat: control
---

读 MIT Cheetah 3 的论文时，很容易卡在一个地方：它说自己用了 **凸 MPC(convex MPC)**，可翻遍上下文也找不到一条叫 "MPC" 的方程。于是产生一个错觉——是不是我漏掉了某个公式？

不是。**MPC 本身就不是一条方程。** 它是一种控制方法，一种"反复求解优化问题"的框架。动力学方程会出现在它内部，但 MPC 不等于那条方程。这篇文章的目标，就是把搅在一起的四个层次拆开，再用一个能用笔算出答案的小例子，把"滚动优化"怎么变成"凸 QP"走一遍。

## 直觉：MPC 是开车，不是地图

先抛开所有符号。模型预测控制(Model Predictive Control, MPC)做的事，和你开车找路其实是一回事：

> 我知道车怎么开(模型)，我想从 A 到 B(目标)，那我**往前看一小段路**，规划出接下来几步怎么打方向盘，**但只执行第一步**，到了下一个路口再重新看、重新规划。

"往前看一小段、只走第一步、然后重来" ——这个滚动向前的动作，就是 MPC 的全部精髓。它不背诵一条固定方程，而是每个控制周期现场解一道优化题。

这里有个一直被混淆的对应关系，值得用导航类比钉死：

| 导航里的角色 | MPC 里的角色 | 它是什么 |
|------|------|------|
| 目标:从 A 到 B | 控制目标 | 让机身位姿跟踪期望值 |
| 地图:路怎么连 | 动力学/运动学方程 | 受力之后机器人怎么动 |
| 问题形式:最短路 | QP / NLP | 这道优化题长什么样 |
| 搜索算法:A\* / Dijkstra | 求解器 | qpOASES / OSQP / HPIPM |

所以"凸 MPC"不是一种新方程，而是说**这道优化题最后被整理成了凸优化的形式**。下面把这道题正式写出来。

## 正式定义:MPC 的优化问题

给定系统的离散动力学 $x_{t+1} = f(x_t, u_t)$,在当前时刻 $t$ 观测到状态 $x_t$,MPC 求解未来 $N$ 步的最优控制序列:

$$\min_{u_0,\dots,u_{N-1}} \ \sum_{k=0}^{N-1} \Big[ (x_k - x_k^{\text{ref}})^\top Q (x_k - x_k^{\text{ref}}) + u_k^\top R\, u_k \Big]$$

$$\text{s.t.}\quad x_{k+1} = f(x_k, u_k),\quad x_k \in \mathcal{X},\quad u_k \in \mathcal{U}$$

其中 $Q \succeq 0$ 是状态跟踪权重,$R \succ 0$ 是控制代价权重,$\mathcal{X}/\mathcal{U}$ 是状态与控制的约束集合(关节限位、力矩上限、摩擦锥等),$N$ 是预测时域(prediction horizon)。

求解后得到一整条 $u_0^\*,\dots,u_{N-1}^\*$,但**只把 $u_0^\*$ 发给电机**,下一周期重新观测、重新求解。

> 取一个 1 维点质量(double integrator),状态 $x=[p,\,v]^\top$(位置 m、速度 m/s),控制 $u$ 是加速度(m/s²),采样 $\Delta t=0.1\text{ s}$,则
> $$x_{k+1} = \begin{bmatrix}1 & 0.1\\ 0 & 1\end{bmatrix} x_k + \begin{bmatrix}0.005\\ 0.1\end{bmatrix} u_k$$
> 设当前 $x_0=[0,\,0]^\top$,目标 $x^{\text{ref}}=[1,\,0]^\top$,取一步控制 $u_0=2.0\ \text{m/s}^2$,代入得
> $$x_1 = \begin{bmatrix}1&0.1\\0&1\end{bmatrix}\begin{bmatrix}0\\0\end{bmatrix} + \begin{bmatrix}0.005\\0.1\end{bmatrix}\cdot 2.0 = \begin{bmatrix}0.01\\0.20\end{bmatrix}$$
> 即 0.1 s 后位置走到 0.01 m、速度到 0.20 m/s。MPC 要做的就是挑一整串 $u_k$,让这条预测轨迹整体最贴近 $x^{\text{ref}}$。

## 为什么会变成 QP

注意上面那道题:如果动力学 $f$ 是**线性**的($x_{k+1}=Ax_k+Bu_k$),代价是**二次型**,约束是**线性**的,那么把状态用控制序列逐步代换、消掉所有 $x_k$ 之后,整道题的变量就只剩控制序列 $\mathbf{u}=[u_0,\dots,u_{N-1}]^\top$,而且目标变成 $\mathbf{u}$ 的二次函数、约束变成 $\mathbf{u}$ 的线性不等式。这正好是**二次规划(Quadratic Programming, QP)** 的标准形式:

$$\min_{\mathbf{x}}\ \tfrac{1}{2}\mathbf{x}^\top H \mathbf{x} + g^\top \mathbf{x} \quad \text{s.t.}\quad A\mathbf{x}\le b,\ \ C\mathbf{x}=d$$

这里的 $\mathbf{x}$ 就是待求的控制变量(对四足机器人而言,常常是未来若干步的足端力)。当 $H \succeq 0$(半正定)且约束线性时,这是一个**凸 QP**——只要求解器收敛,拿到的就是全局最优,不会卡在局部极小,求解时间也稳定可预测。这就是实时控制最看重的性质。

> 取一个最小的标量 QP:$H=4,\ g=-12$,即 $\min\ \tfrac12\cdot4\,x^2 - 12x = 2x^2-12x$。
> 无约束时令导数 $4x-12=0$,得 $x^\*=3$,目标值 $2(9)-12(3)=-18$。
> 若加入约束 $x\le 2$:目标在 $x<3$ 区间随 $x$ 增大而下降,故最优顶到边界 $x^\*=2$,目标值 $2(4)-12(2)=-16$。
> 这两步——求二次型极小、被线性约束顶到边界——就是任何 QP 求解器内部在做的事,只不过真实问题里 $\mathbf{x}$ 是几十上百维的向量。

凸 QP 的对面是**非凸 MPC**:完整四足动力学里有非线性项、接触切换、摩擦、碰撞、关节耦合,这些会把问题推成非凸优化,容易陷局部最优、求解也慢。整个 MPC 家族可以按"最终被整理成什么数学问题"分层:

<svg viewBox="0 0 560 250" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto;" font-family="Inter, sans-serif">
  <!-- 根 -->
  <rect x="220" y="14" width="120" height="40" rx="8" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2.5"/>
  <text x="280" y="39" fill="var(--text-primary)" text-anchor="middle" font-size="15">MPC</text>
  <!-- 四个分支框 -->
  <g>
    <rect x="20" y="110" width="120" height="44" rx="8" fill="var(--bg-secondary)" stroke="var(--accent-color)" stroke-width="2"/>
    <text x="80" y="130" fill="var(--text-primary)" text-anchor="middle" font-size="13">线性 MPC</text>
    <text x="80" y="147" fill="var(--text-soft)" text-anchor="middle" font-size="11">→ 常变成 QP</text>
  </g>
  <g>
    <rect x="160" y="110" width="120" height="44" rx="8" fill="var(--bg-secondary)" stroke="var(--accent-color)" stroke-width="2"/>
    <text x="220" y="130" fill="var(--text-primary)" text-anchor="middle" font-size="13">非线性 NMPC</text>
    <text x="220" y="147" fill="var(--text-soft)" text-anchor="middle" font-size="11">→ 常变成 NLP</text>
  </g>
  <g>
    <rect x="300" y="110" width="120" height="44" rx="8" fill="var(--bg-secondary)" stroke="var(--primary-color)" stroke-width="2"/>
    <text x="360" y="130" fill="var(--text-primary)" text-anchor="middle" font-size="13">凸 MPC</text>
    <text x="360" y="147" fill="var(--text-soft)" text-anchor="middle" font-size="11">→ QP / SOCP</text>
  </g>
  <g>
    <rect x="440" y="110" width="120" height="44" rx="8" fill="var(--bg-secondary)" stroke="var(--secondary-color)" stroke-width="2"/>
    <text x="500" y="130" fill="var(--text-primary)" text-anchor="middle" font-size="13">非凸 MPC</text>
    <text x="500" y="147" fill="var(--text-soft)" text-anchor="middle" font-size="11">→ 更真实更难</text>
  </g>
  <!-- 连线 -->
  <path d="M280 54 L80 110" stroke="var(--border-strong)" stroke-width="1.5" fill="none"/>
  <path d="M280 54 L220 110" stroke="var(--border-strong)" stroke-width="1.5" fill="none"/>
  <path d="M280 54 L360 110" stroke="var(--border-strong)" stroke-width="1.5" fill="none"/>
  <path d="M280 54 L500 110" stroke="var(--border-strong)" stroke-width="1.5" fill="none"/>
  <!-- 底注 -->
  <text x="280" y="210" fill="var(--text-mute)" text-anchor="middle" font-size="12">同一个控制框架,因模型/代价/约束怎么写,落成不同的数学问题</text>
</svg>

## 应用:Cheetah 3 的 convex MPC

MIT Cheetah 3 没有把整台机器狗建成复杂的多刚体非线性模型,而是用**单刚体动力学(Single Rigid Body Dynamics, SRBD)** 把它简化成:

> 一个机身刚体 + 四条腿在触地点产生的接触力。

腿本身的质量、关节耦合都被忽略,机器人就是一个会被四个足端力推动、转动的"盒子"。MPC 优化的主变量,是未来若干步、每只支撑脚的三维接触力:

$$\mathbf{x} = \big[\,f_1^{(0)},\dots,f_4^{(0)},\ \ f_1^{(1)},\dots,f_4^{(1)},\ \ \dots,\ f_1^{(N-1)},\dots,f_4^{(N-1)}\,\big]^\top$$

目标是让机身的位置、速度、姿态跟踪期望步态指令,同时满足摩擦与力大小约束。它之所以能落成凸 QP,靠的是一连串工程简化:

1. 机身当成**单刚体**,绕姿态的旋转动力学做小角度线性化;
2. **接触时序提前给定**——哪只脚支撑、哪只脚摆动是步态规划器先排好的,不进优化;
3. **摩擦锥用线性不等式近似**(金字塔近似),而非真正的二阶锥;
4. 代价函数写成**二次型**;
5. 约束写成**线性**约束。

这样 $H$ 半正定、约束线性,问题就是凸 QP,可以用 qpOASES 在真实机器人上以上百赫兹实时求解。

> 摩擦锥的线性近似:支撑脚法向力 $f_z$、切向力 $f_x,f_y$,摩擦系数 $\mu$。真实约束是 $\sqrt{f_x^2+f_y^2}\le \mu f_z$(二阶锥,非线性)。金字塔近似改写成四条线性不等式:$|f_x|\le \mu f_z,\ |f_y|\le \mu f_z$。
> 取 $\mu=0.6,\ f_z=120\ \text{N}$:近似给出 $|f_x|\le 0.6\times120=72\ \text{N}$。而真实锥允许的水平合力上限也是 $0.6\times120=72\ \text{N}$,只是金字塔把"圆"换成了"方"——边长换算后稍保守,但全是线性约束,QP 能直接吃。

## 进阶:该认识哪几个求解器

求解器(solver)是真正"把最优解算出来"的那段代码。做机器人、MPC、仿真控制,先认识这五个就够:

| 求解器 | 方法 | 适合 | 备注 |
|------|------|------|------|
| **qpOASES** | active-set | 中小规模、连续重复求解的 QP | Cheetah 3 的 convex MPC 用它,warm start 效果好 |
| **OSQP** | ADMM 一阶法 | 稀疏、大规模 QP | 开源、接口友好、鲁棒,中等精度很强 |
| **HPIPM** | 内点法 | 最优控制结构的 QP 子问题 | 常和 acados 配套,面向实时 MPC/NMPC |
| **GUROBI** | 商业通用 | 离线优化、调度、MILP/MIQP | 性能强但商业授权,实时上车成本高 |
| **MOSEK** | 商业凸优化 | 高精度凸优化、SOCP/SDP | 数值稳定,学术建模常见 |

这里 **warm start(热启动)** 值得单独点出:MPC 每一帧要解的 QP 和上一帧极像——只是当前状态变了一点点。active-set 类的 qpOASES 可以拿上一次的解当这次的初值,迭代次数大幅下降,这正是它在实时控制里经久不衰的原因。

更现代的开源生态里还有 **ProxQP / Clarabel / ECOS / SCS** 等(后几个是锥规划求解器,不只解 QP),CVXOPT / quadprog 则偏教学与原型验证。现阶段不必全记,知道"遇到凸 QP 先想 qpOASES / OSQP / HPIPM"即可。

按问题类型建立分诊直觉:

- 凸 QP → qpOASES / OSQP / HPIPM / GUROBI / MOSEK
- 非线性优化 NLP → IPOPT / SNOPT / acados
- 强化学习 PPO → 不用 QP 求解器,而是梯度下降训练神经网络

## 进阶:MPC 与 PPO 是两种东西

最后澄清一个常见混淆。**MPC 是在线优化控制;PPO 是离线训练出的策略网络。**

MPC 每个控制周期都现场解一道优化题:观测当前状态 → 建立 QP → 求解器算出最优控制 → 执行第一步 → 下一周期重来。它不"学习",每一帧都在算。

近端策略优化(Proximal Policy Optimization, PPO)则是在训练阶段反复采样轨迹、算奖励、更新网络参数,训练完部署时只剩神经网络前向推理:状态进、动作出。

所以部署时 PPO 通常比 MPC 快(一次前向 vs 一次求解),但在可解释性、硬约束处理和稳定性上,MPC 更直接——它的关节限位、力矩上限是写死在约束里的,而 PPO 只能靠奖励"软"地鼓励。

把整篇压成一句话:

> **MPC 不是运动学方程,而是"基于模型的滚动优化控制方法"。模型、代价、约束怎么写,决定它落成凸 QP、非线性 NLP 还是混合整数问题。Cheetah 3 的 convex MPC,是把四足机器人简化成单刚体模型、把未来足端力优化整理成凸 QP,从而能用 qpOASES 在真机上实时求解。**

## 术语表

- **acados** — 面向嵌入式实时最优控制的开源框架,常配 HPIPM 求解 NMPC。
- **ADMM (Alternating Direction Method of Multipliers, 交替方向乘子法)** — 一类一阶优化方法,OSQP 的内核。
- **active-set (有效集法)** — 一类 QP 求解方法,通过维护"当前起作用的约束集合"迭代,适合中小规模、可热启动的问题。
- **HPIPM (High-Performance Interior-Point Method)** — 面向最优控制结构的高性能内点法 QP 求解器。
- **IK (Inverse Kinematics, 逆运动学)** — 由末端位姿反解关节角,正文未展开,属运动学层。
- **MILP / MIQP (Mixed-Integer Linear/Quadratic Programming, 混合整数线性/二次规划)** — 含整数变量的优化问题,非凸。
- **MPC (Model Predictive Control, 模型预测控制)** — 滚动时域内反复求解优化问题、只执行第一步的控制框架。
- **NLP (Nonlinear Programming, 非线性规划)** — 目标或约束非线性的优化问题。
- **NMPC (Nonlinear MPC, 非线性模型预测控制)** — 用非线性模型的 MPC,通常落成 NLP。
- **OSQP (Operator Splitting QP solver)** — 基于 ADMM 的开源稀疏 QP 求解器。
- **PPO (Proximal Policy Optimization, 近端策略优化)** — 一种强化学习策略梯度算法。
- **QP (Quadratic Programming, 二次规划)** — 二次目标 + 线性约束的优化问题;$H\succeq0$ 时为凸 QP。
- **qpOASES** — 经典 active-set QP 求解器,Cheetah 3 convex MPC 采用。
- **SDP (Semidefinite Programming, 半定规划)** — 约束含半正定矩阵的凸优化。
- **SOCP (Second-Order Cone Programming, 二阶锥规划)** — 约束含二阶锥的凸优化,真实摩擦锥即属此类。
- **SRBD (Single Rigid Body Dynamics, 单刚体动力学)** — 把机器人简化为单个刚体 + 接触力的近似模型。
- **warm start (热启动)** — 用上一次求解的解作为本次的初值,加速重复求解。
