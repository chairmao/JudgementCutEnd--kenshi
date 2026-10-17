# 1.2.0-dev：真实动作重定向与局部空间折射

当前为源码及资源交付：没有代编译、没有安装新 DLL；游戏仍安装已由用户编译的 1.1.2-dev。冻结 1.0 文件与 ZIP 保持不变。

## 已实现

来源为 [ap05 的公开重制](https://www.nexusmods.com/skyrimspecialedition/mods/76068)，使用用户已有本地 HKX，未从未知下载页获取游戏提取包。
实际解码 Havok 2010.2 的 7 秒、211 帧、242 轨动画。按标准骨名取 23 根骨，计算源/目标全局基准与层级差异，再输出 Kenshi 局部旋转；403 帧、60 Hz、6.7 剪辑秒。原来的原创 IK 资源被真实 HKX 重定向取代。
去掉源 COM 的水平瞬移，仅在 Bip01 添加足底高度修正，其他骨的位置通道为零。源隐藏/瞬移阶段旋转最大跳变约83°/帧，转为持续可见演出后做720°/剪辑秒角速度限制，避免甩动。因此这是移植适配，不是原文件逐帧照搬。
男/女骨架控制骨名核验通过；初始局部朝向最大差异约7.04°，运行时使用角色自己的初始朝向及根骨高度比例。女性及自定义体型的姿势/足底仍需实机确认。

幻影由198顶点、256三角的人形和长衣摆网格组成，按重定向动作逐帧烘焙；沿16条刀路掠过，每路最多4重残影，同时上限32个。不会新建NPC、不复制共享动画缓存；它是通用轮廓，不是角色装备外观克隆。

灰雾、96条裂痕的6层平行运动拖尾、192个瞬态光学片区保留。第四材质层在本插件首段绘制前复制当前HDR目标到自有纹理，用屏幕坐标采样副本，造成局部背景错位与灰色分光。不是实体镜子，不产生落地模型。
只在主相机queue83提交；使用深度测试，每帧最多一次GPU CopyResource，无CPU回读。源/目标宽高、格式、mip、数组、MSAA必须一致且不能同资源；不支持或窗口尺寸变化时关闭折射，其余层继续。失败时第四层写透明占位，避免空几何中断演出。纹理、COM getter 引用与监听在退出时回收。未修改游戏公共材质、相机或compositor。
离线Canvas预览只展示姿态/几何/气氛；没有游戏HDR背景，不能据其证明折射在游戏可见。

## 保持的行为

单键U、无冷却、施放中再次U覆盖；自由视角。
固定350水平圆与圈内敌对目标最多96次100%原生武器伤害、原生部位判定与大踉跄。
三倍演出速度、已有音轨、独立时间所有权及暂停后恢复。
这些输入、时间线和伤害分支有冻结基线/时间恢复回归核验。

## 成本与边界

有界最坏18348顶点、45378索引，低于既有32768/49152预算。只读烘焙网格959092字节。
独立HDR副本每像素4字节，1080p约7.91 MiB，4K约31.64 MiB，加渲染目标/SRV开销；仅施放期间逐帧复制，结束删除自有管理器项。上限4096×4096；不能根据静态核验推断实际帧率或显存回收。
新HLSL尚未由游戏编译，新增native虚接口与渲染路径尚未实机验收。核对本机导出和SDK声明只能减少接口错误，不能替代用户编译和游戏测试。

## 编译与安装

用户编译 E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.sln，Release|x64，v100。本轮没有执行编译器或链接器。
成功后正常退出游戏，运行 tools/Stage-LocalMod.ps1 -Mode Install，整包复制DLL与新资源；不要仅替换材质/动画。脚本先检查PE入口、源码版本标记与时间戳；当前旧1.1.2 DLL已实际被拒绝，未复制任何游戏文件。
日志应出现 version=1.2.0-dev、animation=ap05_HKX_retarget、resources=4，以及 refraction_prepared / refraction_capture_ready；有 refraction_disabled 或 refraction_capture_disabled 则本场仅关闭折射。
实机从自由视角确认拔刀/收刀与人物形态、灰雾/背景错位、结束/取消/失焦/暂停解除后速度、连续U及结束后显存/帧率。

## 可重放资源生成

Python与解码器在工作域，本机目录：
D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCEAssetPort-20261007
工具入口 tools/author_port.py --decoder <上述目录>；使用用户本地 HKX、XPMSSE 骨架与 Kenshi 骨架，不写游戏目录。运行前校验解码器 SHA。
解码器源：[anim_skyrim.py](https://raw.githubusercontent.com/BadDogSkyrim/PyNifly/main/io_scene_nifly/hkx/anim_skyrim.py)、[anim_fo4.py](https://raw.githubusercontent.com/BadDogSkyrim/PyNifly/main/io_scene_nifly/hkx/anim_fo4.py)，准确路径/校验和以工作域已保存文件和 docs/retarget-provenance.json 为准；main若变化需保留已验证的副本，不静默升级。
无需为了游戏运行安装这些工具。
