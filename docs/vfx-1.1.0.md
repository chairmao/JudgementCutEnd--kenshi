# JudgementCutEnd：1.0正式版封存与1.1特效开发

## 正式存档

用户明确指定当前可用版本为1.0正式发行基线。完整存档位于E:\KenshiProject\2.Projects\JudgementCutEnd\releases\1.0.0，ZIP位于E:\KenshiProject\2.Projects\JudgementCutEnd\releases\JudgementCutEnd-1.0.0.zip，SHA256为44f47c6ae17592d6f703e73ff5b263c7d143e7660fa78344638c270ed4ee9f9c。248个原始源码/资源/文档/运行文件逐文件哈希验证，ZIP CRC和内容校验通过。DLL原内部标识0.3.0和原始字节保持，发行标签1.0.0；没有篡改成品或声称重编译。release-manifest.json记录每个文件哈希；mod/JudgementCutEnd供回退，source供恢复源码。编译归档源码应先恢复到原工程路径，归档并未复制整个SDK。

## 用户要求与实现

原版要求：雾状蓝色粒子、沿十几条斩击路径掠过的挥刀幻影、空间像若干镜面被斩碎、结束碎片落地。开发版本1.1.0-dev补齐这些层次：

- 蓝雾：80个稳定布置的软边噪声云团，128个微光粒子；蓄势聚集、斩击维持、收刀下沉淡出。原创TGA纹理由四层确定性噪声制作，不是修改游戏公共纹理。
- 幻影：选择96条真实裂痕中的16条（每6条取一条）；同一路径有主影和弱拖影。每个幻影具有实体躯干、双平面肢体、头部、长衣摆、跨步与挥刀光刃，由本条进度共同控制。没有复制玩家共享动画骨架，没有创建游戏角色。
- 斩痕：保留原主刃，补6段锯齿和3条短分叉。位置/方向/长度/96条数量未变，出现时序从0.55剪辑秒铺开到2.2剪辑秒，全部仍在收刀前出现。保持三倍速度，未延长角色演出。
- 镜面：48个原创薄面分为192三角片，斩击到达时亮起断裂边；使用半透明蓝色面片、视角高光和镜片纹理。收刀时每片按自己的落地时间、旋转轴/方向解体下落，最终展开至施放平面。
- 圆界：所有新增视觉顶点经BoundFx复核水平350范围，光带端点预留半宽；不产生圆外伤害。医疗逻辑、玩家姿势、按键/变速/时间线均与封存源码逐区域对比一致。

这是根据用户描述重新制作的原创视觉层，不是提取DMC原版着色器、真实维吉尔模型、反射画面或物理碎片。蓝色持刀幻影是自制几何剪影。镜片最终落在施放高度+0.8的平面，尚未贴合坡地；所有临时图形在演出结束或取消时清理，没有持久落地物体。最终相似度及场景可辨识度必须实机验收。

## 渲染、资源与生命周期

沿用一个ManualObject与既有HDR队列83、主相机隔离、帧去重、灯光/阴影关闭和世界深度。对象包含Glow/Mist/Glass三段材质，均显式load并检查getBestTechnique，任一失败走已有Finish/ReleaseGraphics回收。场景销毁清空引用，不在错误世界恢复角色/速度。

最多16条幻影路径、80云团、128微粒、192碎片；每帧无新增游戏Entity或粒子系统，不添加钩子。全部效果位置由解析时间与固定种子计算。最坏预算11980顶点/17202索引，硬预留上限32768/49152；新图层有填充成本，预算并不等于帧率保证。

每演出新增阶段日志各一次：vfx_layers_ready（3层/各对象数量）、mirror_cracking、mirror_collapse、debris_landed；保留队列/渲染回调与4096行上限。debris_landed证明图形生成阶段到达，不证明最终像素可见。未改攻击部位选择、96次100%武器命中、大踉跄、范围350、U覆盖/无冷却或音效/原角色动画轨道。

## 验证

原有223项与新增34项非编译检查通过；Node语法及离线模型运行通过。模型检查77760个碎片顶点有限且位于350圈内、16条幻影事件、落地帧；纹理/材质引用、正式存档哈希、几何上界、原生伤害与控制保留均核验。完整结果：E:\KenshiProject\2.Projects\JudgementCutEnd\docs\verification-vfx-1.1.0-20261007-204455-014365.json。

浏览器离线预览实际检查了斩击阶段与落地阶段，蓝雾、镜面碎裂和落地片均可见。离线Canvas与游戏的材质/深度/曝光不同，这不是实机验证。预览可直接打开preview/index.html，或在本轮本地127.0.0.1:18771页使用时间滑杆/幻影/蓝雾/镜片开关。

依据code-modification-principles的“Never attempt to compile, build, link, or regenerate binaries during a conversation.”和项目AGENTS规则，没有运行C++编译/链接。用户编译JudgementCutEnd.sln的Release|x64；当前游戏DLL仍为已封存基线，未自动安装开发特效。

## 文件、备份与编码

修改JudgementCutEnd.cpp、tools/verify.py、package/JudgementCutEnd/assets/slashes.csv与jce.material、preview/scene.json与index.html、两个README、INI版本注释和task-status.json；新增author_vfx.py、verify_vfx.py、jce_mist.tga、jce_glass.tga、jce_shards.csv、vfx-1.1.0.json、验证结果/报告以及正式归档。

已有文件先双备份至D:/CodexBackups/JudgementCutEnd-VFX110-*或VFXAssets-*，镜像E:/AIWorkSpace/_backups下对应目录；逐文件11项即时报告在docs同名审计目录。源码保持UTF-8 BOM/CRLF，其余文本保留UTF-8无BOM/CRLF；新增TGA按32位BGRA二进制写入。读回一致、中文/乱码扫描通过。其他项目、依赖、游戏模组配置和存档均未修改。
