# 2.9.10-dev：施放资格与玩家成员保护

本轮按用户授权扩展同一个JudgementCutEnd.cpp。现有特效定稿2.9.8、350水平半径、96次100%武器伤害、自由镜头、U键默认及CastKeyVK配置保持。

## 启动与持续资格

启动必须：仍为玩家队员、人形（包括机器人，排除动物）、清醒存活且可行动、四肢为原生或已装义肢且健康合格、游戏按攻击条件选中的装备栏近战武器有效。启用伤害时必须成功保存U键伤害快照；准备失败拒绝开始。

四肢状态只接受LIMB_ORIGINAL或LIMB_REPLACED；缺失、摧毁、缺部位、义肢已卸下、未初始化或非有限健康拒绝。血量严格小于0才拒绝，0允许；原生flesh与flesh-fleshStun+juryRigging均不得为负。义肢按装在角色身上的实时MedicalSystem部位判定，不读取卸下物品的过期currentDamage。原生机器人本身的原生肢体也允许。

启动、每帧、每击之前，以及一名敌人的医疗批次结束后，共用CasterBlockedReason。死亡、昏迷、断肢、负血量、不再人形或失去玩家归属立即Finish中断。已经扣除的伤害不回滚，其余斩击停止；恢复资格后不会自行续播，必须重新按键。

武器只在启动时检查。演出中卸下、转交、丢弃或换武器仍使用U键快照；持续资格函数不检查武器。

## 玩家成员免伤

ProtectedPlayer优先于敌对判定，任意一个条件成立都排除：原生玩家标记、当前全部玩家角色名单、本轮启动时保存的玩家serial hand名单。范围不限当前选中角色或当前小队，玩家动物与昏迷队员也保护。原成员在本轮中途离队仍保护；新加入者在每击前按当前归属保护。

目标收集、逐目标、逐击、唯一addWound调用之前的最终闸门都检查保护；踉跄入口也排除玩家。即便其它状态把队员标成敌对，保护仍优先。保护针对本插件的伤害及反应路径，不改变原生战斗或其它插件的伤害。

中断沿用统一Finish：优先偿还时速恢复债务，释放有效骨架手动控制，停止音效和图形，清空伤害快照及保护名单。失去资格的施放者不再被插件强制原生收刀。Damage调用Finish后Tick本帧立即返回，防止继续Draw访问已释放状态。

## 原生证据

- const PlayerInterface::getAllPlayerCharacters实际RVA0x7F18F0返回全部玩家角色列表，而非选中列表。
- Character::isPlayerCharacter实际RVA0x790B30查询派系玩家接口标记。因此施放者同时要求标记与玩家列表，目标保护任一匹配即可。
- MedicalSystem::getLimbState实际RVA0x6430A0查询RobotLimbs状态；getPart(Limb)为0x656B00。
- HealthPartStatus::setRobotLimbItem实际RVA0x643B20将义肢最大健康、磨损、损伤和眩晕映射至角色医疗部位。
- updateDerivedHealths实际RVA0x643190计算flesh-fleshStun+juryRigging的派生健康。

证据目录：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-CasterSafety-20261010-211456；不使用头文件旧public RVA，也未在插件中加入字符串函数签名寻址。

## 验证与编译

33项资格/玩家保护静态检查、139项快照/资源/修改范围检查、70项时间回归通过。76个包资源哈希与2.9.8定稿一致；纯特效、姿势及时间恢复算法保持。以上均为源码/原生机器码合同或离线回归，不是游戏实测。

旧综合verify.py有既存特效接口字符串断言与定稿不匹配，不宣称综合套件全部通过。

源码SHA256：0CB8A4593640C3B4422E97C2E7C3C9452ED6B5E19D93523B5034FF0EBC7E872E。尚未编译、部署；当前安装仍是2.9.8-dev。用户编译JudgementCutEnd.vcxproj，Release|x64，v100；产物E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll应含version=2.9.10-dev，再更新游戏mod。

实机验收建议：无武器和不合格四肢启动拒绝；健康义肢/机器人成功；中途卸武器继续伤害；死亡/昏迷/断肢/离队中断并恢复时间；不同小队、动物队员及昏迷玩家队员不扣血、不踉跄；敌人在命中批次中被招募后停止剩余伤害。无法让旧命中回溯到招募之前，招募成为玩家前已发生的合法敌人伤害不回滚。

## 文件安全

原2.9.9源码双备份在D:\CodexBackups\JCE-CasterSafety-20261010-211927-292326和E:\AIWorkSpace\_backups\JCE-CasterSafety-20261010-211927-292326；最后闸门、日志和验证器修改另有各自时间戳双备份。逐文件报告在证据目录。

CPP保持UTF-8 BOM/CRLF，已有Python保持UTF-8/CRLF，新文档和工具UTF-8无BOM/CRLF。中文回读与乱码扫描通过。没有修改游戏文件、存档、mods.cfg或其他项目。
