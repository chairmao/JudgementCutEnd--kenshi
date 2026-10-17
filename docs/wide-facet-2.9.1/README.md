# 2.9.1：先验收一张源宽面

2.9视频只读审查未达到空间切裂验收。先保存已测试工程与实际游戏mod，再生成独立单宽面验证。

保留归档：E:\KenshiProject\2.Projects\JudgementCutEnd\releases\JudgementCutEnd-2.9.0-tested-retained-JCE-WideProbe291-20261009-235338.zip
归档SHA256：20E4EB34878447388ACF223A25BE5F19BD5F8DD0004DDBB8EF369B7B0EE9B8A7
双备份：D:\CodexBackups\JCE-WideProbe291-20261009-235338; E:\AIWorkSpace\_backups\JCE-WideProbe291-20261009-235338；版本收尾另有同名前缀-VersionLog双备份。

## 参考与适配边界

源网格仍为Skyrim JCE030CutRefraction.nif的screen1/slash3/slash5，几何、UV、索引与原CSV不变。原法线槽与颜色槽均引用fxglowspotlinearalpha.dds，是共享光斑，不将RGB解码成法线。新增DDS逐字复制，仅取Alpha柔化边界。BG3组件31/24的持续、退场包络保持2.9的原始键及归一化映射。

2.9将宽面与长切割面共用尺度，宽面最大跨度约102世界单位；本次宽面相对枢轴最大距离独立适配为0.55半径，比例3.230446，保留原形状/朝向。半径350下范围仍受同一半球/世界深度约束。这个尺寸是Kenshi适配，不是源引擎单位照搬。

宽面使用每张网格的共同枢轴光线和主表面法线决定方向，面内背景一致偏移；24px/1080p是验证用有界映射，继续受旧36px上界约束。不声称完整Skyrim折射方程。正对无方向时零位移；不能恢复被遮挡的景物。源强度只参与宽面的位移，不第二次压低混合Alpha。纹理最多两次采样，共用一份每帧HDR副本；未增加烟雾/刀光/裂面数量、纹理生成或CPU读回。

## 验收配置

JudgementCutEnd.ini的OpticalProbeMode：1=仅宽面（默认）；2=宽面叠加既有特效；0=三面完整演出。重启游戏读取；未出现这个键的旧配置也默认1。

模式1正常情况下看不到原有刀光、范围圈、幻影、烟雾，仍按U执行同一动画/音效/伤害和时间恢复。通过零Alpha/零光能隐藏自有层，保留11段和原有顶点声明/HDR复制时点。两薄面仍提交固定透明拓扑，没有删段。隔离模式不是性能优化，CPU仍生成原几何。

先在围墙、树木或有地面纹理的场景观察：一片范围内轮廓应朝同一方向偏移，面外保持原位；转动视角后位置应保持世界坐标，收刀后恢复原背景。确认后再设2检查是否被刀光/雾盖住。尚未证明实机可见程度。

日志facet_probe_stage每次施放最多三个阶段，记录模式/剪辑秒/宽面源强度/CPU存活/HDR状态，GPU_visible=unmeasured。宽面和其他层零Alpha都不会改伤害、按键、相机、动画、时间恢复或清理逻辑。

## 验证与编译

1087项非编译检查通过：31个保护函数逐字一致、源DDS身份、配置/六个颜色生产者隔离合同、顶点/材质/着色器语义、源几何和BG3键未变、尺寸与地面/半球边界、视角/分辨率/强度/HDR/Alpha模型、编码/BOM/CRLF/中文、其他工程与游戏文件哈希以及归档CRC。模型不是GPU渲染，不能认定效果或帧率合格。

按规则未代编译/未部署。请用户编译JudgementCutEnd.vcxproj，Release|x64（v100）。产物bin/Release/JudgementCutEnd.dll必须含version=2.9.1-dev，配套jce_facets291.hlsl/program、jce.material、jce_source_optical_mask.dds和原jce_facets29.csv一起部署。旧2.9 DLL与新语义不兼容，Stage现有版本保护将拒绝混装。

逐文件报告见本目录file-reports.json；非编译验证记录：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-WideProbe291-20261009-235338\verification.json。
