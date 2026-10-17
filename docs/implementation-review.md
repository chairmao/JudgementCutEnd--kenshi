# 实现审查与证据边界

本版是原创骨骼姿势层与实时演出插件，不是共享动画缓存补丁。它不修改原版 `.skeleton`，也不向 Skeleton resource 插入/删除动画；只控制当前施法者 OldSkeletonInstance 的 10 条骨骼轨道。

## 入口与线程

- `JudgementCutEnd.cpp:368`：`startPlugin` 原子防重复、初始化本插件日志/轨道/配置，通过 KenshiLib 解析两个原生函数入口；任一安装失败保持 ready=0，已经挂上的钩子只调用原函数。
- `JudgementCutEnd.cpp:359`：GPU-sensitive 帧入口调用原函数之后执行 Tick。SDK 签名为 GameWorld*,float；本机原生函数有 AI/render 同步屏障。但其所有调用时序未在运行中确认。
- `JudgementCutEnd.cpp:347`：非施法者直接通过；仅受控角色用 gate 串行化原生 update 与本插件姿势覆盖，且只在已记录渲染线程进行覆盖。不同线程首次记日志，0.5 秒未观察到正常回调就取消。
- 本机二进制显示 updateAnimationTransforms 是空函数，已弃用。Human update 在 0x5C4CC9 调用 thunk 0x3DD16，转到 AnimationClass update 0x5B5E30；本版以 `_NV_update` 为入口。详见 native-evidence.json（诊断 RVA 没有硬编码进源码）。

## 动作与资源合同

- `JudgementCutEnd.cpp:95`：轨道格式 JCECLIP v1；时间必须覆盖 0–6.7 秒，顺序严格递增、四元数有限且单位化，无重复/root 轨道；裂痕 JCESLASH v1，布局最多 192 条。
- `JudgementCutEnd.cpp:214`：initial orientation × 插值局部增量。403 帧由 author_assets.py 对 Kenshi 的骨架制作；不使用 HKX 解码器。角色根位置、腿部、骨长、缩放不属于本姿势控制。
- `JudgementCutEnd.cpp:261`：残影位置经骨骼派生局部坐标→角色节点变换→场景坐标，再减去锚点；使用游戏场景原点补偿。
- `JudgementCutEnd.cpp:163`：特效放在 83 队列，本机 compositor 的 HDR 粒子通道为 82–85。材质引用宿主 Basic_Coloured_Texture_VP/Basic_Texture_FP，采用有深度遮挡的加法混合。原生着色器文件未复制。
- preview/index.html 的内嵌数据与 scene.json、jce.clip 完全相同；预览的简化骨架线条是资源数学检查，不是游戏截图。

## 时间与伤害

- `JudgementCutEnd.cpp:313`：QPC 实时时间推进演出，世界速度只是模拟时间倍率。目标在 2.35 秒快照、5.15 秒结算；damageDone 在循环前置位。大于 1.5 秒卡顿直接取消，避免回来补击。
- `JudgementCutEnd.cpp:220`：256 个查询对象上限，目标最多配置上限 32（可调到 64），只存 serial hand，过滤玩家/非敌人/不在范围/失效目标。
- `JudgementCutEnd.cpp:233`：结算前重新解 hand 和验证敌对/位置；调用原生 MedicalSystem::addWound，不写 HP、不调用需要 CombatTechnique 的接口。返回身体部位写入日志；伤害引用参数值不能单独证明护甲或犯罪语义。
- 一次演出不能让角色完整 AI/物理独立于世界慢放运行。自身姿势按实时播放，其他模拟仍会受慢放影响；没有基于物理光柱命中决定身体部位。

## 生命周期与有界开销

- `JudgementCutEnd.cpp:166`：先检查角色/骨架与其他手动骨骼所有者；准备本场景资源后发布 poseOwner。发布后异常可走恢复；同一 Runtime 同时只执行一个演出。
- `JudgementCutEnd.cpp:197`：只在世界、角色、动画实例仍匹配时恢复骨骼；仅当前速度仍等于本插件的 slow 才恢复旧速度。用户变速/暂停优先，不向旧 GameWorld 写值。
- `JudgementCutEnd.cpp:190`：同一有效场景里销毁 ManualObject/SceneNode。场景已被宿主替换时丢弃旧指针，不试图销毁失效场景中的对象；依赖宿主场景析构清理旧对象，此生命周期须实测。
- 镜头仅在相同 SceneManager 与 camera 对象上恢复；音效由 WinMM 播放，结束停止已启动音效。WinMM 是进程通道，其他插件采用相同 API 时可能冲突。
- 轨道/配置与资源组是插件进程生命周期缓存；不是每次施法新增。每次对象、目标与残影在结束清空。默认 96×2 裂痕光带 + 64 环段 + 不超过 9 份×14 边残影，约 1540 顶点/2310 索引，上界按资源文件 192 条裂痕则约 2308/3462；8192/12288 是预分配估计，不是性能实测。
- 日志仅生命周期、命中与约每 2 秒演出摘要；单进程 4096 条，上限耗尽后不再写；保留原日志与一个轮转文件。Runtime 与资源组驻留到进程结束，无运行中卸载功能。

## 已验证与未确认

52 项静态/格式/数学检查通过；PowerShell AST 通过；浏览器预览无页面错误。原生函数、导出表、本机游戏/依赖哈希及渲染队列有直接文件证据。

[MISSING] C++ 实际编译、实际安装 DLL、皮肤网格对手动骨骼的消费时序、原生 update 回调线程、摄像机跟随系统干预、动作与真实武器外观、伤害与护甲/犯罪结果、场景换区时对象析构以及长期内存/性能测量。若不同线程更新使 pose_thread_mismatch 出现，本版选择取消，不声称支持该运行路径。普通 C++ 异常捕获不处理所有 SEH/访问冲突。

下一步由用户编译 JudgementCutEnd / Release|x64；按 README 的演出→取消/恢复→伤害→重复施法顺序验收，再用具体日志处理失败。现在不能用代码行数、预览或静态检查数量代替实机有效性证明。
