# 2.4 原烟纹理与动态烟带修订

源码版本：2.4.0-dev；资源：2.4-source-smoke-r1。当前只完成源码、材质和资源修改。未运行C++或HLSL编译器，未安装本修订，未进行新版本游戏测试。游戏目录和用户已编译的DLL仍为2.3，不能仅复制本次材质给旧DLL。

## 问题与依据

用户视频3AFFA7E637E88ADA.mp4及上一轮日志确认2.3资源已生效，但均匀蓝色遮罩缺少明显流动烟形。继续增加切片密度会把烟形平均成蓝膜。

本机Skyrim参考模组的主要烟层包含BSStripParticleSystem条带、FXSmokeSoftSub烟形纹理，以及SmokeParticles01独立烟丝。烟丝的SubTexModifier关闭，4×4图集不是已证实的连续翻页动画。原尺寸控制器有200点条带曲线和64点烟丝曲线；烟丝有随机方向的旋转。没有把巨大Bomb/Gravity数值直接搬到Kenshi。

资源提取证据及NIF节点解析位于：
D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCESkyrimFog-20261008-1305

FXSmokeSoftSub取自本机BSA，SmokeParticles01取自用户指定模组。新DDS均字节一致复制。未验证MO2覆盖优先级，也未声称所有纹理一定是原游戏官方版本。

## 修改

- 底雾32片保留，但光学厚度从0.85降到0.16。底雾只承担淡气氛，不遮盖主体烟纹理。
- 新增48条烟带，每条10段。沿现有刀路输运，横向卷动、抬升、扩张和消散；段内连续UV。
- 新增96个独立烟丝槽，实际几何沿各自圆弧移动，同时旋转、扩张、淡出。使用原烟形透明空隙，不叠加规则椭圆轮廓。
- 采用演出剪辑秒，而非被减慢的游戏时间。各槽异相出生；收刀停止新生，已有一代消散；END透明度归零。
- 两个新材质使用普通透明混合、深度测试、禁止深度写入。每层按中心距离远到近提交。图集半纹素内缩并禁用mipmap，防止串格。
- 增加独立2.4烟层shader入口。原刀光、折射、羽光、闪光、尘烟shader及0..8绘制段保持；新增9/10段沿用现有清理路径。
- 有界日志只在阶段首次记录smoke_bands=48、smoke_segments=10、smoke_wisps=96和particle_revision=2.4_source_smoke，不逐粒子刷日志。

新增资源：
- package/JudgementCutEnd/assets/jce_source_soft_smoke.dds
- package/JudgementCutEnd/assets/jce_source_smoke_wisps.dds
- package/JudgementCutEnd/assets/vfx-2.4.0.json

修改文件：
- JudgementCutEnd.cpp：烟层CPU几何、原尺寸曲线、预载、两个新绘制段及版本日志；另修正新助手的const兼容性。
- jce_atmosphere.hlsl：降低底雾，增加原图集烟带/烟丝shader。
- jce_atmosphere.program：新像素程序及底雾程序名。
- jce.material：底雾新程序绑定。
- jce_source.material：追加两个新材质。
- README.md、docs/task-status.json：当前构建、安装与验证状态。

## 验证与限制

34项静态/CPU模型检查通过，详细结果见本轮verification.json。其中逐函数比对了伤害、按键、重播、骨骼姿势、时间恢复、原生绑定、清理及旧刀光；授权范围之外C++逻辑一致。原曲线计数/值、DDS哈希、材质/程序/纹理引用、浮点UV解包、出生结束模型、中文与编码已核对。

固定几何上界19668顶点、47358索引，低于32768/49152限制。新增2304顶点、3456索引，无额外游戏实体或逐帧粒子分配。几何预算不能证明实际GPU速度：透明烟层增加像素覆盖，350范围近镜头仍需实测帧率。

烟丝CPU轨迹模型在0.10真实秒内有明确位移，排除代码只改静态贴图位置的情况；这不能证明最终画面具有期望雾感。按层/中心排序不是逐三角形全局透明排序，交叉烟带可能仍有叠加差异。

本实现重建可验证的条带与烟丝行为，未完整执行Skyrim NIF粒子引擎，也未复制其全部灯光/HDR、物理和后处理。不能承诺完全等同原版次元斩绝。GPU材质加载、相机内外与俯视、最终颜色/烟形、性能及反复U/ESC结束清理均待实机确认。

## 用户编译与验收

编译JudgementCutEnd.vcxproj，Release|x64，v100。本次需要新2.4 DLL及完整配套资源一起安装；不要混用2.3 DLL。现有安装脚本会校验源码版本和构建时间，拒绝旧DLL。

验收日志应出现version=2.4.0-dev以及particle_revision=2.4_source_smoke、layers=11。游戏中观察烟带与烟丝运动、相机近远/俯视/范围内遮挡，反复U覆盖与ESC取消，并核对结束后的时间恢复和帧率。

本轮主备份：
D:\CodexBackups\JudgementCutEnd-SourceSmoke-20261008-133659-646941
E:\AIWorkSpace\_backups\JudgementCutEnd-SourceSmoke-20261008-133659-646941

const兼容性修正和文档分别有-ConstCheck、-Docs双备份目录。源码保留UTF-8 BOM/CRLF，其他文本UTF-8无BOM/CRLF。备份与逐文件11字段报告在docs/JudgementCutEnd-SourceSmoke-20261008-133659-646941，正式1.0/2.0及游戏目录哈希未改。
