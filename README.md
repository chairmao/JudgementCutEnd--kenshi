# 次元斩绝 · JudgementCutEnd

Kenshi 的独立技能模组（RE_Kenshi 插件）。参考《鬼泣5》次元斩绝的演出，把拔刀动作、淡蓝刀光、流动蓝雾、持刀掠影与空间切裂折射带进 Kenshi。

| 项目 | 值 |
|---|---|
| 当前版本 | 2.9.11 |
| 游戏 | Kenshi 1.0.65（Steam） |
| 加载器 | RE_Kenshi 0.3.5 + KenshiLib 0.5.0 |
| 工具集 | Visual Studio v100（VS2010），Release \| x64 |
| 许可 | 代码 GPL-3.0-or-later；本项目原创美术/音频 CC0-1.0 |

## 安装

**必须先装好 RE_Kenshi**（Kenshi 的插件加载器）。它不能由本模组替代，只订阅本模组不会让 DLL 生效。

1. 把 `package/JudgementCutEnd/` 整个目录复制到 `Kenshi/Mods/`
2. 在启动器里勾选 `JudgementCutEnd`，重启游戏

## 使用

- 选中一个符合条件的**玩家方人形角色**，默认按 `U` 施放，`Esc` 取消。
- 半径 350，每目标最多 96 次 100% 基准武器伤害，无冷却。
- 施放条件：玩家控制的人形（含人形机器人，不含动物）、四肢健全（原生或已安装义肢均算健全）、装备栏里有游戏原生选中的近战武器（背包里的武器不算）。
- 键位、半径、伤害与音效开关、踉跄力度在模组目录的 `JudgementCutEnd.ini` 里改，改完重启游戏生效。
- 完整玩法说明、边界条件与已知限制见 `package/JudgementCutEnd/WORKSHOP_DESCRIPTION.txt`。

## 从源码构建

1. 准备依赖并放到工程期望的位置（默认是本仓库上两级目录下的 `1.Dependencies\`）：
   - `KenshiLib_0.5.0\`：`Include\`（KenshiLib 0.5.0/0.5.1 头文件）与 `Libraries\`（`KenshiLib.lib`、`OgreMain_x64.lib`、`MyGUIEngine_x64.lib`）
   - `boost_1_60_0\`：`stage\lib\` 下已构建的 Boost 库

   路径不同就改 `JudgementCutEnd.vcxproj` 里的 `DepsDir` 与 `BoostDir` 两个宏，不要改动其它工程设置。
2. 打开 `JudgementCutEnd.sln`，选择 **Release | x64**，构建。
3. 产物 `JudgementCutEnd.dll` 输出到 `2.Projects/bin/Release/`，复制到模组目录覆盖同名文件即可。

工程固定使用 v100 工具集 + 全程序优化 + LTCG + 关闭增量链接。这几点不是可选项：KenshiLib 取成员函数地址依赖全程序优化，改掉会导致地址解析出错。

## 仓库结构

```
JudgementCutEnd.cpp / .sln / .vcxproj    插件源码与工程
package/JudgementCutEnd/                 可部署的模组内容（材质、HLSL、贴图、音频、vfx 数据、ini、mod）
docs/                                    开发、取证与逐版本变更记录
tools/                                   资源与特效作者脚本（Python / PowerShell）
```

历史发行包与离线预览因体积原因不随仓库分发（见 `.gitignore`：`releases/` 约 309 MB）。逐版本开发过程记录见 `docs/development-log.md`。

## 许可与来源

- 插件源码：GPL-3.0-or-later（与链接 KenshiLib 的要求一致），全文见 `LICENSE`。
- 本项目原创的动画、裂痕布局、渐变贴图与音效：CC0-1.0。
- 参考来源、明确未搬运的内容与许可边界：见 `LICENSE-NOTICE.md`。

本作品是非官方玩法移植，与《鬼泣5》及其权利方无隶属关系。
