# 1.1.2-dev：演出结束后的时间恢复修正

已修正源码；尚未代编译、安装或进行游戏验收。本机21:24编译的1.1.1-dev不含这次修复，已安装DLL仍为1.1.0-dev。1.1.1的灰雾/残迹/空间裂光资源保留，1.0正式存档不动。

## 证据与判断

日志：D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd\logs\JudgementCutEnd.log
- 2335行，21:00:14.542：cast14的speed_before=1。
- 2350行，21:00:16.747：cast14以cancelled_pause_focus_or_escape结束。
- 2354行，21:02:55.787：cast15的speed_before=0.001。
- 2541行，21:07:01.860：cast26 completed；这一阶段施放继续使用0.001基线。

**已确认：** 原始速度快照被0.001污染，导致后续演出即使正常完成，也只恢复到0.001。旧Finish仅在当前速度仍等于slow时恢复；active先清空，清理异常还可能跳过后面的恢复。

**据原生接口推断：** userPause缓存正速度，暂停时速度可为0，解除时从缓存恢复。演出中暂停可把0.001带入缓存：旧恢复guard跳过，解除暂停后缺少后续恢复。旧日志没有分开暂停/失焦/Esc，也没有getter前后证据，具体触发输入仍未确认。

实际接口映射及机器码见[只读证据](time-native-evidence-1.1.2.json)。getFrameSpeedMultiplier直接读取frameSpeedMult，isPaused独立读取暂停标志；没有新增API、钩子、引擎字段写入或暂停开关修改。

## 修改职责

- JudgementCutEnd.cpp：Runtime::RestoreTime独立拥有speedWorld/原速度/本次slow；写slow前建立所有权，Finish先恢复时间再清理骨骼、武器和图形。
- 暂停时不强制解除暂停；保留恢复记录，解除暂停后的帧回调先恢复原速度，再处理新U。未恢复时Begin拒绝覆盖原快照。
- 玩家主动变为1/2/3等新速度时保留用户值；换世界时放弃旧恢复记录，不解引用旧世界。
- 恢复后通过原生getter读回验证。失败保留记录重试；诊断最多三条，暂停等待最多一条。
- 结束日志增加time_owned/time_restore_pending；time_restored记录before/after/expected，取消理由分别记录pause/focus/escape/input。
- verify.py：保持既有回归，改为验证统一时间恢复入口。
- verify_vfx.py：只允许Tick的恢复入口和取消理由差异，其余输入/真实时间线仍与正式版逐字比较；伤害、范围、踉跄、骨骼Pose逐字保持。
- verify_time.py：原生暂停缓存合同模型及源码绑定检查，不把模型当作C++运行。
- README.md、配置注释和task-status.json：同步源版本1.1.2-dev，不更改任何配置值。资源格式和版本保持1.1.1。

## 验证及边界

336项非编译检查通过，其中70项时间恢复检查；覆盖1/2/3倍、正常完成、Esc/失焦/读档取消、暂停解除、重复U、setter异常/读回失败、外部变速、换世界、100次重复。模型复现了旧guard留下0.001，并验证新所有权合同不漂移。

正式版248文件与ZIP哈希验证通过。本轮没有写游戏目录、DLL或其他项目。源码UTF-8 BOM/CRLF，其余文本UTF-8无BOM/CRLF，中文检查通过。

**尚未验证：** 新C++的编译/链接、真实游戏暂停缓存与其他变速插件交互、实际灰雾效果和帧率。离线模型不能证明所有原生路径。没有在未知状态下硬写1倍，不自动修复其他插件造成的慢速。

用户编译[JudgementCutEnd.sln](../JudgementCutEnd.sln)，Release|x64。按skill的“Never attempt to compile, build, link, or regenerate binaries during a conversation.”规定，代理未执行编译。

编译后退出游戏，整体更新模组。实测：
1. 分别选1/2/3倍，按U并等结束：time_restored的after应等于expected。
2. 演出中按空格暂停：演出取消且暂停保留，time_restore_deferred；解除暂停：time_restored，下一次U的speed_before恢复原值。
3. 演出中Esc/失焦、重复U，以及主动选2/3倍：无遗留0.001，也不覆盖主动选的新速度。
4. 读档/换世界：没有旧世界速度写入；time_restore_abandoned属于正确放弃旧指针。

## 安全记录

每个变更文件都有单独11字段报告，位于docs/JudgementCutEnd-TimeRestore-*目录。小文件修改前双备份；未覆盖既有备份。
D盘备份批次：
- D:\CodexBackups\JudgementCutEnd-TimeRestore-20261007-213750-962596
- D:\CodexBackups\JudgementCutEnd-TimeRestore-20261007-213910-118941
- D:\CodexBackups\JudgementCutEnd-TimeRestore-20261007-214112-148084
- D:\CodexBackups\JudgementCutEnd-TimeRestore-20261007-214238-325208
- D:\CodexBackups\JudgementCutEnd-TimeRestore-20261007-214601-305971

E盘镜像备份位于 E:\AIWorkSpace\_backups\ 同名目录。
