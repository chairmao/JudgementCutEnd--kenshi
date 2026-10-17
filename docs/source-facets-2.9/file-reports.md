# 逐文件报告

本轮运行文件修改范围：JudgementCutEnd.cpp、jce.material、LICENSE-NOTICE.md；新增jce_facets29.csv/.hlsl/.program和版本记录。每次已有文件写入前双备份，完整报告均保存于本任务目录。

## JudgementCutEnd.cpp

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp
- **Role**: 原生源裂面包络
- **Code_location**: SpatialFracture hold持续时间
- **Before**: 末刀at==SHEATH时可出现0/0
- **Changes**: 仅为hold包络除数设置0.001剪辑秒下界
- **Reasons**: 既有slashes格式允许at等于SHEATH，不应通过新视觉路径引入NaN
- **After**: 持续时间边界有定义，当前三刀时刻行为不变
- **Impact**: 不改资产格式或伤害事件
- **Validation**: 双备份和UTF-8 BOM/CRLF中文读回通过；数值边界检查随后执行
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-duration-20261009-233017-607666', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-duration-20261009-233017-607666'], 'encoding': 'UTF-8 BOM', 'line_endings': 'CRLF', 'before_sha256': '1702af6aee709f50d5d47edf041782a252d4b59e06bfb21920dff03412d90e70', 'after_sha256': '9b46fdd60e3543474b7ddcc419572b47e8c48a705b009a0ad717cd909095ad0c'}
- **Unresolved**: 编译/GPU/游戏仍待用户验证

## jce.material

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\assets\jce.material
- **Role**: 原生材质连接
- **Code_location**: JCE/Refraction pass
- **Before**: 旧2.8.4文件
- **Changes**: JCE/Refraction切换到三裂面程序，深度/混合/纹理绑定保持
- **Reasons**: 用户要求采用少量独立空间光学裂面并参照两个模组
- **After**: 三张源几何、视角法线折射与独立生命周期的验证资源
- **Impact**: 新原生顶点/资源合同，必须与2.9.0-dev用户构建一起测试；旧DLL不兼容
- **Validation**: 原始数据哈希、UTF-8/CRLF与中文读回通过；静态和模型检查稍后进行
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-20261009-231339-4f896e', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-20261009-231339-4f896e'], 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'before_sha256': 'F8DBA0EB73785CD11CFC9F78013DB712CF3A5E8594A3A11D49FCE75680866F4B', 'after_sha256': '9EFFF5BA42F9B90CE870FE5DB35242188D08C6B4DFE9D1879A6644075483FD0D'}
- **Unresolved**: 未编译与实机验证；参考引擎完整材质响应未还原

## jce_facets29.csv

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\assets\jce_facets29.csv
- **Role**: 源裂面与生命周期数据
- **Code_location**: 新资源
- **Before**: 不存在
- **Changes**: 逐顶点保留screen1/slash3/slash5，转轴、法线、UV、索引及NiTransform尺度键；BG3两条独立包络
- **Reasons**: 用户要求采用少量独立空间光学裂面并参照两个模组
- **After**: 三张源几何、视角法线折射与独立生命周期的验证资源
- **Impact**: 新原生顶点/资源合同，必须与2.9.0-dev用户构建一起测试；旧DLL不兼容
- **Validation**: 原始数据哈希、UTF-8/CRLF与中文读回通过；静态和模型检查稍后进行
- **Safety**: {'backups': '新文件无覆盖', 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'before_sha256': None, 'after_sha256': '88DDFD53FDFA25C9FDD538FD57680348043704270A0EC359AC0F483B81C97948'}
- **Unresolved**: 未编译与实机验证；参考引擎完整材质响应未还原

## jce_facets29.hlsl

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\assets\jce_facets29.hlsl
- **Role**: 独立空间源裂面着色器
- **Code_location**: 新资源
- **Before**: 不存在
- **Changes**: 源法线/真实深度/观察方向驱动受限折射，单次HDR采样，无新增染色
- **Reasons**: 用户要求采用少量独立空间光学裂面并参照两个模组
- **After**: 三张源几何、视角法线折射与独立生命周期的验证资源
- **Impact**: 新原生顶点/资源合同，必须与2.9.0-dev用户构建一起测试；旧DLL不兼容
- **Validation**: 原始数据哈希、UTF-8/CRLF与中文读回通过；静态和模型检查稍后进行
- **Safety**: {'backups': '新文件无覆盖', 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'before_sha256': None, 'after_sha256': '9F3711BB41A194773A137262425D2A9A0517609BB66E29F730E02959DC559B97'}
- **Unresolved**: 未编译与实机验证；参考引擎完整材质响应未还原

## jce_facets29.program

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\assets\jce_facets29.program
- **Role**: 新源裂面程序声明
- **Code_location**: 新资源
- **Before**: 不存在
- **Changes**: NORMAL+UV4接口和两种矩阵自动参数，复用t1与captureValid
- **Reasons**: 用户要求采用少量独立空间光学裂面并参照两个模组
- **After**: 三张源几何、视角法线折射与独立生命周期的验证资源
- **Impact**: 新原生顶点/资源合同，必须与2.9.0-dev用户构建一起测试；旧DLL不兼容
- **Validation**: 原始数据哈希、UTF-8/CRLF与中文读回通过；静态和模型检查稍后进行
- **Safety**: {'backups': '新文件无覆盖', 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'before_sha256': None, 'after_sha256': '8EA2ED256AE8BFA257C3289CCBFDDC563D517C7EDDDF370B2D6A41CCD464190F'}
- **Unresolved**: 未编译与实机验证；参考引擎完整材质响应未还原

## JudgementCutEnd.cpp

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp
- **Role**: 原生特效生产端
- **Code_location**: SourceFacetAsset/LoadSourceFacets、OpticalVertex/SpatialFracture、相关特效与版本日志
- **Before**: 旧2.8.4文件
- **Changes**: 新增严格源数据读取，三张源网格独立绘制、法线和生命周期；日志版本2.9.0-dev
- **Reasons**: 用户要求采用少量独立空间光学裂面并参照两个模组
- **After**: 三张源几何、视角法线折射与独立生命周期的验证资源
- **Impact**: 新原生顶点/资源合同，必须与2.9.0-dev用户构建一起测试；旧DLL不兼容
- **Validation**: 原始数据哈希、UTF-8/CRLF与中文读回通过；静态和模型检查稍后进行
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-20261009-231339-4f896e', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-20261009-231339-4f896e'], 'encoding': 'UTF-8 BOM', 'line_endings': 'CRLF', 'before_sha256': 'FA71E2314349604103D0D73CB07D7EE64C00EB57523D13F8EA76530120F2037D', 'after_sha256': '221DDE2EF3A74ED139253CA5E5CBDEE3813C26E6E8805FE17CEEEA67627C411E'}
- **Unresolved**: 未编译与实机验证；参考引擎完整材质响应未还原

## LICENSE-NOTICE.md

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\LICENSE-NOTICE.md
- **Role**: 资源来源说明
- **Code_location**: 追加2.9资源条目
- **Before**: 旧2.8.4文件
- **Changes**: 追加三张源网格转换数据来源与许可边界，保留原条目
- **Reasons**: 用户要求采用少量独立空间光学裂面并参照两个模组
- **After**: 三张源几何、视角法线折射与独立生命周期的验证资源
- **Impact**: 新原生顶点/资源合同，必须与2.9.0-dev用户构建一起测试；旧DLL不兼容
- **Validation**: 原始数据哈希、UTF-8/CRLF与中文读回通过；静态和模型检查稍后进行
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-20261009-231339-4f896e', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-20261009-231339-4f896e'], 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'before_sha256': '8015F5B7041394FA03DAE4FC1B8C3013796ECE87C38F119A486764799D5F4A50', 'after_sha256': '56EC43F6472C87ABA798197816A3916BD6F5420805F1EBB8797CCF3DD122257A'}
- **Unresolved**: 未编译与实机验证；参考引擎完整材质响应未还原

## jce_facets29.csv

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\assets\jce_facets29.csv
- **Role**: 宽面生命周期适配及证据
- **Code_location**: screen1尺度键/说明
- **Before**: screen1源scale在短闪后长时间为0，不适合持续宽面试验
- **Changes**: 仅宽面保持源峰值几何，以BG3持续包络控制透明度；原键完整保留在取证JSON
- **Reasons**: 读取NiTransformData确认短闪窗口约0.01~0.05源秒，直接照搬不能验证中期宽面
- **After**: 宽面可持续观察，另外两张保留原尺度键
- **Impact**: 显式时间适配，无新形状/噪声或颜色叠层
- **Validation**: 双备份、编码读回；完整检查稍后进行
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-lifetime-20261009-232359-084076', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-lifetime-20261009-232359-084076'], 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'before_sha256': '88ddfd53fdfa25c9fdd538fd57680348043704270a0ec359ac0f483b81c97948', 'after_sha256': 'fca82d54db3080c3f847a32091ac23060b76c9e02d7703b88177770d9e713fc3'}
- **Unresolved**: 游戏观感和GPU未验证

## JudgementCutEnd.cpp

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp
- **Role**: 宽面生命周期适配及证据
- **Code_location**: screen1尺度键/说明
- **Before**: screen1源scale在短闪后长时间为0，不适合持续宽面试验
- **Changes**: 仅宽面保持源峰值几何，以BG3持续包络控制透明度；原键完整保留在取证JSON
- **Reasons**: 读取NiTransformData确认短闪窗口约0.01~0.05源秒，直接照搬不能验证中期宽面
- **After**: 宽面可持续观察，另外两张保留原尺度键
- **Impact**: 显式时间适配，无新形状/噪声或颜色叠层
- **Validation**: 双备份、编码读回；完整检查稍后进行
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-lifetime-20261009-232359-084076', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-lifetime-20261009-232359-084076'], 'encoding': 'UTF-8 BOM', 'line_endings': 'CRLF', 'before_sha256': '221dde2ef3a74ed139253ca5e5cbdee3813c26e6e8805fe17ceeea67627c411e', 'after_sha256': '1702af6aee709f50d5d47edf041782a252d4b59e06bfb21920dff03412d90e70'}
- **Unresolved**: 游戏观感和GPU未验证

## source-provenance.json

- **File**: D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-SourceFacets29-20261009-231339-4f896e\source-provenance.json
- **Role**: 宽面生命周期适配及证据
- **Code_location**: screen1尺度键/说明
- **Before**: screen1源scale在短闪后长时间为0，不适合持续宽面试验
- **Changes**: 仅宽面保持源峰值几何，以BG3持续包络控制透明度；原键完整保留在取证JSON
- **Reasons**: 读取NiTransformData确认短闪窗口约0.01~0.05源秒，直接照搬不能验证中期宽面
- **After**: 宽面可持续观察，另外两张保留原尺度键
- **Impact**: 显式时间适配，无新形状/噪声或颜色叠层
- **Validation**: 双备份、编码读回；完整检查稍后进行
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-lifetime-20261009-232359-084076', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-lifetime-20261009-232359-084076'], 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'before_sha256': 'fb38ce7b01dd655964487016f66dc4430c4f9f18798232dc3db682ba0bfbc353', 'after_sha256': 'c54dd5807c8069d572075dbbbf8c1c41bf32e6db6ff5db3e35281c9b29b31ba3'}
- **Unresolved**: 游戏观感和GPU未验证

## README.md

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\docs\source-facets-2.9\README.md
- **Role**: 结构验证与测试说明
- **Code_location**: 新建2.9验证版记录
- **Before**: 不存在
- **Changes**: 说明三张源网格、真实来源与适配、验证限制、回退归档及用户编译步骤
- **Reasons**: 区分真实来源、适配及验证范围，防止旧DLL混装新顶点合同
- **After**: 用户可编译、核对来源与按步骤验证
- **Impact**: 说明/记录，不改变游戏
- **Validation**: UTF-8/CRLF与中文读回通过；生产端27015项静态/模型检查通过
- **Safety**: {'backup': '新文件，不覆盖既有版本', 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'sha256': 'BCDDE830FBFE5D76140FC2B4756B9E21C75DB4B6495CC02A2F77E26DC41329D9'}
- **Unresolved**: C++/HLSL未编译，GPU与游戏未测，游戏目录未更新

## source-provenance.json

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\docs\source-facets-2.9\source-provenance.json
- **Role**: 源网格和曲线证据
- **Code_location**: 新建2.9验证版记录
- **Before**: 不存在
- **Changes**: 保留NIF和BG3的哈希、实际组件值、统一缩放与宽面时间适配
- **Reasons**: 区分真实来源、适配及验证范围，防止旧DLL混装新顶点合同
- **After**: 用户可编译、核对来源与按步骤验证
- **Impact**: 说明/记录，不改变游戏
- **Validation**: UTF-8/CRLF与中文读回通过；生产端27015项静态/模型检查通过
- **Safety**: {'backup': '新文件，不覆盖既有版本', 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'sha256': 'C54DD5807C8069D572075DBBBF8C1C41BF32E6DB6FF5DB3E35281C9B29B31BA3'}
- **Unresolved**: C++/HLSL未编译，GPU与游戏未测，游戏目录未更新

## vfx-2.9.0.json

- **File**: E:\KenshiProject\2.Projects\JudgementCutEnd\package\JudgementCutEnd\assets\vfx-2.9.0.json
- **Role**: 新原生/资源合同元数据
- **Code_location**: 新建2.9验证版记录
- **Before**: 不存在
- **Changes**: 记录2.9.0-dev新DLL要求、源网格数量、哈希、验证与未安装状态
- **Reasons**: 区分真实来源、适配及验证范围，防止旧DLL混装新顶点合同
- **After**: 用户可编译、核对来源与按步骤验证
- **Impact**: 说明/记录，不改变游戏
- **Validation**: UTF-8/CRLF与中文读回通过；生产端27015项静态/模型检查通过
- **Safety**: {'backup': '新文件，不覆盖既有版本', 'encoding': 'UTF-8 no BOM', 'line_endings': 'CRLF', 'sha256': 'FAB48204927ADF2AA2D8BA24DEDD096A036AD5393293B9925AD0DE421B9FBB72'}
- **Unresolved**: C++/HLSL未编译，GPU与游戏未测，游戏目录未更新

## verify_source_facets29.py

- **File**: D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCE-SourceFacets29-20261009-231339-4f896e\verify_source_facets29.py
- **Role**: 源裂面非编译验证器
- **Code_location**: hold包络边界
- **Before**: 正常选定源刀路时刻的检查
- **Changes**: 镜像0.001除数保护并注入at==SHEATH；最终输出另存
- **Reasons**: 新生产端增加除数保护需要对应有效边界模型
- **After**: 正常矩阵和零持续时间均可核验，旧成功记录保留
- **Impact**: 离线验证；不执行C++/GPU
- **Validation**: 备份和UTF-8/LF读回通过；随后完整验证
- **Safety**: {'backups': ['D:\\CodexBackups\\JCE-SourceFacets29-verifier-20261009-233118-894768', 'E:\\AIWorkSpace\\_backups\\JCE-SourceFacets29-verifier-20261009-233118-894768'], 'encoding': 'UTF-8 no BOM', 'line_endings': 'LF'}
- **Unresolved**: 实机未验证
