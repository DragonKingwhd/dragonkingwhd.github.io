---
layout: post
title: "IsaacLab 地形构建：从高度场到三角网格的完整管线"
date: 2026-05-21
categories: [机器人学, 强化学习]
tags: [IsaacLab, 地形生成, Heightfield, Trimesh, Parkour, 强化学习]
author: "Dragonking"
excerpt: "拆开 IsaacLab 的地形生成：你只在一张二维高度数组上设计地形，剩下的「高度场→三角网格」全是与地形无关的通用管线。结合 Parkour 项目真实代码逐行讲原理。"
kb: true
kb_cat: rl
---

第一次读 IsaacLab 的地形代码，最容易卡住的地方是分不清「哪段是我该写的算法，哪段是引擎要求的样板」。其实只要抓住一个两层结构，整套东西就清楚了：

- **第一步：算高度场**。一张二维数组 `heights[x][y]`，每个格子存一个高度数字。这一步才是你真正在设计地形——台阶、沟壑、斜坡，全在这张表里。
- **第二步：高度场 → 三角网格**。物理引擎不认识二维高度数组，只认识由顶点和三角形拼成的 3D 表面（mesh）。所以需要一段代码把高度数组「翻译」成三角面片。这段翻译跟你设计的是什么地形毫无关系，任何高度场喂进去都能翻。

这篇就沿着这两层，结合 [Parkour 项目](https://arxiv.org/pdf/2309.14341) 里的真实实现，把原理讲透。官方 API 在 [IsaacLab terrains 文档](https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.terrains.html)。

## 一张图看懂整条管线

<div style="margin:1.6rem 0;overflow-x:auto;">
<svg viewBox="0 0 760 300" width="100%" style="max-width:760px;display:block;font-family:var(--font-mono);" role="img" aria-label="地形构建管线：你设计高度场，通用管线翻译成 mesh，引擎使用">
  <text x="120" y="36" text-anchor="middle" fill="var(--text-mute)" font-size="13" font-weight="600">你设计的部分</text>
  <text x="380" y="36" text-anchor="middle" fill="var(--accent)" font-size="13" font-weight="600">通用管线（跟地形无关）</text>
  <text x="640" y="36" text-anchor="middle" fill="var(--text-mute)" font-size="13" font-weight="600">引擎能用的东西</text>
  <rect x="20" y="55" width="200" height="160" rx="6" fill="var(--bg-soft)" stroke="var(--border-strong)" stroke-width="1.5"/>
  <text x="40" y="92" fill="var(--text)" font-size="13">heights[x][y]</text>
  <text x="40" y="116" fill="var(--text-soft)" font-size="12.5">二维高度数组</text>
  <text x="40" y="162" fill="var(--text)" font-size="12.5">extreme_parkour</text>
  <text x="40" y="184" fill="var(--text)" font-size="12.5">_terrians.py</text>
  <line x1="224" y1="135" x2="251" y2="135" stroke="var(--accent)" stroke-width="2" marker-end="url(#tparrow)"/>
  <rect x="255" y="55" width="250" height="160" rx="6" fill="var(--accent-soft)" stroke="var(--accent-border)" stroke-width="1.5"/>
  <rect x="255" y="55" width="4" height="160" fill="var(--accent)"/>
  <text x="275" y="92" fill="var(--text)" font-size="12.5">convert_height_field</text>
  <text x="275" y="112" fill="var(--text)" font-size="12.5">  _to_mesh()</text>
  <text x="275" y="142" fill="var(--accent-hover)" font-size="12.5">@parkour_field_to_mesh</text>
  <text x="275" y="166" fill="var(--text-soft)" font-size="12.5">utils.py</text>
  <text x="275" y="190" fill="var(--text-mute)" font-size="12">（纯几何翻译）</text>
  <line x1="509" y1="135" x2="536" y2="135" stroke="var(--accent)" stroke-width="2" marker-end="url(#tparrow)"/>
  <rect x="540" y="55" width="200" height="160" rx="6" fill="var(--bg-soft)" stroke="var(--border-strong)" stroke-width="1.5"/>
  <text x="560" y="92" fill="var(--text)" font-size="12.5">三角网格 mesh</text>
  <text x="560" y="116" fill="var(--text-soft)" font-size="12.5">（顶点 + 三角形）</text>
  <text x="560" y="162" fill="var(--text)" font-size="12.5">Isaac 渲染 / 碰撞</text>
  <text x="560" y="184" fill="var(--text)" font-size="12.5">trimesh</text>
  <text x="120" y="245" text-anchor="middle" fill="var(--text-soft)" font-size="12" font-style="italic">你写算法的地方</text>
  <text x="380" y="245" text-anchor="middle" fill="var(--text-soft)" font-size="12" font-style="italic">写一次，所有地形复用</text>
  <text x="640" y="245" text-anchor="middle" fill="var(--text-soft)" font-size="12" font-style="italic">物理引擎吃这个</text>
  <defs>
    <marker id="tparrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/>
    </marker>
  </defs>
</svg>
</div>

记住这张图：**左边是你的创作，中间是死板的翻译，右边是引擎的食物**。下面分三步拆。

## IsaacLab 地形框架里的几个角色

在钻进代码前，先认一下官方框架的几个类，免得迷路：

| 类 | 干什么 | 在 Parkour 里对应 |
| --- | --- | --- |
| `TerrainGenerator` | 把多个子地形拼成一个大网格 | `ParkourTerrainGenerator` |
| `TerrainGeneratorCfg` | 网格尺寸、缩放、子地形配比 | `ParkourTerrainGeneratorCfg` |
| `SubTerrainBaseCfg` | 单个地形类型的配置 | `ParkourSubTerrainBaseCfg` |
| `TerrainImporter` | 把生成好的 mesh 塞进仿真器 | `ParkourTerrainImporter` |

还有一个关键区分：IsaacLab 把地形分成两大类。

- **height_field（高度场）**：先在二维高度数组上设计，再转 mesh。灵活，适合台阶、沟壑、起伏地形。
- **trimesh（直接建网格）**：直接拼几何体（盒子、坑、栏杆）。快，但表达力受限。

Parkour 走的是 **height_field 路线**——因为跑酷地形（台阶高低错落、间隙宽窄不一）用高度数组描述最自然。

## 第一步：高度场 —— 你真正设计地形的地方

### 它就是一张二维数组

打开 `extreme_parkour_terrians.py`，每个地形函数开头都长一个样：

```python
width_pixels = int(cfg.size[0] / cfg.horizontal_scale)
length_pixels = int(cfg.size[1] / cfg.horizontal_scale)
height_field_raw = np.zeros((width_pixels, length_pixels))
```

`height_field_raw` 就是那张二维表，`shape = (width_pixels, length_pixels)`。每个格子 `[i][j]` 存一个整数，代表那个位置的高度。**全 0 就是平地，往里写数字就是抬高/下凹。**

设计地形 = 往这张表里写数字。用的全是 numpy 切片，比如把前 `platform_len` 行抬到平台高度：

```python
height_field_raw[0:platform_len, :] = platform_height
```

### 像素和米之间靠两个 scale 换算

这里有个新手必踩的坑：数组的索引是**像素**，不是米。两个缩放系数负责换算（来自 `ParkourSubTerrainBaseCfg`）：

```python
horizontal_scale: float = 0.05   # 水平方向：1 像素 = 0.05 m = 5 cm
vertical_scale:   float = 0.005  # 竖直方向：高度值 1 = 0.005 m = 5 mm
```

所以：
- 想让台阶**水平方向占 1 米**，就要写 `1 / 0.05 = 20` 个像素：`height_field_raw[dis_x : dis_x+20, :]`
- 想让台阶**高 18 cm**，高度值要写 `0.18 / 0.005 = 36`

你举的「后半段全 36」就是这么来的——36 个 `vertical_scale` 单位 = 0.18 m。代码里到处都是 `round(实际米数 / scale)` 这种换算，本质都是「米 → 像素 / 高度单位」。

### 看一个真实地形怎么"画"出来

`parkour_step_terrain`（楼梯地形）是个好例子，去掉边角后核心就这几行：

```python
height_field_raw[0:platform_len, :] = platform_height   # 起点平台
dis_x = platform_len
stair_height = 0
for i in range(num_stones):
    rand_x = np.random.randint(dis_x_min, dis_x_max)    # 这级台阶多深
    if i < num_stones // 2:
        stair_height += step_height                     # 前半段往上爬
    elif i > num_stones // 2:
        stair_height -= step_height                     # 后半段往下走
    height_field_raw[dis_x:dis_x+rand_x, ] = stair_height   # 把这一段抬到当前高度
    dis_x += rand_x
```

逻辑非常朴素：一个游标 `dis_x` 沿着 x 方向往前走，每走一段就把那段的高度设成当前累计的 `stair_height`。前半段一级级加高，后半段一级级降低，就成了一个「先上后下」的楼梯。

**这就是你写算法的地方。** 全程都在操作 `height_field_raw` 这张二维表，没碰任何 3D、顶点、三角形的东西。

### difficulty：一个旋钮控制难度

每个地形函数第一个参数都是 `difficulty`（0~1）。它通过配置里的字符串表达式把难度「翻译」成具体参数：

```python
# extreme_parkour_terrains_cfg.py
step_height: str = '0.1 + 0.35*difficulty'   # 难度 0 → 10cm，难度 1 → 45cm
```

函数里用 `eval` 求值：

```python
step_height = eval(cfg.step_height, {'difficulty': difficulty})
```

`difficulty=0` 时台阶 10 cm，`difficulty=1` 时 45 cm。后面讲 curriculum 时这个旋钮会被自动调度。

## 第二步：高度场 → 三角网格（管线）

高度场设计完了，引擎不认识它。`utils.py` 里的 `convert_height_field_to_mesh` 负责翻译。这段代码我把它拆成三件事看。

### 顶点：每个格子角点造一个

```python
y = np.linspace(0, (num_cols - 1) * horizontal_scale, num_cols)
x = np.linspace(0, (num_rows - 1) * horizontal_scale, num_rows)
yy, xx = np.meshgrid(y, x)

vertices = np.zeros((num_rows * num_cols, 3), dtype=np.float32)
vertices[:, 0] = xx.flatten()                  # 顶点的 x（米）
vertices[:, 1] = yy.flatten()                  # 顶点的 y（米）
vertices[:, 2] = hf.flatten() * vertical_scale # 顶点的 z（米）= 高度值 × scale
```

把二维数组的每个格点变成一个 3D 顶点：x、y 由网格位置决定，z 就是那个格子的高度数字乘上 `vertical_scale`。一张 `200×200` 的高度图就产生 `200×200 = 40000` 个顶点。

### 三角形：每个格子切两片

四个相邻顶点围成一个方格，一个方格切成两个三角形：

```python
for i in range(num_rows - 1):
    ind0 = np.arange(0, num_cols - 1) + i * num_cols   # 左下
    ind1 = ind0 + 1                                    # 右下
    ind2 = ind0 + num_cols                             # 左上
    ind3 = ind2 + 1                                    # 右上
    # 第一个三角形：ind0 → ind3 → ind1
    triangles[start:stop:2, 0] = ind0
    triangles[start:stop:2, 1] = ind3
    triangles[start:stop:2, 2] = ind1
    # 第二个三角形：ind0 → ind2 → ind3
    triangles[start+1:stop:2, 0] = ind0
    triangles[start+1:stop:2, 1] = ind2
    triangles[start+1:stop:2, 2] = ind3
```

<div style="margin:1.6rem 0;overflow-x:auto;">
<svg viewBox="0 0 540 230" width="100%" style="max-width:540px;display:block;font-family:var(--font-mono);" role="img" aria-label="每个方格沿对角线切成两个三角形">
  <polygon points="70,180 70,40 210,40" fill="var(--accent-soft)"/>
  <polygon points="70,180 210,40 210,180" fill="var(--bg-code)"/>
  <rect x="70" y="40" width="140" height="140" fill="none" stroke="var(--text-mute)" stroke-width="1.5"/>
  <line x1="70" y1="180" x2="210" y2="40" stroke="var(--accent)" stroke-width="2"/>
  <circle cx="70" cy="40" r="3.5" fill="var(--text-soft)"/>
  <circle cx="210" cy="40" r="3.5" fill="var(--text-soft)"/>
  <circle cx="70" cy="180" r="3.5" fill="var(--text-soft)"/>
  <circle cx="210" cy="180" r="3.5" fill="var(--text-soft)"/>
  <text x="64" y="32" text-anchor="end" fill="var(--text-soft)" font-size="12.5">ind2</text>
  <text x="216" y="32" text-anchor="start" fill="var(--text-soft)" font-size="12.5">ind3</text>
  <text x="64" y="198" text-anchor="end" fill="var(--text-soft)" font-size="12.5">ind0</text>
  <text x="216" y="198" text-anchor="start" fill="var(--text-soft)" font-size="12.5">ind1</text>
  <text x="108" y="92" text-anchor="middle" fill="var(--accent-hover)" font-size="15" font-weight="600">&#9651;2</text>
  <text x="168" y="138" text-anchor="middle" fill="var(--text-soft)" font-size="15" font-weight="600">&#9651;1</text>
  <text x="270" y="74" fill="var(--text-soft)" font-size="13">每个方格沿对角线 ind0&#8211;ind3 切开：</text>
  <text x="270" y="116" fill="var(--text)" font-size="13">&#9651;1 = (ind0, ind3, ind1)</text>
  <text x="270" y="142" fill="var(--text)" font-size="13">&#9651;2 = (ind0, ind2, ind3)</text>
</svg>
</div>

所以三角形总数 = `2 × (num_rows-1) × (num_cols-1)`。这就是一张完整的 3D 表面网格了。

### slope_threshold：把陡坡掰成垂直墙

这是整段代码里最不直观、但最关键的一步。问题是：如果两个相邻格子高度差很大（比如台阶边缘，0 突然跳到 36），上面那种「直接连顶点」的做法会画出一个**斜坡**，而不是你想要的**垂直台阶面**。

`slope_threshold` 就是用来修这个的。当相邻高度差超过阈值时，把低处的顶点在水平方向**挪到**和高处对齐，让那一段的水平跨度塌缩成 0，于是斜坡变成竖直墙：

```python
slope_threshold *= horizontal_scale / vertical_scale   # 默认 1.5 × (0.05/0.005) = 15
# x 方向：相邻格高度差 > 阈值，就标记顶点要移动
move_x[: num_rows-1, :] += hf[1:num_rows, :] - hf[:num_rows-1, :] > slope_threshold
move_x[1:num_rows, :]   -= hf[:num_rows-1, :] - hf[1:num_rows, :] > slope_threshold
...
xx += (move_x + move_corners * (move_x == 0)) * horizontal_scale
```

直觉版：默认阈值换算后是 15 个高度单位。台阶那个 36 的跳变 `> 15`，触发修正，台阶边缘变成笔直的竖墙；而起伏地形那种每格才差一两个单位的，`< 15`，不修正，保持平滑斜面。**一个阈值同时伺候了「要锐利的台阶」和「要平滑的起伏」两种需求。**

函数最后返回的第三个值 `move_x != 0`，就是标记「哪里有竖直的 x 方向边缘」的掩码（`x_edge_mask`）。Parkour 用它来做奖励设计——比如惩罚机器人脚正好踩在台阶棱上。

## 装饰器 parkour_field_to_mesh：把翻译包成一条龙

你可能注意到每个地形函数头上都挂着 `@parkour_field_to_mesh`。这个装饰器（`utils.py`）才是把「设计」和「翻译」缝起来的胶水。它在你的高度场函数前后各干一摊活：

```python
def parkour_field_to_mesh(func):
    def wrapper(difficulty, cfg, num_goals):
        # 1. 算上边界后的总尺寸，开一张带 border 的大数组
        heights = np.zeros((width_pixels, length_pixels), dtype=np.int16)
        # 2. 调用你写的地形函数，拿到高度场 + 路径点
        z_gen, goals, goal_heights = func(difficulty, cfg, num_goals)
        heights[border_pixels:-border_pixels, border_pixels:-border_pixels] = z_gen
        # 3. 翻译成 mesh（上一节那段）
        vertices, triangles, x_edge_mask = convert_height_field_to_mesh(
            heights, cfg.horizontal_scale, cfg.vertical_scale, cfg.slope_threshold)
        mesh = trimesh.Trimesh(vertices=vertices, faces=triangles)
        # 4. 可选：用二次误差简化网格，减面数
        if cfg.use_simplified:
            mesh = mesh.simplify_quadric_decimation(...)
        # 5. 算出生点（地形中心、最高处）
        origin = np.array([0.5*cfg.size[0], 0.5*cfg.size[1], origin_z])
        return [mesh], origin, goals, goal_heights, x_edge_mask
    return wrapper
```

所以你的地形函数只需要**专心返回三样东西**：高度场 `z_gen`、路径目标点 `goals`、目标高度 `goal_heights`。边界、转 mesh、简化、出生点、边缘掩码这些通用活儿，装饰器全包了。这就是为什么说「翻译跟地形无关」——它对台阶、沟壑、斜坡一视同仁。

## 第三步：子地形拼成大网格

单个子地形（比如一段楼梯）只是一小块。`ParkourTerrainGenerator` 负责把它们拼成一个 `num_rows × num_cols` 的大网格，每个格子塞一种子地形。

拼接靠一个平移矩阵把每块 mesh 挪到自己的格子位置：

```python
def _add_sub_terrain(self, mesh, origin, row, col, sub_terrain_goal):
    transform = np.eye(4)
    transform[0:2, -1] = (row + 0.5) * self.cfg.size[0], (col + 0.5) * self.cfg.size[1]
    mesh.apply_transform(transform)
    self.terrain_meshes.append(mesh)
```

有两种排布模式，差别很重要：

**随机模式（`_generate_random_terrains`）**：每个格子随机抽地形类型 + 随机难度。适合纯随机训练。

**课程模式（`_generate_curriculum_terrains`）**：这是跑酷训练常用的。规则是——**行方向（row）控制难度，列方向（col）控制地形类型**：

```python
difficulty = sub_row / (self.cfg.num_rows - 1)   # 越往后的行越难
difficulty = lower + (upper - lower) * difficulty
```

于是一整列都是同一种地形（比如全是楼梯），但从第一行到最后一行难度递增。机器人学会了简单的，就被「升级」到更难的行。这就是 curriculum learning 在地形上的落地。

## 自己写一个地形：照着改就行

理解了管线，加一个新地形其实很轻。三步：

**1. 写高度场函数**，挂上装饰器，只管填 `height_field_raw` 和 `goals`：

```python
@parkour_field_to_mesh
def my_single_step_terrain(difficulty, cfg, num_goals):
    width_pixels = int(cfg.size[0] / cfg.horizontal_scale)
    length_pixels = int(cfg.size[1] / cfg.horizontal_scale)
    height_field_raw = np.zeros((width_pixels, length_pixels))

    # 起点平台
    platform_len = round(cfg.platform_len / cfg.horizontal_scale)
    height_field_raw[0:platform_len, :] = 0

    # 一个台阶：高度随难度 10cm→45cm
    step_h = round(eval('0.1 + 0.35*difficulty', {'difficulty': difficulty}) / cfg.vertical_scale)
    height_field_raw[platform_len:, :] = step_h          # 后半段全部抬高

    # 路径点：起点 + 台阶上
    mid_y = length_pixels // 2
    goals = np.zeros((num_goals, 2))
    goals[:] = [platform_len + 10, mid_y]
    goals[0] = [platform_len - 1, mid_y]
    goal_heights = np.ones(num_goals) * step_h

    height_field_raw = padding_height_field_raw(height_field_raw, cfg)
    return height_field_raw, goals * cfg.horizontal_scale, goal_heights * cfg.vertical_scale
```

**2. 写配置类**，指向这个函数：

```python
@configclass
class MySingleStepTerrainCfg(ExtremeParkourRoughTerrainCfg):
    function = my_single_step_terrain
```

**3. 把它加进 generator 的 `sub_terrains` 字典**，设个 proportion 就能被采样到。

整个过程你完全不用碰 `convert_height_field_to_mesh` 一行——它对你这个新台阶和原来的楼梯没有任何区别。

## 一句话收尾

> 在 IsaacLab 里设计地形，你的工作永远只在 `heights[x][y]` 这张二维表上。从高度场到三角网格那一段是写一次、所有地形复用的通用管线——它不在乎你画的是台阶、沟壑还是起伏。**分清这两层，地形代码就不再吓人。**

下一步想深挖的话，可以看 `goals` 是怎么被 reward 和 policy 观测使用的，以及 `x_edge_mask` 在跑酷奖励里具体怎么惩罚踩棱——那是把「地形几何」和「策略学习」缝起来的地方。
