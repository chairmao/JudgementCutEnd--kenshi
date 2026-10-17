# 2.5 空间切裂特效改进（2026-10-08）

源码版本2.5.0-dev，资源修订2.5-spatial-partition-r1。当前游戏目录仍为2.4；2.5尚未编译、安装或游戏验证。2.4特别保存包、正式1.0和2.0均保持字节不变。

## 实际参考与实现区别

读取上古卷轴5模组的 `JCE030CutRefraction.nif`，确认8个刀路网格与1个screen网格，各24顶点/12三角形；合计216顶点/108三角形。9个独立折射强度控制器均有原始关键帧，峰值约0.65。精确网格、转换和曲线证据见 [来源记录](spatial-refraction-source-2.5.json)。字段解释依据 [Niftools schema](https://github.com/niftools/nifxml/blob/develop/nif.xml)。峰值是源引擎强度，不是像素偏移单位。

原2.4的折射由192个短促小三角形驱动，背景位移范围与持续时间有限，因此更像细碎高光。新版采用八条现有实际刀路（第0、12、24、36、48、60、72、84条）的平面，把视野中的空间划成相邻区域；裂缝两侧向不同方向采样原背景，区域内部有少量稳定的采样旋转和曝光差，制造空间被切开的感觉。使用原刀路网格宽长比例控制色散带，保留现有冰蓝刀光与2.4流动烟带/烟丝。

这套空间分区是Kenshi渲染适配，不是原NIF的几何拓扑直接执行。九条原始曲线独立导出到 `jce_optics.csv`，运行时把源曲线区间映射到每条刀路出生至收刀后0.45演出秒，随后归零。原Skyrim控制器的实际播放时钟关系、源材质Shader及法线响应没有完整复现，不能声称逐像素相同。

## 运行边界

背景采样总位移最多28屏幕像素（低分辨率缩小）；像素限定在350半径半球内且地面以下裁掉，沿外沿淡出。只复制当前场景HDR纹理，沿用每可见帧一次复制与资源清理，不读回CPU、不创建镜子实体、不改变全局后处理。

本插件11层明确按“折射、刀光、雾气等”顺序进入渲染队列；HDR复制发生在首个实际绘制层之前。中途关闭折射时，透明占位几何保留四分量UV布局，避免BeginUpdate布局变化。现有伤害、U覆盖重施放、动作、自由相机、蓝雾、收刀结算和时间恢复函数逐字节未变。

顶点预算从19668降至19096，索引从47358降至46788，仍低于32768/49152硬限制。新Shader每像素只采一次背景，但增加八个平面等算术；几何下降不能证明整体性能提高，GPU成本仍需实测。

## 编译与验收

请由用户编译 `E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj` 的 **Release | x64**。产物为 `E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll`。依据code-modification-principles的编译边界，代理未调用C++或HLSL编译器。Shader还需游戏实际加载验证。

新DLL必须与完整package配套更新；不要仅复制材质到当前2.4 DLL。现有 `tools/Stage-LocalMod.ps1` 会检查新源码对应的DLL。本轮没有运行部署工具，也没有写入游戏目录。

验收时查看日志 `version=2.5.0-dev`、`optics_revision=2.5_spatial_partition`、`spatial_optics_active` 及原有HDR复制成功记录。检查近距离/俯视/远距离、移动自由相机、裂缝两侧背景是否错位、圆外是否无折射、收刀消退、连续按U覆盖、ESC取消及暂停后时间恢复。若出现Shader编译错误或refraction_disabled，需要收集日志；静态检查不能排除驱动/游戏队列适配问题。

此前2.4日志中的 weapon_changed_or_missing / sheath_damage_skipped 属于原有武器结算路径，本次未修复该独立问题，也不把视觉认可视为伤害功能通过。

## 验证、安全及记录

105项静态/数值检查通过：实际来源曲线、宽长比例、三种相机角度分区、像素上限、图层合同、UV失败分支、受保护函数及所有非授权旧文件的哈希。时间恢复另有模型回归；均不等于C++编译或游戏运行成功。

双份备份：

- `D:\CodexBackups\JudgementCutEnd-SpatialFracture-20261008-143008-651338`
- `E:\AIWorkSpace\_backups\JudgementCutEnd-SpatialFracture-20261008-143008-651338`

局部修正另建唯一后缀备份，未覆盖首次2.4备份。C++保留UTF-8 BOM/CRLF，其余旧文件保留UTF-8/CRLF；新文本UTF-8/CRLF。逐字节读回、中文一致及乱码扫描通过。逐文件11项报告、备份具体路径与检查结果见 [本轮审计目录](JudgementCutEnd-SpatialFracture-20261008-143008-651338/verification.json)。
