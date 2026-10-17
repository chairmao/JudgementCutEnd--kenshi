# 正式版2.0冻结与粒子2.1开发

当前游戏目录保持正式2.0原DLL和资源。正式发行包为 releases/JudgementCutEnd-2.0.0-release.zip；2.1开发源码尚未编译、尚未实机验收。

## 冻结内容和身份

500项文件包括实际已安装的32个模组文件、对应源码/工程、工具文档及有界运行记录；ZIP CRC、每项SHA-256、两处专项备份均核验。正式1.0保存不变。
发行标记2.0.0，旧DLL内部标记1.2.1-dev保持原字节；这不是二进制重编译或改版本字符串。

ZIP SHA-256：4e47e90b637180c8fdf16002bab0e05469cb034d19ad363d6c896d0f74a066b7
DLL SHA-256：61edde0416bde310e8f4901c82e117b674d1292598023b016f5a0734e953bae7

- D:\CodexBackups\JudgementCutEnd-Formal2Clean-20261008-013448-433715\E\KenshiProject\2.Projects\JudgementCutEnd\releases
- E:\AIWorkSpace\_backups\JudgementCutEnd-Formal2Clean-20261008-013448-433715\E\KenshiProject\2.Projects\JudgementCutEnd\releases

恢复方法：关闭游戏，备份当前模组，以发行包mod/恢复JudgementCutEnd目录。不要恢复source/到游戏目录。发行包未包含其他项目、依赖库、存档或模组启用配置；重新编译源码仍依赖原有本地KenshiLib_0.5.0/v100环境。

## 雾霾感与本次调整

2.0有576面半球幕、168个大雾片和48个atlas烟尘片叠加。判断来自绘制代码及用户视觉反馈；没有GPU截图或性能采样证明具体过绘制量。
2.1保留连续灰色空间基调，不增加一堆随机蓝色云团：

| 部分 | 2.0 | 2.1开发 |
|---|---|---|
| 半球幕Alpha乘数 | 0.16 | 0.055 |
| 内部雾片Alpha乘数 | 0.11 | 0.045 |
| 大雾片半宽/半径 | 0.22..0.245 | 0.15..0.165 |
| 48个细雾 | 慢速绕半球的大雾片 | 各跟随独立刀路，拉长、轻微卷曲、淡出后再出生 |
| 雾片动画身份 | 排序后用数组位置选图集帧 | 排序随带稳定id，避免镜头转动导致换帧 |
| 光屑寿命 | 0.2剪辑秒/约0.067真实秒 | 0.64..0.86剪辑秒/约0.21..0.29真实秒 |
| 光屑运动 | 中心随机喷散 | 沿实际刀路方向运动，并有轻微侧向卷曲 |

SourceDust材质独自启用dustDetail=1：根据原DDS Alpha压低稀薄灰底、柔化拉长后的边界。其他四种原纹理材质默认dustDetail=0，颜色/Alpha保持原路径。仍只采样一次原纹理，不改原DDS，不跨图集格子取样，不设置全局场景雾。
这是基于原资源的分层近似，不是真正体积流体，也没有宣称复刻DMC5专有渲染器。

## 修改范围与保护合同

JudgementCutEnd.cpp仅特效范围：HazeCell、Mist、ParticleAngle、SourceDust、SourceSparks、单次资源就绪日志及开发版本标记。伤害、350范围、96次武器命中、U覆盖重施放、原刀光绘制、人物动画、相机、音频、绑定、时间恢复及资源清理均保留。

新增/修改shader生产者、program缺省值和SourceDust材质消费者共同定义dustDetail；未新增GPU程序种类或渲染层。48雾片/128光屑为固定栈/循环预算，无堆分配、逐帧文件读取或每粒子日志。
几何上界仍19828顶点/47598索引，材质段9。雾片占屏面积变小，但较长寿命会增加同时可见光屑数量；实际GPU帧耗时未测，不承诺零开销。

## 验证与限制

616项静态/数学/资源检查通过，完整结果见 verification-particle-2.1-final.json。包括：

- 冻结1.0/2.0每项文件和ZIP哈希、双专项备份及当前游戏32文件身份。
- 医疗、按键、姿势、时间、清理、刀光等34个函数逐字比较；Draw除日志字段外逐字一致。
- 原5DDS、6曲线、头部修正资源、音频、刀光材质不变；新增参数三端一致。
- 15/30/60/144 FPS模型的粒子出生/淡出，全部48/128槽被覆盖，收刀停发且结束前透明。
- 64格图集半纹素边界、排序身份、透明度有界、C++03结构、UTF-8/中文/CRLF。

第一次旧检查将全文件age>life作为持续刀痕限制；现限定Draw主刀光循环，保留真正的持续刀痕合同。失败过程在initial记录中保留，没有删除历史。

静态模型不执行C++/HLSL，不是GPU观感、性能、编译通过或零崩溃证明。旧离线preview未接入本次粒子，不作为2.1画面证明。
2.0日志中仍有武器改变/缺失造成伤害跳过；本次不修改伤害，也不把正式发行标签当作全功能质量认证。

## 编译、更新和验收

code-modification-principles/SKILL.md明确：“Never attempt to compile, build, link, or regenerate binaries during a conversation.”
E:\KenshiProject\AGENTS.md也明确“不代编译”。本轮未运行编译、链接或shader编译器。

请用户编译 JudgementCutEnd.vcxproj，Release|x64/v100；再以Stage-LocalMod.ps1整包更新。新DLL的plugin_ready应显示version=2.1.0-dev，vfx_layers_ready包含particle_revision=2.1_streams。版本门槛仍拒绝旧1.2.1 DLL配新资源，避免误以为新特效已生效。

游戏验收建议：
1. 室外同一角色近/远镜头确认背景通透、细雾随刀路、光屑连续可见。
2. 转镜头确认雾片不突然换图集帧，刀光效果仍与2.0一致。
3. 连按U覆盖、演出完成、Escape取消、失焦与暂停后确认时间恢复及特效清理。
4. 350边界和96次伤害采用原逻辑；持武器实测，不用无武器/武器改变的跳过日志断言无伤害缺陷。

## 文件安全记录

已有文件均双备份到D:\CodexBackups和E:\AIWorkSpace\_backups的JudgementCutEnd-Particle21-*任务目录。C++保留UTF-8 BOM/CRLF，其余文本保留UTF-8无BOM/CRLF；新文档UTF-8/CRLF，中文/乱码扫描通过。

逐文件11项报告已在docs/JudgementCutEnd-Particle21-*目录即时保存，包含每个改动的原/新哈希、位置、理由、验证、备份、编码和未确认范围。所有改动仅本项目；游戏目录本轮未写入。
