# 2.9.3 独立三片光学裂面

当前源码版本：2.9.3-dev。游戏目录仍为2.9.2，DLL尚未重新编译；这份说明不宣称已部署或游戏验收通过。

## 改动

- 三个实例复用已验收的 Skyrim screen1 网格、UV、原始DDS遮罩与逆转置法线。复用原2.9.2 shader ABI，不增加纹理/线条。
- 各片具有独立位置、等比尺寸、偏航/滚转和斩击路径时钟；初斩逐片出现，中期只平滑偏折一次，收刀按各自时钟分离消退。新世界变换是Kenshi适配，不冒称从BG3导入旋转键。
- BG3的停留/退场透明度曲线继续沿用；三片出生剪辑秒为2.35、2.9057895、3.4615789；退场起点为5.15、5.27、5.39；完全透明时刻为5.90、6.02、6.14。游戏演出仍按既有三倍速度运行。
- 模式3恢复原刀光、蓝雾、幻影和其余视觉层。光学部分仍为72顶点/36三角；每帧背景捕获最多1次、每像素shader最多2次纹理采样、错位上限36像素。
- 三片共用同一份背景快照并远到近透明绘制；重叠不是多次累计折射，透明边缘仍可混合。边界与遮挡沿用原shader。
- 每次施放最多1条激活日志和9条逐片阶段日志；投影包围盒仅是深度/遮罩前上界，GPU可见像素和耗时未测。

## 配置与兼容

OpticalProbeMode：0=旧三面；1=已验收单片；2=单片+完整演出；3=独立三片+完整演出（新默认）；4=仅独立三片。

已有INI显式指定1时仍显示单片。打包INI已设3，后续用户编译后部署时必须同步游戏INI的此键；其余游戏参数应保留。

## 验证与限制

静态/数值检查通过：保护函数32个保持原样（伤害/按键/动画/时间恢复/清理/捕获等）、旧单片实现仅改方法名、挂钩绑定不变、三片几何在生命周期内位于半径内且不穿地、角度/位置独立、生命周期有限；游戏和既有DLL哈希未改。

源码保留UTF-8 BOM/CRLF；打包INI保留UTF-8无BOM/CRLF；新增文本UTF-8/CRLF。双备份目录：

- D:\CodexBackups\JCE-IndependentFacets293-20261010-005846
- E:\AIWorkSpace\_backups\JCE-IndependentFacets293-20261010-005846

编译未执行（项目规则）。由用户编译 E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj，Release|x64，v100；输出 E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll。

实际视觉效果、三片重叠辨识度、实机GPU耗时待测试；旧日志中武器变更导致伤害撤销的问题不在本次视觉修改范围。建议同场景对照模式1与3，近/远/侧视各施放一次并确认结束后世界时间正常恢复。

静态检查记录：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-IndependentFacets293-20261010-005846\verification.json
逐文件报告：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-IndependentFacets293-20261010-005846\file-reports.json
