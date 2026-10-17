# JudgementCutEnd 0.3.0：350范围圆与96裂痕拟合

## 请求与结果

用户指定地面圈就是伤害区、半径350，96次裂痕长度匹配该圆。源码默认Radius=350，外圈与伤害半径同值，裂痕中心/长度/宽度按整体包围半径缩放。伤害采用XZ水平圆，不受角色高度差缩小。保留96次独立100%原生武器命中、收刀大踉跄和U覆盖行为。没有编译、没有更新游戏模组。

## 源码位置与合同

JudgementCutEnd.cpp：默认值第143行、朝向拟合第490行、圆形复核第504行、候选收集第510行、地面环第621行、渲染第641行。

Radius是实际半径，layoutScale=Radius/max(1,max(XZ端点长度+0.18/30))。实际朝向先旋转两端，因中心与长度统一缩放，直线段上的点也在端点包围区间；相机朝向改变的Ribbon半宽保守计入。128段环外缘350，宽度全部向内，不再显示扩张的其他环。旧INI的150会被新版按实际150解释，应安装本包350配置。

## 原生候选查询证据

本机Steam 1.0.65，KenshiLib导出槽与RE_Kenshi/RVAs/Steam_1.0.65.br映射；只读游戏PE。

- GameWorld::getObjectsWithinSphere RVA 0x785660；0x78568F将maxNumber写为INT_MAX，0x7856A5经0x25D7E转到ZoneSpacialGrid::getObjects 0x9FE340。
- SpacialCellBasic槽2为0x9FA580；Categorised槽2为0x9FB6B0。
- 距离指令0x9FA5E3与0x9FB737均只取位置offset0和offset8（X/Z），做两次平方相加，没有Y。
- Basic 0x9FA603的comiss后jbe跳过，因此边界是严格小于。候选半径取350.01避免遗漏边界，最终InArea用distanceSquared<=350*350决定命中。多取候选不增加实际伤害区。

## 验证与限制

221项非编译检查通过，包括96端点/半宽、4朝向和4半径、环几何、圆内外/高度/NaN、查询映射与旧生命周期/逐击损伤/资源合同。预览内嵌JavaScript的Node --check通过；C++括号词法检查通过。完整结果：E:\KenshiProject\2.Projects\JudgementCutEnd\docs\verification-circle350-20261007-195931-405730.json。

这些模型和源代码/字节检查不能替代VC100编译、最终像素或游戏HP验收。平面环位于施放高度+0.8，坡地可以遮挡，未实现地形贴合；材质光晕像素也可能超出几何边缘。圈扩大可能纳入更多目标，96次同步医疗结算与画面填充成本可能增加，未测性能。收刀后死亡/失效等仍停止后续击数，并非保证对每个目标均实际完成96击。

## 文件、备份与编码

本次修改JudgementCutEnd.cpp、package/JudgementCutEnd/JudgementCutEnd.ini、tools/verify.py、preview/index.html、README.md、package/JudgementCutEnd/README.md、docs/task-status.json；新增本报告、完整验证JSON及逐文件11项审计记录。
所有已有文件先按原完整路径双备份。D盘根：D:/CodexBackups/JudgementCutEnd-Circle350-*；镜像根E:/AIWorkSpace/_backups/JudgementCutEnd-Circle350-*。具体每文件路径见docs/JudgementCutEnd-Circle350-*中的即时JSON报告。C++保留UTF-8 BOM/CRLF，其余保留UTF-8无BOM/CRLF，中文及替换字符扫描通过。未修改其他项目、依赖、已安装DLL或游戏配置。

## 编译与安装边界

依照code-modification-principles的“Never attempt to compile, build, link, or regenerate binaries during a conversation.”以及本项目AGENTS.md的不代编译规则，用户编译E:/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.sln的Release|x64。新版未安装；当前安装0.2.9，DLL SHA256仍为4b7eb82e9a5061e71896649c1db1f9e61299fed6654e200acf68dd79447334ac。用户编译后再整体更新DLL与INI。
