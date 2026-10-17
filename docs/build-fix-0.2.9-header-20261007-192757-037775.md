# 0.2.9 编译路径修正

用户编译日志：E:\KenshiProject\2.Projects\JudgementCutEnd\obj\Release\JudgementCutEnd.log，最后写入2026-10-07 19:25:13（Asia/Shanghai）。

直接错误：JudgementCutEnd.cpp(18): fatal error C1083: 无法打开包括文件kenshi/CombatClass.h。根因是本次新增include遗漏combat子目录；真实头文件为E:\KenshiProject\1.Dependencies\KenshiLib_0.5.0\Include\kenshi\combat\CombatClass.h。修正源文件include为kenshi/combat/CombatClass.h；工程IncludePath以依赖Include为根，无需修改依赖或工程配置。

此次保持源码版本0.2.9，96次100%伤害和大踉跄逻辑不变。tools/verify.py新增所有直接kenshi/core/ogre/mygui依赖头文件存在性检查，堵住此前191项行为/PE检查遗漏的头路径问题。192项非编译检查通过；CPP词法括号平衡、UTF-8 BOM/CRLF、中文乱码检查通过。status记录用户失败编译与修复后待重编译，已安装DLL仍0.2.7，未部署。

不编译：code-modification-principles规定“Never attempt to compile, build, link, or regenerate binaries during a conversation.” 用户需重新编译JudgementCutEnd.sln Release|x64；尚无修复后编译结果，不能认定不存在后续编译/链接错误。日志里的依赖警告本次未改，致命错误是上述C1083。

## 逐文件报告及安全

- [JudgementCutEnd_cpp-1fc9a690.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-BuildFix-20261007-192655-267651/JudgementCutEnd_cpp-1fc9a690.json)
- [verify_py-d287f34b.json](E:/KenshiProject/2.Projects/JudgementCutEnd/docs/JudgementCutEnd-BuildFix-20261007-192655-267651/verify_py-d287f34b.json)

每个改写文件都先双备份到D:\CodexBackups\JudgementCutEnd-BuildFix-*与E:\AIWorkSpace\_backups\JudgementCutEnd-BuildFix-*，保留原盘符与相对路径；CPP UTF-8 BOM/CRLF，verify.py与状态JSON UTF-8无BOM/CRLF，严格解码/写后读回/中文乱码扫描通过。未修改共享依赖、游戏文件、已安装DLL或其他项目。
