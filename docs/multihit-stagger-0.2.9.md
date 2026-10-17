# 0.2.9 独立96击与原生大踉跄审计

本次仅改JudgementCutEnd.cpp、tools/verify.py、发行包INI、两份README和task-status.json；创建本报告及验证记录。没有编译、安装、启动游戏、改依赖或其他项目。

## 当前行为

## 0.2.9 每条裂痕独立命中与收刀大踉跄

- 按用户确认的实际96条裂痕，每目标最多96次独立原生部位判断，每次100%当前装备近战武器对该目标的基准伤害。不是一次9600%伤害；护甲分别处理96次，可能显著改变实际HP结果。
- 结算全延迟到收刀（真实约1.717秒），在同一批次同步执行。原生addWound将部位随机选择与伤害应用合在一起，因此是“收刀集中逐击处理”，不是先独立预选96个部位再统一手写HP。每击重验serial/生死/敌对/范围和武器，死亡或失效停止余下命中；昏迷本身不会停止仍有效的医疗命中。
- 每目标基准只计算一次；每击使用新的Damages副本。旧DamageMultiplier=44或其他非1值忽略，防止96×44；流血倍率和护甲穿透仍为原生每击基准。
- 命中结束后仅请求一次原生大踉跄，使用最后一次返回部位和相对攻击方向选择目标种族的bigStumble动作；没有大动作时退回普通动作，没有任何匹配动作则记录原因。死亡、KO或非站立状态不强制播放站立动作。
- StaggerForceMultiplier=8只放大医疗入口返回后四通道总和所构成的反应力度，上限1,000,000；反应单独传给CombatClass::_getHit，不再次进入医疗、不添加额外昏迷伤害。大动作与力度不等于固定秒数硬直；当前游戏calculateStumbleBlockTimer返回常量，不能宣称倍率使硬直延长8倍。
- 保留0.2.8共用范围球（默认约218.664）、0.2.7无冷却及U覆盖重播。每目标日志汇总部位ID:次数、requested_hits/landed_hits/no_part_hits、stop、stagger和stagger_force；详细日志最多16条/演出，总计仍限4096条。
- 96次原生医疗调用在同一帧处理，人数越多越可能产生结算卡顿；没有偷偷缩减次数或截断敌人数。须实测HP变化、护甲效果、人形/动物反应、死亡/KO、U覆盖及大量敌人性能。

## 本机原生证据

依据KenshiLib.dll导出桩（6字节/槽）与RE_Kenshi/RVAs/Steam_1.0.65.br映射，读kenshi_x64.exe反汇编；没有将SDK注释里的旧RVA当作入口。

| 接口 | 实际RVA | 证据及用途 |
|---|---:|---|
| MedicalSystem::addWound | 0x64FE40 | 0x650060读hitChance，0x65006B乘hitChanceMult，0x650163经thunk调用随机数；每次入口重选部位 |
| AnimationClass::chooseStumbleAnim | 0x51E990 | 0x51EAC9比动画bigStumble与bigone，0x51EAD6比方向；无候选0x51ED4B返回null |
| AnimationClass::startStumble | 0x51FA00 | 原生替换既有stumble/action并调用播放；不直接写动画缓存或内部状态 |
| CombatClass::_getHit | 0x664A00 | 0x664A66-79求四通道和写stumbleForce；此接口是战斗反应，不是医疗扣血 |
| CharStats::calculateStumbleBlockTimer | 0x8853E0 | movss常量/ret，因此不承诺力度8倍等于硬直时间8倍 |
| Character::getCombatClass | 0x5C8820 | 非虚原生访问；_NV_getProneState=0x5C7380，_NV_isUnconcious=0x5C9380 |
| Character::getAttackOriginationDirection | 0x435260 | 用原生相对攻击方向为目标匹配受击动画 |

不用Character::_startStumble(0x438E50)直接传大伤害希望“必然大踉跄”：该包装器含随机/现有stumble判断，可降低/放弃大动作。本次显式选bigone=true，再startStumble与_getHit各一次；缺种族资源时诚实回退。没有引入强制持续硬直计时器或新动画资源。

## 数据与生命周期

- 主线程Tick到SHEATH仅调用一次Damage；damageDone先置true，U覆盖先于旧时间线。
- Collect按共享AreaRadius筛选、hand非虚比较去重；逐目标getTotalAttackDamageFor提供各自武器/属性/种族基准。
- inner loop取实际slashes.size()，当前96；每击Damages(base)复制，原生护甲对引用的修改不累积到下一击。
- 每击重新解析caster和target、武器、敌对、范围及生死；不跨帧排队，不储存已失效医疗对象。
- 回传部位按stringID汇总；最后part只用于本次原生反应选择，不长期保存角色或动画指针。
- 反应力度由有效返回参数之和计算，double累计后截到1,000,000，只送_getHit。before/after伤害参数不是最终HP损失。
- source_version=0.2.9；installed_version=0.2.7，旧DLL SHA256 198920c19f94a1e4c9c05134a3ba8dd33b9f4fe332abeb91bf94472fa29e4601，未改变。

## 验证与限制

通过191项非编译检查，覆盖资源/编码、96行资产、每击独立参数、部位汇总、死亡停止、反应与医疗分离、本机导出/机器码、范围、原有U覆盖和资源恢复。包含入口合同模型，未执行宿主C++，不能证明实际HP损失/护甲/犯罪经验/反应动作或性能。验证明细：E:\KenshiProject\2.Projects\JudgementCutEnd\docs\verification-0.2.9-20261007-192347-755337.json。

仍须用户编译JudgementCutEnd.sln Release|x64，再整体更新发行包。试验时应同时检查requested_hits/landed_hits/bodyparts/stagger；死亡提前停止或种族无大动作是明确分支。96次医疗在同一帧处理，多敌人可能出现结算卡顿。

## 逐文件即时报告及安全

- [JudgementCutEnd_cpp-1fc9a690.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-191908-809290/JudgementCutEnd_cpp-1fc9a690.json)
- [JudgementCutEnd_ini-ae35de38.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192044-013532/JudgementCutEnd_ini-ae35de38.json)
- [verify_py-d287f34b.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192044-013532/verify_py-d287f34b.json)
- [JudgementCutEnd_cpp-1fc9a690.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192138-106609/JudgementCutEnd_cpp-1fc9a690.json)
- [verify_py-d287f34b.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192138-106609/verify_py-d287f34b.json)
- [README_md-5443f1f4.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192347-132389/README_md-5443f1f4.json)
- [README_md-bc24033e.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192347-132389/README_md-bc24033e.json)
- [task-status_json-95bfed78.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192347-132389/task-status_json-95bfed78.json)
- [verification-0_2_9-20261007-192347-755337_json-07ce636a.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-Multihit-20261007-192347-132389/verification-0_2_9-20261007-192347-755337_json-07ce636a.json)

每次改写前原字节双备份到D:\CodexBackups\JudgementCutEnd-Multihit-*与E:\AIWorkSpace\_backups\JudgementCutEnd-Multihit-*，路径保持原盘符和目录。CPP保留UTF-8 BOM/CRLF，其余保留UTF-8无BOM/CRLF；严格解码、读回比对及中文乱码扫描通过。新审计文件以exclusive create新建，不覆盖历史证据。
