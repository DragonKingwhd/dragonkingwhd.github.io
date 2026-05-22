---
layout: post
title: "PPO 调参笔记（二）：Surrogate Loss"
date: 2026-05-20
categories: [强化学习, 计算机科学]
tags: [PPO, Surrogate Loss, Clip, 策略梯度, 强化学习]
author: "Dragonking"
excerpt: "PPO 真正在最小化的策略损失叫 surrogate loss，写成那个长长的 min-clip 公式。这一篇拆开讲它每个部件在干什么，以及训练曲线里的尖峰意味着什么。"
kb: true
kb_cat: rl
series: "PPO 调参笔记"
series_order: 2
---

PPO 论文里的策略损失公式叫 **surrogate loss**（替代损失），代码里通常打成 `policy_loss` 或 `surrogate_loss`：

$$
\mathcal{L}^{\text{CLIP}}(\theta)
 = \mathbb{E}_t\!\left[\min\!\Big(r_t(\theta)\,A_t,\;\text{clip}(r_t(\theta),\,1-\epsilon,\,1+\epsilon)\,A_t\Big)\right]
$$

第一次看这个公式基本是劝退的。但拆开看其实就三件事：**重要性比率**、**clip 裁剪**、**min 选最小**。这篇把它一点点拆。

## 第一件事：比率 $r$

$r_t(\theta) = \dfrac{\pi_\theta(a_t \mid s_t)}{\pi_{\theta_\text{old}}(a_t \mid s_t)}$，叫**重要性采样比率**。

为什么要有它？PPO 跟原生 policy gradient 不一样的地方在于：一批采样数据要被多个 epoch 反复用（off-policy 一点点）。但这批数据是用旧策略 $\pi_\text{old}$ 采的，现在策略已经更新成 $\pi_\theta$ 了——用旧数据评估新策略，得乘上这个比率做修正，不然梯度方向不对。

直觉：
- $r > 1$：新策略比旧策略更喜欢这个动作
- $r < 1$：新策略比旧策略更不喜欢
- $r = 1$：完全没变（每个 PPO update 的第一个 epoch 就是这样）

公式里另一个 $A_t$ 是 advantage（动作好坏的相对评分），正表示这个动作好于平均水平，负表示差。

## 第二件事：clip 裁剪

把比率裁剪到 $[1-\epsilon, 1+\epsilon]$ 区间内，$\epsilon$ 常取 0.1 ～ 0.3，默认 0.2。

这是 PPO 最核心的设计：**不允许新策略离旧策略太远**。如果 $r$ 已经超出 $[0.8, 1.2]$（取 $\epsilon=0.2$ 时），就把它当 0.8 或 1.2 来处理，不让它继续往外走。

这等价于在做 trust region：TRPO 解一个带 KL 约束的二阶优化问题来限制步长，PPO 用 clip 这种粗暴但管用的一阶替代。

## 第三件事：min 取小

为什么是 $\min$？这是 PPO 最巧妙也最容易绕不过来的地方。一句话：**min 让 surrogate 变成真实目标的悲观下界**。

我们最大化 $\mathcal{L}^{\text{CLIP}}$，min 会选小值，所以提供的优化空间更保守。具体看六种情况：

| Advantage | 比率 $r$ | 梯度状态 | 含义 |
| --- | --- | --- | --- |
| $A > 0$（好动作）| $r > 1+\epsilon$ | **停** | 好动作概率已经涨够了 |
| $A > 0$ | $1-\epsilon \le r \le 1+\epsilon$ | 流 | 正常区间，按常规更新 |
| $A > 0$ | $r < 1-\epsilon$ | 流 | 把好动作概率拉回来 |
| $A < 0$（坏动作）| $r > 1+\epsilon$ | 流 | 把坏动作概率压下去 |
| $A < 0$ | $1-\epsilon \le r \le 1+\epsilon$ | 流 | 正常区间，按常规更新 |
| $A < 0$ | $r < 1-\epsilon$ | **停** | 坏动作概率已经压够了 |

要点是 clip 只在两种情况停止梯度：**好动作涨够了**、**坏动作压够了**。其他情况——包括「策略在朝错误方向移动」——梯度都还在，会把策略拉回来。

## 训练曲线该怎么看

`Loss/surrogate` 通常是一个绝对值很小的数，在 0 附近上下波动，偶尔出现尖峰。这是健康样子。

| 现象 | 解读 |
| --- | --- |
| 0 附近小幅震荡 | 健康，多数 batch 没被 clip |
| 持续上升 | advantage 量纲在变化，常见于 reward shaping 改动或 GAE $\lambda$ 不合适 |
| 长时间精确等于 0 | 策略不再更新——advantage 全 0、或者全部被 clip |
| 突然飙到 1+ | 某个 batch 出现极大 advantage，结合 reward 看是不是 reward 爆炸 |
| 尖峰频率越来越高 | 策略变化越来越大，结合 KL 看步长是否失控 |

## 一次真实训练曲线的解读

抽象的「正常 / 不正常」表对刚入门的人帮助有限，这里拿一次真实的 locomotion 训练（约 1100 个 PPO iteration）的实际数值，按 step 对齐看 surrogate 跟其他三条曲线的关系。

> 表头里 **lr** = learning rate（学习率），是优化器每一步给网络参数走多大步长的系数；**entropy** = 策略的「犹豫程度」；**value loss** = 价值网络预测得多准；**surrogate** = 本篇主角，策略损失数值。

| step 段 | lr | entropy | value loss | surrogate |
| --- | --- | --- | --- | --- |
| 0 ~ 100 | 0.01（峰值）| 5.0 → 0 | 0 ↗ 上升中 | ≈ 0 |
| 100 ~ 200 | 0.01 → ~0 | 0 → -3 | 1.5（峰）↘ 下降 | 出现 ~0.05 基线 |
| 200 ~ 500 | ~0（1e-5 量级）| -3 → 缓慢回升 | 0.5 → 0.3 | 基线 0.05 ~ 0.08 |
| 500 ~ 1100 | ~0 | -2（稳态）| 0.3（稳态）| 基线 0.05 ~ 0.1，尖峰最高 0.3 |

把 surrogate 这一列单独拎出来，逐阶段讲为什么是这个形状。

**Step 0 ~ 100：贴近 0**

这一段策略剧烈变化（entropy 从 5 一路掉到 0），但 surrogate 反而很小。原因是 PPO 每个 update 的第一个 epoch 必然 $r = 1$，此时 surrogate $= \mathbb{E}[A]$；而 advantage 经过 batch 归一化后均值为 0，所以即使每个 sample 的 $r \cdot A$ 不小，平均下来也接近 0。同时 lr 还高、clip 还没频繁触发，min() 几乎不咬人，整个 loss 数值就被压在 0 附近。

**Step 100 ~ 300：基线慢慢抬起来**

这一段最反直觉：lr 在快速衰减，**但 surrogate 反而开始变大**。原因是 critic 终于追上来了——value loss 在 step ~150 见顶之后开始下降，意味着 advantage 估计变准、单个 sample 的 |A| 平均变大。同时多 epoch 重用让 $r$ 偏离 1，min() 不再是零选择，surrogate 数值爬到 ~0.05 baseline。

**Step 300+：稳态 + 尖峰**

基线 0.05 ~ 0.08 是健康水平。这一段最值得看的特征是**尖峰偶尔窜到 0.3**——这些尖峰几乎都对应着某个 batch 里出现了高 |A| 样本（机器人差点摔倒、刚好踩到崎岖地形、reward 函数里某个稀疏项激活）。

尖峰本身不是问题，只要满足三点：
- reward 不同步暴跌
- KL 不同步爆炸
- 尖峰之间能回到基线

如果尖峰频率越来越密、基线越来越偏离 0，那就是策略在被某种「极端样本」反复拽来拽去，得回头查 reward shaping 是不是有个项的量纲不合理。

### 一个反直觉点

按直觉，lr 跌到 0 之后策略应该不再更新，surrogate 也应该归零。但上面那条曲线里 lr 早早就降到 1e-5 级别了，surrogate **仍然在 0.05 附近动**。

原因是 surrogate 报告的是「**如果按这个梯度更新会得到多大的 loss 值**」，跟 lr 没直接关系——lr 控制的是参数变化步长，surrogate 测量的是新旧策略之间的「评价差」。只要 $r \ne 1$（多 epoch 重用时几乎一定不等于），surrogate 就有非零数值。

所以「lr 变 0、surrogate 还在动」不是 bug。真正会同步归零的指标是 KL（下一篇会讲）。

## 几个调参点

**`eps` 取多大**。默认 0.2。连续控制可以拉到 0.3 让策略动得快一点，离散控制保守一点用 0.1。我在 locomotion 上用 0.2 没出过事，sim2real 部署阶段会降到 0.1 让策略输出稳一点、抖动小一点。

**`num_epochs` 重用一份数据几次**。通常 4 ～ 10。次数越多，$r$ 离 1 越远，clip 越频繁触发；次数太少又浪费采样。最稳的做法是配 KL 一起看，KL 超阈值就 early stop（下一篇细讲）。

**advantage 一定要归一化**。

```python
adv = (adv - adv.mean()) / (adv.std() + 1e-8)
```

不归一化的话，advantage 量纲会跟 reward shaping 强耦合，调一个超参影响一片。这是 PPO 实现里最容易忘的一行。

## clip 触发率：一个被忽视的指标

很多框架会打印「clip fraction」——每个 batch 里有多少比例的 sample 被 clip 了。这个数比 surrogate loss 本身更有诊断价值：

| clip fraction | 含义 |
| --- | --- |
| < 5% | clip 几乎不工作，步长很小，可能 lr 太低 |
| 10 ～ 30% | 健康，clip 在适度限制 |
| > 50% | 步长太大，多数更新被截断 |

如果框架没打印，自己加一行：

```python
clipped = (ratio < 1 - eps) | (ratio > 1 + eps)
clip_frac = clipped.float().mean()
```

---

surrogate loss 控制的是「这次更新该往哪个方向、走多远」，但走得多远具体能量化吗？这就是下一篇 KL 的事。

**PPO 调参笔记系列**

1. [Entropy]({% post_url 2026-05-20-ppo-entropy %})
2. **Surrogate Loss（本文）**
3. [KL Divergence]({% post_url 2026-05-18-ppo-kl-divergence %})
4. [Learning Rate]({% post_url 2026-05-17-ppo-learning-rate %})
