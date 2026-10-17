# 0.2.3 修正记录

用户反馈：自由相机正常；人物僵硬向前平移；斩击范围至少五倍；视觉太淡。

直接证据：runtime-0.2.2.log 中 cast=1 的 hand_local 前向坐标0.652626、45.5722、91.3941、136.039；matrix_error=0.888132..2.85664。cast=5同类漂移。不能据日志单独判定上游位移是哪段游戏动画。
本机运行库sha256=7d3888d21398647519f10a89b1f300d8606f761ad159e6021a797b1b9b3df5f6。
ogre-consumer-disassembly.txt保留本机updateAnimation、cacheBoneMatrices和OldNode位置函数。updateAnimation+0x6E先测试skip；true跳过cache调用。cacheBoneMatrices+0x4B测试skip；true只绕过原生AnimationState重放，随后仍调用骨矩阵生成。
纠正此前判断：dirty+_updateAnimation在skip=true下不能发布身体矩阵。现在先显式cache再dirty+_updateAnimation，保存并恢复skip。导出名称解析，不在运行代码写死本机RVA。

源代码0.2.3持有受控23骨骼的局部位置和朝向；每次覆盖前记录当前位置漂移，再重新写入快照；恢复时同时还原。未改角色逻辑位置、场景位置、相机或其他骨架/共享动画资源。
包配置Radius=150，上限300；同参数驱动敌对检索与视觉。宽度随半径同比变为五倍；HDR浮点uniform四倍；顶点颜色钳制；裂痕保持到收刀0.65秒淡出。默认目标上限32和伤害数值保留，几何预算保持。
原始动作轨道/音频/贴图未修改。该版本还未执行宿主C++，不能保证动画外观已达到用户要求；需自由视角实测手臂、刀鞘、腿部、重复施放与Esc恢复。

111项非编译检查见verification-0.2.3.json。包含实际PE导出/分支字节、同帧与跨帧缓存消费模型、位置累加后归位模型、材质shader参数合同、输入/自由相机/资源/有界日志等。
现用游戏DLL仍0.2.2，不做部分部署；用户编译JudgementCutEnd.sln Release|x64后整体安装。

所有旧文件覆盖前双备份，详见本目录逐文件JSON报告；verify.py的解析/字节签名修正在相邻VerifyRepair/VerifyBranch目录另有备份报告。源码UTF-8 BOM/CRLF，其余修改文本UTF-8无BOM/CRLF；写后读回及中文乱码检查通过。
主备份D:\CodexBackups\JudgementCutEnd-RootVFX-20261007-164157-081257；第二份E:\AIWorkSpace\_backups\同名目录。
