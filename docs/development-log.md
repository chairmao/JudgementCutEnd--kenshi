# JudgementCutEnd — 次元斩绝独立 RE_Kenshi 插件 2.5.0-dev

当前源码/资源修订 **2.5-spatial-partition-r1** 与用户编译的2.5 DLL已整体更新至游戏模组目录；完整包逐字节核验通过，尚待游戏验收。本轮没有调用编译器。

[本次空间切裂说明](docs/spatial-fracture-2.5-20261008.md)：按Skyrim原NIF九条独立折射曲线及刀路宽长比例，以八条实际刀路划分空间，让裂缝两侧背景产生不同采样偏移。显式保证折射先于刀光/烟层绘制，补齐折射失败时的UV布局。保留2.4流动蓝雾、动画、350范围、96次伤害、U覆盖、自由相机及时间恢复。

105项静态/数值检查通过，GPU效果和性能仍需实测。用户已编译JudgementCutEnd.vcxproj的 **Release | x64**，并完成DLL与package完整部署。查看日志version=2.5.0-dev、optics_revision=2.5_spatial_partition。

已特别保存 [2.4视觉版本](releases/JudgementCutEnd-2.4.0-special-20261008-141211-865716.zip)；正式 [1.0](releases/JudgementCutEnd-1.0.0.zip)、[2.0](releases/JudgementCutEnd-2.0.0-release.zip)保持冻结。双备份与逐文件报告见 [本轮验证](docs/JudgementCutEnd-SpatialFracture-20261008-143008-651338/verification.json)。

下方为历史记录，旧版本参数、安装状态和结论不代表当前事实。当前以本次说明与docs/task-status.json为准。旧preview没有接入本次烟层，不能作实机观感证明。

## 2.1历史记录

正式版2.0已冻结：[发行包](releases/JudgementCutEnd-2.0.0-release.zip)、[说明](releases/2.0.0/RELEASE-README.md)。发行标签2.0.0，保留用户已经编译的DLL内部历史标记1.2.1-dev；没有重新编译或修改二进制。500项源文件、资源和运行证据哈希核验，另有双盘专项备份。

当前追加资源修订 **2.1-pale-blue-r1** 已同步到游戏：主刀光冰蓝、拖尾青蓝、細雾/光屑淡蓝，背景灰雾保留。仅更新四个材质/shader文件，C++和2.1DLL字节不变，不需重编译DLL；画面待游戏验收。[本轮配色与备份](docs/pale-blue-20261008.md)。

当前开发版2.1只改粒子：更通透的灰色半球、48个沿刀路流动的独立细雾、128个较长寿命冷白光屑。刀光、原五张DDS、六条曲线、头部姿势修正、350范围、96次伤害、U覆盖及时间恢复逻辑与正式2.0保持一致。

[粒子改进与验收](docs/particle-2.1-20261008.md)。用户已编译2.1.0-dev，DLL与全部32个模组文件已同步到游戏mods/JudgementCutEnd；PE64、入口导出、版本、编译时间和逐项哈希通过。双备份已核验，正式2.0归档保持。当前尚未进行2.1游戏验收，启动游戏按U测试即可。安装记录见[本次更新](docs/installation-particles-20261008-014947-0776219.json)。

下方是历史记录，其中旧版本参数、安装状态和结论不代表当前事实。当前以docs/task-status.json和本次说明为准。离线preview仍是旧模型，没有接入2.1粒子/shader，不能用作本次实机观感证明。


## 1.1.2历史记录


当前源码按用户参考图修正：整体灰色半球气氛、96道斩击各六层运动残迹、16条路径各四层持刀掠影、短促错位空间高光。没有实体镜子、闭合镜片边框或落地碎片。保留350水平圆、96次100%武器命中、按键和角色动作。

用户已编译1.1.2-dev，并整体安装到游戏mods/JudgementCutEnd目录。DLL含时间恢复修复，配套特效资源为1.1.1。安装哈希核验通过，实机效果待验收；1.0.0正式存档完整保留。

本次新增[时间恢复修正](docs/time-restore-1.1.2.md)：结束/取消先恢复原速度，暂停期间保留玩家暂停并在解除后恢复；恢复记录独立于演出，不会被再次U覆盖。有界日志time_restored记录恢复前后速度。特效资源版本仍为1.1.1。

日志vfx_material_loaded / vfx_queue_submitted / vfx_render_callback仅证明绘制链路，不能代替最终画面验收。

## 正式存档与当前特效修正

- 正式版：[1.0归档](releases/1.0.0/RELEASE-README.md)，[ZIP](releases/JudgementCutEnd-1.0.0.zip)；全部248文件哈希和ZIP保持。
- 96道刀痕各六层延迟拖尾，16路径各四层掠影；持刀剪影为原创几何，未复制玩家模型。
- 连续半球薄幕和168个规则重叠雾格点共同营造灰色气氛；不随机撒蓝色粒子，不修改全局场景雾。
- 192个独立光学片区沿真实斩痕短暂闪现，原位消散；不是镜子或真实折射。
- 一个ManualObject/三个材质段，最坏16492顶点、23490索引；结束、取消和读档仍统一回收。
- [修正说明](docs/vfx-1.1.1.md)和[离线预览](preview/index.html)记录效果、验证和限制。
- 用户编译JudgementCutEnd.sln，Release|x64；退出游戏后整体更新DLL与资源。不能只复制材质给旧DLL。

## 0.3.0 历史：半径350的范围圈与96条裂痕

- Radius=350现在直接表示范围圈外圆半径，也是伤害半径；可配置5–1000。旧版的Radius=150是布局缩放值，约218.664的伤害球不会沿用到新默认值。更新时必须同时安装新INI；保留旧INI的150会得到半径150的圆。
- 唯一范围圈从演出开始固定显示350，收刀后只淡出；环带宽度向内展开，128段外圆顶点均在350边界。收刀以目标逻辑位置相对固定施放中心的XZ距离判定，包含边界、不因高度差缩小；整个圆是伤害区，并非沿亮线进行碰撞。
- 每次按实际角色朝向，将96条裂痕的两端投影至XZ，连同最大光带半宽计算包围半径；统一缩放中心、长度和宽度，使整体匹配350圈。保留不同长度及相对分布，不把每条改成同样的700长直径。
- 本机原生候选查询虽然名为getObjectsWithinSphere，SpacialCellBasic/Categorised实际均只读取X/Z计算距离，并使用严格小于半径。查询多取0.01以避免遗漏边界；最终InArea仍按350含边界复核，不扩张伤害范围。
- 96次100%原生部位命中及大踉跄逻辑保持。半径扩大可能包含更多敌人并增大画面填充和同步医疗结算成本；平面环仍位于施放高度+0.8，深度测试可能被坡地遮挡，未做地形贴合。材质光晕像素可能超出几何边缘。
- 验证、原生RVA证据和逐文件备份见[范围报告](docs/circle350-0.3.0.md)。静态检查通过不等于C++已编译或实际画面与伤害验收通过。

## 0.2.9 历史：每条裂痕独立命中与收刀大踉跄

- 按用户确认的实际96条裂痕，每目标最多96次独立原生部位判断，每次100%当前装备近战武器对该目标的基准伤害。不是一次9600%伤害；护甲分别处理96次，可能显著改变实际HP结果。
- 结算全延迟到收刀（真实约1.717秒），在同一批次同步执行。原生addWound将部位随机选择与伤害应用合在一起，因此是“收刀集中逐击处理”，不是先独立预选96个部位再统一手写HP。每击重验serial/生死/敌对/范围和武器，死亡或失效停止余下命中；昏迷本身不会停止仍有效的医疗命中。
- 每目标基准只计算一次；每击使用新的Damages副本。旧DamageMultiplier=44或其他非1值忽略，防止96×44；流血倍率和护甲穿透仍为原生每击基准。
- 命中结束后仅请求一次原生大踉跄，使用最后一次返回部位和相对攻击方向选择目标种族的bigStumble动作；没有大动作时退回普通动作，没有任何匹配动作则记录原因。死亡、KO或非站立状态不强制播放站立动作。
- StaggerForceMultiplier=8只放大医疗入口返回后四通道总和所构成的反应力度，上限1,000,000；反应单独传给CombatClass::_getHit，不再次进入医疗、不添加额外昏迷伤害。大动作与力度不等于固定秒数硬直；当前游戏calculateStumbleBlockTimer返回常量，不能宣称倍率使硬直延长8倍。
- 保留0.2.8共用范围球（默认约218.664）、0.2.7无冷却及U覆盖重播。每目标日志汇总部位ID:次数、requested_hits/landed_hits/no_part_hits、stop、stagger和stagger_force；详细日志最多16条/演出，总计仍限4096条。
- 96次原生医疗调用在同一帧处理，人数越多越可能产生结算卡顿；没有偷偷缩减次数或截断敌人数。须实测HP变化、护甲效果、人形/动物反应、死亡/KO、U覆盖及大量敌人性能。

## 0.2.8 历史：特效与伤害共用空间边界

- 旧Radius=150只放大裂痕布局；43条裂痕端点超出旧伤害球，最长归一化端点1.451760736。新增包围系数=max(1,所有端点长度+0.18/30)，实际球半径=Radius×系数，默认约218.664。保留既有裂痕大小；斩击开始显示完整边界环，环宽度和高度也预留在球内。
- 渲染与查询共享施放时的anchor。渲染用当前场景位置加anchor与当前角色逻辑位置的差向量，抵消浮动原点；不会在允许的小位移期间视觉随角色移动而伤害中心不动。球形AOE包含高度差，按角色逻辑位置判定，不是逐亮线/逐肢体碰撞。
- 收刀结算时重新筛选当前全范围敌人，圈内后进入者也纳入，圈外/玩家/友军/无效/死亡目标仍不命中。不再限制前32/64人；旧MaxTargets非零值忽略。医疗调用仍每目标一次、serial hand去重。大量目标会增加本次同步结算成本，须实机检验。
- 原生getObjectsWithinSphere在本机0x78568F直接传INT_MAX给空间查询，没有读取调用者maxNumber；旧256并非真实原生截断。实际32/64截断来自插件循环；现已移除。详细命中/非法基准日志合计最多16条/演出，另记录总数量，保留全进程4096条上限。
- 部位选择继续交给原生MedicalSystem::addWound(false,CUT_DEFAULT,...)；权重为hitChance×hitChanceMult（默认区域），先排除原生不合格/缺失部位，再累计权重随机选一个。没有使用裂痕碰撞点或同时击伤所有肢体。日志bodypart是游戏返回的实际部位ID。
- 181项非编译检查通过：端点/半宽、范围环、4组Radius、高度/边界、浮动原点、100目标、进出圈、原生选择字节及原有生命周期/资源检查。详情和逐文件即时报告见[范围报告](docs/range-bodypart-0.2.8.md)。待用户编译Release|x64；当前安装0.2.7保持。

## 0.2.7 无冷却与覆盖重播

- 每个U按键上升沿立即施放。演出期间再按U，先恢复旧角色骨骼/本插件拔出的武器/仍由本插件持有的世界速度，停止旧音效、注销图形监听并销毁旧特效，然后对当前所选角色从剪辑零点重新施放；长按U不会逐帧重播。
- 新输入先于旧演出的时间线处理。被中断演出尚未结算的伤害不会补算；已结算伤害不回滚。新演出仍在自己的收刀时刻按目标最多结算一次。
- 不排队、没有结束后等待。旧配置Cooldown键仅兼容读取，不再启用冷却。暂停/读档/文本框/非全局输入模式/不可用角色等既有施放门槛仍有效。
- 新日志cast_restart_requested记录旧cast id、剪辑时间和是否已结算；旧cast_end reason=restarted_by_key紧接新cast_begin，便于核验无状态叠加。
- 156项非编译检查通过，包含多个覆盖阶段、结算同帧优先级、长按、已结算伤害及100次连续覆盖模型；模型不执行宿主C++，不能证明实机无泄漏或伤害成功。详情见[报告](docs/recast-0.2.7.md)。

## 0.2.6 历史：句柄比较与冷却诊断

- 0.2.5日志18:24:34显示cache_before与preferred均为223874-1155273472-0-0-2，却damage_armed=0；18:24:34.946找到2个目标，结算被跳过。18:23–18:25有5次施放完成，其余U输入明确被cooldown或paused阻止，不是施放状态永久残留。
- 旧0.2.5 DLL在0x477C/0x4796以call [rbx]比较两份hand。实际hand构造器设置的游戏虚表槽0为operator==(bool)，槽1才是operator==(const hand&)；依赖头的重载声明编译顺序与游戏不同。0.2.6显式调用hand::_NV_operator_equal(const hand&)映射到真实0xCD020，保留type/container/containerSerial/index/serial校验及原生空句柄语义。
- 目标去重也替换std::find，避免同一错误虚调用导致重复伤害。最多32（配置上限64）个目标，逐个非虚比较；伤害仍对每个目标只结算一次。
- weapon_prepare增加cache_after。cast_blocked: cooldown增加remaining_real_seconds，cast_end增加cooldown_real_seconds。默认冷却仍从结束后计15真实秒；期间按U不排队、不自动重放，Cooldown=0的既有配置能力保留。
- 未修改依赖头、已安装DLL或运行中游戏。原生/旧成品证据、逐文件报告和备份见docs/handle-compare-fix-0.2.6.md；145项非编译检查不能替代C++编译及真实损伤测试。

## 0.2.5 武器准备与演出放行

- 纠正0.2.4“CharStats::weapon包括收鞘、可直接当装备栏”的假设。hasWeapon只测试战斗缓存hand；本机原生CharacterHuman::drawWeapon会调用CharStats::setWeapon更新缓存。日志证明旧门槛拒绝施放，但没有记录其子条件，不能断言玩家当时实际没有装备。
- 施放前先完成骨架、可见身体、渲染和速度验证；然后由getThePreferredWeapon选择当前手持或主/副装备栏武器。若是收鞘的近战装备，使用原生drawWeapon和物品原inventorySection，同时建立手持模型和伤害属性；不直接临时改写CharStats，不扫描/叠加背包武器。
- 无近战装备、远程/天然空手武器、拔刀失败或缓存未同步时仍播放动画/特效/音效，只跳过武器伤害。中途换装或缓存变化也只取消伤害资格。演出结束/取消时，仅收回本插件拔出的同一个serial hand；原本已手持的武器、外部换装或失效旧世界均不恢复。
- 保留单键U、自由镜头、三倍速度、半径150与44倍原生逐目标伤害。weapon_prepare记录cache_before、preferred、draw_attempted、draw_ok、damage_armed；cast_begin也记录damage_armed。无伤害资格会出现cast_visual_only；结算跳过、换装撤销与收刀恢复分别记录。
- 原生导出映射/PE只读检查、生命周期模型与既有资源检查通过；这不代表已在游戏验证。用户应编译JudgementCutEnd.sln的Release|x64，再在退出游戏后整体安装。详情见docs/weapon-gate-fix-0.2.5.md。

## 0.2.4 三倍速度与武器伤害

- 原关键帧/裂痕文件的剪辑时轴仍是6.7秒，QPC真实时间统一乘3。真实时刻：0.700秒拔刀、0.783秒裂空、1.717秒收刀结算、2.233秒恢复。冷却15秒、世界速度0.001和卡顿取消门槛1.5秒仍按原单位；卡顿差值先把上一帧剪辑秒除3，避免单位混用。
- 音效改为独立文件assets/jce_sequence_fast.wav，五段参考声音触发点和窗口除3；保持44100Hz原采样率/音调，使用各段前部片段和淡出，不声称整段声音无损加速。旧音轨保留供旧版合同检查；预览也按三倍推进。
- 使用CharStats::getTotalAttackDamageFor(target)逐目标计算，再调用Damages::multiply(44)。本机原生CombatClass::attackImpactCheck同样先取基准伤害，再应用impactPoints中的power到切割、钝击、穿刺、extraStun四通道；流血倍率与护甲穿透不重复乘44。4400%是44倍总倍率，不是45倍，也不是44次攻击。
- 基准来自属性系统当前采用的装备近战武器，包含原生武器/属性/种族修正；背包备用武器不叠加。记录武器serial hand并在施放和结算时重验；原0.2.4将空手/远程装备及空缓存拒绝为施放错误，并在换装时取消整个演出；此门槛已在0.2.5改为只撤销伤害资格。
- DamageMultiplier默认44，允许0–100；旧CutDamage/BluntDamage记录弃用日志，不再决定伤害。NaN/Inf或非法负伤害拒绝提交。保留每目标一次addWound、敌对/身份/范围重验、玩家保护和目标数量上限。
- sheath_hit记录weapon、base/scaled四通道、multiplier、bleed_mult、armour_penetration和addWound参数返回值。44倍指受伤入口前的伤害参数；实际HP损失及护甲/韧性/犯罪/经验等完整战斗语义须实测，本插件没有复制普通近战格挡/攻击流程。
- 128项非编译检查通过，涵盖15/30/60/144FPS一次性时序、真实卡顿、同步音频精确98490帧、倍率/流血/穿透/异常数值及现有蒙皮与自由相机。C++未编译，游戏测试未完成。原生片段、接口槽位和验证报告见docs/JudgementCutEnd-SpeedWeapon-20261007-172113-138619。

## 0.2.3 蒙皮消费链、位置漂移与特效修正

- 本机 Entity::updateAnimation（RVA 0xC1620）在 skip=true 时绕过 cacheBoneMatrices；0.2.2 用临时 skip=true 保护姿势，却因此没有生成新蒙皮矩阵。此前“设置 dirty 再调用 _updateAnimation 即发布”的判断不完整，由这次反汇编与矩阵误差更新纠正。
- 新增绑定真实 cacheBoneMatrices 导出。作用域内保持 skip=true，显式生成身体/同骨架衣物矩阵，再重新发布 dirty 并更新世界矩阵；随后恢复原 skip。cacheBoneMatrices 内 skip 仅抑制旧动画重放，不抑制矩阵生成。本机具体行为与通用 OGRE 代码需区别，未添加全局 Entity 钩子或写 GPU 数组。
- 每根受控骨骼同时捕获局部位置与朝向。施放期间重新写入捕获位置，结束/取消恢复同一快照，防止原生位置轨道累积；不移动角色逻辑位置或场景节点。漂移的最终上游来源仍未完整归因，这次控制的是实例姿势边界。
- 默认 Radius 从 30 改为 150，上限从 60 改为 300。敌对目标查询、距离复核与视觉使用同一参数；对象数仍最多 32（配置上限64），伤害数值保持原值。
- 光带宽度随范围同比放大；默认边缘半宽 0.9、核心半宽 0.175；裂痕出现后至少维持80%强度到收刀，收刀后0.65秒淡出。材质浮点 colour RGB=4，顶点颜色钳制0–1，防止归一化颜色溢出；GPU深度保留。
- 96条裂痕和两层光带不增加，几何预算不扩大；范围/宽度增大会增加潜在像素填充开销，实际帧率须测试。
- 每次最多四条 pose_skin_published 增加 position_drift_corrected。验收应检查 matrix_error 接近零、手局部位置不随时间单向累积，并实际看到拔刀/挥斩/收刀；这些数值仍不能单独证明演出质量。
- 111项非编译检查通过，含本机PE分支字节、八个导出、缓存/共享消费者模型、403帧位置归位模型、半径/HDR合同和现有资源。C++编译与0.2.3游戏测试未执行；见 docs/JudgementCutEnd-RootVFX-20261007-164157-081257。

## 0.2.2 单键 U 与 Entity ABI 修正

- 默认单独按 U（CastKeyVK=85），按住不重复、松开后可重试；文本编辑、暂停、读档、非全局输入模式等原门槛保留。旧 0.2.1 DLL 即使配置改为 85 仍要求 Ctrl+Shift，且存在误拒绝，必须重编译。
- 0.2.1 成品 DLL 在 RVA 0x5340 读取 Entity+0x300 为初始化标记，0x534D 读取 Entity+0x2F8 为骨架；本机 OgreMain 导出的 isInitialised/getSkeleton 读取 0x308/0x300。不是快捷键未被收到，也不能通过去掉检查放行。
- 启动时从已加载 OgreMain_x64.dll 绑定骨架、初始化、共享集合、跳过动画状态开关及蒙皮矩阵/数量共七个真实导出，缺失则在挂钩之前禁用。不改变依赖头、不写死运行字段或函数 RVA，不修改其他项目。
- 施放前最多四条 skin_binding_checked 输出可见身体、动画骨架、初始化和匹配结果。蒙皮刷新临时开关及矩阵诊断也使用真实运行接口，避免只修第一道检查而继续读写错位字段。
- 本机七个导出均存在，101 项非编译检查通过；C++ 编译和新版本游戏测试尚未执行。证据见 docs/native-entity-abi-20261007-161614。

## 0.2.1 自由视角与蒙皮发布

- 演出开始/结束及逐帧逻辑不再写相机位置、朝向或跟随目标。旧 CinematicCamera=1 也会被忽略。
- 本机 OgreMain_x64.dll 的 Skeleton::_updateTransforms（RVA 0x344FC0）清除 manual-dirty；Entity::cacheBoneMatrices（0xC2A30）同帧会根据该标记决定是否重新生成矩阵。旧 Pose 调用了前者却没有发布新矩阵；这是代码中已确认的缺口，是否是人物不动的全部原因仍待实测。
- 写骨骼/更新节点后发布 dirty，使用官方 Entity::_updateAnimation 刷新施法者身体和共用同一骨架的衣物缓存；仅在刷新作用域内跳过一次旧 AnimationState 重放，异常也恢复原值。不直接写 GPU/矩阵数组，不添加全局 Entity 钩子。
- 每次施放最多四条 pose_skin_published，包含衣物数量、右手位置、局部蒙皮矩阵误差和 dirty；可以分辨轨道在变而人物矩阵没变的情况。这仍不是最终像素验收。

## 0.2.0 修正

- 脊柱单帧 44° 突跳改成分段平滑曲线；IK 挥斩角速度尖峰经过四元数同半球滤波，最大单帧变化 10.885°。骨长保持，足部在制作坐标中不漂移。
- 根朝向、骨盆、腿、肩颈一起持有；进入/结束与捕获姿态平滑混合。动画覆盖放在整个 AnimationClassHuman::update 结束后；该位置调整不等于已经证实旧版骨骼被原生覆盖。
- 特效直接跟随角色可见场景节点，避免大世界坐标减浮动原点的约定混用；显式加载和检查材质。
- 使用官方 postFindVisibleObjects 扩展点，把本插件有界几何加入主相机的 HDR 队列。仅绕过本效果的 CPU 可见物扫描，深度遮挡保留；自动提交关闭以避免双绘制，阴影/其他相机过滤；仅在本帧相机已到达队列 83 后提交，每帧一次，结束时注销监听。
- 弃用旧合成声；改用所提供参考目录的动作音效按演出时刻混音，处理边缘淡入淡出并防叠加削波，没有另外添加音乐或人声。

## 当前内容

- 2.233 真实秒演出（三倍速度）：蓄势、0.700 秒拔刀、0.783 秒裂空、1.717 秒收刀结算、2.233 秒恢复。
- 403 帧、60 Hz 的原创骨骼姿势，23 条局部四元数轨道，覆盖本机 Kenshi 人形骨架的完整父子朝向链。动画存储在 `assets/jce.clip`，插件直接读取并驱动角色实例。
- 96 条蓝白空间裂痕、蓄势/收刀地环、骨架轮廓残影、光带刀鞘、原创渐变贴图与参考资源重混的 2.233 秒同步音效。
- 世界默认降速至 0.001 倍，演出按真实时间推进。仅施法者的指定骨骼姿势独立播放；这不等于让角色的所有 AI、移动和物理获得时停豁免。
- 默认收刀时对范围内的非玩家敌对角色各结算一次原生伤害，先锁定目标、结算前再验证身份与范围。没有通过碰撞决定伤害部位，也没有真正切开模型。
- 暂停、Esc、失去前台、读档、施法者不可用/移动、世界或场景更换、长时间卡顿、原生姿势回调没有到达时取消。取消后尝试恢复仍属于本插件的姿势与速度；不接管镜头。
- 日志覆盖启动、拒绝原因、施法、原生姿势回调、目标快照、收刀命中部位、结束/取消。4096 条/进程上限，约 2 MiB 轮转，不给全部 NPC 逐帧刷日志。

## 先看预览

双击 `E:\KenshiProject\2.Projects\JudgementCutEnd\preview\index.html`。可播放、拖时间、调整视角。

预览为同源骨架/轨道/裂痕的数学可视化，没有角色皮肤网格，也不模拟 Kenshi 的光照、镜头控制和伤害。`preview\slash-preview.png` 为早期版本 2.50 秒截图，未用作 0.2.0 验收依据；本轮以更新后的交互预览为准。

参考目录 `E:\skyrimspecialedition\mods\Judgement Cut End - ap05's Remake` 内未找到骨架；五个 HKX 文件哈希相同。本版参考其 PayloadInterpreter 演出时间，重新编排 Kenshi 动作，不是 HKX 转换/重定向。没有复制 NIF、DDS；音效使用参考目录中的 Intro、Draw、CutAll、Sheath、Finish 五段 WAV，来源、哈希和时刻见 docs/audio-provenance.json。与鬼泣 5/参考模组的动作、模型残影和特效精细度仍有差异。

## 编译与安装

现有依赖已经可用，无需下载新环境。使用 v100、x64、/GL、/LTCG、非增量链接、动态 CRT `/MD`，链接已有 KenshiLib 0.5.0 / OGRE / MyGUI；当前头文件来自 0.5.1，运行时与导入库为 0.5.0。挂钩地址由 KenshiLib 解析，本机确认范围为 Steam Kenshi 1.0.65。其他游戏版本尚未验证。

1. 打开 `E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.sln`，编译 **JudgementCutEnd，Release|x64**。
2. 应生成 `E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll`。
3. 正常关闭 Kenshi 后执行下面命令。`Bypass` 只作用于这次 PowerShell 进程，不改系统执行策略。脚本不会编译、停止游戏或编辑 mod 勾选。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\KenshiProject\2.Projects\JudgementCutEnd\tools\Stage-LocalMod.ps1" -Mode Install
```

脚本把 DLL 和资源安装到 `D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd`。覆盖旧文件之前在 `D:\CodexBackups` 与 `E:\AIWorkSpace\_backups` 各备份一份，并核对复制哈希。如果只要整理本项目分发包，改用 `-Mode Stage`。

4. 在游戏启动器手动启用 JudgementCutEnd；RE_Kenshi 已安装是前提。不要把 DLL 再添加到另一个插件清单，避免重复入口。
5. 游戏中选中一名清醒、未被搬运的人形玩家角色，按 **U**。默认冷却从演出结束/取消起算 15 秒；**Esc** 可取消。

现有项目规则 `E:\KenshiProject\AGENTS.md` 要求“不代编译”；技能 `C:\Users\周凡稀\.agents\skills\code-modification-principles\SKILL.md` 明确要求“Never attempt to compile, build, link, or regenerate binaries during a conversation.” 因此本次未运行编译器、未生成 DLL，编译与实机验收留给用户。

## 参数与日志

参数文件：安装目录内 `JudgementCutEnd.ini`；游戏重新启动时读取。

| 参数 | 默认值 | 行为 |
|---|---:|---|
| CastKeyVK | 85 | 单键；85=U，119=F8；只接受 A-Z（65–90）或 F1–F12（112–123）的整数。避开其他模组占用键 |
| Radius | 150 | 游戏坐标单位；原默认半径五倍，限制 5–300；视觉与目标检索同步 |
| WorldSpeed | 0.001 | 演出时世界速度，限制 0.001–0.1 |
| DamageMultiplier | 44 | 原生装备近战武器逐目标伤害的总倍率，44=4400%；限制0–100，旧固定伤害项弃用 |
| MaxTargets | 32 | 最多结算对象，限制 1–64 |
| Cooldown | 15 | 演出结束/取消后的真实秒数，限制 0–120 |
| DamageEnabled | 1 | 改为 0 可先检查动作与特效，不结算伤害 |
| SoundEnabled | 1 | 播放参考动作音效重混的同步轨道；WinMM 与其他使用同一音效接口的插件可能互相打断 |
| CinematicCamera | 0 | 兼容旧配置；0.2.1 已移除镜头控制，即使值为 1 也不接管视角 |

日志：`D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd\logs\JudgementCutEnd.log`。

启动时先有两条 `native_binding`，记录真实桩 DLL 内 RVA 与解析目标；不得把本插件的导入跳板交给 KenshiLib。导出缺失或不在桩表内时记录 `plugin_disabled`。安装器还会拒绝早于 cpp/vcxproj 修改时间的旧 DLL。

正常路径应出现 `plugin_ready → frame_hook_seen → cast_key_detected → cast_begin → damage_snapshot → sheath_damage → cast_end reason=completed`。命中时另有 `sheath_hit`，包含 target、bodypart 与伤害引用参数值。

0.1.1 的 `plugin_ready` 输出实际键值；`cast_blocked` 标明冷却、暂停、读档、输入模式、输入框等拒绝原因；`cast_rejected` 表示骨架/角色状态不合要求；`pose_thread_mismatch` 或 `pose_hook_not_observed` 表示原生回调线程/调度尚不适配，应以日志定位，不能把特效出现当作姿势正确。`runtime_error` 会进入恢复流程；普通 C++ 异常捕获无法保证捕获原生访问冲突。

建议先用 `DamageEnabled=0` 检查：手臂是否实际拔刀/收刀、腿部是否正常、镜头和速度是否恢复；再恢复默认伤害，在敌人附近确认只结算一次、不伤玩家。分别尝试 Esc/暂停、读档、连续重复施法，并查看最后日志。这些是待实测项目，目前没有对应通过记录。

## 已完成验证与边界

原始 `docs\verification.json` 记录 52 项只读检查；链接配置修正后 54 项通过。0.1.1 的专项复核记录另存本项目 `docs\JudgementCutEnd-InputFix-20261007-142533-005949`。检查涵盖：Python AST、工程 XML/依赖、零数据记录 mod、403 帧单位四元数、骨长不变/足部不漂、HTML 与运行时动作同源、资源格式、渲染队列/宿主着色器合同及小时间模型。旧版安装脚本曾执行完成；修正版复制前检查 DLL 实际导出并拒绝旧 C 导出，PowerShell AST 和离线夹具检查另存专项记录。浏览器预览无页面错误。

这些检查不执行宿主 C++。旧版 DLL 已由用户编译；0.1.1 实测在原生函数绑定处断言；0.1.2 已由用户实测，室外无特效、肢体抽动、音效不符。0.2.0 的 94 项静态/资源检查已通过，结果见 docs/verification-0.2.0-20261007-153735-517426.json；0.2.0 已由用户编译并测试；0.2.1 已编译安装，但实际被错位内联接口误拒绝施放；0.2.2 已实测 U 与自由镜头生效，但人物僵硬平移且视觉淡；0.2.3 的蒙皮消费链/位置/范围/亮度修正待编译与实测。未验证骨骼蒙皮/武器附件显示、镜头和其他插件配合、伤害/护甲/犯罪语义、运行性能和内存增长。不能据此宣布复刻已经完整有效或零崩溃。

动作没有根位移/瞬移；残影是骨架光带而非完整角色模型副本；视觉刀鞘不会隐藏真实装备。接口是快捷键原型，未加入技能树、技能栏、消耗和 NPC 技能 AI。目标为先提供可独立测试的核心演出和日志，再根据游戏证据调整。

制作工具 `tools\author_assets.py` 只读本机骨架并生成本项目资源；再次运行会双备份已存在输出。它不会改变游戏骨架或原始 Skyrim 模组。`tools\verify.py` 仅检查，不编译、不安装。

详情：`docs\implementation-review.md`、`docs\native-evidence.json`、`docs\asset-provenance.json`、`docs\change-report.md`。
