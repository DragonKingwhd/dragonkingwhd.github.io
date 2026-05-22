---
layout: post
title: "PPO 调参笔记（三）：KL Divergence"
date: 2026-05-20
categories: [强化学习, 计算机科学]
tags: [PPO, KL Divergence, 策略梯度, 强化学习]
author: "Dragonking"
excerpt: "KL 不在 PPO 的 loss 里，但它是判断「这次更新步子是不是太大」的核心指标，也是 KL-adaptive learning rate 的依据。"
kb: true
kb_cat: rl
series: "PPO 调参笔记"
series_order: 3
---

PPO 的 loss 公式里其实**没有 KL**——clip 已经替代了显式的 KL 约束。但几乎所有 PPO 实现都会**监控** KL，并且很多实现（rsl_rl、IsaacLab）直接用它来动态调节学习率。

KL 在 PPO 里扮演两个角色：步长警报、LR 调度器的输入。

## KL 到底是什么

KL（Kullback-Leibler divergence）量化两个分布之间的「距离」。在 PPO 里我们关心的是旧策略 $\pi_{\theta_\text{old}}$ 和新策略 $\pi_\theta$ 之间的 KL：

$$
\text{KL}(\pi_\text{old} \,\|\, \pi_\theta)
 = \mathbb{E}_{a \sim \pi_\text{old}}\!\left[\log \frac{\pi_\text{old}(a)}{\pi_\theta(a)}\right]
$$

几个性质：
- 不对称——$\text{KL}(P \,\|\, Q) \neq \text{KL}(Q \,\|\, P)$
- 恒非负，两个分布一样时为 0
- 越大表示新旧策略差越远

## 两种近似计算方式

精确 KL 算起来贵（要对动作空间积分），实现里都用近似。常见两种。

**方式一：朴素近似**

$$
\hat k_1 = \log \pi_\text{old}(a) - \log \pi_\theta(a) = -\log r
$$

PPO 原始实现里就是这种写法。问题是：**它的期望确实是 KL，但 sample 级别可以是负数**。如果你在 wandb 看到 `approx_kl` 偶尔显示负值，原因就在这。

**方式二：John Schulman 的更好近似**

$$
\hat k_2 = (r - 1) - \log r
$$

这个 sample 级别**恒非负**，期望也是 KL，方差更小。新一点的实现（CleanRL、SB3 默认）都用这个。

实现起来：

```python
with torch.no_grad():
    log_ratio = logp - logp_old
    ratio = log_ratio.exp()
    approx_kl_old = -log_ratio.mean()
    approx_kl_new = ((ratio - 1) - log_ratio).mean()
```

两种数都打出来对比，方便诊断。

## 健康的 KL 是多大

经验区间（每次 PPO 更新结束后测得的平均 KL）：

| KL 范围 | 含义 |
| --- | --- |
| < 0.001 | 策略几乎没动——可能 lr 太小、advantage 全 0 |
| 0.005 ～ 0.02 | 健康区间，多数任务的甜区 |
| 0.02 ～ 0.05 | 步子稍大但通常没事 |
| > 0.05 | 偏大，注意稳定性 |
| > 0.1 | 显著过大，clip 已经管不住 |
| 0.5+ | 训练正在崩 |

不同框架对 `desired_kl` 有不同默认：rsl_rl 是 0.01，CleanRL 是 0.015，TRPO 经典也是 0.01。

## 如果 KL 太大怎么办

三个层次的应对，从轻到重：

**1. early stopping**。每个 epoch 结束查一次 KL，超过 `target × 1.5` 就停止本轮 PPO 更新。CleanRL、SB3 都有这个开关。

```python
if approx_kl > 1.5 * target_kl:
    break
```

**2. 缩 `eps`**。clip 的 $\epsilon$ 从 0.2 降到 0.1，新旧策略距离强行压小。

**3. 降学习率**。最常用。这就是下一篇要讲的 KL-adaptive LR 的事。

## 在 wandb / TensorBoard 哪里找它

不同框架命名不一样，可惜没有统一标准：

| 框架 | 字段名 | 分组 |
| --- | --- | --- |
| rsl_rl / legged_gym | `mean_kl` | Loss 或 Policy |
| stable-baselines3 | `approx_kl` | train |
| CleanRL | `approx_kl`、`old_approx_kl` | losses |
| IsaacLab | `KL` 或 `mean_kl` | Train 或 Loss |

**很重要的一点**：如果你只看到 Loss 分组里有 entropy / value / surrogate 而**没有 KL**，KL 多半在另一个分组里被你漏掉了。往上下滚一下其他分组，或者搜索框直接输 `kl`。

## KL 和 entropy 不是一回事

这俩特别容易混。都跟「策略形状」相关，但管不同的事：

| | 管什么 | 控制 |
| --- | --- | --- |
| **KL** | 这次更新**跨度多大**（新旧策略距离）| 步长 |
| **Entropy** | 当前策略**多随机**（分布形状）| 探索 |

对照一下：KL = 0 不代表 entropy = 0。如果策略没动，KL 是 0，但 entropy 可以是任何值。反过来 entropy = 0（完全确定性策略）也不代表 KL = 0——你完全可以从一个确定性策略更新到另一个确定性策略，KL 会很大。

## 一个真实场景

之前我训一个机器人 locomotion，曲线长这样：

- entropy 缓慢下降，从 5 跌到 -2，正常
- surrogate 在 0 ～ 0.1 之间晃，正常
- reward 平稳上升
- **但 KL 从第 100 步开始就一直贴着 0.001 以下**

reward 在涨，所以表面看一切正常。但 KL 这么小意味着每次 PPO 更新策略几乎没动——它其实是被 KL-adaptive LR 调度卡住了，lr 早就降到接近 0，后期那点 reward 提升是靠 critic 还在学，policy 实际停滞。

所以**永远把这四张图并排看**：entropy、surrogate、KL、lr。单看任何一张都可能被骗。

---

KL 是 PPO 隐含的步长尺，但它也常常变成 learning rate 的反馈信号——这就是下一篇要讲的 KL-adaptive LR，也是你看到「lr 跑着跑着归零」的根本原因。

**PPO 调参笔记系列**

1. [Entropy]({% post_url 2026-05-20-ppo-entropy %})
2. [Surrogate Loss]({% post_url 2026-05-19-ppo-surrogate-loss %})
3. **KL Divergence（本文）**
4. [Learning Rate]({% post_url 2026-05-17-ppo-learning-rate %})
