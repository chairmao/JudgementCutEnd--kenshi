# 2.2：淡蓝氤氲与连续烟流

源码 **2.2.0-dev**，资源 **2.2-blue-wisps-r1**。修改已完成，**未编译、未安装、未运行新版游戏**；当前游戏的2.1版本未动。

## 改动和依据

视频 E:\QQdata\1009E7~1.MP4（约13.254秒）4.4秒/10秒帧可见淡蓝刀光，但雾薄且零碎。旧灰色顶点、576个半球壳面、小独立烟团和低密度Alpha压制是代码确认的对应路径。

- 背景：96个宽软云片、取消576壳面。施放局部空间的低频连续密度场缓慢流动；方片边缘全透明，范围末18%柔和淡出。
- 烟流：48条真实刀路，每条3个重叠软段（144固定槽），寿命1.65～1.90剪辑秒=约0.55～0.63真实秒，稳定ID独立时钟，全体远到近排序。收刀停发，END严格零Alpha；取消仍由原清理处理。
- 图集：原64格DDS相邻帧插值，半纹素内缩不跨格，恢复低密度细丝。
- 色表：原NIF烟雾确实引用gradshockdisintegrate，原DDS逐字复制。18%源蓝紫渐变与82%冷蓝基色按密度适配；不是完整复制Skyrim渲染公式。
- 严格零Alpha片提前返回透明，避免预出生/结束阶段无意义采样。

## 逐文件范围

| 文件 | 作用和变更 |
|---|---|
| JudgementCutEnd.cpp | 仅雾函数/数量、新SmokeSprite、版本和首次有界日志；四分量UV传时钟或连续帧/半径。 |
| assets/jce.material | 仅Mist改自有程序/噪声/色表；Glow、Glass、Refraction逐字保留。 |
| assets/jce_source.material | 仅SourceDust改自有程序/三纹理；其他刀光/闪光/光屑逐字保留。 |
| assets/jce_atmosphere.hlsl | 自有局部位置VP、底雾/烟流FP、柔边、原图插值。 |
| assets/jce_atmosphere.program | vs_4_0/ps_4_0入口和本机worldviewproj_matrix自动矩阵。 |
| assets/jce_fog_noise.tga | 确定性256²低频双通道周期场，没有逐帧CPU生成。 |
| assets/jce_source_fog_palette.dds | 原DDS逐字复制，源SHA：9c69744602fe4506cd4a1d2d85949f831e8162f7a2d67ffd62f16110cb1b003f。 |
| assets/vfx-2.2.0.json | 来源、时钟、预算与尚未编译/验收标记。 |
| tools/author_blue_fog.py | 可复现作者、基线保护、双备份；不要在已经修改的版本再次运行生成。 |
| tools/verify_blue_fog.py | 本轮只读保护区/跨层/几何/寿命/资源验证，不编译。 |
| docs/task-status.json | 区分待编译2.2源码与仍安装的2.1版本。 |

每个写入文件的完整11字段报告即时保存于：E:\KenshiProject\2.Projects\JudgementCutEnd\docs\JudgementCutEnd-BlueFog-20261008-120105-326056。

## 验证与限制

114项静态/数值检查通过，80784个生命周期样本、64512个相机/半径边界角点检查通过。排除获授权的雾区域/数量/版本/首日志后，整份源码与原版逐字一致；伤害、U覆盖、动作/三倍速、时间恢复、清理、HDR副本与9段索引保持。当前安装、用户编译DLL、正式1.0/2.0归档哈希保持。

保守预算：19828→17620顶点，47598→44286索引；硬上限32768/49152未变。底雾3次/烟流4次纹理采样，**几何减少不代表GPU更快**；透明排序、帧率、HDR观感待实测。噪声周期边界最大相邻差1/255，模型保持B>G>R，不把模型当游戏画面证明。

报告：E:\KenshiProject\2.Projects\JudgementCutEnd\docs\verification-blue-fog-2.2-20261008.json
源码SHA：cc66e596f5db61a56cdcdfd6b8b06d3322ddd234a3d1f063173085dd075644fc

## 编译与后续

编译工程：E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj，**Release|x64 / v100**。Skill及项目规则禁止代理代编译，本轮C++与shader编译器均未调用。

关闭游戏后，通过既有 tools/Stage-LocalMod.ps1 -Mode Install 成套安装新DLL和新雾资源；该脚本验证版本/入口/时间戳/游戏进程并双备份。不修改mods.cfg或存档。**不能只复制雾材质给旧2.1 DLL**，旧UV没有新时钟/半径分量。

验收：同场景近/远镜头按U检查淡蓝烟流、连续雾、角色清晰度、无卡片边缘/灰颗粒与帧率；施放中U覆盖、Esc取消、正常完成、暂停后恢复，确认没有残雾/时间静止。日志应有 [JCE 2.2.0-dev] 和 particle_revision=2.2_blue_wisps dust_paths=48 dust_slots=144。

## 备份与编码

主要代码/材质备份：
- D:\CodexBackups\JudgementCutEnd-BlueFog-20261008-120105-326056
- E:\AIWorkSpace\_backups\JudgementCutEnd-BlueFog-20261008-120105-326056

后续检查点精确路径在逐文件报告。源码UTF-8 BOM/CRLF，其余文本UTF-8无BOM/CRLF；读回/乱码检查通过。正式2.0归档未改。
