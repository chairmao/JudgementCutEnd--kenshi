# U无反应：成员指针布局拒绝修正（2026-10-08）

## 直接证据与原因

游戏插件日志：
2026-10-08 01:07:06.209 [JCE 1.2.1-dev] source_fx_assets_ready curves=6 textures=5 schema=JCEFXCURVES1
2026-10-08 01:07:06.217 [JCE 1.2.1-dev] plugin_disabled: Unsupported native member pointer layout

RE_Kenshi_log.txt:249–250 同时记录 DLL 已加载以及该错误。没有 plugin_ready、frame_hook_seen 或本次 cast_key_detected。源码 startPlugin 在 skin.Load / LoadAssets 后、AddHook 前调用 NativeAddress；因此插件未安装主循环与姿势钩子，U输入逻辑根本没有运行。CastKeyVK=85 与无冷却配置正确，直接失败发生在绑定初始化。

原因是上一轮新增的 sizeof(method)!=sizeof(stub) 检查错误地要求成员函数指针与 void* 等长。实际失败只证明两者不等；旧日志没有输出本机具体长度，不能虚构16或24字节。KenshiLib Include/core/Functions.h:15–17 的模板通过 (void*&)fun 读取首个地址字段，不要求成员指针总长等于8。更大的成员指针表示可包含继承布局信息。

## 本轮修正

仅修改 JudgementCutEnd.cpp 的 NativeAddress helper：
- 最低长度检查改为 sizeof(method)<sizeof(stub)，只拒绝无法安全读取完整首地址字段的表示。
- 保留 std::memcpy 读取首个地址字段以及 FUNC_BEGIN / FUNC_END 桩表校验。
- SDK仍接收原成员函数指针，目标仍是声明中的两个非虚_NV入口，未回退字符串函数签名。
- 不调用成员指针，不手动执行附加this调整；只解析当前声明类方法的原生入口用于Hook。
- 成功绑定日志增加 member_bytes 与 address_bytes，明确实际编译布局。
- 伤害、键位、动画、时间恢复、特效绘制、两条AddHook和回调未变化。

本次失败保护原意是避免坏地址进入SDK触发断言，但等长约束超出了SDK合同。这是本次修改造成的初始化失败，不能将其归因于用户按键、其他mod抢键或粒子特效加载。上轮1,356项静态检查没有证明ABI布局正确；本轮据真实启动错误纠正，并未把静态通过当作游戏成功。

## 验证与未决

docs/verification-member-layout-fix-20261008.json 中 check_count=520：
基础/光影273、新原纹理特效125、移植及已观察产物49、时间70、绑定范围/首字合同模型3，均通过。

整个C++ helper以外区域与本轮修改前双备份逐字一致。合同模型确认附加布局字节变化不影响首地址字段；模型不是VC100执行，也不能证明编译后的实际桩地址。

具体成员长度和/GL优化后的真实桩地址仍待新DLL日志确认。如果再次出现桩表外地址，需要依据日志继续定位导入跳板；本轮保留错误拒绝，未自动跳过SDK安全检查。五个原纹理层和凯瑟琳头部修正的画面亦尚待实际测试。

## 编译与部署

本轮没有运行编译器，也没有替换游戏DLL。请用户重新编译：
E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj，Release|x64 / v100。

目前游戏目录仍是上次编译的1.2.1-dev失败产物；版本号相同不代表已经含布局修正。新DLL需晚于本轮源码且不再含 Unsupported native member pointer layout 错误标记，成功日志须包含两条 native_binding method=... member_bytes=...，随后 plugin_ready / frame_hook_seen。编译后再核验、更新mod并测试U。

## 安全与逐文件报告

C++双备份：
D:\CodexBackups\JudgementCutEnd-MemberLayoutFix-20261008-011233-397410\E\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp
E:\AIWorkSpace\_backups\JudgementCutEnd-MemberLayoutFix-20261008-011233-397410\E\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp

C++ UTF-8 BOM / CRLF 保留，其他文本UTF-8无BOM/CRLF；中文和乱码扫描通过。tools/verify.py同步最低长度合同，docs/task-status.json将当前源码标为待编译、已安装产物标为非当前，历史安装/检查记录未覆盖。逐文件11字段报告在 docs/JudgementCutEnd-MemberLayoutFix-*。
