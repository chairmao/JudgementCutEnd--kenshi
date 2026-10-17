# 授权与来源

插件源码及工具采用 GPL-3.0-or-later；KenshiLib 链接要求仍适用。

1.2.0 的 jce.clip 是 ap05《Judgement Cut End - ap05's Remake》的 HKX 动作重定向结果，不能再标为本项目原创动画或 CC0。来源：https://www.nexusmods.com/skyrimspecialedition/mods/76068 。作者允许署名修改、跨游戏转换和非商业使用；该声明不替代原包中其他作者资产的许可。本次没有复制 NIF、DDS 或原 HKX 到运行包。

jce_phantom.bin 的通用人形拓扑由本项目独立制作，其动作帧使用上述重定向结果，因此完整烘焙资源同样保留 ap05 来源限制。不是施放角色外观/装备克隆，也不是 Capcom 官方角色模型。
本项目原创裂痕布局、灰雾/裂光纹理及局部折射 shader 可按 CC0-1.0 使用；不能把这个声明扩展到参考动作或声音。

jce_sequence.wav / jce_sequence_fast.wav 沿用已有五段参考 WAV 的混音/三倍时间线，非原创/CC0。本轮没有新增参考声音；原包列出的 DMC5 等声音来源保留，项目仍用于本机测试。来源与哈希见 docs/audio-provenance.json 和 docs/fast-audio-provenance.json。

骨架尺寸/名称仅用于适配；Kenshi 与 XPMSSE 的原骨架文件没有进入运行包。源/输出校验和与骨名映射见 docs/retarget-provenance.json。
解码使用 PyNifly 的 GPL-3.0 Python 源码，放在 Codex 工作域并保留许可证；游戏运行不依赖 Python、Blender 或 Skyrim。
本作品不是 Capcom 官方内容，不能承诺与 DMC5 原版逐帧一致。

2.9.0-dev验证版的jce_facets29.csv包含上述ap05模组JCE030CutRefraction.nif的screen1、slash3、slash5几何转换数据（位置、法线、UV、三角索引及尺度键），因此不是原创或CC0。BG3维吉尔模组提供生命周期曲线参考，来源包与组件哈希见docs/source-facets-2.9；本轮未复制BG3模型/贴图。原NIF/DDS/HKX仍未直接进入包。源引擎完整材质响应未还原。

## 2.9.1 光学遮罩

新增 jce_source_optical_mask.dds 按字节取自 ap05 源模组的 fxglowspotlinearalpha.dds，仅使用 Alpha，不解释成法线。尺寸与24px一致偏折是 Kenshi 适配；不代表已还原 Skyrim/BG3 原材质。原第三方资源许可与公开分发限制继续适用。
