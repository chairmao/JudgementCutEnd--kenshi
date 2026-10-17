# 0.2.5 武器准备修正（历史）

0.2.4日志反复收到U后提示Equip a melee weapon for weapon-scaled damage。0.2.5改为原生getThePreferredWeapon选择装备/手持武器，drawWeapon同步手持与CharStats缓存；未准备好只取消伤害资格，视觉演出保留，并按serial hand恢复插件拥有的拔刀状态。
用户于2026-10-07 18:13编译，18:15安装0.2.5，14文件核对一致，DLL SHA256=8cc8b1f637a89c5734b9c14ec2430c690b933a8a31adc732a4be406914690c56。
随后实测演出可以重复，但同一武器句柄比较错误造成damage_armed=0，因此0.2.5未完成伤害修复。0.2.6证据与修正见handle-compare-fix-0.2.6.md；不可把0.2.5安装或138项静态检查视为真实伤害通过。
