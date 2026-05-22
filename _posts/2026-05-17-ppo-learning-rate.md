---
layout: post
title: "PPO 调参笔记（四）：Learning Rate"
date: 2026-05-20
categories: [强化学习, 计算机科学]
tags: [PPO, Learning Rate, KL-Adaptive, 强化学习]
author: "Dragonking"
excerpt: "为什么 PPO 的学习率会跑着跑着归零？讲清楚 KL-adaptive LR 的工作机制、各种调度方式的取舍，以及看到 lr 失常时该怎么排查。"
kb: true
kb_cat: rl
series: "PPO 调参笔记"
series_order: 4
---

PPO 的 learning rate 看起来好像不该是什么大问题——选个 3e-4 或 1e-3 似乎就够了。但只要你用了 rsl_rl、legged_gym、IsaacLab 这类基于 KL 自适应的实现，你会发现一件神奇的事：**lr 会自己变**。有时候它跑着跑着就变成 0，整个训练已经停了你还没察觉。

这一篇讲清楚为什么。

## 三种主流 LR 调度

**固定**。从头到尾不变，最简单，CleanRL 默认就是。

**线性退火**。从 $\text{lr}_0$ 线性降到下限（通常 0）。原 PPO 论文 Atari 实验用这个。

```python
lr = lr_init * (1 - progress)
```

**KL-adaptive**。根据上一轮的 KL 动态调 lr。rsl_rl、IsaacLab 默认。这是「lr 自己归零」的元凶，也是这篇主角。

## KL-adaptive LR 的逻辑

rsl_rl 的实现核心是这段：

```python
if kl_mean > desired_kl * 2.0:
    learning_rate = max(1e-5, learning_rate / 1.5)
elif kl_mean < desired_kl / 2.0 and kl_mean > 0.0:
    learning_rate = min(1e-2, learning_rate * 1.5)
```

每次 PPO 更新结束测一个 mean KL，然后：

- KL 比目标大 2 倍 → lr 缩小 1.5 倍（步子迈大了，慢点）
- KL 比目标小一半 → lr 放大 1.5 倍（步子太小，加速）
- 中间区段不动

`desired_kl` 默认 0.01，lr 上下界默认 1e-2 和 1e-5。

直觉很合理：动得快就刹车，动得慢就加速。问题是边界情况。

## 为什么 lr 会跑成 0

回到你训练里 `Loss/learning_rate` 在某一步之后变 0 的情况。基本路径是：

1. 训练前期策略剧烈变化，KL 经常超过目标，lr 被压小
2. lr 越来越小 → 策略变化越来越小 → KL 越来越小
3. 进入「KL 一直小于一半 desired_kl」的区段，按理 lr 应该被放大

但有时候 lr 就是不涨，反而看起来一直贴在 0。两种可能：

**可能一：y 轴量级骗了你**。rsl_rl 的下限是 `max(1e-5, lr / 1.5)`，理论上不会低于 1e-5。但 1e-5 在量级 0.01 的 y 轴上看起来就是 0。把 y 轴换成 log 尺，或者直接 hover 看具体数值。

**可能二：你用的实现不是标准 rsl_rl 的 KL-adaptive**。比如某些 IsaacLab 配置混了线性退火 + KL-adaptive，或者用 `decay_factor` 把 lr 推到比 1e-5 更小，或者总步数算错把 progress 推到 1.0 之后就停在 0。

排查方法很简单，别看图，直接打印实际数值：

```python
print(self.optimizer.param_groups[0]['lr'])
```

## desired_kl 设多大

rsl_rl 默认 0.01，多数 locomotion 任务能用。但有几种情况要调：

- **早期训练 reward 全 0、策略瞎动**：把 desired_kl 放大到 0.02 ~ 0.05，让 lr 不至于早早被压死
- **任务复杂、奖励信号细腻**：用 0.005 ～ 0.01，保步长稳
- **稀疏奖励**：不建议 KL-adaptive，改用固定 lr + larger eps，避免 lr 被错误 KL 信号带歪

## 完全关掉 KL-adaptive 行不行

可以。改成固定或线性：

```python
# rsl_rl: cfg.algorithm.schedule = "fixed"
# 或自己实现：
for g in optimizer.param_groups:
    g['lr'] = lr_init                       # 固定
    # 或
    g['lr'] = lr_init * (1 - progress)      # 线性
```

什么时候关：

- 调试期，KL-adaptive 会和别的超参互相干扰，关掉后可控性高
- 已知 desired_kl 不合适，与其调它不如直接固定
- 单卡跑、batch 比较小，KL 估计方差大，自适应反而抖

什么时候保留：

- 多卡训练，KL 估计方差小，自适应很可靠
- 大规模 locomotion / manipulation，超参懒得调
- rsl_rl / IsaacLab 默认配置已经验证过的任务

## 一份诊断流程

看到 lr 行为异常，按这个顺序排查：

1. 打印实际 lr 值（不要光看图）
2. 同时打印 KL 值，对照 desired_kl
3. 如果 KL 一直很小但 lr 不涨：检查 `kl_mean > 0.0` 这个条件是不是因为浮点精度被卡住，或者上限 `1e-2` 已经撞顶
4. 如果 KL 一直很大但 lr 不降：检查 `kl_mean` 用的是哪种近似（`approx_kl_old` 可能为负，导致条件触发不一致）
5. 实在不对就关掉 KL-adaptive，先用固定 lr 跑通流程，再回头查

## 一个小经验

调 PPO 时我有个习惯：**先用固定 lr = 3e-4 跑一轮**，看 entropy、KL、surrogate、reward 各自的形状。形状稳了再切到 KL-adaptive。

这样的好处是先确认任务/网络/reward 本身没问题，再上自适应。如果一开始就 KL-adaptive，看到 lr 突然变化你不知道是它在干活还是别的地方坏了。

---

PPO 这四个旋钮——entropy、surrogate、KL、lr——单看每一个都不够。它们是耦合的：lr 变了 KL 跟着变，KL 变了 lr 跟着变，surrogate 的尖峰会反应在 KL 上，entropy 塌陷又会让 KL 失去意义。盯曲线时永远是四张图并排看。

这个系列到这里。

**PPO 调参笔记系列**

1. [Entropy]({% post_url 2026-05-20-ppo-entropy %})
2. [Surrogate Loss]({% post_url 2026-05-19-ppo-surrogate-loss %})
3. [KL Divergence]({% post_url 2026-05-18-ppo-kl-divergence %})
4. **Learning Rate（本文）**
