# 0.2.7 无冷却与按键覆盖

用户要求：取消冷却；按U未完成演出时，再按U清理后重新执行动画。

实现：删除Settings.cooldown与Runtime.nextAllowed，旧Cooldown非零值只记录忽略。输入仍检测上升沿，保留输入模式/暂停/读档/编辑框门槛。新按键在旧时间线前处理，Finish("restarted_by_key")先恢复骨骼、已拔武器、所持有速度，再停止音效、注销监听、销毁图形、清空目标与残影；Begin再捕获当前选中角色并归零演出状态。清理后新角色不可施放则记录拒绝，不保留旧演出。

伤害：覆盖抢占旧的待结算事件，不补刀。已提交医疗伤害不会回滚。新演出重新获取敌对目标并在自身收刀时刻按目标结算一次。保留0.2.6 hand::_NV_operator_equal原生比较修复和44倍装备伤害。

验证：156项非编译检查通过，包括输入优先级、旧非零配置、多个覆盖时刻、长按不重放、已结算伤害保留、100次覆盖只有一个资源所有者。Python AST、中文与CRLF检查通过。模型不能代替宿主C++编译或证明真实游戏中无泄漏/伤害有效。

部署：源码0.2.7，已安装DLL仍0.2.5；本轮未编译、未安装、未实机测试。用户编译Release|x64后再安装，不能把旧DLL作为0.2.7使用。仅修改JudgementCutEnd项目。

## 逐文件即时报告


### E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp
- **Role**: 运行时施放与资源生命周期
- **Code location**: Settings / Runtime / Finish / Tick
- **Before**: 演出中拒绝U；结束后冷却15秒
- **Changes**: 删除冷却时钟；旧Cooldown键忽略；U上升沿在旧时间线前清理并重启；新增覆盖日志；版本0.2.7
- **Reasons**: 实现无冷却覆盖，避免旧待结算伤害及资源残留
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184401-491718\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\JudgementCutEnd.cpp", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184401-491718\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\JudgementCutEnd.cpp"], "encoding": "UTF-8 BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL

### E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\JudgementCutEnd.ini

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\JudgementCutEnd.ini
- **Role**: 发布默认配置
- **Code location**: Cooldown及施放说明
- **Before**: 默认Cooldown=15
- **Changes**: 设为0并声明旧键忽略；说明再次按U覆盖
- **Reasons**: 与无冷却运行时合同一致
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184454-494380\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\JudgementCutEnd.ini", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184454-494380\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\JudgementCutEnd.ini"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL

### E:\KenshiProject\2.Projects\JudgementCutEnd\tools\verify.py

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\tools\verify.py
- **Role**: 非编译静态与生命周期验证
- **Code location**: 速度时钟与重施放验证段
- **Before**: 检查15秒冷却边界
- **Changes**: 替换成无冷却/旧配置忽略/输入优先/资源恢复检查；增加多个演出阶段及100次覆盖模型
- **Reasons**: 验证覆盖前清理和一次性结算边界，明确模型不执行宿主C++
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184454-494380\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\tools\\verify.py", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184454-494380\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\tools\\verify.py"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL

### E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\JudgementCutEnd.ini

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\JudgementCutEnd.ini
- **Role**: 发布配置注释
- **Code location**: Radius说明
- **Before**: 匹配15同时误替换半径150注释
- **Changes**: 恢复五倍范围说明
- **Reasons**: 仅修改冷却语义，保持原范围说明
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184539-042161\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\JudgementCutEnd.ini", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184539-042161\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\JudgementCutEnd.ini"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL

### E:\KenshiProject\2.Projects\JudgementCutEnd\tools\verify.py

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\tools\verify.py
- **Role**: 非编译验证
- **Code location**: 重施放检查局部变量
- **Before**: 新检查用未定义begin_cpp并覆盖原begin
- **Changes**: 沿用原Begin代码切片；索引单独命名begin_pos
- **Reasons**: 保持验证器变量语义一致
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184539-042161\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\tools\\verify.py", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184539-042161\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\tools\\verify.py"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL

### E:\KenshiProject\2.Projects\JudgementCutEnd\README.md

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\README.md
- **Role**: 项目行为与版本说明
- **Code location**: 版本总览/0.2.7/历史0.2.6
- **Before**: 0.2.6保留15秒冷却
- **Changes**: 记录无冷却覆盖、资源所有权、一次性伤害、验证边界及新日志
- **Reasons**: 让文档符合当前源代码；保留历史证据
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184705-410089\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\README.md", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184705-410089\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\README.md"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL

### E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\README.md

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\README.md
- **Role**: 发布操作说明
- **Code location**: 施放/冷却/诊断/版本
- **Before**: 15秒冷却说明
- **Changes**: 更新0.2.7无冷却覆盖重播与伤害规则；156非编译检查
- **Reasons**: 提供与发布配置一致的使用指南
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184705-410089\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\README.md", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184705-410089\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\package\\JudgementCutEnd\\README.md"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL

### E:\KenshiProject\2.Projects\JudgementCutEnd\docs\task-status.json

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\docs\task-status.json
- **Role**: 项目状态及验收边界
- **Code location**: source_version / source_configuration / pending
- **Before**: 0.2.6等待编译
- **Changes**: 声明0.2.7源版本、零冷却、覆盖合同；安装仍0.2.5
- **Reasons**: 区分当前源代码与旧DLL的实际状态
- **After**: 0.2.7源码取消冷却并支持按键覆盖；已安装0.2.5不变
- **Impact**: 仅 JudgementCutEnd；取消冷却并清理后重新施放，不改其他项目/已安装DLL
- **Validation**: 原字节双备份，写后读回一致；UTF-8/BOM/CRLF保留，中文乱码扫描通过
- **Safety**: {"backups": ["D:\\CodexBackups\\JudgementCutEnd-Recast-20261007-184705-410089\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\docs\\task-status.json", "E:\\AIWorkSpace\\_backups\\JudgementCutEnd-Recast-20261007-184705-410089\\E\\KenshiProject\\2.Projects\\JudgementCutEnd\\docs\\task-status.json"], "encoding": "UTF-8 without BOM", "line_endings": "CRLF"}
- **Unresolved**: 0.2.7待用户编译及实机验证；不代编译或安装旧DLL
