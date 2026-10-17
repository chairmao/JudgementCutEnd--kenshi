# 2.9.11-dev：五项施放条件已接入源码

本轮按用户“实现之前五点”的范围核对。第1、2、3、4点已在2.9.10中接入，保持该实现；本轮补齐第5点配置读取及分发说明。没有改动已定稿特效、姿势、时速恢复算法、伤害快照或玩家保护。

| 要求 | 实现与边界 | 源码位置 |
|---|---|---|
| 人形，包括机器人 | Character::isHuman可用且不是Animal；不按robot种族标志排除；只有玩家队员可发动 | JudgementCutEnd.cpp:741 CasterBlockedReason |
| 四肢健全，义肢算健全 | 四部位仅ORIGINAL/REPLACED；义肢必须已安装且医疗部位有效；原flesh与含眩晕/维修的有效健康都不得为负；0可通过肢体门槛，仍需清醒存活 | CasterBlockedReason |
| 加载安全 | 按键边沿先消费、加载拒绝在选中角色解析前；加载结束不补放；演出进入加载/换世界/换骨架即取消；启动检查身体与骨架激活/身份/控制所有权 | Tick:2092、Begin:959 |
| 使用攻击武器 | 游戏_NV_getThePreferredWeapon选择，装备栏身份核验，不扫描背包；武器仅启动条件；启用伤害时准备失败拒绝；按键快照成功后卸下/更换/转交不撤销 | PreferredDamageWeapon、EquippedWeapon:604、PrepareWeapon、Begin |
| 配置自定义键位 | CastKeyVK完整十进制整数，A-Z(65-90)/F1-F12(112-123)，默认U=85，J=74，F8=119；支持空格、UTF-8 BOM和#或;行末注释；85abc/85.5/空值/越界拒绝且保留上一合法值 | Settings:187 |

配置与DLL同目录，示例：`CastKeyVK = 119 # F8`；改配置后重启游戏读取。单键，不需要Ctrl/Shift。文本框、暂停、加载、非全局输入模式禁止发动；按键与其它mod冲突仍需自己选择不冲突的键，插件不消费原版键事件。

演出角色死亡、昏迷、不再人形、四肢不合格或离队立即中断；已提交伤害不回滚，其余斩击停止。玩家全部小队成员（含动物/昏迷者）及本轮起始队员均被排除于本插件伤害和踉跄。时间恢复保持此前债务机制，不能以静态检查保证所有未知加载时序绝对安全，仍需实机验收。

本轮修正INI/README中仍称“无武器也播放/换武器撤销伤害”的旧说明。所有INI数值默认值保持原样。真实CPP差异仅Settings解析及版本日志；其余2.9.10功能逐字一致。资产/视觉及时间算法继续与2.9.8定稿核验。

## 验证与交付边界

- 五项合同/配置边界：36项通过。
- 人形四肢与玩家保护/本机原生证据：33项通过。
- 武器快照、数值配置、冻结资产与改动范围：142项通过。
- 时间恢复合同模型及源码连接：70项通过。

检查不调用编译器或启动游戏。旧综合verify.py存在此前特效接口字符串失配，因此不宣称全套综合检查通过。新专项检查曾出现验证器Python相邻字符串导致默认U误报，已修正；生产默认U一直正确，最终上述检查全通过。

源码版本2.9.11-dev，SHA256 `E565CF55922E8944C87BBD408F50C71BF06F0B0088BAF30B5F08AB9A6BBD6E61`。尚未编译或部署，游戏目录DLL仍2.9.8-dev。用户编译`E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj`的Release|x64(v100)，产物`E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll`应包含`version=2.9.11-dev`；不要把旧DLL当成新条件已生效。

建议实机依次检查：机器人/健康义肢成功；动物/缺肢/负健康/无装备武器拒绝；双武器室内外选择日志；中途卸武器按原快照；演出中读档取消且加载结束不补放；连续施放/取消后时间正常；所有玩家小队及动物队员不扣血、不踉跄；修改F8重启后生效。

## 文件安全与逐文件报告

主双备份：`D:\CodexBackups\JCE-FiveRequirements-20261010-213313-65f044`、`E:\AIWorkSpace\_backups\JCE-FiveRequirements-20261010-213313-65f044`。验证器修正另有JCE-FiveRequirements-CheckFix时间戳双备份。CPP UTF-8 BOM/CRLF，其余修改文件保留UTF-8无BOM/CRLF；中文回读、乱码扫描通过。没有修改其他项目、游戏目录、mods.cfg或存档。

证据与各文件完整变更报告：`D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-FiveRequirements-20261010-213144-141d13`。包括源文件、INI、README、快照验证器、新五项验证器及本说明；历史归档和旧验证报告不覆盖。
