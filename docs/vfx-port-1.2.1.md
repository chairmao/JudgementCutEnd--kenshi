# 次元斩绝 1.2.1-dev：原始特效纹理与曲线移植

本轮完成可供编译测试的特效实现。尚未运行 C++ 编译器、HLSL 编译器或游戏；已安装版本仍是 1.2.0-dev。1.0 正式冻结版未改动。

## 本轮实际接入

原始文件来自用户提供的本机目录 E:\skyrimspecialedition\mods\Judgement Cut End - ap05's Remake。没有修改原始 Skyrim 模组。

| 新运行时资源 | 原始资源 | 用途 |
|---|---|---|
| jce_source_blade09.dds | textures/effects/zjc/4905/blade_effect09.dds | 每道斩击的弧形刀光主体 |
| jce_source_blade08.dds | textures/effects/zjc/4905/blade_effect08.dds | 多重弧形拖影纹理 |
| jce_source_dust.dds | textures/effects/zjc/fxsmokepuffanim01dark.dds | 8×8 灰色烟尘动画图集 |
| jce_source_flash.dds | textures/effects/zjc/FXGlowSpotLinear.dds | 斩击与收刀时的柔光 |
| jce_source_spark.dds | textures/effects/zjc/fxspark.dds | 短寿命光屑 |

五张 DDS 均为逐字节复制，哈希与原文件一致。完整来源、原文件实际路径、哈希、曲线关联见 package/JudgementCutEnd/assets/vfx-1.2.1.json。

工具不再任取 NIF 中某个浮点动画，而是沿 NiControllerSequence → shader property controller → interpolator → float data 解析真实关联；拒绝未绑定或歧义关联。对应实现：tools/inspect_skyrim_vfx.py 和 tools/author_skyrim_vfx.py。

| 输出曲线 | 来源 NIF / shader block | float data block | 序列速度 |
|---|---|---:|---:|
| screen_flash | JCE030ScreenFx.nif / 107 | 29 | 1 |
| screen_veil | JCE030ScreenFx.nif / 110 | 37 | 1 |
| finish_glow | JCE040Finish.nif / 108 | 38 | 1 |
| finish_halo | JCE040Finish.nif / 120 | 60 | 1 |
| fracture_alpha | JCE030CutAllActi.nif / 188 | 197 | 1.16 |
| cut_flash | JCE030CutAllActi.nif / 106 | 29 | 1.16 |

六条 Alpha 曲线共 49 个关键帧，保存原时间、值、前后切线和序列速度。NIF 二次插值使用区间归一化 Hermite 切线；不能再乘区间时长。语义核对来源为 [NIFtools schema](https://raw.githubusercontent.com/niftools/nifxml/develop/nif.xml) 与 [NifSkope 插值实现](https://github.com/niftools/nifskope/blob/develop/src/gl/glcontroller.cpp)。

JudgementCutEnd.cpp:218 的 SourceCurve 和 :282 的加载器读取新曲线；出生前和最后关键帧后归零。格式版本、顺序、数量、有限值、时间递增及尾部垃圾都有边界检查，加载失败发生在安装 Hook 前。

## 渲染适配

JudgementCutEnd.cpp:1052–1128 为新增绘制逻辑，:1184–1188 接入第 4–8 段。既有四段保留，原场景副本仍由首段回调捕获；监听器按 FX_SECTIONS=9 识别所有段。

- 96 条现有路径新增主体与拖影两层，并保留原有每道六条延迟线痕；所有顶点经既有 350 水平圆裁剪。
- 灰色半球和原有 168 格雾继续存在，追加 48 片原烟尘图集细节，按视距排序。图集 64 格逐格播放，UV 有半纹素内缩。
- 斩击柔光与结束耀斑分别使用原 Alpha 曲线。
- 空间高光和局部 HDR 背景折射乘原 fracture_alpha 曲线；没有实体镜子或落地镜片。
- 新增最多 128 个短寿命光屑，复用同一 ManualObject 生命周期，无新增永久游戏实体。
- 专用 shader 使用原 DDS RGB/Alpha 与顶点色；HDR 增益在像素阶段实现，防止顶点颜色归一化压低亮度。材质保留深度测试、关闭深度写入。

保守上限为 19,828 顶点 / 47,598 索引，低于既有 32,768 / 49,152 预算。这是几何预算核验，不是运行性能实测。新增段会增加绘制成本；没有帧率或 GPU 时间数据，暂不估算具体开销。

## 保持不变与移植边界

静态逐字对比证明本轮未改变伤害选取/武器倍率/踉跄、U 键覆盖重施放、时间恢复、角色 Pose 与蒙皮发布、Hook 绑定和失败处理。启动日志仅更新版本和特效资源数。上一轮人形轴修正 r1 的 jce.clip / jce_phantom.bin 保留；头部修正尚需凯瑟琳实测。

这不是整个 Skyrim 粒子引擎的移植：

- NIF 原几何、发射器状态机、发射概率和完整运动控制器尚未逐项复现；使用有界固定路径/雾片/光屑适配。
- 图集 20 fps、透明度权重、HDR 增益和图形尺寸是 Kenshi 适配参数，不声称等于原模组全部配置。
- 原 spark palette 尚未完整复现；使用纹理灰度强度和蓝白顶点颜色。
- ScreenFX 曲线用于场景空间柔光，不接管全屏或相机；原 BSLightingShader 由本插件既有局部折射路径适配。
- 离线 preview/index.html 仍是上一轮效果模型，没有验证新增 HLSL 或游戏实际画面。
- 原纹理来源和作者信息记录于资源清单；本轮为用户本机测试资源，未核实对外再分发授权。

## 验证与下一步

docs/verification-source-vfx-1.2.1.json 记录 1,346 项通过：
原有基础 230、光影 43、移植接口 48、时间模型 70、骨架轴 830、新特效 125。新检查包含五张原 DDS 字节、六条曲线真实关联与关键帧、速度、Hermite 数学、截断/NaN/超量/乱序/尾部污染拒绝、材质资源及 shader 接口文本、所有 64 格 UV、预算、无帧内文件 IO/显式堆分配、生命周期、日志上限、编码和中文。C++/HLSL 是否编译通过及最终画面未确认。

用户需编译 JudgementCutEnd.vcxproj：Release|x64，v100。本轮遵循 AGENTS.md 和 code-modification-principles 的不代编译边界。原 1.2.0 DLL 无法运行新增逻辑，安装脚本会拒绝旧 DLL 与 1.2.1 源码混用。编译后须核验 DLL 身份，并整体更新 package/JudgementCutEnd 的 DDS、CSV、HLSL、program、material，以及已修正的动作/幻影资源；仅换 DDS 不够。

实机验收观察：
1. 日志 source_fx_assets_ready curves=6 textures=5，plugin_ready version=1.2.1-dev，vfx_layers_ready layers=9。
2. 96 道路径是否出现弧形主体与多重拖影，灰雾是否保持完整，收刀时是否有柔光与光屑，无遮挡时是否可见。
3. 是否有 shader/material 加载错误、纯矩形、图集串格或零 Alpha 发光。
4. 完成/取消/连续 U 重施放后时间是否恢复，凯瑟琳头部是否仍扭转，伤害与范围是否维持既有行为。

## 备份与逐文件审计

C++ 修改前双备份目录：
D:\CodexBackups\JudgementCutEnd-VFXPort-20261008-003948-386021
E:\AIWorkSpace\_backups\JudgementCutEnd-VFXPort-20261008-003948-386021

其他覆写文件各自有唯一时间戳双备份；新增文件不伪造原文件备份。逐文件 11 字段记录位于 docs/JudgementCutEnd-VFXPort-* 与 docs/JudgementCutEnd-SkyrimVFXAssets-*，汇总见 docs/vfx-port-change-index-1.2.1.json。原 C++ UTF-8 BOM/CRLF 保留，其余文本 UTF-8 无 BOM/CRLF；原 DDS 二进制不转换。写后中文与乱码检查通过。
