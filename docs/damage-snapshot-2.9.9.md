# 2.9.9-dev：U键攻击伤害快照

本轮只修复伤害失效。特效定稿2.9.8保留；源码已改，未编译，游戏目录仍是2.9.8-dev DLL。

## 规则

- 按下配置施放键（默认U），通过游戏的 preferred weapon / 原生拔刀流程，保存攻击方的切割、钝击、穿刺、额外眩晕、流血倍率、护甲穿透及种族加成数值。
- 快照成功以后，自动收鞘、缓存清空、卸下、丢弃、转交、更换武器和攻击方属性变化，不撤销或重算本轮伤害。
- 收刀时仍收集当时350水平半径内的有效敌人。敌人列表不是U键时快照；每击仍用原生addWound处理当前身体、护甲和医疗状态。
- 每目标最多按实际96条刀光结算96次100%武器伤害，途中死亡/无效/离开范围则停止；每击使用独立Damages副本。大踉跄逻辑未改。
- 再次按键覆盖旧演出时，未结算的旧伤害取消，旧快照清空，重新取得新快照。读档、换世界、角色失效及既有取消条件仍中断；医疗回调后逐击复查加载和世界。
- 快照仅保存数值。特定种族GameData地址只作不解引用的身份键，演出结束即清空，不保留武器/CharStats裸指针跨帧。
- 施放时快照失败仍沿用原有“仅演出”行为并记录原因。本轮尚未完成新的四肢资格和无武器禁止演出等全部五项限制。

## 问题证据

已安装2.9.8的最近日志中，准备阶段出现draw_ok=1 damage_armed=1；随后8次完整演出出现cast_damage_disarmed: weapon_changed_or_missing以及sheath_damage_skipped: melee_weapon_not_ready_or_changed。旧SameDamageWeapon把实时战斗缓存当作资格，缓存清空会永久关闭本轮伤害。

本机Steam1.0.65原生sheatheWeapon在RVA0x5CBE31调用setWeapon(NULL)，并在0x5CBE68清空手持对象。由该流程与日志推断，自动收鞘是缓存失效的合理原因；未捕获具体是哪一个AI回调触发，不能据此声称已定位该AI。

原生getTotalAttackDamageFor在0x885B66检查空目标，0x885B69明确跳到0x885C8D的skillMultDamage处理。因此可在U键获取完整公共攻击基准，再冻结bonusRobots/Humans/Animals/Races和bonusArmourPenetration。在收刀时按原生机器人优先、动物、人形顺序套用目标加成。空目标分支不设置穿透，故单独保存。

完整只读原生证据：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-DamageFix-20261010-204750\getTotalAttackDamageFor-full.asm.txt。

## 验证结果与限制

专项127项静态检查通过，76个包内资源哈希匹配2.9.8定稿。绘制、骨骼、姿势、范围、目标收集、踉跄和时间恢复代码逐字匹配基线。时间恢复70项离线模型及源码连接检查通过。

旧综合verify.py未全通过：第108项manual render submission and camera/shadow isolation仍使用旧视觉接口字符串，2.9.8定稿也缺少geometry->_updateRenderQueue(。本轮未修改特效以迁就旧断言；专项核对证明相关代码与定稿一致。

先乘自身技能，再乘目标加成，与原生的先目标后技能在浮点舍入上有极小差别；常见数值样本最大相对差为8.87e-08。这不是游戏实测。第三方插件若按非空目标定制getTotalAttackDamageFor，其特殊钩子兼容性尚未验证。

不得把静态通过描述为游戏伤害已修复。需要编译后检查weapon_damage_snapshot，并在有有效敌人的场景看到sheath_hit source=u_key_snapshot / total_landed_hits>0；还需实际确认卸下武器后仍造成伤害、重放和读档无旧伤害泄漏、时间恢复正常。

## 编译和文件安全

用户编译JudgementCutEnd.vcxproj，Release|x64，v100；输出E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll。源码版本2.9.9-dev，SHA256 864E26B40E2DB4CE66CDEF0B10CB3A9BB3C895D22294A2ED75113B7E7CDBF35F。没有代编译、部署或修改存档/mods.cfg。

原源码双备份：D:\CodexBackups\JCE-DamageFix-20261010-204750 与 E:\AIWorkSpace\_backups\JCE-DamageFix-20261010-204750；快照重写和最后边界修改另有时间戳双备份，详细逐文件报告保存在D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-DamageFix-20261010-204750。

CPP保持UTF-8 BOM/CRLF；验证器保持UTF-8/CRLF；新文档UTF-8无BOM/CRLF。中文和乱码扫描通过。
