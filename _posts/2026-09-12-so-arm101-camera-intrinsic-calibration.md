---
layout: post
title: "从像素到射线：SO-ARM101 场景相机内参标定实战"
date: 2026-09-12 20:00:00 +0800
categories: [机器人视觉, ROS 2]
tags: [相机标定, ChArUco, OpenCV, ROS2, SO-ARM101]
author: "Dragonking"
excerpt: "一次完整的 SO-ARM101 场景相机内参标定记录：从针孔模型、畸变参数和 ChArUco 原理，到 ROS 2 采样、误差判断、YAML 接入与真实踩坑。最终在 640×480 下取得 0.3196 px 重投影误差。"
permalink: /blog/camera-intrinsic-calibration/
---

<div class="cal-hero">
  <div class="cal-hero-copy">
    <span class="cal-kicker">SO-ARM101 · VISION NOTE 01</span>
    <h2>先让相机知道<br><em>自己怎么看世界</em></h2>
    <p>固定相机能看见桌面，不代表机器人理解了这幅图像。内参标定要做的，就是建立三维相机坐标与二维像素之间可靠的数学映射。</p>
    <div class="cal-flow" aria-label="标定流程">
      <span>ChArUco</span><b>→</b><span>2D–3D 对应</span><b>→</b><span>K + D</span>
    </div>
  </div>
  <div class="cal-lens" aria-hidden="true">
    <div class="cal-lens-ring"><div class="cal-lens-core"></div></div>
    <span class="ray ray-a"></span><span class="ray ray-b"></span><span class="ray ray-c"></span>
    <div class="sensor"><i></i><i></i><i></i><i></i><i></i><i></i></div>
  </div>
</div>

<div class="cal-result-strip">
  <div><small>IMAGE</small><strong>640 × 480</strong></div>
  <div><small>REPROJECTION</small><strong>0.3196 px</strong></div>
  <div><small>FOCAL LENGTH</small><strong>527.85 / 528.71 px</strong></div>
  <div><small>BOARD</small><strong>8 × 6 ChArUco</strong></div>
</div>

## 这次到底在标定什么？

我的目标是标定固定在 SO-ARM101 主从臂之间的 `front` 场景相机。它负责俯视或斜视工作台，之后还会参与方块定位与机械臂抓取。

内参描述的是**相机自身的成像规律**，主要包括：

- 焦距 $f_x,f_y$：把归一化相机坐标缩放到像素坐标；
- 主点 $c_x,c_y$：光轴与成像平面的交点；
- 畸变参数 $D$：修正镜头造成的径向与切向弯曲。

这里最容易混淆的是内参与外参：

<div class="cal-compare">
  <div><span class="cal-num">01</span><h3>内参 Intrinsics</h3><p>回答“这台相机如何把光线变成像素”。只要相机、镜头焦距和分辨率不变，相机在桌面上移动后仍可继续使用。</p></div>
  <div><span class="cal-num">02</span><h3>外参 Extrinsics</h3><p>回答“相机坐标系位于机器人基座的哪里”。移动相机后通常需要重新求解，也是完成抓取前的下一步。</p></div>
</div>

> **一句话区分：**内参属于相机，外参属于相机与另一个坐标系之间的关系。本次只完成前者，并不意味着像素已经能直接转换成机械臂基座坐标。

---

## 从针孔模型理解 $K$

忽略畸变时，空间点 $P_c=(X_c,Y_c,Z_c)$ 在相机坐标系中先被透视除法投到归一化平面：

$$
x=\frac{X_c}{Z_c},\qquad y=\frac{Y_c}{Z_c}
$$

再通过内参矩阵映射到像素 $(u,v)$：

$$
\begin{bmatrix}u\\v\\1\end{bmatrix}
=
\underbrace{\begin{bmatrix}
f_x & 0 & c_x\\
0 & f_y & c_y\\
0 & 0 & 1
\end{bmatrix}}_{K}
\begin{bmatrix}x\\y\\1\end{bmatrix}
$$

也就是：

$$
u=f_x\frac{X_c}{Z_c}+c_x,\qquad
v=f_y\frac{Y_c}{Z_c}+c_y
$$

<div class="cal-note">
  <strong>为什么焦距单位是 px？</strong>
  <p>物理焦距本来以毫米计，但成像计算还受到像元尺寸影响。标定把二者合并为像素尺度，所以 YAML 中的 <code>fx</code>、<code>fy</code> 是像素单位，而不是镜头上写的毫米数。</p>
</div>

### 镜头畸变：直线为什么会弯

这次使用 ROS 常见的 `plumb_bob` 模型，也就是 OpenCV 的五参数畸变模型：

$$
D=[k_1,k_2,p_1,p_2,k_3]
$$

其中 $k_1,k_2,k_3$ 描述径向畸变，$p_1,p_2$ 描述镜头与传感器不完全平行等因素造成的切向畸变。令 $r^2=x^2+y^2$，典型修正形式为：

$$
x_d=x(1+k_1r^2+k_2r^4+k_3r^6)+2p_1xy+p_2(r^2+2x^2)
$$

$$
y_d=y(1+k_1r^2+k_2r^4+k_3r^6)+p_1(r^2+2y^2)+2p_2xy
$$

畸变在画面边缘更明显。因此，**只把标定板放在中央拍很多张，并不能得到高质量标定**；边缘与四角的观测反而很关键。

---

## 为什么选择 ChArUco，而不是普通棋盘格？

ChArUco 把 ArUco 编码标记嵌入棋盘格：ArUco 提供身份识别，棋盘交点提供亚像素级角点定位。它兼顾了两类标定板的优点：

- 每个角点拥有稳定 ID，局部可见时仍能建立对应关系；
- 标定板倾斜或部分出画时，通常仍可检测；
- 棋盘交点适合精确定位；
- 更容易把有效角点送到图像边缘，约束畸变参数。

本次标定板参数如下：

| 参数 | 实际配置 |
| --- | --- |
| 棋盘格数量 | 8 × 6 squares |
| 可用内角点 | $(8-1)\times(6-1)=35$ |
| 方格边长 | 25 mm |
| ArUco 标记边长 | 18 mm |
| 字典 | `DICT_5X5_250` |
| 输出规格 | A4，300 DPI |

<figure class="cal-figure cal-board">
  <div class="cal-board-frame">
    <img src="{{ '/assets/img/camera-intrinsic-calibration/charuco-board-a4.png' | relative_url }}" alt="本次内参标定使用的 8×6 ChArUco 标定板">
  </div>
  <figcaption>本次实际生成的 ChArUco 板。打印必须选择“实际大小 / 100%”，并用尺子复核单格为 25 mm。</figcaption>
</figure>

标定板尺寸一旦写错，焦距的像素值未必明显异常，但平移尺度与后续位姿估计会出问题。纸张还应贴在平整、刚性的背板上；卷曲的纸并不是理想平面，会把系统误差带入结果。

---

## 我的 ROS 2 标定流程

### 1. 先辨认真实设备

本机实际环境是 **ROS 2 Humble**。场景相机与腕部相机不能凭 `/dev/video0`、`/dev/video2` 的编号猜测，因为 USB 重新插拔后编号可能改变。

```bash
cd ~/Desktop/soarm101
source env.sh
python detect_devices.py
python preview.py
```

在浏览器打开 `http://localhost:8000`，确认 `front` 对应场景相机后停止预览。当前场景相机稳定路径是：

```text
/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9.3.3:1.0-video-index0
```

### 2. 启动相机节点并检查话题

```bash
cd ~/Desktop/so101-ros-physical-ai
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch so101_bringup follower_vision.launch.py
```

另开终端检查：

```bash
ros2 topic list | grep static_camera
ros2 topic hz /static_camera/image_raw
```

本机的正确图像话题是 `/static_camera/image_raw`，约 30 Hz。不要误用 `/static_camera/cam_overhead/image_raw`。

### 3. 打开 Web 标定器

```bash
cd ~/Desktop/so101-ros-physical-ai
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run so101_camera_calibration camera_intrinsic_calibration_node \
  --ros-args -p image_topic:=/static_camera/image_raw
```

浏览器打开 `http://localhost:8080`。标定器会显示实时画面、角点数量、运动量，以及 `X / Y / Size / Skew` 四个覆盖指标：

| 指标 | 应该怎样改变标定板 |
| --- | --- |
| X / Y | 移到中心、四边与四角 |
| Size | 靠近和远离相机，改变画面占比 |
| Skew | 绕不同方向倾斜，不要永远正对镜头 |

代码要求单张至少检测 12 个 ChArUco 角点、至少采集 10 张后才允许计算；实践中我建议准备 **15～25 张清晰且差异明显的样本**。数量不是最终目标，几何覆盖才是。

<div class="cal-do-dont">
  <div class="do"><h3>✓ 应该这样采</h3><ul><li>保持相机固定，只移动标定板</li><li>覆盖中心、四角、远近和倾角</li><li>等待画面稳定后再 Capture</li><li>尽量让每帧达到 35/35 角点</li></ul></div>
  <div class="dont"><h3>× 不要这样采</h3><ul><li>连续采一堆几乎相同的姿态</li><li>全程只在桌面平移</li><li>用运动模糊或反光严重的帧</li><li>中途误点 Reset captures</li></ul></div>
</div>

`pose too similar` 不是故障，而是程序根据四维特征的 L1 距离拒绝重复姿态；`hold still` 则说明角点帧间运动超过阈值。这个机制比单纯计数更有价值。

### 4. OpenCV 兼容处理

部分 OpenCV 版本没有 `cv2.aruco.calibrateCameraCharuco`。本项目将 ChArUco ID 对应的平面三维点与图像二维角点整理后，改用通用接口：

```python
err, K, D, rvecs, tvecs = cv2.calibrateCamera(
    objectPoints=object_points,
    imagePoints=image_points,
    imageSize=image_size,
    cameraMatrix=None,
    distCoeffs=None,
    flags=0,
)
```

数学问题没有改变：仍然是利用多组已知平面点的 2D–3D 对应关系，联合估计每一帧的板位姿、相机内参与畸变参数。节点还会统计每视图误差，并尝试剔除显著高于中位数的离群帧。

---

## 最终标定结果

这台场景相机在 **640 × 480** 分辨率下得到：

$$
K=\begin{bmatrix}
527.8478 & 0 & 339.4325\\
0 & 528.7060 & 236.4990\\
0 & 0 & 1
\end{bmatrix}
$$

$$
D=[-0.10802,\ 0.21297,\ 0.00568,\ 0.00123,\ -0.23693]
$$

<div class="cal-metrics">
  <div><span>重投影误差</span><strong>0.3196<small> px</small></strong><p>低于 0.5 px，表现良好</p></div>
  <div><span>主点偏移</span><strong>+19.43<small> px (x)</small></strong><p>相对图像几何中心</p></div>
  <div><span>估算视场角</span><strong>62.5°<small> H</small></strong><p>垂直方向约 48.8°</p></div>
</div>

视场角由 $2\arctan(\text{image size}/2f)$ 粗略计算，主要用于直观理解，并不能替代畸变修正后的精确几何计算。

### 重投影误差究竟表示什么？

标定完成后，把标定板三维角点通过估计出的位姿、$K$ 和 $D$ 重新投影到图像，再与实际检测角点比较：

$$
e_{\mathrm{RMS}}=\sqrt{\frac{1}{N}\sum_{i=1}^{N}\lVert p_i-\hat p_i\rVert^2}
$$

0.3196 px 表示角点预测与观测之间的均方根距离约为三分之一像素，是一个不错的结果。但不能只盯着单个 RMS 数字：如果样本全在中心，整体误差也可能很低，边缘去畸变却依旧不准。可靠结论应同时满足：

1. 重投影误差合理；
2. 每视图误差没有明显异常；
3. 图像区域、尺度和倾角覆盖充分；
4. 去畸变后的直线在边缘也保持笔直。

---

## 将结果接入 ROS

保存按钮虽然写着 `Save to /tmp/camera_cal.npz`，节点实际会同时生成：

```text
/tmp/camera_cal.npz
/tmp/camera_cal.yaml
```

本机最终使用：

```text
~/.ros/camera_info/cam_overhead.yaml
```

YAML 中除了原始相机矩阵 `K`，还包含畸变 `D`、单位阵校正矩阵 `R`，以及通过 `cv2.getOptimalNewCameraMatrix` 得到的投影矩阵 `P`。因此 `P` 中焦距与 `K` 略有差异是正常的，不要手动强行改成相同。

启动相机后验证：

```bash
ros2 topic echo --once /static_camera/camera_info
```

应该能看到：

```yaml
distortion_model: plumb_bob
k: [527.8478, 0.0, 339.4325, 0.0, 528.7060, 236.4990, 0.0, 0.0, 1.0]
d: [-0.10802, 0.21297, 0.00568, 0.00123, -0.23693]
```

如果 `k` 全是 0，说明相机节点并未加载标定文件，此时不要继续做外参标定。

---

## 这次最值得记住的坑

### ROS 工作区存在，不代表包已经可见

遇到 `ros2` 找不到 `so101_bringup`，要先构建并 source：

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

本机是 Humble，不要混用仓库文档里的 Jazzy 环境。

### 第一次提示 calibration file 不存在是正常的

启动 `usb_cam` 时出现 `cam_overhead.yaml not found`，恰恰可能是因为这是首次标定。只要图像话题正常发布，就可以继续；标定完成后再安装 YAML。

### 分辨率变化后需要重新标定或正确缩放

内参以像素为单位。切换到不同分辨率、改变裁剪方式、数码变焦或镜头焦距后，不能无条件复用原参数。若只是严格等比例缩放完整图像，可以同比例缩放 $f_x,f_y,c_x,c_y$；实际相机驱动可能使用裁剪或不同传感器模式，最稳妥的方法仍是按目标工作分辨率重新标定。

### 标定成功不等于机器人已经会抓

目前只得到：

```text
三维相机坐标 → 二维像素
```

接下来还要建立：

```text
场景相机坐标系 → 桌面坐标系 → 从臂基座坐标系
```

也就是外参 / 手眼标定。等内外参都可靠后，目标检测给出的像素位置才有机会稳定变成机械臂可执行的抓取位置。

---

## 一份可复用的检查清单

<div class="cal-checklist">
  <label><input type="checkbox"> 相机、焦距、分辨率与最终运行配置一致</label>
  <label><input type="checkbox"> 标定板以 100% 比例打印，尺寸经直尺复核</label>
  <label><input type="checkbox"> 图像中心、四边、四角都有有效样本</label>
  <label><input type="checkbox"> 包含远近尺度变化与多个倾斜方向</label>
  <label><input type="checkbox"> 剔除模糊、反光、遮挡和异常误差帧</label>
  <label><input type="checkbox"> 检查 RMS 与每视图误差，而非只看样本数</label>
  <label><input type="checkbox"> YAML 已被 ROS 相机节点正确加载</label>
  <label><input type="checkbox"> 用边缘直线检查去畸变效果</label>
</div>

## 参考资料

- [OpenCV：Camera Calibration and 3D Reconstruction](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)
- [OpenCV：Calibration with ChArUco Boards](https://docs.opencv.org/4.x/da/d13/tutorial_aruco_calibration.html)
- [ROS 2 `sensor_msgs/CameraInfo` 消息定义](https://docs.ros.org/en/rolling/p/sensor_msgs/msg/CameraInfo.html)
- [Zhang, 2000：A Flexible New Technique for Camera Calibration](https://doi.org/10.1109/34.888718)

<style>
.cal-hero{position:relative;display:grid;grid-template-columns:minmax(0,1.4fr) minmax(220px,.6fr);min-height:350px;margin:0 0 1.1rem;padding:3rem;border:1px solid #24354a;border-radius:18px;overflow:hidden;color:#f5f7fb;background:radial-gradient(circle at 82% 48%,rgba(46,211,183,.16),transparent 25%),linear-gradient(135deg,#101b2a 0%,#14293a 55%,#0d1724 100%);box-shadow:0 20px 55px rgba(15,23,42,.17)}
.cal-hero:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:32px 32px;mask-image:linear-gradient(90deg,#000,transparent)}
.cal-hero-copy{position:relative;z-index:2;align-self:center}.cal-kicker{font:500 .7rem/1.2 var(--font-mono);letter-spacing:.18em;color:#6ee7d2}.cal-hero h2{margin:.8rem 0 1rem;border:0;padding:0;color:#fff;font:600 clamp(2rem,4.5vw,3.5rem)/1.08 var(--font-sans)}.cal-hero h2 em{font-family:var(--font-serif);font-weight:400;color:#8ee9da}.cal-hero p{max-width:580px;margin:0;color:#b7c7d6;font:400 1rem/1.75 var(--font-sans)}.cal-flow{display:flex;align-items:center;gap:.65rem;margin-top:1.5rem;font:.69rem var(--font-mono);color:#d8e3ec}.cal-flow span{padding:.38rem .6rem;border:1px solid rgba(142,233,218,.28);border-radius:5px;background:rgba(255,255,255,.04)}.cal-flow b{color:#57d9c2}
.cal-lens{position:relative;display:flex;align-items:center;justify-content:center;min-height:230px}.cal-lens-ring{position:relative;width:152px;height:152px;border:1px solid #567188;border-radius:50%;background:radial-gradient(circle,#07101d 0 25%,#1f5667 26%,#101a29 50%,#263c4b 51%,#0b1421 68%);box-shadow:0 0 0 15px rgba(76,109,127,.12),0 0 40px rgba(69,224,198,.12)}.cal-lens-ring:after,.cal-lens-ring:before{content:"";position:absolute;inset:13px;border:1px dashed rgba(144,220,211,.28);border-radius:50%}.cal-lens-ring:before{inset:38px}.cal-lens-core{position:absolute;inset:55px;border-radius:50%;background:#63dfcb;box-shadow:0 0 28px #47bda9}.sensor{position:absolute;right:-6px;display:grid;grid-template-columns:repeat(2,6px);gap:5px;padding:7px;border:1px solid #6b8797}.sensor i{width:6px;height:6px;background:#65dec9}.ray{position:absolute;right:16px;width:100px;height:1px;background:linear-gradient(90deg,transparent,#62dfca);transform-origin:right}.ray-a{transform:rotate(28deg)}.ray-b{transform:rotate(0)}.ray-c{transform:rotate(-28deg)}
.cal-result-strip{display:grid;grid-template-columns:repeat(4,1fr);margin-bottom:2.5rem;border:1px solid var(--border);border-radius:10px;background:var(--bg-soft);overflow:hidden}.cal-result-strip div{padding:.9rem 1rem;border-right:1px solid var(--border)}.cal-result-strip div:last-child{border:0}.cal-result-strip small{display:block;margin-bottom:.3rem;color:var(--text-mute);font:500 .62rem var(--font-mono);letter-spacing:.12em}.cal-result-strip strong{font:600 .85rem var(--font-mono);color:var(--text)}
.cal-compare{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1.5rem 0}.cal-compare>div{position:relative;padding:1.4rem;border:1px solid var(--border);border-radius:10px;background:var(--bg-soft)}.cal-compare h3{margin:.2rem 0 .55rem!important}.cal-compare p{margin:0;color:var(--text-soft);font-size:.92rem}.cal-num{color:var(--accent);font:500 .7rem var(--font-mono);letter-spacing:.12em}
.cal-note{margin:1.5rem 0;padding:1.1rem 1.25rem;border-left:3px solid #0ea5a0;border-radius:0 8px 8px 0;background:rgba(14,165,160,.08)}.cal-note strong{font-family:var(--font-sans);color:#0f8f89}.cal-note p{margin:.35rem 0 0}
.cal-figure{margin:2rem 0;text-align:center}.cal-board-frame{padding:1.4rem;border:1px solid var(--border);border-radius:12px;background:#eef1f3}.cal-board img{display:block;max-width:min(100%,610px);max-height:520px;margin:auto;object-fit:contain;box-shadow:0 12px 32px rgba(15,23,42,.13)}.cal-figure figcaption{margin-top:.75rem;color:var(--text-mute);font:400 .78rem/1.6 var(--font-sans)}
.cal-do-dont{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1.5rem 0}.cal-do-dont>div{padding:1.1rem 1.3rem;border-radius:9px}.cal-do-dont h3{margin:0 0 .65rem!important;font-size:1rem}.cal-do-dont ul{margin:0;padding-left:1.2rem;font-size:.9rem}.cal-do-dont .do{border:1px solid rgba(16,185,129,.26);background:rgba(16,185,129,.07)}.cal-do-dont .do h3{color:#0f9b70}.cal-do-dont .dont{border:1px solid rgba(239,68,68,.2);background:rgba(239,68,68,.055)}.cal-do-dont .dont h3{color:#d14b4b}
.cal-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin:1.5rem 0}.cal-metrics>div{padding:1.15rem;border:1px solid var(--border);border-radius:9px;background:var(--bg-soft)}.cal-metrics span{display:block;color:var(--text-mute);font:.72rem var(--font-sans)}.cal-metrics strong{display:block;margin:.4rem 0;color:var(--accent);font:600 1.55rem var(--font-mono)}.cal-metrics strong small{font-size:.65rem}.cal-metrics p{margin:0;color:var(--text-soft);font:.75rem var(--font-sans)}
.cal-checklist{display:grid;grid-template-columns:1fr 1fr;gap:.65rem 1.1rem;margin:1.5rem 0;padding:1.3rem;border:1px solid var(--border);border-radius:10px;background:var(--bg-soft)}.cal-checklist label{display:flex;gap:.55rem;align-items:flex-start;color:var(--text-soft);font:400 .87rem/1.5 var(--font-sans)}.cal-checklist input{margin-top:.22rem;accent-color:var(--accent)}
@media(max-width:720px){.cal-hero{grid-template-columns:1fr;padding:2rem 1.4rem}.cal-lens{display:none}.cal-result-strip{grid-template-columns:1fr 1fr}.cal-result-strip div:nth-child(2){border-right:0}.cal-result-strip div:nth-child(-n+2){border-bottom:1px solid var(--border)}.cal-compare,.cal-do-dont,.cal-metrics,.cal-checklist{grid-template-columns:1fr}.cal-hero h2{font-size:2.1rem}.cal-flow{gap:.35rem;flex-wrap:wrap}.cal-flow span{font-size:.62rem}}
</style>
