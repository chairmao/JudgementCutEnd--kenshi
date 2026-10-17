# 2.9.6-dev：五裂面的内容映射与遮挡改善

用户要求：28A5DE视频仍看不清空间破裂，继续修改现有特效。

## 证据与判断

- 视频已抽取82张预览帧并看原分辨率2秒画面：多次施放时刀光连续，细小背景偏移难辨。
- 2.9.5日志证明五片提交到渲染回调，但仅有遮挡/遮罩前CPU包围盒；不证明五片实际可见。
- 原代码把折射section3排在100，其余自有视觉段101..110；背景副本在首个自有段前捕获。故后绘制刀光/烟层不参加裂面错位。
- 原294着色器每片只算一个屏幕平移向量。CPU面在偏转，但画面内容不随位置产生对应的偏转。结合视频，判断这两项是辨识度不足的因素；尚未进行改版GPU验证。

## 实现

1. 五片各保存出生时未偏折的局部参考位置/朝向。每个顶点追加第五组UV（float3），由296 VP用同一worldViewProjMatrix投影成float4参考坐标。FP透视正确插值后除w，以当前像素反查参考画面，得到随面内位置变化的内容映射。
2. 独立模式3/4的section3优先级111，其他自有段仍101..110，全部先绘制。只在section3实际渲染入口复制一次HDR；副本同时包含本帧背景与已绘制的刀光/蓝雾，随后让它们一起产生局部错位。副本不包含本次折射输出，避免同帧自反馈。
3. 总采样位移仍按viewport缩放，最大36像素；两次纹理采样、单HDR副本不变。参考点在相机后方回退原偏折，半像素范围夹紧。不是屏幕回读、全屏染色或新增裂线。
4. 同步新增296 HLSL/program，材质只替换Refraction的两处程序名。原294与历史版本清单保留。DLL与这些assets必须配套更新。
5. 限量阶段日志追加reference_warp_vertex_max_px（参考映射的顶点幅度，未裁总预算/未测遮罩和深度），每次施放最多25条阶段记录；不可称为GPU实际偏移或可见像素。

位置、大小、五片数量、源网格/遮罩、刀光/雾颜色、出生/退场时钟保持2.9.5。未改伤害、武器取值、按键、姿势动画、世界时间恢复、native hooks、配置或存档。旧模式0/1/2仍先折射再视觉，且负揭开标记跳过新参考映射。

这是Kenshi中对两份参考模组的适配，不声称复制Skyrim/BG3原始旋转键或完整渲染管线。

## 验证与边界

- 全文隔离检查：除明确光学范围、版本字符串与Draw诊断外一致。
- 39个保护函数逐字一致，包括CaptureBackground、PrepareRefraction、ReleaseRefraction、伤害/输入/时间恢复、蓝雾/刀光生产函数。
- CPU五组UV → VP第五组输入 → FP参考clip坐标匹配；失败透明占位也使用同一声明。
- 五种模式队列/复制入口配套。透明队列实际驱动行为仍须游戏日志与画面确认。
- 真实网格生命周期采样仍在球内、地面以上；120顶点60三角，额外1440字节参考坐标，生命周期6.45剪辑秒归零，END6.7不变。
- 5种viewport、5000组合位移样本满足36px最大预算与采样边界；800项透视插值数学样本吻合参考表面，出生参考映射恒等误差0。此数学模型不等于真实游戏GPU测试。
- 其他项目文件及游戏mod目录哈希未变（运行日志排除）。素材与材质hash写入assets/vfx-2.9.6.json。
- 编译、HLSL编译、游戏性能/可见性：未执行，遵循项目和Skill的不代编译规则。[MISSING] 改版GPU实际画面、遮挡后的五片面积、帧耗时。

## 下一步测试

用户编译 E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.vcxproj，Release|x64（v100）。产物 E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll。

编译后需一起更新DLL、jce.material、jce_facets296.hlsl、jce_facets296.program、vfx-2.9.6.json。当前游戏仍为2.9.5，这轮未部署。不要单独把新版材质交给旧DLL；第五UV是配套合同。

建议对同一场景、固定镜头施放：观察初斩逐片揭开、中期刀光是否在各面内出现不同方向偏折、收刀分离后是否完整消退。无需改强度/颜色或增加亮线。日志应显示2.9.6-dev、visuals_then_refraction_snapshot、reference_to_current；检查无vfx_queue_error/refraction_capture_disabled及shader加载错误。背景复制一次/帧、时间恢复仍需运行日志验证。

## 安全与逐文件报告

已有源码与材质双备份：
- D:\CodexBackups\JCE-FacetClarity296-20261010-191843
- E:\AIWorkSpace\_backups\JCE-FacetClarity296-20261010-191843

源码UTF-8 BOM/CRLF保持；材质UTF-8无BOM/CRLF保持；新增文本UTF-8无BOM/CRLF。写后扫描无新乱码，保护函数中文逐字保留。

报告目录：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-FacetClarity296-20261010-191843。
report-01（C++）、02（HLSL）、03（program）、04（材质）、05（版本清单）、06（本说明），各自包含File/Role/Code location/Before/Changes/Reasons/After/Impact/Validation/Safety/Unresolved。每个文件写入后立即保存单独报告。验证结果verification296.json。
