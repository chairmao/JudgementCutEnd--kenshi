# 次元斩绝 2.6.0 开发版：参照 BG3 的分层节奏优化

已完成自有特效源码与材质调整。当前游戏安装仍是2.5.0-dev，正式2.5.0归档保持原SHA256。新2.6版本尚未编译或部署，不能把静态验证当作实机效果证明。

## 参考证据与实现判断

参考是 E:\次元斩绝 内的BG3维吉尔mod，其拆包评估见上一任务的 [BG3次元斩绝特效评估](D:/CodexWorkSpace/Sessions/20261002-235652-kenshi-crash-407794f2/Task-JudgementCutEnd-Formal25-BG3-20261009-005520-911010/BG3次元斩绝特效评估.md)。该mod本身也是复刻；尚未取得鬼泣5原始shader或证明能逐像素还原。

从解析的效果组件可确认：准备烟、主体蓝烟、空间切裂和终结退场分层出现；主体蓝烟从约2.58秒延续到7秒，空间切裂有多组不同时间窗。完整数据并不等于所有组件都在生效，原引擎材质算法仍有未解析部分。本轮据此借鉴阶段设计，自主实现局部光影，不复制BG3纹理、网格、音频、动画或3000粒子配置。参考作者资产许可见 [原mod页面](https://www.nexusmods.com/baldursgate3/mods/22096)。已有Skyrim资源来源与声明保持原状。

## 本轮完成的改进

- **蓝雾连续流动**：48条烟带、每条10段和96个烟丝共用施放局部位置与剪辑时钟的双向噪声场。去掉按随机烟形偏移流场的方式，增加卷动与输运；宽而低透明度的烟带连接成烟流。没有增加粒子槽位。
- **生命期颜色变化**：新生烟丝偏亮青蓝，老烟转为低亮深蓝；准备阶段较淡，初斩后形成主体，收刀阶段柔和退场。底雾及共用它的旧尘烟蓝色基底也降低白灰感；旧尘烟图集及翻页算法保留。
- **空间被切开的光影**：八个实际刀路切面各自出生，切口短亮，收刀后每面错开0.018剪辑秒产生分离脉冲，然后完全透明。背景片区有小幅旋转、位移和冷蓝对比，保持连贯切口，没有实体镜子。原始独立强度曲线仍参与调制。
- **终结瞬态层次**：利用已有两张闪光四边形分开表现短亮与外扩余辉；保持原场景范围和退出清理。
- **有界诊断日志**：版本为2.6.0-dev，首次有效空间切裂日志包含 independent_cut_birth_release；每次施放首次绘制资源日志标记 continuous_blue_flow。没有在逐粒子循环加日志。

关键源码位置：[SpatialFracture](E:/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp:1122)、[烟雾生命周期](E:/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp:1319)、[烟带生产](E:/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp:1359)、[烟丝生产](E:/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp:1394)、[闪光](E:/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp:1416)。

程序声明、材质引用和HLSL消费者同步使用2.6标识；新增八个float4切面生命期参数。纹理槽位、四分量UV编码、深度测试与Alpha混合合同保持原样。

## 检查与限制

261项跨层、字节身份和边界检查通过；另有70项既有时间恢复模型检查通过。[完整跨层结果](verify_bg3_design-results.json)、[时间模型结果](verify_time-results.json)。验证器不调用编译器，也不执行C++或GPU。

全部C++在10个明确授权的特效函数和版本标识以外与2.5基线逐字一致。伤害350半径、96次100%武器伤害、U键上升沿覆盖重施放、无冷却、三倍播放、骨骼动画、自由相机、时间恢复及资源清理均未改动。其余原有资产逐字身份与正式2.5清单核对通过；安装目录DLL和资产也与正式归档一致。

历史 tools/verify.py 在“manual render submission and camera/shadow isolation”断言处停止：它仍要求 geometry->_updateRenderQueue( 字符串，而未改动的2.5基线已没有这条调用。该历史检查不是本轮通过项；历史脚本保持不改。本轮验证器对整个授权范围以外源码及渲染资源清理作身份核对，并检查实际程序声明/材质链接。

固定几何上界仍为19096顶点、46788索引，11个材质段、32层底雾、8个切面。折射片元仍只采样一次背景，位移限制28像素。主体烟雾新增一次噪声采样；更宽透明烟带会增加像素覆盖与重叠。因此不能宣称无性能损失，也没有实测帧率、显存或泄漏数据。透明排序、近远距离细节、HDR颜色和实际shader加载仍需游戏验收。

## 编译与验收

用户编译 [JudgementCutEnd.vcxproj](E:/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.vcxproj)，**Release|x64**。本机规则明确禁止代理代编译，故本轮没有运行C++或HLSL编译器。

编译后再将新DLL与本轮完整材质资源一起更新mod。旧DLL不生产 cutLife 参数，不能与新材质混用；本轮没有向游戏安装目录写入文件。部署工具仍会核对源版本与用户产物，避免混装。

游戏验收观察：U启动是否有准备烟；初斩烟流是否连贯、流动而非静止颗粒；相机移动是否仍见连贯切口；收刀时片区是否短促分离后消失；演出结束、连续U覆盖及中途暂停/取消后游戏时间是否恢复；日志有无shader加载或参数缺失错误。保持350圆与96次结算。

## 安全记录

所有8个原文件修改前双备份到：

- `D:\CodexBackups\JudgementCutEnd-BG3Design26-20261009-012311-016714`
- `E:\AIWorkSpace\_backups\JudgementCutEnd-BG3Design26-20261009-012311-016714`

C++保留UTF-8 BOM和CRLF，其他已有文件保持UTF-8无BOM和CRLF；新增文本同样UTF-8无BOM/CRLF。中文写后检查正常。[逐文件变更索引](file-reports.md)列出每个文件的角色、修改点、理由、影响、检查与未决项。验证器路径修正也先双备份，记录在独立报告中。
