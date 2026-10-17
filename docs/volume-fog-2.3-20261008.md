# 连续蓝雾2.3：视频复核与待编译修正

已看用户8.61秒视频40680D~1.MP4（2560×1440），抽取4FPS联系表与2.55秒全帧。
帧目录：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCEFogVideo-20261008-1235

视频中角色周边透明，远右侧出现孤立亮蓝块；主斩击期间没有连贯卷烟。
安装shader哈希与r2一致，12:34日志显示剪辑时间推进至6.09秒，结束后速度恢复1；没有据此判为时间冻结。
上一版仅验证纹理随时间变化，遗漏了实际云片的空间覆盖，所以数值运动不能证明形成了雾；本次纠正这一验证不足。

源码仅改HazeVertex/HazeQuad/Mist、SourceDust的强度、版本和一次性日志。
32个平行深度切片从远到近贯穿半球，像素共享连续局部密度场，以Beer-Lambert式Alpha累积。
四角不再挤回半球，实际透明边界由像素函数给出；场景深度检测保留。
这不是全屏雾、不是完整3D纹理光线步进，也没有增添永久实体。刀路尾烟降为四分之一。
U、96击医疗结算、350圆、骨骼姿势、刀光及时间恢复的代码在完整保护区核对中保持原样。

非编译检查：100项；五种相机位置、1445条视线，1403条进入雾体、19404个取样点均落入对应切片包围。
16/32/64片在均匀密度时累计Alpha相同；真实非均匀密度和薄交线仍有32片离散误差。
雾几何从384顶点/576索引降到128/192；总体上界17364/43902。
每雾片元仍3次纹理采样；连续覆盖更大，所以不能用减少顶点保证GPU更快。
球外/地下片元在采样前返回透明。真实GPU性能、透明物体排序和最终雾的观感尚未验证。

需用户编译：E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.sln，Release|x64 / v100。
输出：E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll。
然后用既有Stage-LocalMod.ps1整体安装，脚本会拒绝版本不符、比源码旧的DLL及游戏运行中安装。
本轮没有触发任何编译器，也未覆盖当前游戏2.2-r2文件或DLL；2.3资源与2.2云团DLL不能混装。

双备份：D:\CodexBackups\JudgementCutEnd-VolumeFog-20261008-124150-858878 和 E:\AIWorkSpace\_backups\JudgementCutEnd-VolumeFog-20261008-124150-858878；
边界早退追加备份目录同名加-BoundaryGuard。CPP保留UTF-8 BOM/CRLF，其它文本保留UTF-8无BOM/CRLF。
每文件详情见本次审计目录中的*-file.json。正式1.0/2.0档案哈希不变。
