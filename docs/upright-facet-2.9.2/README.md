# 2.9.2：立向单裂面验证

用户27E8D6视频只显示小块错位，2.9.1的CPU启动/强度日志不代表GPU可见面积。本次继续单片验证，不增加烟雾、刀光强度、线条或裂面数量。

## 实现与参考边界

Skyrim JCE030CutRefraction.nif的screen1源24顶点/12三角形、原UV/源DDS仍保留；CSV、两张薄面和BG3组件31/24包络未改。源主平面正交基在启动时求出，按几何中心而非偏置pivot映射，适配为角色朝向上的立向裂面。目标宽1.36R、高0.66R、中心高0.40R；半径350时尺寸476×231、厚度约2.057。这个朝向、长宽适配和Alpha映射是Kenshi移植决定，不能称为源模组原样表现。

非均匀缩放后法线使用逆转置，与顶点朝向一起适配，前后面门控仍防止封闭薄网格两面叠加。裂面保持施放时世界朝向，不跟随镜头。源遮罩Alpha经smoothstep(.025,.22)保留柔边，宽面持续阶段包络经smoothstep(.02,.70)避免整片半透明重影冲淡偏折。仍保留原出生/收刀/退场时钟；零强度/零Alpha/HDR失败均透明。近似正对且折射方向为零时位移为零。

最长36px的有界偏移、两次纹理采样、每帧一次HDR副本、世界深度检测、11段绘制合同保持。未修改伤害/输入/动画/时间恢复、相机和既有挂钩；默认OpticalProbeMode仍为1，其他自有视觉层保持隐藏。0/2模式合同不变。

## 投影诊断与限制

facet_probe_stage每次施放最多三条，补充projected_vertices、bbox_px、bbox_viewport_fraction和plane_view_abs_dot。读取当前相机矩阵和特效节点坐标；日志明确projection=pre_depth_pre_mask_bbox以及GPU_visible=unmeasured。包围盒是遮挡和透明裁剪前的几何上界，不是实际可见面积，也不是GPU计时；相机附近跨越近裁剪面时仅投影正w顶点，因此更不能当准确覆盖数。

立向单片在近垂直俯视或沿边侧看时仍会变窄，这是固定世界裂面的角度限制，当前不擅自改成镜头幕布或扩成多片。未来若单片验收成立，再按独立方向扩展。预期改进未在游戏证明。

## 检查与安装

1455项非编译检查通过：31个保护函数原样、源CSV/DDS和BG3键未变、正交基/逆转置/三角形方向、1/10/100/350/1000半径及退场位移、遮罩和包络边界、多个俯角/侧向/距离投影模型、顶点shader材质合同、原配置默认、有界日志、版本/资源哈希、UTF8 BOM/CRLF/中文、游戏目录文件哈希不变。新增只读相机接口的导入名存在于工程链接的OGRE库；不代表本轮已执行这些接口。

未调用编译器或更新游戏目录。请编译E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj，Release|x64（v100）。产物仍为E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll，需含version=2.9.2-dev；部署时与jce_facets292.hlsl/program、jce.material配套。旧291资源保留，2.9.1 DLL不得混装新材质。现有Stage脚本的版本/时间戳检查将拒绝旧DLL。

实测先使用默认模式1，在地面石块/墙体前观察片内背景是否连贯偏移，片外原位；转动镜头确认固定世界位置，收刀消退后背景恢复。需同时提供新视频和facet_probe_stage日志，才能判断实际屏幕覆盖。验证成功后再设模式2叠加既有特效。

## 安全与报告

双备份D:\CodexBackups\JCE-UprightProbe292-20261010-002156和E:\AIWorkSpace\_backups\JCE-UprightProbe292-20261010-002156；源码UTF8 BOM/CRLF，材质UTF8无BOM/CRLF，新文本UTF8/CRLF。每个被写文件即时生成独立报告；工程逐文件报告见本目录file-reports.json，完整静态记录见D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-UprightProbe292-20261010-002156\verification-final.json。历史2.9.1文档/资源/归档不覆盖。
