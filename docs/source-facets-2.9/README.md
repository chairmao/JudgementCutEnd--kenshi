# 2.9.0-dev：三张源网格的空间光学验证

本轮先保留已安装2.8.4，再改变空间折射生产结构。验证版不扩增刀光、亮线、噪声或粒子数量；只用三张源网格观察独立空间位置、源法线与生命周期是否能提供更可靠的空间切裂感。它是小规模验证，暂不宣称完整半球大片已经复刻。

## 保留版本

归档：E:\KenshiProject\2.Projects\JudgementCutEnd\releases\JudgementCutEnd-2.8.4-retained-20261009-231339-4f896e.zip

SHA-256：BEABCAEDEF456DC65568AB291CBE47AD8813D0D553AA52CAAA4D007E1E5438F8

归档包含839个源工程/项目分发包/已安装mod文件及逐文件清单，ZIP CRC与所有清单哈希通过。排除IDE缓存、构建obj和既有releases，避免嵌套归档；当前运行包没有遗漏。已安装mod的工坊介绍、ID、配置与DLL原样保留在installed-game-mod下，便于准确回退。

初始双备份：

- D:\CodexBackups\JCE-SourceFacets29-20261009-231339-4f896e
- E:\AIWorkSpace\_backups\JCE-SourceFacets29-20261009-231339-4f896e

中间生命周期适配与除数保护的双备份见本任务report-lifetime和report-duration文件，均在D:\CodexBackups与E:\AIWorkSpace\_backups。

## 真实参考与适配

Skyrim：E:\skyrimspecialedition\mods\Judgement Cut End - ap05's Remake\Meshes\effects\AP05\JCE030CutRefraction.nif

源NIF哈希：20f12b7ab7156ebc4767630499994a20ec1fda35fb1c238a4c0651c687f4a942

本轮重新只读解析原NIF，与已有取证逐字一致。screen1是较宽的薄网格，slash3和slash5是薄切割网格；三张均24顶点、12三角形。保留实际位置、UV、法线、三角索引和对象旋转；Z-up转Y-up伴随反射，三角索引同步倒序。没有生成随机多边形、镜框或新面板形状。切线与完整LightingShader/法线贴图响应尚未接入。

所有网格使用同一半径适配比例，保留源相对尺度/位置/朝向；最大源顶点距离归一为0.78半径，公共高度为0.28半径。施放时仅再乘角色朝向，网格不朝向相机重建。源码中的生成矩阵与来源值在source-provenance.json可核对。NiTransformController的尺度替换对象静态scale，不能再次乘静态scale。

screen1原尺度控制器只有很短的显露脉冲，随后长期为0。为验证持续宽面的光学响应，本版明确保持其源峰值几何，改用BG3持续包络控制停留；原尺度键完整留在原NIF取证中。slash3/slash5继续采样原尺度键。这是适配，不是源动画逐帧照搬。

BG3：E:\次元斩绝中的维吉尔模组已解析组件。中期参考组件31 SpaceDebris（2.450382~5.664122）的Alpha 0.283871→0.2129032；退场参考组件24 SpaceWarp1（3.353046~6.246176）的Alpha 0.1354839→0.1416129→0，关键帧归一时间0、0.8229692、1。逐曲线按峰值归一化，再映射到本演出的停留/退场；组件原时间与生命周期映射分别记录，不能当作完全相同的时间线。使用线性键采样；未复制BG3未知依赖材质、粒子数量或模型。

## 原生与着色器合同

- 原生只改JudgementCutEnd.cpp中的源特效读取、OpticalVertex/SpatialFracture和相关版本日志。其余代码按恢复授权块的方式与2.8.4基线逐字核对一致，包括伤害、U键覆盖重施放、三倍播放、动画、相机、时间恢复、HDR复制和资源清理。
- 三张网格分别关联原刀路0/24/48与源强度曲线8/2/4，出生受实际刀路控制；各自退场从SHEATH加0/0.024/0.048剪辑秒开始，5.9剪辑秒前清空。宽面持续包络、切割面尺度与强度均独立处理。
- 收刀沿源面积最大的表面法线作0.025半径的有界分离。这是Kenshi适配距离，没有读取到相同的源物理位移参数。无随机旋转或掉落实体。
- 新顶点合同是POSITION/NORMAL/COLOR/UV4，NORMAL来自源网格；HDR失效后的零Alpha占位也保持该声明，避免BeginUpdate改变顶点布局。UV4仍携带源UV、剪辑秒和半径。COLOR仅携带包络/强度，不染场景RGB。
- 独立视图位置/法线驱动受限屏幕折射。折射率1.06、像素比例0.05为Kenshi适配值，不能称作Skyrim/BG3原材质参数。仍只读一次已有HDR副本、保留36像素上限、半球裁剪、世界深度与UV边界。源UV已保留，目前没有法线纹理采样。
- 只输出偏折后的场景颜色，没有新增蓝幕、灰底、发光边框或裂线。保留已有刀光/蓝雾等其他层。
- 三张远到近的排序使用固定栈数组，无每帧源数据加载、材质复制或额外纹理。只是按网格枢轴排序；相互穿插面的完整逐像素透明排序尚未实现，需实机看重叠结果。
- 新固定预算72顶点/108索引，较原四边形增加68顶点/102索引；总上界19164/46890，仍低于32768/49152。源网格法线引入每顶点新属性；像素着色器不再循环八个屏幕分区，但三张网格可能产生重叠，不能仅凭算术量断言帧率改善。

## 验证

27015项非编译检查通过，含保护文件/游戏目录哈希、归档清单、NIF几何/UV/法线/索引身份、BG3曲线身份、三视角/三朝向/三分辨率的生命周期与光学边界、HDR失效、背面透明、零持续时间和损坏合同拒绝。模型采用源顶点和近似视图光线偏折；未执行C++/GPU、实际场景深度或纹理采样，也不能通过它证明三张裂面一定在游戏中显眼。

正式记录：D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-SourceFacets29-20261009-231339-4f896e\verification-final.json

## 编译与小规模验收

本轮按项目规则未运行编译器。用户编译JudgementCutEnd.vcxproj，Release|x64（v100）；输出E:\KenshiProject\2.Projects\bin\Release\JudgementCutEnd.dll。原生日志版本为2.9.0-dev。分发包中的DLL仍是旧2.8.0-dev，暂不具备部署条件；Stage工具已有版本字符串检查，会拒绝旧DLL。

新DLL必须与jce_facets29.csv、jce_facets29.hlsl、jce_facets29.program、jce.material一起更新。当前游戏mod目录保持2.8.4，尚未部署。

建议先在有建筑/植被参照的室外测试几次，分别使用低、中、高视角，并在中期转动相机。观察一张宽面和两张切割面是否有不同深度/偏折，原场景是否变成灰玻璃或出现重影，收刀是否分离清空。通过后再决定是否增加来源明确的片面；本版不为填满350半球复制大量网格。

日志source_facets_ready证明资源合同读入；spatial_optics_active每次施放只出现首次有效一条，标记camera_billboard=0、vertex_normals=source、CPU_submit_ms和GPU_ms=unmeasured。CPU提交耗时不是GPU耗时，实际性能需相同场景/相机下对照帧时间。只读日志不等于目视效果确认。

全部已有文件修改前双备份；C++保留UTF-8 BOM/CRLF，其余资源与新说明为UTF-8无BOM/CRLF，中文读回检查通过。
