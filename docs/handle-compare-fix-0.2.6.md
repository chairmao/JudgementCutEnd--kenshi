# 0.2.6 伤害资格和重复施放修正

2026-10-07，已安装0.2.5日志：18:24:34.154 cache_before=223874-1155273472-0-0-2 preferred=223874-1155273472-0-0-2 draw_attempted=0 draw_ok=1 damage_armed=0。
18:24:34.946 cut_snapshot targets=2；18:24:35.879 sheath_damage_skipped: melee_weapon_not_ready_or_changed。
18:24:36.401 cast_end reason=completed；18:24:41–50的U输入被cooldown阻止；18:24:54成功开始下一次；18:25:11又成功施放。故伤害资格有错误，但重复施放不是状态永久残留。

本机游戏hand构造器RVA 0xCCFC0以lea设置虚表0x16842D0。前三项经跳板解析后：0xCD0C0（hand==bool）、0xCD020（hand==hand）、0xCD070（hand!=hand）。
已安装0.2.5 DLL中，两次武器句柄比较RVA 0x477C和0x4796都是FF 13（call [rbx]），误走槽0。
KenshiLib的非虚导出?_NV_operator_equal@hand@@QEBA_NAEBV1@@Z映射槽3815，实际RVA 0xCD020；该函数比较type、container、containerSerial、index、serial。
0.2.6由SameHand显式调用这个非虚接口；目标去重也用SameHand，保留游戏原生身份/serial语义，无须修改依赖头或虚表。

默认冷却从cast_end开始15真实秒，正常演出加冷却约17.233秒。0.2.6保持数值，增加remaining_real_seconds和cooldown_real_seconds；Cooldown=0已有配置能力可关闭。没有实现按键排队或自动重放。

145项非编译检查通过：真实游戏虚表、非虚导出与原生五字段比较、重复目标一次结算、冷却边界、3倍速度/44倍基准伤害及既有渲染资源合同。
C++编译按Skill禁止执行；用户需编译E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.sln，Release|x64。已安装DLL仍为0.2.5；0.2.6真实损伤、恢复和再次施放尚未验证。

源码备份：
D:\CodexBackups\JudgementCutEnd-HandleCompareFix-20261007-183416-488743
E:\AIWorkSpace\_backups\JudgementCutEnd-HandleCompareFix-20261007-183416-488743
验证器备份：
D:\CodexBackups\JudgementCutEnd-HandleCompareFix-20261007-183511-996072
E:\AIWorkSpace\_backups\JudgementCutEnd-HandleCompareFix-20261007-183511-996072
本轮说明和状态文件备份使用本报告所在审计时间戳；每个改动文件的11字段报告在docs/JudgementCutEnd-HandleCompareFix-*中。
源码保持UTF-8 BOM/CRLF，其余文本保持UTF-8无BOM/CRLF；读回与中文乱码扫描通过。

未解决：[MISSING]修正后的DLL及游戏实际损伤证据。当前不宣称44倍入口等于最终HP损失或完整普通攻击语义。
