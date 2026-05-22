---
layout: post
title: "PPO 调参笔记（一）：Entropy"
date: 2026-05-20
categories: [强化学习, 计算机科学]
tags: [PPO, Entropy, 策略梯度, 强化学习, 探索, 正则化]
author: "Dragonking"
excerpt: "PPO 总损失三块里，能不能学起来常常是 entropy 在背后管事。这篇拆开讲它是什么、为什么要放进 loss、训练曲线该怎么读，以及连续控制里那条最重要的 clamp。"
kb: true
kb_cat: rl
series: "PPO 调参笔记"
series_order: 1
---

PPO 的总损失由三块拼起来——policy loss、value loss、entropy bonus。多数人盯前两块，但真正决定一次训练能不能跳出局部最优、会不会过早把策略压死的，常常是最不起眼的 entropy。

它本质上就是「策略有多犹豫」的度量。这是我反复跑 locomotion 之后才真正搞清楚的事，这一篇把它拆开讲。

> 这篇里会反复出现的几个符号：$\pi$（策略，看到状态告诉你做啥的概率分布）、$s$（状态）、$a$（动作）、$H$（熵）、$\sigma$（连续策略下动作分布的标准差）。

## 它到底量的是什么

想象智能体面前有 4 个按钮，策略告诉你按每个按钮的概率：

| 情形 | A | B | C | D | 直觉 | 熵 |
| --- | --- | --- | --- | --- | --- | --- |
| ① | 25% | 25% | 25% | 25% | 完全没主见 | 最大 |
| ② | 70% | 10% | 10% | 10% | 偏向 A，但还会探索 | 中等 |
| ③ | 100% | 0% | 0% | 0% | 死磕 A | 0 |

公式是：

$$
H[\pi(\cdot\mid s)] = -\sum_{i=1}^{n} p_i \log p_i
$$

$p_i$ 是第 $i$ 个动作的概率，$n$ 是动作总数。前面那个负号是因为 $\log p_i$ 本身是负数（概率小于 1），加负号让熵变成正的。

代入算一下：情形 ① 是 $-4 \times 0.25 \log 0.25 \approx 1.386$，情形 ③ 是 $-1 \times \log 1 = 0$。

分布越平均熵越大，分布越集中熵越小，就这么简单。

## 连续动作下它实际只是 $\sigma$

机器人控制里动作不是按按钮，是「关节角度 = 0.37」这种连续值，策略本身是个正态分布：

$$
\pi(a \mid s) = \mathcal{N}\big(\mu(s),\,\sigma^2\big)
$$

$\mu$ 是最想做的动作，$\sigma$ 是在 $\mu$ 周围抖动多少。它的熵公式：

$$
H = \frac{1}{2}\log(2\pi e) + \log\sigma
$$

要记住一个事实：高斯熵 **完全由 $\sigma$ 决定，跟 $\mu$ 一点关系都没有**。

也就是说，看 entropy 曲线，本质上就是在看「策略标准差有多大」。entropy 下降，意味着 $\sigma$ 在变小，意味着策略越来越果断。

## 它在 PPO loss 里的位置

PPO 的总损失大致这样：

$$
\mathcal{L}_{\text{PPO}}
 = \mathcal{L}^{\text{CLIP}}
 + c_1 \cdot \mathcal{L}^{\text{VF}}
 - c_2 \cdot H[\pi_\theta]
$$

三项分别是策略损失（surrogate loss）、价值损失、熵项。熵项前面是 **减号**——我们想最大化熵保留探索，而整体 loss 要最小化，所以减掉它。$c_2$（代码里通常叫 `ent_coef`）控制探索强度。

为什么非要加这一项？因为 PPO 的 clip 机制只防策略一步迈太大，挡不住它**慢慢把所有概率往一个动作上挤**。几个 epoch 之后策略就会坍缩成「不管什么状态都按 A」，然后再也跳不出来。entropy bonus 就是在背后不停喊「再随机一点」。

## 训练时该长什么样

entropy 应该缓慢下降，既不能不降，也不能断崖式跌。

| 现象 | 解读 | 怎么办 |
| --- | --- | --- |
| 平稳缓降，reward 同步上升 | 健康 | 不动 |
| 一直不降，reward 不涨 | 探索过强 | 降 `ent_coef` |
| 早期断崖下跌 | 过早坍缩 | 提高 `ent_coef`，或减小 lr |
| 突然反弹冲高 | 训练崩了 | 看 KL / value loss 是不是同时炸 |
| 跌成负数 | 连续策略里很常见 | 看下一段 |

关于负熵：连续分布的熵可以是负数（密度可以大于 1），数学上完全正常。例如 12 维动作、$\sigma=0.3$ 时熵就接近 0，$\sigma=0.1$ 时已是较大负数。Locomotion 后期熵跌到 -2 ～ -3 都很常见，不用慌——但要结合 $\sigma$ 量级判断，光看数字没意义。

## ent_coef 怎么定

经验起点：

- 离散控制（Atari、网格世界）：`0.01 ～ 0.05`
- 连续控制（MuJoCo、IsaacLab）：`0.0 ～ 0.01`，很多任务直接设 0
- 稀疏奖励：`0.05 ～ 0.1`，配合退火

连续控制里可以设 0，是因为 $\log\sigma$ 本身是可学参数，会被梯度自己推着往下走，不需要外部推力。

退火方式有三种。**固定**——连续控制默认就这么干。**线性退火**：

```python
ent_coef = max(ent_coef_final, ent_coef_init * (1 - progress))
```

`progress` 是训练进度 0→1。前期多探索，后期多利用。**自适应**——仿照 SAC，设个目标熵 $H^*$，让 coef 自己调：

$$
\alpha \leftarrow \alpha + \eta\,(H^* - \bar H)
$$

熵低于目标就加大系数，高于目标就减小。在 PPO 上不常见，但稀疏奖励里很好用。

## 一定要给 log_std 加 clamp

这是我前后调几个 locomotion 项目之后总结出最重要的一条：

```python
log_std = torch.clamp(log_std, min=-5.0, max=2.0)
```

下限 -5：$\sigma = e^{-5} \approx 0.0067$，再小梯度就消失，策略一旦塌到这里基本救不回来。上限 2：$\sigma = e^{2} \approx 7.4$，再大动作直接发散。

我有过一次训练，entropy 从 5 一路跌到 -12，怎么调 `ent_coef` 都拉不回来，最后追到就是 `log_std` 没 clamp。这种坑提前 clamp 比事后调系数有效得多。

策略参数化也有两种写法：

| 写法 | 实现 | 特点 |
| --- | --- | --- |
| State-independent | `log_std = nn.Parameter(zeros(d))` | 全局可学，**默认首选** |
| State-dependent | $\log\sigma(s)$ 由网络输出 | 表达力强但易崩 |

普通 locomotion / manipulation 用 state-independent 就够了，要让不同状态用不同探索量再考虑 state-dependent，但务必 clamp。

## 几个容易踩的坑

**把熵当 reward 监控**。熵高 ≠ 策略好，它只说「多随机」，不说「多对」。永远要跟 episode return 一起看。

**advantage 没归一化**。PPO 里 advantage 通常做 batch normalization。如果忘了，策略 loss 数值会被熵项压制，看起来像「熵系数太大」，实际是 advantage 量纲不对。

**部署时切到确定性动作时忘了关熵**。sim2real 前常把策略改成直接输出 $\mu$，这时 entropy bonus 完全失效，但代码里仍在算和打印，日志会误导你。

**把 KL 限制和 entropy 限制混为一谈**。KL 管「新旧策略差多远」（步长控制），entropy 管「当前策略多随机」（形状控制）。两件事，不能互相替代。

## 一份最小可用的实现

```python
import torch
import torch.nn as nn

class GaussianActor(nn.Module):
    def __init__(self, obs_dim, act_dim):
        super().__init__()
        self.mu = nn.Sequential(
            nn.Linear(obs_dim, 256), nn.Tanh(),
            nn.Linear(256, 256), nn.Tanh(),
            nn.Linear(256, act_dim),
        )
        self.log_std = nn.Parameter(torch.zeros(act_dim))

    def dist(self, obs):
        mu = self.mu(obs)
        log_std = self.log_std.clamp(-5.0, 2.0)
        return torch.distributions.Normal(mu, log_std.exp())

# 一次更新里的熵计算
dist = actor.dist(obs_batch)
logp = dist.log_prob(act_batch).sum(-1)
entropy = dist.entropy().sum(-1).mean()

ratio = (logp - logp_old).exp()
clip_adv = torch.clamp(ratio, 1 - eps, 1 + eps) * adv
policy_loss = -torch.min(ratio * adv, clip_adv).mean()
value_loss = ((v_pred - v_target) ** 2).mean()

loss = policy_loss + c1 * value_loss - c2 * entropy
```

三个关键点对应正文：`log_std` 全局可学并 clamp、熵在动作维度上求和、熵项前的负号。

---

熵讲完了，但单看熵推不出训练是不是健康——它要和 surrogate loss、KL、learning rate 三个东西配合着看。下一篇写 surrogate loss。

**PPO 调参笔记系列**

1. **Entropy（本文）**
2. [Surrogate Loss]({% post_url 2026-05-19-ppo-surrogate-loss %})
3. [KL Divergence]({% post_url 2026-05-18-ppo-kl-divergence %})
4. [Learning Rate]({% post_url 2026-05-17-ppo-learning-rate %})
