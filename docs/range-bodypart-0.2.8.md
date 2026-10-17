# 0.2.8 范围一致性与受伤部位

用户请求：伤害范围应与特效范围一致，并解释敌人受伤部位的选择。

## 直接证据
- 原assets/slashes.csv共96条，43条有端点位于归一化半径1以外；max(|centre±direction×length|)=1.4517607362512068。Radius150时原伤害球150，裂痕宽带外缘218.66411043768102。
- KenshiLib真实导出/RVA表：MedicalSystem::addWound槽4865→0x64FE40；GameWorld::getObjectsWithinSphere槽3616→0x785660，不能用头文件注释RVA替代。
- 原生addWound在0x650060读取部位+0x38 hitChance，0x65006B乘+0x3C hitChanceMult，0x65007E累加。0x65002E检查机器人/缺失肢体状态，0x64FFCD–0x64FFE9检查部位状态。默认CUT_DEFAULT=0，lowBlow=false。
- 0x650163随机调用经0x4B80D跳到0x9B0DB0。后者将随机整数转浮点、归一化、乘(总权重-0)再加0；0x650176–0x650192按累计阈值选择部位。正常正权重集合下P_i≈w_i/Σw（离散随机数与浮点有舍入）。
- 原生0x78568F将0x7FFFFFFF传给空间查询，未读取调用者maxNumber；原调用256不是真实截断。插件原for循环settings.maxTargets才截断32/64。

## 最终实现
共用AreaRadius=Radius×max(1,每条裂痕端点长度+0.18/30)。裂痕维持现有规模，边界环从CUT开始可见，冲击环与目标查询/复核用同一个包围球。环抬高0.8并预留半宽，顶点不超球。球是全范围AOE，按敌人逻辑位置，包含高度差；地环表示其水平范围，装饰性角色刀/鞘/残影不定义伤害边界。不是逐条裂痕或肢体物理碰撞。

固定anchor保持伤害中心；场景节点位置加(anchor-currentWorldPosition)抵消浮动原点并对齐中心。收刀时Collect当前全范围敌人，不保留早期快照、不截断32/64；每目标仍去重并一次addWound。详细命中/非法基准最多16条/演出，汇总数量完整。圈内大量敌人增加同步结算成本，需实机确认。

原生部位选择没有改动：当前有效部位权重随机一次；无同一个敌人所有部位同时受伤、无96次攻击。伤害44倍、U覆盖、无冷却、玩家与友军保护保持。护甲/韧性导致最终HP损失不等于入口参数；不宣称复制完整普通攻击流程。

## 验证与部署
181项非编译检查通过，包括所有端点+宽带、4组半径边界环、球边界及高度、浮动原点平移、100敌人、当前进出圈、原生权重/随机/全空间查询字节，以及既有生命周期/资源检查。非编译模型不能代替真实DLL编译、像素可见性、HP或性能验收。
源码0.2.8未编译/未安装；本地0.2.7保持。用户编译JudgementCutEnd.sln Release|x64后再更新模组。

## 逐文件即时报告

### E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp
- **Role**: 演出/空间查询/原生医疗
- **Code location**: LoadAssets / AreaRadius / InArea / Collect / Damage / Draw
- **Before**: 裂痕最大外缘218.7与伤害150不一致；早期快照+32人截断
- **Changes**: 共用资产包围球；全敌人结算时扫描；边界环；固定同一中心；详细命中日志最多16条；记录原生部位权重语义；版本0.2.8
- **Reasons**: 43条裂痕超出旧球；原生addWound读取hitChance*hitChanceMult累计权重并随机选择
- **After**: 0.2.8源码统一特效与伤害范围；已安装0.2.7不变
- **Impact**: 仅 JudgementCutEnd；统一裂痕外缘、范围环和结算筛选，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Range-20261007-190223-206453\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\JudgementCutEnd.cpp", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Range-20261007-190223-206453\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\JudgementCutEnd.cpp"], "encoding": "UTF-8 BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.8待用户编译及实机验证；不代编译，不改变部位选择

### E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\JudgementCutEnd.ini

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\JudgementCutEnd.ini
- **Role**: 发布范围合同
- **Code location**: Radius / MaxTargets / version
- **Before**: Radius150却裂痕外缘218.7；默认32目标
- **Changes**: 说明资产外缘半径；MaxTargets0并忽略旧上限
- **Reasons**: 配置与全范围伤害/可见环一致
- **After**: 0.2.8源码统一特效与伤害范围；已安装0.2.7不变
- **Impact**: 仅 JudgementCutEnd；统一裂痕外缘、范围环和结算筛选，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Range-20261007-190447-891149\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\JudgementCutEnd.ini", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Range-20261007-190447-891149\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\JudgementCutEnd.ini"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.8待用户编译及实机验证；不代编译，不改变部位选择

### E:\KenshiProject\2.Projects\JudgementCutEnd\tools\verify.py

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\tools\verify.py
- **Role**: 非编译空间/原生选择验证
- **Code location**: 包围球与收刀目标集合/原生PE检查
- **Before**: 只核验共用radius名，未检查实际几何外缘
- **Changes**: 检验端点+半宽、范围环、边界/高度、浮动原点、100目标/进出圈、原生部位累计权重和随机跳转
- **Reasons**: 建立渲染/筛选合同及部位选择解释的直接字节证据；模型不当作实机验证
- **After**: 0.2.8源码统一特效与伤害范围；已安装0.2.7不变
- **Impact**: 仅 JudgementCutEnd；统一裂痕外缘、范围环和结算筛选，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Range-20261007-190447-891149\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\tools\\verify.py", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Range-20261007-190447-891149\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\tools\\verify.py"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.8待用户编译及实机验证；不代编译，不改变部位选择

### E:\KenshiProject\2.Projects\JudgementCutEnd\README.md

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\README.md
- **Role**: 项目行为与证据说明
- **Code location**: 版本0.2.8/空间及原生部位选择
- **Before**: 0.2.7说明无统一真实边界
- **Changes**: 记录218.664包围球、当前范围目标、中心修正、原生权重公式及181检查
- **Reasons**: 以代码/PE证据纠正旧范围推断，保留历史版本证据
- **After**: 0.2.8源码统一特效与伤害范围；已安装0.2.7不变
- **Impact**: 仅 JudgementCutEnd；统一裂痕外缘、范围环和结算筛选，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Range-20261007-190641-403369\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\README.md", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Range-20261007-190641-403369\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\README.md"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.8待用户编译及实机验证；不代编译，不改变部位选择

### E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\README.md

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\README.md
- **Role**: 发布使用与边界说明
- **Code location**: 空间范围/原生部位/版本
- **Before**: 已安装0.2.7说明
- **Changes**: 新增真实AOE与部位公式；区分0.2.8未编译与0.2.7已安装
- **Reasons**: 避免配置半径、伤害球及部位碰撞含义混淆
- **After**: 0.2.8源码统一特效与伤害范围；已安装0.2.7不变
- **Impact**: 仅 JudgementCutEnd；统一裂痕外缘、范围环和结算筛选，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Range-20261007-190641-403369\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\README.md", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Range-20261007-190641-403369\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\README.md"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.8待用户编译及实机验证；不代编译，不改变部位选择

### E:\KenshiProject\2.Projects\JudgementCutEnd\docs\task-status.json

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\docs\task-status.json
- **Role**: 源代码/部署状态
- **Code location**: source_configuration及验证阶段
- **Before**: 已安装0.2.7
- **Changes**: 0.2.8源版本/范围合同/181检查，安装保留0.2.7
- **Reasons**: 区分当前源码与真实部署版本
- **After**: 0.2.8源码统一特效与伤害范围；已安装0.2.7不变
- **Impact**: 仅 JudgementCutEnd；统一裂痕外缘、范围环和结算筛选，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Range-20261007-190641-403369\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\docs\\task-status.json", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Range-20261007-190641-403369\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\docs\\task-status.json"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.8待用户编译及实机验证；不代编译，不改变部位选择
