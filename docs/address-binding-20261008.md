# JudgementCutEnd：成员函数地址式绑定修正（2026-10-08）

用户明确要求不要使用字符串函数签名定位主循环。修改只涉及 JudgementCutEnd.cpp 的两处 KenshiLib Hook 取址、辅助校验与完整类型 include；同步静态检查和状态记录。

## 当前绑定

```cpp
intptr_t frame=NativeAddress(&GameWorld::_NV_mainLoop_GPUSensitiveStuff,"frame");
intptr_t pose=NativeAddress(&AnimationClassHuman::_NV_update,"pose");
```

NativeAddress 现在是成员指针模板，内部调用 KenshiLib::GetRealAddress(method)。frame/pose 只是日志标签，不参与目标查址。目标函数的 Windows 修饰名查询已从插件源码中删除。

证据：
- Include/core/Functions.h:12–17 明确提供 GetRealAddress(&Class::function) 用法，模板按 void*& 获取 VC100 成员指针首字；不支持虚函数指针。
- Include/kenshi/GameWorld.h:196 声明非虚 _NV_mainLoop_GPUSensitiveStuff(float)。
- Include/kenshi/Animation/AnimationClassHuman.h:23 声明非虚 _NV_update(float)。新增完整类型头文件避免只对前置声明取址；该类单继承 AnimationClass。
- Source/core/Functions.cpp:140–175 在非桩地址时会触发 assert_release；不能删除前置校验。

本插件先检查成员指针大小与当前单继承 ABI、已加载 KenshiLib.dll 和 FUNC_BEGIN/FUNC_END 桩表范围，再将原成员指针交给 SDK。这里只按固定标记查询桩表边界，不查询目标函数名，也没有数字 RVA 或字符串回退。无效布局、空指针、非桩地址以及空目标均抛普通异常，走原 plugin_disabled 路径；每个绑定只记录一条 native_binding method=...。

如果工具链仍产生插件内导入跳板，校验会拒绝该地址，不会继续触发原致命断言。这属于失败保护，不能据此声称钩子运行成功。现有工程已经 WholeProgramOptimization=true、LTCG、LinkIncremental=false；本轮未修改工程设置。必须由用户编译后的 DLL 和启动日志证明最终地址实际落在 KenshiLib 桩表内。

## 验证

docs/verification-address-binding-20261008.json：
- 与本轮修改前双备份作整个 C++ 文件比较，除绑定 helper、两处调用、完整类型 include 及相关注释外逐字一致。
- 桩表校验、成员指针布局校验、日志上界、SDK 调用顺序等专项静态检查 10 项通过。
- 原有 1,346 项基础、特效、移植、时间和骨架静态回归通过。
- 共 1,356 项通过；未编译、链接或游戏验证。

回归 tools/verify.py 改为检查成员地址式接口与前置防护；tools/verify_source_vfx.py 只精确排除本轮授权的两处取址变化，继续比对两条 AddHook、回调及错误处理。伤害、时间恢复、姿势和新增特效绘制保持不变。

检查时发现 bin/Release/JudgementCutEnd.dll 已由外部更新为 1.2.1-dev，SHA256 fdb879af92b834d1a57a3f52133d2e205a70649fe1f0ea2dff88a486a6854c8c，时间 00:54:50。只读 PE 检查确认 x64 和真实入口导出，但其日志标记仍是 native_binding export=，早于本轮 00:58:00 源码修改，尚未包含成员地址式修正。分发包和游戏内 DLL 仍为 1.2.0-dev，本轮没有复制 DLL。

## 编译与验收

用户重新编译 E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj，Release|x64 / v100。本轮遵循 code-modification-principles 和 AGENTS.md 的不代编译要求。

新产物应包含 native_binding method= 标记。启动后需要 frame 与 pose 两条有效绑定、plugin_ready，以及正常 frame_hook_seen；若出现 Native member address is not inside KenshiLib stub table，表示成员地址仍落在导入跳板，不应当作已解决，也不自动回退到修饰名查询。编译和运行是否成功目前未确认。

## 安全与逐文件记录

C++ 修改前双备份：
- D:\CodexBackups\JudgementCutEnd-AddressBinding-20261008-005800-837871\E\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp
- E:\AIWorkSpace\_backups\JudgementCutEnd-AddressBinding-20261008-005800-837871\E\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp

C++ UTF-8 BOM/CRLF 保留；检查器和文档 UTF-8 无 BOM/CRLF 保留。中文和乱码扫描通过。其他覆写文件各有唯一双备份，逐文件11字段记录位于 docs/JudgementCutEnd-AddressBinding-*，索引见 docs/address-binding-change-index-20261008.json。历史特效报告未覆盖。
