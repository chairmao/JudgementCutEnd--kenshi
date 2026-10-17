// 次元斩绝：独立实例姿势层 + 主线程演出；不修改共享动画缓存或原版资源。
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <mmsystem.h>
#include <d3d11.h>
#include <ogre/OgreTextureManager.h>
#include <ogre/OgreTextureUnitState.h>
#include <ogre/OgreHardwarePixelBuffer.h>
#include <ogre/OgreRenderWindow.h>
#include <ogre/OgreGpuProgramParams.h>
#include <ogre/OgreTechnique.h>
#include <ogre/OgrePass.h>
#include <ogre/OgreRenderTexture.h>
#include <cstring>
#include <core/Functions.h>
#include <Debug.h>
#include <kenshi/Globals.h>
#include <kenshi/GameWorld.h>
#include <kenshi/Character.h>
// 原生人形武器选择/拔刀/收刀接口；直接调用 _NV 版本，不依赖新增虚函数布局。
#include <kenshi/CharacterHuman.h>
// 原生伤害值与部位日志需要完整类型，不能依赖 Character.h 的前置声明。
#include <kenshi/Damages.h>
// 使用原生 CharStats 公式在U键时生成伤害快照；此后不依赖AI随时可清空的战斗缓存。
#include <kenshi/CharStats.h>
// 只在U键快照时核对装备栏；目标种族加成按原生顺序使用已冻结的武器系数。
#include <kenshi/Inventory.h>
#include <kenshi/RaceData.h>
// CombatClass实际位于依赖Include/kenshi/combat目录；保持与工程IncludePath相对路径一致。
// 踉跄仅走原生战斗反应入口，不写恢复计时器或添加第二份医疗损伤。
#include <kenshi/combat/CombatClass.h>
#include <kenshi/Gear.h>
#include <kenshi/GameData.h>
#include <kenshi/PlayerInterface.h>
#include <kenshi/InputHandler.h>
#include <kenshi/Renderer.h>
#include <kenshi/Animation/AnimationClass.h>
// 成员取址需要完整人形类型，确保解析派生类非虚_NV入口及正确成员指针布局。
#include <kenshi/Animation/AnimationClassHuman.h>
#include <ogre/OgreOldSkeletonInstance.h>
#include <ogre/OgreOldBone.h>
#include <ogre/OgreSceneManager.h>
#include <ogre/OgreSceneNode.h>
#include <ogre/OgreManualObject.h>
// 独立光学层需要明确绘制优先级；只调用本机DLL已有的公开非内联队列接口。
#include <ogre/OgreRenderQueue.h>
#include <ogre/OgreVector4.h>
#include <ogre/OgreResourceGroupManager.h>
#include <ogre/OgreCamera.h>
#include <ogre/OgreEntity.h>
#include <ogre/OgreMatrix4.h>
#include <ogre/OgreMaterialManager.h>
#include <ogre/OgreMaterial.h>
#include <ogre/OgreRoot.h>
#include <ogre/OgreRenderObjectListener.h>
#include <mygui/MyGUI_InputManager.h>
#include <mygui/MyGUI_EditBox.h>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <float.h>
#include <algorithm>
#include <stdexcept>

namespace JCE {
using Ogre::Vector3;
using Ogre::Quaternion;
const char* GROUP="JudgementCutEnd/Resources/v1";
const float DRAW=2.1f, CUT=2.35f, SHEATH=5.15f, END=6.7f;
// 轨道/裂痕仍用原剪辑秒，真实时钟统一乘三；保持所有动作和特效事件同步。
// 世界降速和卡顿门槛仍用真实秒，不能随演出倍率一起变化。
const float PLAYBACK_RATE=3.f;
// 32个深度切片仅铺淡底雾；原纹理烟带与独立烟丝承担流动、扩张和消散。
// 顶点/索引硬预算仍沿用32768/49152；其他幻影、刀光与光屑数量不变。
const unsigned PHANTOM_PATHS=16, PHANTOM_ECHOES=4, SLASH_ECHOES=6, MIST_SLICES=32;
// 原烟带48条×10段、烟丝96个固定槽不变；独立裂面从三片到五片只增加48顶点/72索引。
const unsigned SMOKE_BANDS=48, SMOKE_SEGMENTS=10, SMOKE_WISPS=96;
// 已验证的资源上界，与绘制端32个人形预算独立；事件数量仍为16条路径。
const unsigned PHANTOM_BODY_LIMIT=32;
const unsigned VFX_VERTEX_LIMIT=32768, VFX_INDEX_LIMIT=49152;
// 保留全部11个段索引；按独立优先级排序，背景副本在首个自有段绘制前抓取。
const unsigned FX_SECTIONS=11;
// 原NIF的八组切割折射 + 一组大范围折射；强度键保持独立，空间拓扑按实际刀路适配。
const unsigned OPTICAL_PLANES=8;
// 2.9只验证三张实际源网格；旧8面参数/资源留作归档，不扩增96道刀光或粒子数量。
const unsigned SOURCE_FACET_COUNT=3;
// 2.9.5：源CSV仍严格读取三张，独立模式复用screen1五次；不能改源数量而破坏旧资源合同。
// 退场总尾段仍是1.30剪辑秒，五片错开0.15、各用0.70；不延长演出或世界降速持有期。
const unsigned INDEPENDENT_FACET_COUNT=5;
const float FACET_RELEASE_INTERVAL=.15f,FACET_RELEASE_DURATION=.70f;
// 2.9.7：揭开0.45剪辑秒（实际0.15秒）；剩余停留段只用55%完成原有偏折，其后姿态稳定。
// 仅影响五片独立模式，各片仍由自己的刀路出生时间计算；不延长END/世界降速或修改源曲线。
const float FACET_REVEAL_DURATION=.45f,FACET_BEND_FRACTION=.55f;
const float FACET_LIFETIME_TAIL=FACET_RELEASE_INTERVAL*float(INDEPENDENT_FACET_COUNT-1)+FACET_RELEASE_DURATION;
// v100按C++03编译，模板排序的值类型不能是函数内局部类；固定数组仍由当前帧栈持有。
struct HazeCell {Vector3 p;float depth,size;unsigned id;bool operator<(const HazeCell& b) const{return depth>b.depth;}};
struct Guard { CRITICAL_SECTION* p; Guard(CRITICAL_SECTION& c):p(&c){EnterCriticalSection(p);} ~Guard(){LeaveCriticalSection(p);} };
CRITICAL_SECTION gate;
volatile LONG ready=0, started=0, frameThread=0;
PVOID volatile poseOwner=0;
std::wstring directory;
LARGE_INTEGER frequency;
unsigned logLines=0;

double Seconds() { LARGE_INTEGER n;QueryPerformanceCounter(&n);return double(n.QuadPart)/double(frequency.QuadPart); }
bool Finite(float x) {return _finite(x)!=0;}
float Clamp(float x,float a,float b){return std::max(a,std::min(b,x));}
void Log(const std::string& message) {
    // 日志每个生命周期事件一条，不逐角色逐帧刷屏。单进程硬上限 4096 条、文件约 2 MiB。
    if(logLines++>=4096)return;
    CreateDirectoryW((directory+L"logs").c_str(),0);
    std::wstring path=directory+L"logs\\JudgementCutEnd.log";
    WIN32_FILE_ATTRIBUTE_DATA a;
    if(GetFileAttributesExW(path.c_str(),GetFileExInfoStandard,&a)&&a.nFileSizeLow>2*1024*1024)
        MoveFileExW(path.c_str(),(path+L".1").c_str(),MOVEFILE_REPLACE_EXISTING);
    SYSTEMTIME t;GetLocalTime(&t);char prefix[100];
    sprintf_s(prefix,"%04u-%02u-%02u %02u:%02u:%02u.%03u [JCE 2.9.11-dev] ",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds);
    std::ofstream f(path.c_str(),std::ios::binary|std::ios::app);f<<prefix<<message<<"\r\n";
}
template<class Method> intptr_t NativeAddress(Method method,const char* label) {
    // 使用头文件中的非虚 _NV 成员函数指针，签名由编译器核对；label仅用于日志，不参与查址。
    // KenshiLib模板用(void*&)只读取成员指针首个地址字段，后面可包含编译器的继承布局字段。
    // 成员指针总长不必等于普通指针；上一版等长检查使本机启动直接禁用。这里只防止首字读取越界。
    // 本函数只解析声明在当前类中的非虚_NV入口，不调用成员指针，也不手工应用附加的this调整字段。
    HMODULE library=GetModuleHandleW(L"KenshiLib.dll");
    if(!library)throw std::runtime_error("KenshiLib is not loaded");
    void* stub=0;
    if(sizeof(method)<sizeof(stub))throw std::runtime_error("Native member pointer is too small for SDK address field");
    std::memcpy(&stub,&method,sizeof(stub));
    // 仅用固定桩表边界导出做校验；不查询目标函数修饰名，不硬编码游戏RVA。
    // 即使工具链留下本插件导入跳板，也先抛普通异常禁用插件，不把坏地址交给SDK。
    uintptr_t begin=reinterpret_cast<uintptr_t>(GetProcAddress(library,"FUNC_BEGIN"));
    uintptr_t end=reinterpret_cast<uintptr_t>(GetProcAddress(library,"FUNC_END"));
    uintptr_t address=reinterpret_cast<uintptr_t>(stub);
    if(!stub||!begin||end<=begin||address<begin||address>=end)
        throw std::runtime_error(std::string("Native member address is not inside KenshiLib stub table: ")+label);
    intptr_t target=KenshiLib::GetRealAddress(method);
    if(!target)throw std::runtime_error(std::string("Native target is unavailable: ")+label);
    // 启动时每个目标一条日志；保存实际桩RVA和解析目标，可判断/GL+LTCG是否消除了导入跳板。
    std::ostringstream s;s<<"native_binding method="<<label<<" member_bytes="<<sizeof(method)<<" address_bytes="<<sizeof(stub)<<" stub_rva=0x"<<std::hex
        <<(address-reinterpret_cast<uintptr_t>(library))<<" target=0x"<<target;Log(s.str());
    return target;
}

// 0.2.1 的 Entity 内联访问按依赖头布局生成：骨架偏移 0x2F8、初始化 0x300；
// 本机 OgreMain_x64.dll 导出实际访问 0x300 / 0x308，不能把内联字段读取当作运行库 API。
// 只对本插件新增的 Entity 蒙皮接口走运行库真实导出；不改依赖头、不硬写字段或函数 RVA。
// x64 实例函数首参数为 this；返回类型、bool/ushort 宽度及容器类型保持原接口合同。
template<class Fn> Fn OgreExport(const char* name){
    HMODULE library=GetModuleHandleW(L"OgreMain_x64.dll");
    FARPROC address=library?GetProcAddress(library,name):0;
    if(!address)throw std::runtime_error(std::string("OGRE skin export unavailable: ")+name);
    std::ostringstream s;s<<"ogre_skin_binding export="<<name<<" rva=0x"<<std::hex
        <<(reinterpret_cast<uintptr_t>(address)-reinterpret_cast<uintptr_t>(library));Log(s.str());
    return reinterpret_cast<Fn>(address);
}
struct SkinApi{
    typedef Ogre::OldSkeletonInstance*(__fastcall* SkeletonFn)(const Ogre::Entity*);
    typedef bool(__fastcall* BoolFn)(const Ogre::Entity*);
    typedef const Ogre::Entity::EntitySet*(__fastcall* SharingFn)(const Ogre::Entity*);
    typedef void(__fastcall* SkipFn)(Ogre::Entity*,bool);
    typedef const Ogre::Matrix4*(__fastcall* MatricesFn)(const Ogre::Entity*);
    typedef unsigned short(__fastcall* CountFn)(const Ogre::Entity*);
    typedef bool(__fastcall* CacheFn)(Ogre::Entity*);
    SkeletonFn skeleton;BoolFn initialised,skip;SharingFn sharing;SkipFn setSkip;
    MatricesFn matrices;CountFn count;CacheFn cache;
    SkinApi():skeleton(0),initialised(0),skip(0),sharing(0),setSkip(0),matrices(0),count(0),cache(0){}
    void Load(){
        // 启动时一次性验证八个导出，缺失则在安装钩子之前禁用；绝不退回错误的内联实现。
        skeleton=OgreExport<SkeletonFn>("?getSkeleton@Entity@Ogre@@QEBAPEAVOldSkeletonInstance@2@XZ");
        initialised=OgreExport<BoolFn>("?isInitialised@Entity@Ogre@@QEBA_NXZ");
        sharing=OgreExport<SharingFn>("?getSkeletonInstanceSharingSet@Entity@Ogre@@QEBAPEBV?$set@PEAVEntity@Ogre@@U?$less@PEAVEntity@Ogre@@@std@@V?$STLAllocator@PEAVEntity@Ogre@@V?$CategorisedAllocPolicy@$0A@@2@@2@@std@@XZ");
        skip=OgreExport<BoolFn>("?getSkipAnimationStateUpdate@Entity@Ogre@@QEBA_NXZ");
        setSkip=OgreExport<SkipFn>("?setSkipAnimationStateUpdate@Entity@Ogre@@QEAAX_N@Z");
        matrices=OgreExport<MatricesFn>("?_getBoneMatrices@Entity@Ogre@@QEBAPEBVMatrix4@2@XZ");
        count=OgreExport<CountFn>("?_getNumBoneMatrices@Entity@Ogre@@QEBAGXZ");
        cache=OgreExport<CacheFn>("?cacheBoneMatrices@Entity@Ogre@@IEAA_NXZ");
    }
} skin;

struct Settings {
    float radius,slow,damageMultiplier,staggerForceMultiplier;
    unsigned castKey,opticalProbeMode; bool damage,sound;
    Settings():radius(350),slow(.001f),damageMultiplier(1),staggerForceMultiplier(8),castKey('U'),opticalProbeMode(3),damage(true),sound(true){}
    static std::string ConfigText(const std::string& text){
        // INI手动编辑允许缩进、等号两侧空格和行末注释；保留原键名大小写与旧数值项语义。
        size_t first=text.find_first_not_of(" \t\r");if(first==std::string::npos)return "";
        size_t last=text.find_last_not_of(" \t\r");return text.substr(first,last-first+1);
    }
    void Load(){
        std::ifstream f((directory+L"JudgementCutEnd.ini").c_str());std::string line;bool firstLine=true;
        while(std::getline(f,line)) {
            // Windows编辑器可能保存UTF-8 BOM；仅跳过文件头三个字节，不改文件或进行有损转码。
            if(firstLine&&line.compare(0,3,"\xEF\xBB\xBF")==0)line.erase(0,3);firstLine=false;
            line=ConfigText(line);size_t e=line.find('=');if(e==std::string::npos||line[0]==';'||line[0]=='#')continue;
            std::string k=ConfigText(line.substr(0,e));std::string value=ConfigText(line.substr(e+1));
            size_t comment=value.find_first_of("#;");if(comment!=std::string::npos)value=ConfigText(value.substr(0,comment));
            if(k=="CastKeyVK"){
                // 键位必须是完整十进制整数；拒绝85abc/85.5/空值，不能由atof截断后悄悄绑定为U。
                // 只允许A-Z及F1-F12，保留默认U和Esc取消、文本框/暂停/加载禁用合同。
                char* end=0;long vk=strtol(value.c_str(),&end,10);
                if(!value.empty()&&end!=value.c_str()&&*end=='\0'&&((vk>=65&&vk<=90)||(vk>=VK_F1&&vk<=VK_F12)))castKey=unsigned(vk);
                else Log("config_invalid CastKeyVK; previous/default key retained");
                continue;
            }
            float v=float(atof(value.c_str()));if(!Finite(v))continue;
            // Radius直接表示地面伤害圆半径，默认350；不再把布局缩放额外乘成更大的伤害球。
// 旧Radius键仍可读，但语义已按用户本次请求改为圆半径；分发配置同步更新。
            if(k=="Radius")radius=Clamp(v,5,1000);
            else if(k=="WorldSpeed")slow=Clamp(v,.001f,.1f);
            // 每条真实裂痕固定100%攻击；旧44倍必须忽略，避免96次又各乘44。
            // 保留字段/旧配置键供日志兼容，但不允许配置改变用户本次确认的单击倍率。
            else if(k=="DamageMultiplier"&&v!=1)Log("config_ignored: DamageMultiplier; per_slash_100_percent");
            // 仅放大收刀后的原生踉跄力度，绝不进入medical.addWound；单位为反应倍率。
            else if(k=="StaggerForceMultiplier")staggerForceMultiplier=Clamp(v,1,100);
            else if(k=="CutDamage"||k=="BluntDamage")Log("config_ignored legacy fixed damage; use DamageMultiplier");
            // 兼容旧配置键，但不再允许旧的非零数值重新启用冷却。
            else if(k=="Cooldown"&&v!=0)Log("config_ignored: Cooldown; cooldown_removed");
            // 全范围伤害不再截断前32/64人；保留旧键读取兼容，非零旧值明确忽略。
            else if(k=="MaxTargets"&&v!=0)Log("config_ignored: MaxTargets; all_enemies_in_area");
            // 2.9.5：0保留旧三面；1/2保留已验收单片（仅面/完整）；3独立五片完整；4仅独立五片。
            // 默认3恢复刀光/蓝雾/幻影；旧配置显式1/2仍可对照，仅读取自有特效显示模式。
            else if(k=="OpticalProbeMode"){
                if(v==floorf(v)&&v>=0&&v<=4)opticalProbeMode=unsigned(v);
                else Log("config_invalid OpticalProbeMode; previous/default mode retained");
            }
            else if(k=="DamageEnabled")damage=v!=0;
            else if(k=="SoundEnabled")sound=v!=0;
            // 保留旧配置项的解析兼容，但用户已要求移除镜头接管；即使旧值为 1 也不移动相机。
            else if(k=="CinematicCamera"&&v!=0)Log("config_ignored CinematicCamera; free camera only");
        }
    }
};
// v2在旋转后增加局部位移；v1仍只读旋转并将位移初始化为零。
struct Keyframe {float t;Quaternion q;Vector3 p;};
struct Track {std::string name;std::vector<Keyframe> keys;};
struct Slash {Vector3 centre,direction;float length,at,life;};
std::vector<Track> clip;
struct PhantomAsset {unsigned frames,vertices,triangles;float fps,duration;std::vector<unsigned short> indices;std::vector<Vector3> positions;};
PhantomAsset phantomAsset;
// 不通过Ogre内联字段读取跨DLL布局；纹理/窗口只走声明的原生虚接口，D3D资源遵守COM所有权。
template<class T> struct ComOwned {
    T* p;ComOwned():p(0){}~ComOwned(){if(p)p->Release();}
private:ComOwned(const ComOwned&);ComOwned& operator=(const ComOwned&);
};
std::vector<Slash> slashes;
// 原NIF网格已离线统一转到Y-up和施放半径单位；每张保留独立顶点/法线/UV、尺度键与曲线编号。
// 数据只在启动读入三张；旧模式绘制三张，独立模式复用screen1五次并栈上排序，不逐帧加载文件或创建材质/纹理。
struct FacetKey {float t,value;};
struct SourceFacetAsset {
    std::string name;unsigned optical,path;Vector3 pivot,axis;float scaleStart,scaleEnd;
    std::vector<Vector3> positions,normals,uv;std::vector<unsigned short> indices;std::vector<FacetKey> scaleKeys;
};
std::vector<SourceFacetAsset> sourceFacets;
// 2.9.2将源screen1的局部主平面适配为角色朝向内的立向裂面，而非跟随镜头的幕布。
// 源顶点/UV/索引不改；启动时缓存正交基、几何中心和有界的非均匀尺度，每帧仅做点积。
// 目标宽1.36R、高0.66R、中心高0.40R；单位为技能半径，仍受像素shader的半球裁剪。
Vector3 wideFacetRight=Vector3::UNIT_X,wideFacetUp=Vector3::UNIT_Y,wideFacetCentre=Vector3::ZERO;
Vector3 wideFacetScale(1,1,1);
Vector3 WideFacetPoint(const Vector3& source){
    Vector3 q=source-wideFacetCentre;
    return Vector3(q.dotProduct(wideFacetRight)*wideFacetScale.x,
        q.dotProduct(wideFacetUp)*wideFacetScale.y,q.dotProduct(sourceFacets[0].axis)*wideFacetScale.z);
}
Vector3 WideFacetNormal(const Vector3& source){
    // 非均匀缩放的法线必须使用逆转置；否则面已立起来而前后面判断仍沿旧水平法线。
    Vector3 n(source.dotProduct(wideFacetRight)/wideFacetScale.x,
        source.dotProduct(wideFacetUp)/wideFacetScale.y,source.dotProduct(sourceFacets[0].axis)/wideFacetScale.z);
    n.normalise();return n;
}
std::vector<FacetKey> facetEnvelopes[2];
float FacetSample(const std::vector<FacetKey>& keys,float t){
    if(keys.empty())return 1.f;
    if(t<=keys.front().t)return keys.front().value;
    for(size_t i=1;i<keys.size();++i)if(t<=keys[i].t){
        float u=Clamp((t-keys[i-1].t)/(keys[i].t-keys[i-1].t),0,1);
        return keys[i-1].value+(keys[i].value-keys[i-1].value)*u;
    }
    return keys.back().value;
}
float FacetScale(const SourceFacetAsset& asset,float phase){
    // 原TransformController的scale替换静态对象scale；转换器已按其峰值保存，禁止再乘一次静态scale。
    // 只把源可见时间区间映射到各自刀路出生至退场，保留原线性关键帧比例。
    return FacetSample(asset.scaleKeys,asset.scaleStart+Clamp(phase,0,1)*(asset.scaleEnd-asset.scaleStart));
}
struct MirrorShard {Vector3 a,b,c;float at;};
std::vector<MirrorShard> shards;
// 裂痕资产保留归一化布局；其显示缩放在每次施放时按角色朝向和水平圆边界拟合。


// 本轮源特效曲线与贴图在LoadAssets阶段读取一次；每帧只采样，不分配、不读磁盘。
// CURVE携带原sequence倍速与NiFloatData的归一化切线，独立于世界减速。
struct SourceFxKey {float t,value,backward,forward;};
struct SourceFxCurve {unsigned interpolation;float frequency;std::vector<SourceFxKey> keys;};
SourceFxCurve sourceFxCurves[6];
float SourceCurve(unsigned id,float age){
    if(id>=6||age<0)return 0;
    const SourceFxCurve& curve=sourceFxCurves[id];const std::vector<SourceFxKey>& k=curve.keys;
    float t=age*curve.frequency;if(k.empty()||t>k.back().t)return 0;
    if(t<=k.front().t)return k.front().value;
    for(size_t i=1;i<k.size();++i)if(t<=k[i].t){
        const SourceFxKey& a=k[i-1];const SourceFxKey& b=k[i];float u=(t-a.t)/(b.t-a.t);
        if(curve.interpolation==1)return a.value+(b.value-a.value)*u;
        // NiFloatData type2与NifSkope一致：左Backward/右Forward，不额外乘时间跨度。
        float u2=u*u,u3=u2*u;
        return (2*u3-3*u2+1)*a.value+(-2*u3+3*u2)*b.value+
            (u3-2*u2+u)*a.backward+(u3-u2)*b.forward;
    }
    return k.back().value;
}


// 独立强度数据不复用Alpha曲线。只在启动读取九条键，每帧最多采样九条，不分配资源。
// Skyrim强度是引擎单位，先按各自峰值归一化，再由自有shader限制最大像素偏移。
SourceFxCurve opticalCurves[9];
float opticalPeaks[9]={0};
float OpticalStrength(unsigned id,float age,float duration){
    if(id>=9||age<0||duration<=0||age>=duration)return 0;
    const SourceFxCurve& curve=opticalCurves[id];const std::vector<SourceFxKey>& keys=curve.keys;
    if(keys.empty()||opticalPeaks[id]<=0)return 0;
    // 将原控制器完整时间区间映射到这道斩击出生至收刀退场；保留原关键帧比例与曲线形状。
    // 频率的原持续时间也参与映射；不使用几乎静止的世界时钟，不改变3倍动作播放速度。
    float sourceDuration=keys.back().t/curve.frequency;
    float t=(age/duration*sourceDuration)*curve.frequency,value=keys.front().value;
    for(size_t i=1;i<keys.size();++i)if(t<=keys[i].t){
        const SourceFxKey& a=keys[i-1];const SourceFxKey& b=keys[i];
        float u=Clamp((t-a.t)/(b.t-a.t),0,1);
        if(curve.interpolation==1)value=a.value+(b.value-a.value)*u;
        else{
            float u2=u*u,u3=u2*u;
            value=(2*u3-3*u2+1)*a.value+(-2*u3+3*u2)*b.value+
                (u3-2*u2+u)*a.backward+(u3-u2)*b.forward;
        }
        break;
    }
    return Clamp(value/opticalPeaks[id],0,1)*Clamp(age/.10f,0,1);
}

void LoadSourceFacets(){
    std::ifstream f((directory+L"assets\\jce_facets29.csv").c_str());
    std::string tag;unsigned version=0,count=0;f>>tag>>version>>count;
    if(!f||tag!="JCEFACETS"||version!=1||count!=SOURCE_FACET_COUNT)throw std::runtime_error("Invalid source facets header");
    const char* names[]={"screen1","slash3","slash5"};const unsigned optical[]={8,2,4},paths[]={0,24,48};
    sourceFacets.clear();sourceFacets.reserve(SOURCE_FACET_COUNT);
    for(unsigned i=0;i<SOURCE_FACET_COUNT;++i){
        SourceFacetAsset a;unsigned nv=0,nt=0,nk=0;
        f>>tag>>a.name>>a.optical>>a.path>>nv>>nt>>nk
         >>a.pivot.x>>a.pivot.y>>a.pivot.z>>a.axis.x>>a.axis.y>>a.axis.z>>a.scaleStart>>a.scaleEnd;
        // 固定少量源拓扑、编号和预算；拒绝损坏数据/NaN/不完整键，在钩子安装前失败。
        if(!f||tag!="FACET"||a.name!=names[i]||a.optical!=optical[i]||a.path!=paths[i]||a.path>=slashes.size()||
           nv!=24||nt!=12||nk>128||!Finite(a.pivot.squaredLength())||a.pivot.length()>1||
           !Finite(a.axis.squaredLength())||fabs(a.axis.length()-1)>.005||!Finite(a.scaleStart)||!Finite(a.scaleEnd)||
           a.scaleStart<0||a.scaleEnd>10||(nk&&a.scaleEnd<=a.scaleStart)||(!nk&&(a.scaleStart!=0||a.scaleEnd!=0)))
            throw std::runtime_error("Invalid source facet contract");
        a.positions.reserve(nv);a.normals.reserve(nv);a.uv.reserve(nv);a.indices.reserve(nt*3);a.scaleKeys.reserve(nk);
        for(unsigned j=0;j<nv;++j){
            Vector3 p,n,uv(0,0,0);f>>tag>>p.x>>p.y>>p.z>>n.x>>n.y>>n.z>>uv.x>>uv.y;
            if(!f||tag!="VERT"||!Finite(p.squaredLength())||p.length()>.781f||!Finite(n.squaredLength())||
               fabs(n.length()-1)>.005||!Finite(uv.x)||!Finite(uv.y)||uv.x<0||uv.x>1||uv.y<0||uv.y>1)
                throw std::runtime_error("Invalid source facet vertex");
            n.normalise();a.positions.push_back(p);a.normals.push_back(n);a.uv.push_back(uv);
        }
        for(unsigned j=0;j<nt;++j){
            unsigned x=0,y=0,z=0;f>>tag>>x>>y>>z;
            if(!f||tag!="TRI"||x>=nv||y>=nv||z>=nv||x==y||y==z||x==z||
               (a.positions[y]-a.positions[x]).crossProduct(a.positions[z]-a.positions[x]).squaredLength()<1e-18f)
                throw std::runtime_error("Invalid source facet index");
            a.indices.push_back(static_cast<unsigned short>(x));a.indices.push_back(static_cast<unsigned short>(y));a.indices.push_back(static_cast<unsigned short>(z));
        }
        for(unsigned j=0;j<nk;++j){
            FacetKey k;f>>tag>>k.t>>k.value;
            if(!f||tag!="SCALE"||!Finite(k.t)||!Finite(k.value)||k.t<0||k.t>10||k.value<0||k.value>1||
               (j==0&&k.t!=0)||(j&&k.t<=a.scaleKeys.back().t))throw std::runtime_error("Invalid source facet scale key");
            a.scaleKeys.push_back(k);
        }
        if(nk&&(a.scaleKeys.back().t!=a.scaleEnd||fabs(a.scaleKeys.back().value)>.00001f))
            throw std::runtime_error("Source facet scale must retire");
        sourceFacets.push_back(a);
    }
    const SourceFacetAsset& wide=sourceFacets[0];
    // 从真实源主面建立右/上基，平移到几何中心后拟合，避免源pivot偏置让一侧面积被球边界裁掉。
    wideFacetRight=Vector3::UNIT_X-wide.axis*wide.axis.dotProduct(Vector3::UNIT_X);
    if(wideFacetRight.squaredLength()<.01f)throw std::runtime_error("Invalid wide facet basis");
    wideFacetRight.normalise();wideFacetUp=wide.axis.crossProduct(wideFacetRight);wideFacetUp.normalise();
    Vector3 lo(FLT_MAX,FLT_MAX,FLT_MAX),hi(-FLT_MAX,-FLT_MAX,-FLT_MAX);
    for(size_t j=0;j<wide.positions.size();++j){
        const Vector3& p=wide.positions[j];Vector3 q(p.dotProduct(wideFacetRight),p.dotProduct(wideFacetUp),p.dotProduct(wide.axis));
        lo.x=std::min(lo.x,q.x);lo.y=std::min(lo.y,q.y);lo.z=std::min(lo.z,q.z);
        hi.x=std::max(hi.x,q.x);hi.y=std::max(hi.y,q.y);hi.z=std::max(hi.z,q.z);
    }
    if(!Finite((hi-lo).squaredLength())||hi.x-lo.x<.001f||hi.y-lo.y<.001f)
        throw std::runtime_error("Invalid wide facet span");
    Vector3 centre=(lo+hi)*.5f;
    wideFacetCentre=wideFacetRight*centre.x+wideFacetUp*centre.y+wide.axis*centre.z;
    wideFacetScale=Vector3(1.36f/(hi.x-lo.x),.66f/(hi.y-lo.y),1.f);
    wideFacetScale.z=std::min(wideFacetScale.x,wideFacetScale.y);
    if(!Finite(wideFacetScale.squaredLength())||wideFacetScale.x>8.f||wideFacetScale.y>8.f)
        throw std::runtime_error("Wide facet scale budget exceeded");
    const char* envelopes[]={"hold","release"};
    for(unsigned i=0;i<2;++i){
        std::string name;unsigned keys=0;f>>tag>>name>>keys;
        if(!f||tag!="ENVELOPE"||name!=envelopes[i]||keys<2||keys>128)throw std::runtime_error("Invalid facet envelope");
        facetEnvelopes[i].clear();facetEnvelopes[i].reserve(keys);
        for(unsigned j=0;j<keys;++j){
            FacetKey k;f>>tag>>k.t>>k.value;
            if(!f||tag!="KEY"||!Finite(k.t)||!Finite(k.value)||k.t<0||k.t>1||k.value<0||k.value>1||
               (j==0&&k.t!=0)||(j&&k.t<=facetEnvelopes[i].back().t))throw std::runtime_error("Invalid facet envelope key");
            facetEnvelopes[i].push_back(k);
        }
        if(facetEnvelopes[i].back().t!=1||(i==1&&fabs(facetEnvelopes[i].back().value)>.00001f))
            throw std::runtime_error("Incomplete facet envelope");
    }
    f>>std::ws;if(!f.eof())throw std::runtime_error("Unexpected source facet fields");
    Log("source_facets_ready revision=2.9.2-dev source=ap05_NIF screen1_slash3_slash5 meshes=3 vertices=72 triangles=36 normals=source BG3_alpha=31_24");
}

void LoadAssets() {
    std::ifstream f((directory+L"assets\\jce.clip").c_str());std::string line,tag;unsigned version,count;float duration;
    if(!std::getline(f,line))throw std::runtime_error("Missing animation: assets/jce.clip");
    std::istringstream header(line);header>>tag>>version>>duration>>count;
    if(!header||!Finite(duration)||tag!="JCECLIP"||(version!=1&&version!=2)||fabs(duration-END)>.001||count<1||count>30)throw std::runtime_error("Invalid animation header");
    unsigned clipVersion=version;
    for(unsigned i=0;i<count;++i){
        Track tr;if(!std::getline(f,line)||line.substr(0,5)!="BONE ")throw std::runtime_error("Missing bone");
        tr.name=line.substr(5);if(!tr.name.empty()&&tr.name[tr.name.size()-1]=='\r')tr.name.erase(tr.name.size()-1);
        if(tr.name.empty())throw std::runtime_error("Invalid/root track");
        bool ended=false;
        while(std::getline(f,line)) {
            if(line=="END"||line=="END\r"){ended=true;break;}
            Keyframe k;k.t=0;k.q=Quaternion::IDENTITY;k.p=Vector3::ZERO;std::istringstream s(line);s>>tag>>k.t>>k.q.w>>k.q.x>>k.q.y>>k.q.z;
            if(clipVersion==2)s>>k.p.x>>k.p.y>>k.p.z;
            // 不允许资源借动画通道改变骨长或导入瞬移；仅Bip01的有限竖直补偿。
            if(!Finite(k.p.squaredLength())||fabs(k.p.x)>.00001f||fabs(k.p.z)>.00001f||fabs(k.p.y)>12.f||
                (tr.name!="Bip01"&&k.p.squaredLength()>.00000001f))throw std::runtime_error("Invalid translation channel");
            bool parsed=bool(s);std::string extra;if(parsed&&(s>>extra))throw std::runtime_error("Unexpected keyframe fields");s.clear();
            float norm=k.q.Norm(); // 失败读取也只计算已初始化数据；下行拒绝解析失败。
            if(!parsed||tag!="KEY"||!Finite(k.t)||!Finite(norm)||fabs(norm-1)>.005||k.t<0||k.t>END+.001||(!tr.keys.empty()&&k.t<=tr.keys.back().t)||tr.keys.size()>=1000)
                throw std::runtime_error("Invalid keyframe");
            k.q.normalise();tr.keys.push_back(k);
        }
        if(!ended||tr.keys.size()<2||fabs(tr.keys.front().t)>.001||fabs(tr.keys.back().t-END)>.001)throw std::runtime_error("Incomplete animation track");
        for(size_t j=0;j<clip.size();++j)if(clip[j].name==tr.name)throw std::runtime_error("Duplicate bone");
        clip.push_back(tr);
    }
    std::ifstream v((directory+L"assets\\slashes.csv").c_str());v>>tag>>version>>count;
    if(!v||tag!="JCESLASH"||version!=1||count<1||count>192)throw std::runtime_error("Invalid VFX layout");
    for(unsigned i=0;i<count;++i){
        Slash s;v>>s.centre.x>>s.centre.y>>s.centre.z>>s.direction.x>>s.direction.y>>s.direction.z>>s.length>>s.at>>s.life;
        if(!v||!Finite(s.centre.squaredLength())||!Finite(s.direction.squaredLength())||fabs(s.direction.length()-1)>.005||!Finite(s.length)||s.length<=0||s.length>2||!Finite(s.at)||s.at<CUT||s.at>SHEATH||!Finite(s.life)||s.life<=0||s.life>3)throw std::runtime_error("Invalid VFX segment");
        float extent=std::max((s.centre-s.direction*s.length).length(),(s.centre+s.direction*s.length).length())+.18f/30.f;
        if(!Finite(extent)||extent>8.f)throw std::runtime_error("VFX envelope too large");
        slashes.push_back(s);
    }
    // 192原创三角片来自48个面板，共享裂痕出现时间；失败在安装钩子前禁用。
    std::ifstream glass((directory+L"assets\\jce_shards.csv").c_str());glass>>tag>>version>>count;
    if(!glass||tag!="JCESHARDS"||version!=1||count!=192)throw std::runtime_error("Invalid mirror shard header");
    for(unsigned i=0;i<count;++i){
        MirrorShard s;glass>>s.a.x>>s.a.y>>s.a.z>>s.b.x>>s.b.y>>s.b.z>>s.c.x>>s.c.y>>s.c.z>>s.at;
        if(!glass||!Finite(s.a.squaredLength())||!Finite(s.b.squaredLength())||!Finite(s.c.squaredLength())||
            s.a.length()>8||s.b.length()>8||s.c.length()>8||!Finite(s.at)||s.at<CUT||s.at>SHEATH||
            (s.b-s.a).crossProduct(s.c-s.a).squaredLength()<.00000001f)throw std::runtime_error("Invalid mirror shard");
        shards.push_back(s);
    }
    // 精确固定六条源曲线合同，先完整校验再进入渲染；拒绝错序、NaN、过量/非递增键与尾随垃圾。
    std::ifstream sourceFx((directory+L"assets\\jce_source_curves.csv").c_str());
    sourceFx>>tag>>version>>count;
    if(!sourceFx||tag!="JCEFXCURVES"||version!=1||count!=6)throw std::runtime_error("Invalid source FX curves header");
    const char* names[]={"screen_flash","screen_veil","finish_glow","finish_halo","fracture_alpha","cut_flash"};
    for(unsigned i=0;i<6;++i){
        std::string name;unsigned keys=0;SourceFxCurve& c=sourceFxCurves[i];
        sourceFx>>tag>>name>>c.interpolation>>c.frequency>>keys;
        if(!sourceFx||tag!="CURVE"||name!=names[i]||(c.interpolation!=1&&c.interpolation!=2)||
            !Finite(c.frequency)||c.frequency<=0||c.frequency>4||keys<2||keys>128)
            throw std::runtime_error("Invalid source FX curve");
        c.keys.clear();c.keys.reserve(keys);
        for(unsigned j=0;j<keys;++j){
            SourceFxKey k;sourceFx>>tag>>k.t>>k.value>>k.backward>>k.forward;
            if(!sourceFx||tag!="KEY"||!Finite(k.t)||!Finite(k.value)||!Finite(k.backward)||!Finite(k.forward)||
                k.t<0||k.t>10||fabs(k.value)>8||fabs(k.backward)>8||fabs(k.forward)>8||
                (j==0&&fabs(k.t)>.00001f)||(j&&k.t<=c.keys.back().t))
                throw std::runtime_error("Invalid source FX key");
            c.keys.push_back(k);
        }
    }
    sourceFx>>std::ws;if(!sourceFx.eof())throw std::runtime_error("Unexpected source FX fields");
    Log("source_fx_assets_ready curves=6 textures=5 schema=JCEFXCURVES1");
    // 九条原RefractionStrength曲线是新shader的必要输入；先严格校验再安装任何钩子。
    // 旧六条Alpha资源与格式不变。拒绝错序、非有限数、过量/重复键、非零末键和尾随数据。
    std::ifstream optics((directory+L"assets\\jce_optics.csv").c_str());
    optics>>tag>>version>>count;
    if(!optics||tag!="JCEOPTICS"||version!=1||count!=9)throw std::runtime_error("Invalid optics header");
    const char* opticalNames[]={"slash1","slash2","slash3","slash4","slash5","slash6","slash7","slash8","screen1"};
    for(unsigned i=0;i<9;++i){
        SourceFxCurve& curve=opticalCurves[i];unsigned keys=0;std::string name;
        optics>>tag>>name>>curve.interpolation>>curve.frequency>>opticalPeaks[i]>>keys;
        if(!optics||tag!="CURVE"||name!=opticalNames[i]||(curve.interpolation!=1&&curve.interpolation!=2)||
            !Finite(curve.frequency)||curve.frequency<=0||curve.frequency>4||
            !Finite(opticalPeaks[i])||opticalPeaks[i]<=0||opticalPeaks[i]>8||keys<2||keys>128)
            throw std::runtime_error("Invalid optics curve");
        curve.keys.clear();curve.keys.reserve(keys);
        for(unsigned j=0;j<keys;++j){
            SourceFxKey k;optics>>tag>>k.t>>k.value>>k.backward>>k.forward;
            if(!optics||tag!="KEY"||!Finite(k.t)||!Finite(k.value)||!Finite(k.backward)||!Finite(k.forward)||
                k.t<0||k.t>10||k.value<0||k.value>opticalPeaks[i]+.00001f||fabs(k.backward)>8||fabs(k.forward)>8||
                (j==0&&fabs(k.t)>.00001f)||(j&&k.t<=curve.keys.back().t))
                throw std::runtime_error("Invalid optics key");
            curve.keys.push_back(k);
        }
        if(curve.keys.back().t<=0||fabs(curve.keys.back().value)>.00001f)
            throw std::runtime_error("Optics curve must dissolve to zero");
    }
    optics>>std::ws;if(!optics.eof())throw std::runtime_error("Unexpected optics fields");
    Log("optics_assets_ready source=ap05_cut_refraction curves=9 peak_normalized=1");
    LoadSourceFacets();
    // 独立只读人形网格烘焙：先验证全部尺寸、长度和索引，再分配；任何损坏发生在安装钩子之前。
    std::ifstream mesh((directory+L"assets\\jce_phantom.bin").c_str(),std::ios::binary);
    char magic[8]={0};mesh.read(magic,8);
    mesh.read(reinterpret_cast<char*>(&phantomAsset.frames),4);mesh.read(reinterpret_cast<char*>(&phantomAsset.vertices),4);
    mesh.read(reinterpret_cast<char*>(&phantomAsset.triangles),4);mesh.read(reinterpret_cast<char*>(&phantomAsset.fps),4);
    mesh.read(reinterpret_cast<char*>(&phantomAsset.duration),4);
    if(!mesh||memcmp(magic,"JCEPHM2",8)||phantomAsset.frames!=403||phantomAsset.vertices!=198||phantomAsset.vertices>256||
        phantomAsset.triangles!=256||phantomAsset.triangles>320||!Finite(phantomAsset.fps)||fabs(phantomAsset.fps-60)>.001f||
        !Finite(phantomAsset.duration)||fabs(phantomAsset.duration-END)>.001f)throw std::runtime_error("Invalid phantom asset header");
    phantomAsset.indices.resize(phantomAsset.triangles*3);
    mesh.read(reinterpret_cast<char*>(&phantomAsset.indices[0]),phantomAsset.indices.size()*2);
    for(size_t i=0;i<phantomAsset.indices.size();++i)if(phantomAsset.indices[i]>=phantomAsset.vertices)throw std::runtime_error("Invalid phantom index");
    phantomAsset.positions.resize(phantomAsset.frames*phantomAsset.vertices);
    for(size_t i=0;i<phantomAsset.positions.size();++i){
        Vector3& q=phantomAsset.positions[i];mesh.read(reinterpret_cast<char*>(&q.x),4);
        mesh.read(reinterpret_cast<char*>(&q.y),4);mesh.read(reinterpret_cast<char*>(&q.z),4);
        if(!mesh||!Finite(q.squaredLength())||q.length()>50.f)throw std::runtime_error("Invalid phantom vertex");
    }
    if(!mesh||mesh.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Invalid phantom asset length");


}
Quaternion Sample(const Track& tr,float time) {
    if(time<=tr.keys.front().t)return tr.keys.front().q;
    if(time>=tr.keys.back().t)return tr.keys.back().q;
    size_t lo=0,hi=tr.keys.size()-1;
    while(hi-lo>1){size_t mid=(lo+hi)/2;if(tr.keys[mid].t<=time)lo=mid;else hi=mid;}
    return Quaternion::Slerp((time-tr.keys[lo].t)/(tr.keys[hi].t-tr.keys[lo].t),tr.keys[lo].q,tr.keys[hi].q,true);
}
Vector3 SampleTranslation(const Track& tr,float time){
    if(time<=tr.keys.front().t)return tr.keys.front().p;
    if(time>=tr.keys.back().t)return tr.keys.back().p;
    size_t lo=0,hi=tr.keys.size()-1;
    while(hi-lo>1){size_t mid=(lo+hi)/2;if(tr.keys[mid].t<=time)lo=mid;else hi=mid;}
    float u=(time-tr.keys[lo].t)/(tr.keys[hi].t-tr.keys[lo].t);
    return tr.keys[lo].p*(1-u)+tr.keys[hi].p*u;
}
// 位置通道只有根骨竖直补偿；保存每个实例快照，退出时恢复，不写Character/SceneNode位置。
struct BoneState {Ogre::OldBone* bone;Quaternion previous;Vector3 previousPosition;};
struct Ghost {float birth;std::vector<Vector3> joints;};
// 依赖头的重载虚函数排列与游戏不同：VC100 把 hand==hand 编为槽0，游戏槽0却是 hand==bool。
// 真实 hand==hand 位于槽1；直接调用已映射的非虚导出，保留原生五字段/空句柄语义。
// 不自行改头/虚表/句柄字段；目标去重也必须走同一接口，避免同一敌人被重复结算。
bool SameHand(const hand& a,const hand& b){return a._NV_operator_equal(b);}
// 2.9.9：快照只持有伤害数值和种族加成值，不保留CharStats/Weapon裸指针。
// bonusRaces的GameData地址仅作不解引用的身份键；同一演出遇到读档/换世界即清理，不能跨世界沿用。
struct WeaponDamageSnapshot {
    float cut,blunt,pierce,stun,bleed,armour,robots,humans,animals;
    std::map<GameData*,float> raceBonuses;bool valid;
    WeaponDamageSnapshot(){Clear();}
    void Clear(){cut=blunt=pierce=stun=armour=0;bleed=robots=humans=animals=1;raceBonuses.clear();valid=false;}
};
struct Runtime : Ogre::SceneManager::Listener, Ogre::RenderObjectListener {
    Settings settings;GameWorld* world;hand caster,castWeapon;WeaponDamageSnapshot castDamage;
    AnimationClass* animation;Ogre::OldSkeletonInstance* skeleton;
    std::vector<BoneState> bones;std::vector<hand> targets,protectedPlayers;std::vector<Ghost> ghosts;
    Ogre::SceneManager* scene;Ogre::SceneNode* node;Ogre::ManualObject* geometry;
    Ogre::TexturePtr background;ID3D11DeviceContext* captureContext;bool refractionReady;unsigned long captureFrame;unsigned captureCopies;
    float poseHeightScale;
    Vector3 anchor;Quaternion facing;
    // 演出状态与时间所有权独立：暂停会把当前速度置零，再从原生缓存恢复施放中的慢速。
    // 结束演出不能清掉恢复债务；旧世界失效则只放弃记录，不再解引用旧指针。
    GameWorld* speedWorld;float ownedSlow;bool speedOwned,speedRestorePending,speedWaitNoted;unsigned speedRestoreErrors;
    double beginning;float time,previousSpeed,layoutScale;
    bool active,cutDone,damageDone,damageArmed,drewWeapon,resourcesAdded,section,wasKey,soundOwned,poseSeen,wrongThreadNoted;
    unsigned castId,poseCalls,queueCalls,renderCalls,poseDiagnostics,fxStages;unsigned long lastQueuedFrame;double lastSummary;bool listenersAdded,queueWarning;
    Runtime():world(0),animation(0),skeleton(0),scene(0),node(0),geometry(0),captureContext(0),refractionReady(false),captureFrame(~0ul),captureCopies(0),poseHeightScale(1),speedWorld(0),ownedSlow(0),speedOwned(false),speedRestorePending(false),speedWaitNoted(false),speedRestoreErrors(0),beginning(0),time(0),previousSpeed(1),layoutScale(1),active(false),cutDone(false),damageDone(false),damageArmed(false),drewWeapon(false),resourcesAdded(false),section(false),wasKey(false),soundOwned(false),poseSeen(false),wrongThreadNoted(false),castId(0),poseCalls(0),queueCalls(0),renderCalls(0),poseDiagnostics(0),fxStages(0),lastQueuedFrame(0),lastSummary(0),listenersAdded(false),queueWarning(false){}
    Character* Resolve() {return caster.getCharacter();}
    Weapon* DamageWeapon(Character* c){
        // 这是当前战斗属性缓存，不是装备栏：原生 drawWeapon 会调用 setWeapon 更新它。
        // hand 每次现场解析；没有缓存时返回空，绝不能把空手公式冒充装备武器伤害。
        CharStats* stats=c?c->getStats():0;
        Item* item=stats&&stats->hasWeapon()?stats->weapon.getItem():0;
        Weapon* weapon=item?item->isWeapon():0;
        return weapon&&weapon->isSword()&&weapon->getCategory()!=SKILL_UNARMED?weapon:0;
    }
    Weapon* PreferredDamageWeapon(Character* c){
        // 已拔出的武器优先，否则由游戏按主/副装备栏、手臂与室内条件选择；不扫描背包。
        // isHuman 是游戏的人形类型查询；动物即使有近似骨架也不强转为 CharacterHuman。
        CharacterHuman* human=c?c->isHuman():0;
        Weapon* weapon=human?human->_NV_getThePreferredWeapon():0;
        return weapon&&weapon->isSword()&&weapon->getCategory()!=SKILL_UNARMED?weapon:0;
    }
    bool EquippedWeapon(Character* c,Weapon* weapon){
        // 启动资格只认可游戏选中的装备栏武器；背包内有武器不算携带可攻击装备。
        if(!c||!weapon)return false;Inventory* inventory=c->_NV_getInventory();if(!inventory)return false;
        lektor<Item*> equipped;inventory->getEquippedWeapons(equipped);
        const hand& selected=weapon->getHandle();
        for(unsigned i=0;i<equipped.size();++i)
            if(equipped[i]&&SameHand(selected,equipped[i]->getHandle()))return true;
        return false;
    }
    bool SameDamageWeapon(Character* c){
        // 仅在U键准备快照时验证游戏选择的武器仍属于本角色装备栏，动物/背包不当作可用武器。
        // 用户明确要求：快照成功后，即使演出中卸下或换装也照原快照结算，不再调用此函数撤销伤害。
        if(!c||!c->isValid()||c->isDestroyed())return false;
        Weapon* preferred=PreferredDamageWeapon(c);
        if(!preferred||!SameHand(castWeapon,preferred->getHandle()))return false;
        return EquippedWeapon(c,preferred);
    }
    bool DamageCacheMatches(Character* c){
        Weapon* cached=DamageWeapon(c);
        return cached&&SameHand(castWeapon,cached->getHandle());
    }
    bool CaptureDamageSnapshot(Character* c){
        castDamage.Clear();
        if(!world||world!=ou||world->isLoadingFromASaveGame()||!SameDamageWeapon(c)||!DamageCacheMatches(c))return false;
        CharStats* stats=c->getStats();if(!stats)return false;
        // 本机原生getTotalAttackDamageFor显式支持target=NULL：跳过目标种族分支，仍计算完整攻击伤害/skillMultDamage。
        // 先冻结这一公共基准，再冻结对机器人、人形、动物和特定种族的加成；不把目标列表锁在U键时。
        // NULL分支不赋bonusArmourPenetration，故独立保存该参数；收刀时只读目标当前类型并套用快照。
        Damages base=stats->getTotalAttackDamageFor(0);
        if(!ValidDamage(base)||double(base.cut)+base.blunt+base.pierce+base.extraStun<=0)return false;
        if(!Finite(stats->bonusArmourPenetration)||!Finite(stats->bonusRobots)||!Finite(stats->bonusHumans)||!Finite(stats->bonusAnimals))return false;
        if(stats->bonusRobots<0||stats->bonusHumans<0||stats->bonusAnimals<0||stats->bonusRaces.size()>4096)return false;
        castDamage.cut=base.cut;castDamage.blunt=base.blunt;castDamage.pierce=base.pierce;
        castDamage.stun=base.extraStun;castDamage.bleed=base.bleedMult;castDamage.armour=stats->bonusArmourPenetration;
        castDamage.robots=stats->bonusRobots;castDamage.humans=stats->bonusHumans;castDamage.animals=stats->bonusAnimals;
        typedef std::map<GameData*,float,std::less<GameData*>,Ogre::STLAllocator<std::pair<GameData* const,float>,Ogre::GeneralAllocPolicy> > NativeRaceBonuses;
        for(NativeRaceBonuses::const_iterator i=stats->bonusRaces.begin();i!=stats->bonusRaces.end();++i){
            if(!i->first||!Finite(i->second)||i->second<0){castDamage.Clear();return false;}
            castDamage.raceBonuses[i->first]=i->second;
        }
        // 只在全部校验成功后发布；此后换武器/收鞘/力量变化均不重读攻击方stats。
        castDamage.valid=true;return true;
    }
    Damages SnapshotDamageFor(Character* target){
        Damages d(castDamage.cut,castDamage.blunt,castDamage.pierce,castDamage.bleed,castDamage.armour);d.extraStun=castDamage.stun;
        // 原生优先判断robot种族，再分动物/人形；机器人不按肉体与义肢比例归类。
        // 特定种族加成只乘伤害四通道，bleed/armour仍保持快照值，护甲和随机部位继续交原生addWound处理。
        RaceData* race=target?target->_NV_getRace():0;
        if(!castDamage.valid||!race){d.cut=d.blunt=d.pierce=d.extraStun=0;return d;}
        float mult=race->robot?castDamage.robots:target->isAnimal()?castDamage.animals:target->isHuman()?castDamage.humans:1.f;
        std::map<GameData*,float>::const_iterator specific=castDamage.raceBonuses.find(race->data);
        if(specific!=castDamage.raceBonuses.end())mult*=specific->second;
        d.multiply(mult);return d;
    }
    void PrepareWeapon(Character* c){
        castWeapon.setNull();castDamage.Clear();damageArmed=false;drewWeapon=false;
        if(!settings.damage)return;
        Weapon* before=DamageWeapon(c);Weapon* weapon=PreferredDamageWeapon(c);
        std::string beforeHandle=before?before->getHandle().toString():"none";
        CharacterHuman* human=c->isHuman();bool attempted=false,drawOK=false;
        if(weapon&&human){
            castWeapon=weapon->getHandle();
            bool equipped=SameDamageWeapon(c);
            if(equipped&&(human->_NV_getCurrentWeapon()!=weapon||!DamageCacheMatches(c))){
                // 通过游戏原生流程同时建立手持模型和伤害缓存，不能直接 setWeapon 后回滚。
                // 记录施放前收鞘的所有权；若原生调用部分成功后抛错，Finish 仍按 hand 检查收刀。
                attempted=true;
                bool alreadyHeld=human->_NV_getCurrentWeapon()==weapon;
                if(!alreadyHeld)drewWeapon=true;
                // drawWeapon对已手持同把武器会提前返回，不刷新空缓存；U键准备阶段仅做一次完整收拔。
                // 未接管原本已经手持的收刀所有权；不在后续帧或结算时再次拔刀。
                try{if(alreadyHeld)human->_NV_sheatheWeapon();drawOK=human->_NV_drawWeapon(weapon,weapon->inventorySection);}
                catch(const std::exception& e){Log(std::string("weapon_prepare_error: ")+e.what());}
            }else drawOK=equipped;
            damageArmed=drawOK&&CaptureDamageSnapshot(c);
        }
        // 每次准备一条诊断，区分实际无装备、收鞘缓存未就绪和原生拔刀失败；启用伤害时由Begin拒绝启动。
        Weapon* after=DamageWeapon(c);
        std::ostringstream s;s<<"weapon_prepare cache_before="<<beforeHandle<<" preferred="<<castWeapon.toString()
            <<" cache_after="<<(after?after->getHandle().toString():"none")
            <<" draw_attempted="<<attempted<<" draw_ok="<<drawOK<<" damage_armed="<<damageArmed;Log(s.str());
        if(damageArmed){
            std::ostringstream snapshot;snapshot<<"weapon_damage_snapshot next_id="<<(castId+1)<<" weapon="<<castWeapon.toString()
                <<" cut="<<castDamage.cut<<" blunt="<<castDamage.blunt<<" pierce="<<castDamage.pierce<<" stun="<<castDamage.stun
                <<" bleed="<<castDamage.bleed<<" armour="<<castDamage.armour<<" robot_bonus="<<castDamage.robots
                <<" human_bonus="<<castDamage.humans<<" animal_bonus="<<castDamage.animals<<" race_bonuses="<<castDamage.raceBonuses.size()
                <<" policy=u_key_snapshot equipment_change_after_begin=ignored";Log(snapshot.str());
        }else Log("weapon_snapshot_not_ready: begin_will_reject");
    }
    void RestoreWeapon(Character* c){
        // 仅收回本插件从收鞘状态拔出的同一个 serial hand；已有手持/换装/旧世界均不接管。
        // 死亡/昏迷/断肢/离队或加载取消时，只释放插件控制，不替失去资格的角色执行原生收刀。
        if(!drewWeapon||CasterBlockedReason(c))return;
        CharacterHuman* human=c->isHuman();Item* item=castWeapon.getItem();
        Weapon* owned=item?item->isWeapon():0;
        Inventory* inventory=c->_NV_getInventory();
        // 卸下/转交不撤销伤害，但清理绝不接管已经转交或移出本角色库存的武器。
        if(human&&owned&&inventory&&inventory->hasItem(owned)&&human->_NV_getCurrentWeapon()==owned){
            try{human->_NV_sheatheWeapon();Log("weapon_restore: owned_draw_sheathed");}
            catch(const std::exception& e){Log(std::string("weapon_restore_error: ")+e.what());}
        }else Log("weapon_restore_skipped: ownership_changed");
    }
    bool ValidDamage(const Damages& d){
        // 正负护甲穿透保持原公式；所有通道先拒绝 NaN/Inf，伤害通道不允许负值。
        return Finite(d.cut)&&Finite(d.blunt)&&Finite(d.pierce)&&Finite(d.extraStun)
            &&Finite(d.bleedMult)&&Finite(d.armourPenetration)
            &&d.cut>=0&&d.blunt>=0&&d.pierce>=0&&d.extraStun>=0&&d.bleedMult>=0;
    }
    bool CharacterReady(Character* c){return c&&c->isValid()&&!c->isDestroyed()&&!c->isDead()&&!c->medical.unconcious&&!c->isRagdoll()&&!c->isBeingCarried();}
    bool CurrentPlayerMember(Character* c){
        // 取全部玩家角色，不限当前选中角色/当前小队/是否倒地；不得用敌对关系推导玩家归属。
        if(!c||!world||world!=ou||!world->player||world->isLoadingFromASaveGame())return false;
        const PlayerInterface* player=world->player;
        const lektor<Character*>& members=player->getAllPlayerCharacters();
        if(members.size()>4096)return false; // 异常名单不继续施放，避免无界扫描。
        for(unsigned i=0;i<members.size();++i)if(members[i]==c)return true;
        return false;
    }
    bool ProtectedPlayer(Character* c){
        // 玩家保护优先于敌对判定：当前玩家标记、全部玩家名单、本轮起始名单任一匹配就排除。
        // 名单只保存serial hand；原成员中途离队仍保护，新成员在每击前按当前名单保护。
        if(!c||!world||world!=ou||!world->player||world->isLoadingFromASaveGame())return true;
        if(c->isPlayerCharacter()||CurrentPlayerMember(c))return true;
        const hand& h=c->getHandle();
        for(size_t i=0;i<protectedPlayers.size();++i)if(SameHand(protectedPlayers[i],h))return true;
        return false;
    }
    void CaptureProtectedPlayers(){
        protectedPlayers.clear();
        if(!world||world!=ou||!world->player||world->isLoadingFromASaveGame())throw std::runtime_error("Player roster unavailable");
        const PlayerInterface* player=world->player;
        const lektor<Character*>& members=player->getAllPlayerCharacters();
        if(members.size()>4096)throw std::runtime_error("Player roster exceeds safety bound");
        for(unsigned i=0;i<members.size();++i){
            Character* member=members[i];if(member&&member->isValid()&&!member->isDestroyed())protectedPlayers.push_back(member->getHandle());
        }
    }
    const char* CasterBlockedReason(Character* c){
        // 启动、每帧和每击共用同一资格；这里不检查武器，卸下武器仍按U键快照结算。
        if(!world||world!=ou||!world->player)return "caster_world_unavailable";
        if(world->isLoadingFromASaveGame())return "loading";
        if(!c||!c->isValid()||c->isDestroyed())return "caster_invalid";
        if(c->isDead())return "caster_dead";
        if(c->medical.unconcious||c->_NV_isUnconcious())return "caster_unconscious";
        if(c->isRagdoll()||c->isBeingCarried()||c->isCarryingSomething)return "caster_unable";
        if(!c->isHuman()||c->isAnimal())return "caster_not_humanoid"; // 人形机器人允许，不以robot种族标志排除。
        if(!c->isPlayerCharacter()||!CurrentPlayerMember(c))return "caster_left_player_roster";
        const char* missing[]={"caster_left_arm_missing","caster_right_arm_missing","caster_left_leg_missing","caster_right_leg_missing"};
        const char* injured[]={"caster_left_arm_injured","caster_right_arm_injured","caster_left_leg_injured","caster_right_leg_injured"};
        for(int i=0;i<4;++i){
            RobotLimbs::Limb limb=static_cast<RobotLimbs::Limb>(i);
            LimbState state=c->medical.getLimbState(limb);
            if(state!=LIMB_ORIGINAL&&state!=LIMB_REPLACED)return missing[i];
            MedicalSystem::HealthPartStatus* part=c->medical.getPart(limb);
            if(!part||part->me!=c||part->medical!=&c->medical||(state==LIMB_REPLACED&&!part->robotLimb))return missing[i];
            // 原生setRobotLimbItem把义肢实时健康映射到flesh/fleshStun；不要读卸下物品的过期currentDamage。
            // 原生派生健康为flesh-fleshStun+juryRigging；同时拒绝flesh<0，不能靠临时维修掩盖负血量。
            // 严格小于0才拒绝，0符合用户边界；NaN/Inf及未初始化部位一律拒绝，避免加载中误放。
            float health=part->flesh-part->fleshStun+part->juryRigging;
            float maximum=part->maxHealth();
            if(!Finite(part->flesh)||!Finite(part->fleshStun)||!Finite(part->juryRigging)||!Finite(health)||!Finite(maximum)||maximum<=0||part->flesh<0||health<0)return injured[i];
        }
        return 0;
    }
    Renderer* Render(){return world&&world->render?static_cast<Renderer*>(world->render):0;}
    bool SameRenderer(){Renderer* r=Render();return r&&r->getSceneManager()==scene;}
    bool SameAnimation(Character* c){return c&&c->getAnimationClass()==animation&&animation&&animation->skeleton==skeleton&&animation->body&&skin.skeleton(animation->body)==skeleton;}
    bool Foreground(){DWORD pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&pid);return pid==GetCurrentProcessId();}
    bool Editing(){MyGUI::InputManager* im=MyGUI::InputManager::getInstancePtr();MyGUI::Widget* f=im?im->getKeyFocusWidget():0;return f&&f->castType<MyGUI::EditBox>(false);}
    // 只提交本插件的几何，挂在官方“可见物搜索之后”的扩展点。
    // 不依赖游戏对自定义 MovableObject 类型的可见物扫描；CPU 剔除仅对这个有界短时特效绕过，
    // GPU 的深度测试仍保留。关闭自动可见性避免同一段几何被自动和手动重复提交。
    virtual void postFindVisibleObjects(Ogre::SceneManager* source,Ogre::SceneManager::IlluminationRenderStage stage,Ogre::Viewport*){
        Guard lock(gate);
        if(!active||world!=ou||!section||source!=scene||!geometry||stage!=Ogre::SceneManager::IRS_NONE)return;
        Ogre::Camera* current=source->getCameraInProgress();
        if(!Render()||current!=Render()->getCamera())return; // 不污染阴影、图标与小地图相机。
        // 同一相机会依次渲染 GBuffer、天空、水和粒子。不能在每个阶段都硬插 queue 83：
        // 等相机本帧的队列状态包含 83 后才提交，并以 Root 帧号去重，避免误写 GBuffer/后续调试通道。
        unsigned long frame=Render()->getRoot()->getNextFrameNumber();
        if(!current->isRenderedRq(83)||(queueCalls&&lastQueuedFrame==frame))return;
        try{
            // 2.9.6独立模式先画本对象刀光/雾，再在折射段入口捕获包含它们的HDR并切裂整幅局部图像。
            // 复制时点与优先级必须配套：后画却仍复制旧背景会擦除刀光；不能只交换队列顺序。
            // 旧0/1/2模式继续先折射再视觉；仅排列本对象11段，不改全局队列/其他材质，深度测试保留。
            if(geometry->getNumSections()!=FX_SECTIONS)throw std::runtime_error("Incomplete VFX sections");
            Ogre::RenderQueue* queue=source->getRenderQueue();
            for(unsigned i=0;i<FX_SECTIONS;++i){
                unsigned short priority=static_cast<unsigned short>(i==3?(settings.opticalProbeMode>=3?111:100):(i<3?101+i:100+i));
                queue->addRenderable(geometry->getSection(i),83,priority);
            }
            lastQueuedFrame=frame;
            if(++queueCalls==1)Log("vfx_queue_submitted id="+Number(castId));
        }catch(const std::exception& e){Log(std::string("vfx_queue_error: ")+e.what());}
    }
    // 该回调位于单对象渲染入口，比“顶点已生成”多一层证据，但仍不能保证像素可见。
    virtual void notifyRenderSingleObject(Ogre::Renderable* rend,const Ogre::Pass*,const Ogre::AutoParamDataSource*,const Ogre::LightList*,bool){
        Guard lock(gate);
        if(active&&geometry&&section){
            // 2.9.6独立模式只在section3实际渲染前复制，此时前面的自有刀光/烟层已在HDR里。
            // 旧模式仍在实际首个自有段前复制；CaptureBackground的帧号去重/资源归属/失败透明不变。
            // 仍每帧至多一个独立副本，不从正在写入的渲染目标直接采样，也不重复捕获每张裂面。
            for(unsigned i=0;i<FX_SECTIONS;++i)if(rend==geometry->getSection(i)){
                if(settings.opticalProbeMode<3||i==3)CaptureBackground();
                if(++renderCalls==1)Log("vfx_render_callback id="+Number(castId));break;
            }
        }
    }
    static std::string Number(unsigned value){std::ostringstream s;s<<value;return s.str();}
    virtual void sceneManagerDestroyed(Ogre::SceneManager* source){
        Guard lock(gate);
        if(source==scene){ReleaseRefraction();geometry=0;node=0;scene=0;section=false;listenersAdded=false;}
    }

    void ReleaseRefraction(){
        refractionReady=false;
        if(captureContext){captureContext->Release();captureContext=0;}
        if(!background.isNull()){
            // 先断开材质引用，再移除本插件纹理；关机时管理器可能已析构，先查指针避免Singleton断言。
            try{Ogre::MaterialManager* manager=Ogre::MaterialManager::getSingletonPtr();
                Ogre::MaterialPtr m=manager?manager->getByName("JCE/Refraction",GROUP):Ogre::MaterialPtr();
                if(!m.isNull())m->getTechnique(0)->getPass(0)->getTextureUnitState(1)->setTextureName("jce_glow.tga");
            }catch(const std::exception& e){Log(std::string("refraction_material_release_error: ")+e.what());}
            // 材质断开失败也独立移除自己的管理器项；限定基类调用避免重载虚槽差异。
            try{Ogre::TextureManager* manager=Ogre::TextureManager::getSingletonPtr();
                if(manager)manager->Ogre::ResourceManager::remove(Ogre::String("JCE/SceneCopy"));}
            catch(const std::exception& e){Log(std::string("refraction_texture_release_error: ")+e.what());}
            background.setNull();
        }
    }
    void PrepareRefraction(){
        refractionReady=false;captureFrame=~0ul;captureCopies=0;
        try{
            Renderer* r=Render();ID3D11Device* device=0;
            if(!r||!r->window)throw std::runtime_error("Window unavailable");
            r->window->getCustomAttribute("D3DDEVICE",&device); // 借用指针，不释放窗口的设备引用。
            if(!device)throw std::runtime_error("No D3D11 device");
            unsigned width=r->window->getWidth(),height=r->window->getHeight();
            if(width<1||height<1||width>4096||height>4096)throw std::runtime_error("Refraction viewport budget exceeded");
            // 本机Lighting_HDR使用PF_R11G11B10_FLOAT；严格匹配，不在渲染回调临时重建纹理。
            background=Ogre::TextureManager::getSingleton().createManual("JCE/SceneCopy",GROUP,Ogre::TEX_TYPE_2D,
                width,height,1,0,Ogre::PF_R11G11B10_FLOAT,Ogre::TU_RENDERTARGET,0,false,0);
            Ogre::MaterialPtr m=Ogre::MaterialManager::getSingleton().getByName("JCE/Refraction",GROUP);
            if(m.isNull())throw std::runtime_error("Refraction material missing");
            m->getTechnique(0)->getPass(0)->getTextureUnitState(1)->_setTexturePtr(background);
            m->load();if(!m->getBestTechnique())throw std::runtime_error("Refraction shader unsupported");
            m->getTechnique(0)->getPass(0)->getFragmentProgramParameters()->setNamedConstant("captureValid",0.f);
            device->GetImmediateContext(&captureContext);if(!captureContext)throw std::runtime_error("Immediate context unavailable");
            refractionReady=true;
            Log("refraction_prepared; independent_HDR_copy; CPU_readback=0");
        }catch(const std::exception& e){ReleaseRefraction();Log(std::string("refraction_disabled: ")+e.what());}
    }
    void CaptureBackground(){
        if(!refractionReady||!captureContext||background.isNull())return;
        unsigned long frame=Render()->getRoot()->getNextFrameNumber();if(captureFrame==frame)return;
        captureFrame=frame;
        try{
            ComOwned<ID3D11RenderTargetView> view;captureContext->OMGetRenderTargets(1,&view.p,0);
            if(!view.p)throw std::runtime_error("No bound HDR target");
            ComOwned<ID3D11Resource> source;view.p->GetResource(&source.p);
            ComOwned<ID3D11Texture2D> texture;
            if(FAILED(source.p->QueryInterface(__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(&texture.p))))
                throw std::runtime_error("HDR target is not Texture2D");
            ID3D11Texture2D* destination=0; // Ogre纹理拥有它，此处只是借用。
            background->getBuffer(0,0)->getRenderTarget()->getCustomAttribute("ID3D11Texture2D",&destination);
            if(!destination||destination==texture.p)throw std::runtime_error("Invalid independent scene copy");
            D3D11_TEXTURE2D_DESC src,dst;texture.p->GetDesc(&src);destination->GetDesc(&dst);
            if(src.Width!=dst.Width||src.Height!=dst.Height||src.Format!=dst.Format||src.SampleDesc.Count!=1||
                src.MipLevels!=dst.MipLevels||src.ArraySize!=1||dst.ArraySize!=1||src.SampleDesc.Quality!=dst.SampleDesc.Quality||dst.SampleDesc.Count!=1)
                throw std::runtime_error("HDR copy format/viewport changed");
            // 若副本仍被上一通道作为SRV绑定，短暂解绑后原样恢复，避免DX11读写资源冲突；
            // COM getter持有的每个引用由局部所有者释放。不触碰渲染目标、着色器、暂停或相机状态。
            ComOwned<ID3D11ShaderResourceView> old;captureContext->PSGetShaderResources(1,1,&old.p);
            ID3D11ShaderResourceView* none=0;captureContext->PSSetShaderResources(1,1,&none);
            captureContext->CopyResource(destination,texture.p);
            captureContext->PSSetShaderResources(1,1,&old.p);
            Ogre::MaterialPtr m=Ogre::MaterialManager::getSingleton().getByName("JCE/Refraction",GROUP);
            m->getTechnique(0)->getPass(0)->getFragmentProgramParameters()->setNamedConstant("captureValid",1.f);
            if(++captureCopies==1)Log("refraction_capture_ready; copies_per_frame<=1");
        }catch(const std::exception& e){
            // 故障仅关闭折射，其他三层继续演出；不销毁当前队列正在使用的纹理。
            refractionReady=false;
            try{Ogre::MaterialPtr m=Ogre::MaterialManager::getSingleton().getByName("JCE/Refraction",GROUP);
                if(!m.isNull())m->getTechnique(0)->getPass(0)->getFragmentProgramParameters()->setNamedConstant("captureValid",0.f);
            }catch(...){}
            Log(std::string("refraction_capture_disabled: ")+e.what());
        }
    }
    void MakeResources(){
        Renderer* r=Render();if(!r)throw std::runtime_error("Renderer not ready");scene=r->getSceneManager();if(!scene)throw std::runtime_error("Scene missing");
        if(!resourcesAdded){
            int n=WideCharToMultiByte(CP_UTF8,0,(directory+L"assets").c_str(),-1,0,0,0,0);std::vector<char> utf8(n);
            WideCharToMultiByte(CP_UTF8,0,(directory+L"assets").c_str(),-1,&utf8[0],n,0,0);
            Ogre::ResourceGroupManager& rm=Ogre::ResourceGroupManager::getSingleton();
            rm.addResourceLocation(&utf8[0],"FileSystem",GROUP);rm.initialiseResourceGroup(GROUP);resourcesAdded=true;
        }
        // 脚本解析成功不代表材质/纹理实际加载；此处显式加载并拒绝无可用 technique 的演出。
        Ogre::MaterialPtr mat=Ogre::MaterialManager::getSingleton().getByName("JCE/Glow",GROUP);
        if(mat.isNull())throw std::runtime_error("JCE/Glow material is missing");
        mat->load();
        if(!mat->getBestTechnique())throw std::runtime_error("JCE/Glow has no supported technique");
        Log("vfx_material_loaded group=JudgementCutEnd/Resources/v1");
        // 新雾/玻璃材质同样显式加载，任何缺资源均走Begin失败和已有清理路径。
        const char* extra[]={"JCE/Mist","JCE/Glass","JCE/SourceBlade","JCE/SourceFeather","JCE/SourceDust","JCE/SourceFlash","JCE/SourceSpark","JCE/SourceSmokeRibbon","JCE/SourceSmokeWisp"};
        // 所有自有材质逐个预加载；新增烟带/烟丝缺失仍走Begin失败清理，禁止半途缺层。
        for(unsigned i=0;i<sizeof(extra)/sizeof(extra[0]);++i){
            Ogre::MaterialPtr layer=Ogre::MaterialManager::getSingleton().getByName(extra[i],GROUP);
            if(layer.isNull())throw std::runtime_error("Missing VFX layer material");
            layer->load();if(!layer->getBestTechnique())throw std::runtime_error("Unsupported VFX layer material");
        }
        PrepareRefraction();
        node=scene->getRootSceneNode()->createChildSceneNode();
        geometry=scene->createManualObject();geometry->setDynamic(true);
        // 原版 main.compositor 的 82–85 是 HDR 粒子通道；默认 50 会误入 GBuffer。
        geometry->setRenderQueueGroup(83);geometry->setCastShadows(false);geometry->estimateVertexCount(VFX_VERTEX_LIMIT);geometry->estimateIndexCount(VFX_INDEX_LIMIT);
        node->attachObject(geometry);geometry->setVisible(false);section=false;
        scene->addListener(this);listenersAdded=true;scene->addRenderObjectListener(this);
    }
    void RestoreTime(const char* reason,bool validWorld=true){
        if(!speedOwned)return;
        // 不改暂停开关，不访问换掉的世界。恢复使用原生接口，避免直接写字段或修改暂停缓存。
        if(!validWorld||!world||speedWorld!=world||speedWorld!=ou){
            Log(std::string("time_restore_abandoned: world_replaced reason=")+reason);
            speedOwned=speedRestorePending=false;speedWorld=0;return;
        }
        try{
            float current=world->getFrameSpeedMultiplier();
            if(world->isPaused()||!Finite(current)||current<=0){
                // 保留玩家暂停；解除暂停后的帧回调会先恢复速度，再处理新的U键快照。
                speedRestorePending=true;
                if(!speedWaitNoted){speedWaitNoted=true;std::ostringstream s;s<<"time_restore_deferred id="<<castId<<" reason="<<reason<<" current="<<current<<" paused="<<world->isPaused()<<" expected="<<previousSpeed;Log(s.str());}
                return;
            }
            bool owned=fabs(current-ownedSlow)<.00005f;
            bool restored=fabs(current-previousSpeed)<.00005f;
            if(!owned||restored){
                // 玩家选择1/2/3倍或其他插件接管速度时保留新值；仅已知的本次慢速可以被回收。
                std::ostringstream s;s<<"time_restore_released id="<<castId<<" reason="<<reason<<" current="<<current<<" expected="<<previousSpeed<<" external="<<(!restored);Log(s.str());
                speedOwned=speedRestorePending=false;speedWorld=0;return;
            }
            world->setFrameSpeedMultiplier(previousSpeed);
            float after=world->getFrameSpeedMultiplier();
            bool verified=Finite(after)&&fabs(after-previousSpeed)<.00005f;
            if(verified){
                std::ostringstream s;s<<"time_restored id="<<castId<<" reason="<<reason<<" before="<<current<<" after="<<after<<" expected="<<previousSpeed;Log(s.str());
                speedOwned=speedRestorePending=false;speedWorld=0;
            }else{
                speedRestorePending=true;
                if(speedRestoreErrors<3){++speedRestoreErrors;std::ostringstream s;s<<"time_restore_unverified id="<<castId<<" after="<<after<<" expected="<<previousSpeed;Log(s.str());}
            }
        }catch(const std::exception& e){
            // 时间接口失败也不丢弃快照；后续帧重试，诊断至多三条，避免空闲逐帧刷日志。
            speedRestorePending=true;if(speedRestoreErrors<3){++speedRestoreErrors;Log(std::string("time_restore_error: ")+e.what());}
        }
    }
    void Begin(Character* c,double now){
        // 恢复债务未清偿时拒绝新快照，防止把0.001记成新的“正常速度”。
        if(speedOwned)throw std::runtime_error("Previous world speed restoration pending");
        const char* blocked=CasterBlockedReason(c);if(blocked)throw std::runtime_error(blocked);
        // 武器仅是启动条件；无装备栏近战武器不得进入演出，后续帧不重新要求携带。
        if(!EquippedWeapon(c,PreferredDamageWeapon(c)))throw std::runtime_error("caster_requires_equipped_melee_weapon");
        castWeapon.setNull();castDamage.Clear();protectedPlayers.clear();damageArmed=false;drewWeapon=false;
        animation=c->getAnimationClass();if(!animation||!animation->isHuman()||!animation->skeleton||!animation->node||!animation->getIsActivated())throw std::runtime_error("No active humanoid skeleton");
        skeleton=animation->skeleton;bones.clear();
        // 保留可见身体身份校验，但必须由真实 DLL 接口取值；错误内联偏移曾误拒绝所有施放。
        Ogre::Entity* body=animation->body;
        Ogre::OldSkeletonInstance* visible=body?skin.skeleton(body):0;
        bool initialised=body&&skin.initialised(body);
        // 每进程最多四条绑定证据，明确区分未初始化、真正换骨架及 ABI 取值问题。
        static unsigned bindingChecks=0;
        if(bindingChecks++<4){std::ostringstream s;s<<"skin_binding_checked body="<<body<<" animation_skeleton="<<skeleton
            <<" visible_skeleton="<<visible<<" initialised="<<initialised<<" match="<<(visible==skeleton);Log(s.str());}
        if(!body||!initialised||visible!=skeleton)throw std::runtime_error("Visible body/skeleton mismatch");
        const Ogre::Entity::EntitySet* shared=skin.sharing(body);
        if(shared&&shared->size()>64)throw std::runtime_error("Too many shared skin entities");
        const char* required[]={"Bip01 L Thigh","Bip01 R Thigh","Bip01 L Calf","Bip01 R Calf","Bip01 L Foot","Bip01 R Foot","Bip01 Pelvis"};
        for(int i=0;i<7;++i)if(!skeleton->hasBone(required[i]))throw std::runtime_error("Missing VFX joint");
        // 必须所有轨道均可绑定；已有手动骨骼代表其他姿势所有者，拒绝抢占。
        for(size_t i=0;i<clip.size();++i){
            if(!skeleton->hasBone(clip[i].name))throw std::runtime_error("Incompatible skeleton bone: "+clip[i].name);
            BoneState b;b.bone=skeleton->getBone(clip[i].name);if(b.bone->isManuallyControlled())throw std::runtime_error("Another plugin owns pose bone");
            b.previous=b.bone->getOrientation();b.previousPosition=b.bone->getPosition();bones.push_back(b);
        }
        // 根骨高度按实例缩放竖直补偿，保持男女/身材差异；不改变骨长、横向根位移或角色坐标。
        poseHeightScale=Clamp(fabsf(skeleton->getBone("Bip01")->getInitialPosition().y)/9.98592377f,.5f,2.f);
        previousSpeed=world->getFrameSpeedMultiplier();if(!Finite(previousSpeed)||previousSpeed<=0)throw std::runtime_error("Paused/invalid world speed");
        MakeResources();anchor=c->getPosition();facing=animation->getSceneNodeOrientation();caster=c->getHandle();
        FitSlashLayout(); // 每次按实际角色朝向拟合，包含光带半宽，不让最长裂痕越过350圆。
        PrepareWeapon(c);
        if(!EquippedWeapon(c,PreferredDamageWeapon(c)))throw std::runtime_error("caster_weapon_lost_during_begin");
        if(settings.damage&&!damageArmed)throw std::runtime_error("weapon_damage_snapshot_not_ready");
        blocked=CasterBlockedReason(c);if(blocked)throw std::runtime_error(blocked);
        CaptureProtectedPlayers(); // 冻结本轮起始队员保护名单，范围不限当前小队。
        beginning=now;time=0;cutDone=damageDone=false;targets.clear();ghosts.clear();poseSeen=false;wrongThreadNoted=false;poseCalls=0;queueCalls=renderCalls=0;poseDiagnostics=0;fxStages=0;queueWarning=false;lastSummary=now;
        active=true;InterlockedExchangePointer(&poseOwner,animation);
        for(size_t i=0;i<bones.size();++i)bones[i].bone->setManuallyControlled(true);
        // active 在全部前提具备后发布；全状态都由 gate 保护，不插入共享 Skeleton 动画缓存。
        active=true;++castId;
        // 写慢速前先发布所有权；即使原生setter抛异常，Finish也知道仍需恢复哪个快照。
        speedWorld=world;ownedSlow=settings.slow;speedOwned=true;speedRestorePending=false;speedWaitNoted=false;speedRestoreErrors=0;
        world->setFrameSpeedMultiplier(settings.slow);
        if(settings.sound){soundOwned=PlaySoundW((directory+L"assets\\jce_sequence_fast.wav").c_str(),0,SND_FILENAME|SND_ASYNC|SND_NODEFAULT)!=FALSE;}
        // 用户自行选择镜头距离与朝向；演出开始、结束都不写相机或跟随目标。
        std::ostringstream s;s<<"cast_begin id="<<castId<<" caster="<<caster.toString()<<" speed_before="<<previousSpeed<<" slow="<<settings.slow<<" tracks="<<bones.size()<<" radius="<<settings.radius<<" area_radius="<<AreaRadius()<<" area_shape=horizontal_circle layout_scale="<<layoutScale<<" damage="<<settings.damage<<" weapon="<<castWeapon.toString()<<" damage_armed="<<damageArmed<<" damage_multiplier="<<settings.damageMultiplier<<" playback_rate="<<PLAYBACK_RATE<<" real_duration="<<END/PLAYBACK_RATE<<" sound_started="<<soundOwned;Log(s.str());
    }
    void ReleaseGraphics(bool validScene){
        if(validScene&&scene){
            // 回收顺序先解除监听，再销毁被监听对象，防止下一次提交引用已释放的 section。
            if(listenersAdded){scene->removeRenderObjectListener(this);scene->removeListener(this);}
            if(geometry){if(node)node->detachObject(geometry);scene->destroyManualObject(geometry);}
            if(node)scene->destroySceneNode(node);
        }
        ReleaseRefraction();
        geometry=0;node=0;scene=0;section=false;listenersAdded=false;
    }
    void Finish(const char* reason,bool validWorld=true){
        bool wasActive=active;active=false;
        // 先恢复时间，再进行可能抛异常的骨骼/武器/图形清理；不依赖已经清掉的active。
        if(speedOwned)speedRestorePending=true;
        RestoreTime(reason,validWorld);
        bool validScene=validWorld&&world==ou&&SameRenderer();
        Character* c=validWorld&&world==ou?Resolve():0;
        if(wasActive&&c&&c->isValid()&&!c->isDestroyed()&&SameAnimation(c)){
            // 位置与朝向作为同一所有权快照恢复；未触碰逻辑 Character/SceneNode 位置，也不留下累加根位移。
            for(size_t i=0;i<bones.size();++i){bones[i].bone->setPosition(bones[i].previousPosition);bones[i].bone->setOrientation(bones[i].previous);bones[i].bone->setManuallyControlled(false);}
            skeleton->_updateTransforms();
            try{RefreshSkin();}catch(const std::exception& e){Log(std::string("pose_restore_skin_error: ")+e.what());}
        }
        RestoreWeapon(c);
        if(soundOwned){PlaySoundW(0,0,0);soundOwned=false;}
        InterlockedExchangePointer(&poseOwner,0);
        ReleaseGraphics(validScene);bones.clear();targets.clear();protectedPlayers.clear();ghosts.clear();animation=0;skeleton=0;caster.setNull();castWeapon.setNull();castDamage.Clear();damageArmed=false;drewWeapon=false;
        if(wasActive){std::ostringstream s;s<<"cast_end id="<<castId<<" reason="<<reason<<" pose_calls="<<poseCalls<<" queue_calls="<<queueCalls<<" render_calls="<<renderCalls<<" world_valid="<<validWorld<<" cooldown_real_seconds=0 time_owned="<<speedOwned<<" time_restore_pending="<<speedRestorePending;Log(s.str());}
    }
    unsigned RefreshSkin(){
        // 本机 updateAnimation 在 skip=true 时连 cacheBoneMatrices 都不调用（0.2.2 矩阵误差非零）。
        // cacheBoneMatrices 自身仍能在 skip=true 时生成矩阵，只跳过旧 AnimationState 重放。
        // 因此作用域内先显式 cache，再重新标记 dirty 强制世界矩阵更新；不能仅靠 _updateAnimation。
        // 只处理施法者的实例和同骨架衣物；真实导出绑定，不硬写字段、矩阵数组或共享动画资源。
        Ogre::Entity* body=animation?animation->body:0;
        if(!body||!skin.initialised(body)||skin.skeleton(body)!=skeleton)
            throw std::runtime_error("Skin binding changed");
        std::vector<Ogre::Entity*> entities;entities.push_back(body);
        const Ogre::Entity::EntitySet* sharing=skin.sharing(body);
        if(sharing){
            if(sharing->size()>64)throw std::runtime_error("Too many shared skin entities");
            for(Ogre::Entity::EntitySet::const_iterator i=sharing->begin();i!=sharing->end();++i)
                if(*i&&*i!=body&&skin.initialised(*i)&&skin.skeleton(*i)==skeleton){
                    if(entities.size()>=64)throw std::runtime_error("Too many shared skin entities");
                    entities.push_back(*i);
                }
        }
        struct StateUpdateGuard{
            Ogre::Entity* entity;bool previous;
            StateUpdateGuard(Ogre::Entity* e):entity(e),previous(skin.skip(e)){skin.setSkip(entity,true);}
            ~StateUpdateGuard(){skin.setSkip(entity,previous);}
        };
        for(size_t i=0;i<entities.size();++i){
            // 同一骨架第一个消费者会清标记，所以每个衣物 Entity 各自发布后更新其世界蒙皮矩阵。
            skeleton->_notifyManualBonesDirty();
            StateUpdateGuard guard(entities[i]);
            if(!skin.cache(entities[i]))throw std::runtime_error("Manual skin cache not refreshed");
            // cache 会清 manual-dirty；再次发布使 updateAnimation 同帧也进入世界蒙皮刷新。
            // 此时 guard 仍为 true，不再重放动画；离开（含异常）恢复原 skip 值。
            skeleton->_notifyManualBonesDirty();entities[i]->_updateAnimation();
        }
        // 此后游戏正常渲染入口仍可消费新姿势，不依赖它是否已在本帧缓存过这个角色。
        skeleton->_notifyManualBonesDirty();
        return unsigned(entities.size());
    }
    void Pose(AnimationClass* a,bool observed=false){
        if(!active||a!=animation||a->skeleton!=skeleton)return;
        // 完整控制根朝向、骨盆、腿和肩颈，避免上半身 IK 与游戏继续播放的父节点互相拉扯。
        // v2真实HKX含全身旋转与根骨竖直地面补偿；v1位置为零。每帧从快照计算，禁止累加或导入水平瞬移。
        // 日志曾出现手前向坐标 0.65 -> 136，位置累积来源尚未完全归因，但不能继续让它污染演出。
        // 进入、退出平滑混合捕获朝向；位置在退出/取消时同样还原，防止残留位移。
        float weight=Clamp(time/.45f,0,1)*Clamp((END-time)/.65f,0,1);
        weight=weight*weight*(3-2*weight);
        float positionDrift=0;
        for(size_t i=0;i<bones.size();++i){
            positionDrift=std::max(positionDrift,(bones[i].bone->getPosition()-bones[i].previousPosition).length());
            bones[i].bone->setPosition(bones[i].previousPosition+SampleTranslation(clip[i],time)*(weight*poseHeightScale));
            Quaternion authored=bones[i].bone->getInitialOrientation()*Sample(clip[i],time);
            bones[i].bone->setOrientation(Quaternion::Slerp(weight,bones[i].previous,authored,true));
        }
        skeleton->_updateTransforms();
        unsigned skins=RefreshSkin();
        // 每次施放最多四条，区分“钩子执行”与“身体矩阵消费”；误差为局部蒙皮矩阵的最大元素差。
        // 该核对不等于屏幕像素/蒙皮外观已验收，仍须用户从自由视角观察拔刀、挥斩和收刀。
        if(poseDiagnostics<4&&time>=float(poseDiagnostics)*2){
            Ogre::OldBone* handBone=skeleton->getBone("Bip01 R Hand");
            Ogre::Matrix4 expected;handBone->_getOffsetTransform(expected);
            Ogre::Entity* body=animation->body;const Ogre::Matrix4* actual=skin.matrices(body);
            if(!actual||handBone->getHandle()>=skin.count(body))throw std::runtime_error("Skin matrices unavailable");
            float error=0;for(int row=0;row<4;++row)for(int col=0;col<4;++col)
                error=std::max(error,fabsf(expected[row][col]-actual[handBone->getHandle()][row][col]));
            Vector3 handPosition=handBone->_getDerivedPosition();
            std::ostringstream s;s<<"pose_skin_published id="<<castId<<" t="<<time<<" skins="<<skins
                <<" matrix_error="<<error<<" hand_local="<<handPosition.x<<","<<handPosition.y<<","<<handPosition.z
                <<" position_drift_corrected="<<positionDrift<<" dirty="<<skeleton->getManualBonesDirty();Log(s.str());++poseDiagnostics;
        }
        if(observed){poseSeen=true;++poseCalls;}
    }
    float AreaRadius() const {return settings.radius;}
    void FitSlashLayout(){
        // 将资产端点旋转至本次朝向，再用XZ投影包围半径拟合指定伤害圆。
        // 外宽光带的半宽0.18/30计入归一化外缘；相机改变光带朝向也不会越出水平圆。
        // 统一缩放中心/长度/宽度，保留96条的相对分布，不把每条硬拉成同一条直径。
        float envelope=1.f;
        for(size_t i=0;i<slashes.size();++i){
            const Slash& s=slashes[i];
            Vector3 a=facing*(s.centre-s.direction*s.length),b=facing*(s.centre+s.direction*s.length);
            float extent=std::max(sqrtf(a.x*a.x+a.z*a.z),sqrtf(b.x*b.x+b.z*b.z))+.18f/30.f;
            if(!Finite(extent)||extent>8.f)throw std::runtime_error("Invalid horizontal VFX envelope");
            envelope=std::max(envelope,extent);
        }
        layoutScale=AreaRadius()/envelope;
    }
    bool InArea(const Vector3& position) const {
        // 伤害按地面圆投影判定，坡地/屋顶不会因高度差被旧三维球漏掉；边界点包含。
        // 角色逻辑位置与特效仍共用anchor；这是整个圆的AOE，不是亮线或肢体碰撞。
        Vector3 delta=position-anchor;float distanceSquared=delta.x*delta.x+delta.z*delta.z,radius=AreaRadius();
        return Finite(distanceSquared)&&distanceSquared<=radius*radius;
    }
    void Collect(){
        Character* c=Resolve();if(!c)return;
        targets.clear();lektor<RootObject*> list;
        // 本机原生SpacialCell用XZ距离且严格小于半径；候选多取0.01，最终InArea仍严格350含边界。
        world->getObjectsWithinSphere(list,anchor,AreaRadius()+.01f,CHARACTER,2147483647,c);
        // 在收刀结算时取当前全范围敌人，不锁死0.783秒的早期快照，也不限制前32人。
        // 只保存serial hand；原生空间查询后仍重验敌对、位置与身份，攻击前再次解析。
        for(unsigned i=0;i<list.size();++i){
            RootObject* obj=list[i];if(!obj)continue;Character* other=obj->getHandle().getCharacter();
            if(!other||!other->isValid()||other->isDestroyed()||other->isDead()||other==c||ProtectedPlayer(other)||!c->isEnemy(other,true))continue;
            if(!InArea(other->getPosition()))continue;
            // 使用原生非虚比较去重；同一个角色即使被空间查询返回多次也只结算一次。
            hand h=other->getHandle();bool found=false;
            for(size_t j=0;j<targets.size();++j)if(SameHand(targets[j],h)){found=true;break;}
            if(!found)targets.push_back(h);
        }
        std::ostringstream s;s<<"damage_snapshot id="<<castId<<" targets="<<targets.size()<<" scanned="<<list.size()<<" area_radius="<<AreaRadius();Log(s.str());
    }
    const char* Stagger(const hand& target,GameData* part,double landedForce,float& force){
        // 96次损伤后只请求一次反应；重新解析serial，不能沿用医疗回调前的角色指针。
        // 死亡/昏迷/倒地保留游戏自身状态，不把尸体或KO角色强拉成站立踉跄。
        Character* c=Resolve();Character* v=target.getCharacter();force=0;
        if(CasterBlockedReason(c))return "caster_no_longer_eligible";
        if(!v||!v->isValid()||v->isDestroyed()||v->isDead()||!part)return "target_unavailable_or_dead";
        if(ProtectedPlayer(v)||!c->isEnemy(v,true)||!InArea(v->getPosition()))return "protected_or_no_longer_enemy";
        if(v->_NV_isUnconcious()||v->_NV_getProneState()!=PS_NORMAL)return "unconscious_or_prone";
        AnimationClass* a=v->getAnimationClass();CombatClass* combat=v->getCombatClass();
        if(!a||!combat)return "reaction_interface_unavailable";
        CutOrigination origin=v->getAttackOriginationDirection(c);
        AnimationData* reaction=a->chooseStumbleAnim(part,origin,true);bool large=reaction!=0;
        // 种族没有对应大踉跄时退回其普通反应并如实记录，不能凭空创建不存在的动作。
        if(!reaction)reaction=a->chooseStumbleAnim(part,origin,false);
        if(!reaction)return "race_has_no_stumble_animation";
        // 力度来自各次医疗入口返回后的有效四通道之和；double累计避免溢出。
        // 只传给_getHit反应接口（本机原生仅写stumbleForce），不额外扣血、不设置医疗extraStun。
        // 力度上限避免极端武器数值污染后续战斗；大动作由bigone=true显式选择。
        force=float(std::min(1000000.0,std::max(1.0,landedForce*settings.staggerForceMultiplier)));
        Damages response(0,force,0,1,0);
        // startStumble自行替换既有反应；不直写共享动画数据或CombatClass的内部计时字段。
        a->startStumble(reaction);combat->_getHit(CUT_DEFAULT,response,c,true);
        return large?"large_stumble_requested":"small_stumble_fallback";
    }
    void Damage(){
        // 先标记本轮批次不可重复；所有独立命中都延迟到SHEATH，在此同步集中结算。
        // 不是先选96个部位再直接改HP：每次原生addWound都重新选部位并即时处理护甲/医疗状态。
        damageDone=true;Character* c=Resolve();const char* blocked=CasterBlockedReason(c);
        if(blocked){Finish(blocked);return;}unsigned applied=0,skipped=0,hitDiagnostics=0;
        // U键的完整武器数值快照是本次演出的契约；收刀不再解析武器、战斗缓存或攻击方stats。
        // 中途卸下/转移/换装仍使用原快照。读档、换世界、角色失效由Tick/Finish取消并清空快照。
        if(settings.damage&&(!damageArmed||!castDamage.valid)){Log("sheath_damage_skipped: weapon_snapshot_unavailable");return;}
        const unsigned strikeCount=unsigned(slashes.size());unsigned totalHits=0,staggered=0;
        Collect();
        // 当前资产96条，循环数取实际裂痕数量；LoadAssets已把资产数量限制在1..192。
        // 对每个目标在U键攻击快照上套用已冻结的种族加成；每击独立复制，避免护甲修改参数后串到下一击。
        for(size_t i=0;i<targets.size();++i){
            // 原生回调可能撤销施法者；跨目标只重验角色身份，不重新读取武器或攻击属性。
            c=Resolve();
            blocked=CasterBlockedReason(c);
            if(blocked){Log("sheath_damage_aborted id="+Number(castId)+" committed_hits="+Number(totalHits)+" reason="+blocked);Finish(blocked);return;}
            Character* v=targets[i].getCharacter();
            if(!v||!v->isValid()||v->isDestroyed()||v->isDead()||ProtectedPlayer(v)||!c->isEnemy(v,true)||!InArea(v->getPosition())){++skipped;continue;}
            if(!settings.damage)continue;
            Damages base=SnapshotDamageFor(v);
            if(!ValidDamage(base)||double(base.cut)+base.blunt+base.pierce+base.extraStun<=0){
                ++skipped;if(hitDiagnostics++<16)Log("sheath_damage_invalid_base id="+Number(castId));continue;
            }
            unsigned hits=0,misses=0;double landedForce=0;GameData* lastPart=0;
            std::map<std::string,unsigned> bodyHits;const char* stop="completed";
            for(unsigned strike=0;strike<strikeCount;++strike){
                // 医疗回调可能改变生死/实体或加载状态；逐击重验世界与身份，死亡/换档后不访问旧对象。
                Character* currentCaster=Resolve();v=targets[i].getCharacter();
                blocked=CasterBlockedReason(currentCaster);
                if(blocked||currentCaster!=c){const char* reason=blocked?blocked:"caster_changed";
                    Log("sheath_damage_aborted id="+Number(castId)+" committed_hits="+Number(totalHits)+" reason="+reason);Finish(reason);return;}
                // 当前或本轮起始玩家队员永不进入医疗入口；中途招募同样立即停止余下命中。
                if(!v||!v->isValid()||v->isDestroyed()||v->isDead()||ProtectedPlayer(v)||!c->isEnemy(v,true)||!InArea(v->getPosition())){
                    stop="target_dead_invalid_or_left_area";break;
                }
                Damages d(base); // 单击固定100%；不能复用上一击被原生护甲逻辑改过的d，也不乘旧44倍。
                int material=0;AttackDirection::Enum direction=AttackDirection::FRONT;
                // 敌对/位置查询之后再次设最终保护闸门，紧贴唯一医疗调用；即便被判敌对，玩家队员也不扣血。
                if(ProtectedPlayer(v)){stop="player_protected";break;}
                GameData* part=v->medical.addWound(false,CUT_DEFAULT,d,material,c,direction,0);
                if(part){
                    ++hits;++totalHits;lastPart=part;++bodyHits[part->stringID];
                    // 返回部位证明原生入口完成；after参数不是实际HP损失，只作反应力度/诊断依据。
                    if(ValidDamage(d))landedForce+=double(d.cut)+d.blunt+d.pierce+d.extraStun;
                }else ++misses;
            }
            blocked=CasterBlockedReason(Resolve());
            if(blocked){Log("sheath_damage_aborted id="+Number(castId)+" committed_hits="+Number(totalHits)+" reason="+blocked);Finish(blocked);return;}
            float force=0;const char* reaction=hits?Stagger(targets[i],lastPart,landedForce,force):"no_landed_hit";
            if(std::string(reaction)=="large_stumble_requested"||std::string(reaction)=="small_stumble_fallback")++staggered;
            if(hits)++applied;else ++skipped;
            // 每目标汇总部位次数，不写96行；单次演出详细日志仍合计最多16条。
            if(hitDiagnostics++<16){std::ostringstream hit;hit<<"sheath_hit id="<<castId<<" target="<<targets[i].toString()<<" weapon="<<castWeapon.toString()
                <<" source=u_key_snapshot multiplier="<<settings.damageMultiplier<<" requested_hits="<<strikeCount<<" landed_hits="<<hits<<" no_part_hits="<<misses<<" stop="<<stop
                <<" base_cut="<<base.cut<<" base_blunt="<<base.blunt<<" base_pierce="<<base.pierce<<" base_stun="<<base.extraStun
                <<" bleed_mult="<<base.bleedMult<<" armour_penetration="<<base.armourPenetration
                <<" stagger="<<reaction<<" stagger_force="<<force<<" bodyparts=";
                for(std::map<std::string,unsigned>::const_iterator j=bodyHits.begin();j!=bodyHits.end();++j)hit<<j->first<<":"<<j->second<<",";
                Log(hit.str());
            }
        }
        std::ostringstream s;s<<"sheath_damage id="<<castId<<" enabled="<<settings.damage<<" applied="<<applied<<" skipped="<<skipped
            <<" hits_per_target="<<strikeCount<<" total_landed_hits="<<totalHits<<" stagger_requests="<<staggered;Log(s.str());
    }
    unsigned vertex;
    // 隔离模式只压掉自有视觉能量，不取消演出或改11段结构；HDR失效时宽面严格透明。
    void Vertex(const Vector3& p,float u,float v,float r,float g,float b){
        // 2.7：旧刀光把亮度乘RGB再逐通道钳制，brightness>=1.54时(.65,.85,1)变成(1,1,1)。
        // 将色相比值与能量分开：RGB除共同峰值保留比例，Alpha编码0..2的亮度；自有Glow27恢复能量。
        // 仅Ribbon/范围圈调用此入口；不改变顶点位置、UV、索引、医疗范围或其他Alpha材质。
        float energy=std::max(r,std::max(g,b)),inverse=energy>.000001f?1.f/energy:0.f;
        geometry->position(p);geometry->textureCoord(u,v);
        geometry->colour(Clamp(r*inverse,0,1),Clamp(g*inverse,0,1),Clamp(b*inverse,0,1),((settings.opticalProbeMode==1||settings.opticalProbeMode==4)?0.f:Clamp(energy*.5f,0,1)));
    }
    void Ribbon(const Vector3& a,const Vector3& b,float width,float brightness,const Vector3& eye){
        if(brightness<=.001f)return;Vector3 d=b-a;if(d.squaredLength()<.000001f)return;
        Vector3 side=d.crossProduct(eye-(a+b)*.5f);if(side.squaredLength()<.000001f)side=d.crossProduct(Vector3::UNIT_Y);
        if(side.squaredLength()<.000001f)side=Vector3::UNIT_X;side.normalise();side*=width;
        Vertex(a-side,0,0,.65f*brightness,.85f*brightness,brightness);Vertex(a+side,0,1,.65f*brightness,.85f*brightness,brightness);
        Vertex(b+side,1,1,.65f*brightness,.85f*brightness,brightness);Vertex(b-side,1,0,.65f*brightness,.85f*brightness,brightness);
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
    }
    void GroundRing(float radius,float width,float brightness){
        // 水平环带直接用内/外圆顶点，外圆半径就是伤害边界；不使用朝向相机的Ribbon表示范围。
        // 128段减少远距离圆边界折线误差；环宽向内展开，任何顶点都不超过指定半径。
        if(brightness<=.001f)return;float inner=std::max(0.f,radius-2*width);
        for(unsigned i=0;i<128;++i){
            float a=i*6.2831853f/128,b=(i+1)*6.2831853f/128;
            Vertex(Vector3(cosf(a)*inner,.8f,sinf(a)*inner),0,0,.65f*brightness,.85f*brightness,brightness);
            Vertex(Vector3(cosf(a)*radius,.8f,sinf(a)*radius),0,1,.65f*brightness,.85f*brightness,brightness);
            Vertex(Vector3(cosf(b)*radius,.8f,sinf(b)*radius),1,1,.65f*brightness,.85f*brightness,brightness);
            Vertex(Vector3(cosf(b)*inner,.8f,sinf(b)*inner),1,0,.65f*brightness,.85f*brightness,brightness);
            geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);
            geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
        }
    }
    // 全部特效都以固定施放中心为局部坐标；新增粒子/幻影/碎片也不能越出350圆。
    // 仅夹住视觉顶点，不参与医疗结算；实际伤害依然只由InArea和96次原生入口决定。
    Vector3 BoundFx(Vector3 p,float margin=0.f) const {
        float r=std::max(0.f,AreaRadius()-margin),n=p.x*p.x+p.z*p.z;
        if(n>r*r&&n>.000001f){float k=r/sqrtf(n);p.x*=k;p.z*=k;}return p;
    }
    static float FxRandom(unsigned i,unsigned salt){
        unsigned n=i*374761393u+salt*668265263u+1100u;
        n=(n^(n>>13))*1274126177u;return float((n^(n>>16))&65535u)/65535.f;
    }
    void VertexAlpha(const Vector3& p,float u,float v,float r,float g,float b,float alpha){
        geometry->position(BoundFx(p));geometry->textureCoord(u,v);
        geometry->colour(Clamp(r,0,1),Clamp(g,0,1),Clamp(b,0,1),((settings.opticalProbeMode==1||settings.opticalProbeMode==4)?0.f:Clamp(alpha,0,1)));
    }
    void QuadFx(const Vector3& a,const Vector3& b,const Vector3& c,const Vector3& d,float glow,float alpha=1.f){
        VertexAlpha(a,0,0,.24f*glow,.58f*glow,glow,alpha);VertexAlpha(b,1,0,.24f*glow,.58f*glow,glow,alpha);
        VertexAlpha(c,1,1,.24f*glow,.58f*glow,glow,alpha);VertexAlpha(d,0,1,.24f*glow,.58f*glow,glow,alpha);
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);
        geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
    }
    void TriangleFx(const Vector3& a,const Vector3& b,const Vector3& c,float glow,float alpha){
        VertexAlpha(a,0,0,.36f*glow,.68f*glow,glow,alpha);VertexAlpha(b,1,0,.36f*glow,.68f*glow,glow,alpha);
        VertexAlpha(c,.5f,1,.65f*glow,.88f*glow,glow,alpha);
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);vertex+=3;
    }
    void SpriteFx(const Vector3& p,float size,float stretch,float angle,float light,const Vector3& eye){
        // 使用实际相机视线计算朝向，不接管相机。软边来自原创噪声纹理，UV覆盖整个云团。
        Vector3 view=eye-p;if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
        Vector3 right=view.crossProduct(Vector3::UNIT_Y);if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
        Vector3 up=right.crossProduct(view);up.normalise();
        Vector3 a=(right*cosf(angle)+up*sinf(angle))*size,b=(-right*sinf(angle)+up*cosf(angle))*(size*stretch);
        QuadFx(p-a-b,p+a-b,p+a+b,p-a+b,light);
    }
    Vector3 BoundAtmosphere(Vector3 p) const {
        // 灰雾严格限制在以范围圈为底的半球，边界裁剪只作用于视觉，不改变XZ医疗判定。
        p.y=std::max(.8f,p.y);Vector3 v=p-Vector3(0,.8f,0);float n=v.length(),r=AreaRadius();
        if(n>r&&n>.000001f)v*=r/n;return v+Vector3(0,.8f,0);
    }
    void HazeVertex(const Vector3& p,float u,float v,float opticalStep){
        // UV仍为局部坐标/剪辑秒/半径；颜色Alpha改传相位乘归一化切片厚度，而非单片云团浓度。
        // 不能把四角逐点挤回半球：那会折叠平面并重新造成孤立蓝块；半球/地面由像素边界裁切。
        geometry->position(p);geometry->textureCoord(u,v,time,AreaRadius());
        geometry->colour(.82f,.91f,1.f,((settings.opticalProbeMode==1||settings.opticalProbeMode==4)?0.f:Clamp(opticalStep,0,1)));
    }
    void HazeQuad(const Vector3& a,const Vector3& b,const Vector3& c,const Vector3& d,float opticalStep){
        HazeVertex(a,0,0,opticalStep);HazeVertex(b,1,0,opticalStep);
        HazeVertex(c,1,1,opticalStep);HazeVertex(d,0,1,opticalStep);
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);
        geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
    }
    void Mist(const Vector3& eye){
        // 旧96团随机云片在实际视角留下大片空白；改为对整个半球做有界切片积分近似。
        // 所有片采样同一局部3D密度场，不按片使用椭圆贴图边缘，也不增加世界实体/全屏后处理。
        float rise=Clamp((time-.5f)/1.4f,0,1),end=Clamp((END-time)/(END-SHEATH),0,1);
        float phase=rise*rise*(3-2*rise)*(time<SHEATH?1.f:end*end*(3-2*end));
        float radius=AreaRadius(),step=2.f/float(MIST_SLICES);
        Vector3 origin(0,.8f,0),view=eye-origin;
        if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
        Vector3 right=view.crossProduct(Vector3::UNIT_Y);
        if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
        Vector3 up=right.crossProduct(view);up.normalise();
        // 相机在半球外/内均从远到近提交；真实场景深度检测保留，雾片不会盖在后方实体的前面。
        // 固定32片×4顶点/6索引；CPU无排序、堆分配或逐片日志。演出结束仍由既有Finish清理。
        for(unsigned i=0;i<MIST_SLICES;++i){
            float d=-1.f+(float(i)+.5f)*step;
            float span=radius*sqrtf(std::max(0.f,1.f-d*d));
            Vector3 p=origin+view*(radius*d),a=right*span,b=up*span;
            HazeQuad(p-a-b,p+a-b,p+a+b,p-a+b,phase*step);
        }
    }
    void SlashAfterimages(const Slash& s,unsigned id,float width,float light,const Vector3& eye){
        // 每道斩击自身都生成六层平行的运动残迹；与16条持刀幻影独立，不能用人形影代替刀痕拖尾。
        // 残迹沿扫掠的侧向依次延迟产生，再渐弱收拢；新增纹理带也受同一350圆约束。
        Vector3 p=facing*(s.centre*layoutScale),d=facing*(s.direction*s.length*layoutScale);
        Vector3 side=d.crossProduct(eye-p);if(side.squaredLength()<.000001f)side=Vector3::UNIT_Y;side.normalise();
        float age=time-s.at;
        for(unsigned echo=1;echo<=SLASH_ECHOES;++echo){
            float delayed=age-.025f*echo;if(delayed<0)continue;
            float birth=Clamp(delayed/.05f,0,1),fade=.20f+.80f*Clamp(1-delayed/.8f,0,1);
            float spread=(.8f+2.6f*Clamp(1-age/.65f,0,1))*width*echo;
            Vector3 offset=side*spread*((id&1)?1.f:-1.f);
            float power=light*birth*fade*(.32f-.038f*echo);
            Vector3 a=BoundFx(p-d+offset,width),b=BoundFx(p+d+offset,width);
            Ribbon(a,b,width*.48f,power*.45f,eye);Ribbon(a,b,width*.09f,power,eye);
        }
    }

    void Phantom(const Vector3& path,float progress,float light,const Vector3& heading,const Vector3& eye){
        Vector3 forward(heading.x,0,heading.z);if(forward.squaredLength()<.000001f)forward=Vector3::UNIT_Z;forward.normalise();
        Vector3 right=Vector3::UNIT_Y.crossProduct(forward);right.normalise();
        // 使用真实拔刀到挥刀的HKX区间，每个残影独立采样；不用正弦“摆手”代替实际演出。
        float sample=(DRAW+progress*.5f)*phantomAsset.fps;
        unsigned lo=std::min(unsigned(sample),phantomAsset.frames-2);float u=sample-float(lo);
        float scale=Clamp(AreaRadius()*.075f,14.f,30.f)/19.584061f;
        unsigned base=vertex;Vector3 posed[256];
        for(unsigned i=0;i<phantomAsset.vertices;++i){
            Vector3 p=phantomAsset.positions[lo*phantomAsset.vertices+i]*(1-u)+phantomAsset.positions[(lo+1)*phantomAsset.vertices+i]*u;
            posed[i]=BoundFx(path+(right*p.x+Vector3::UNIT_Y*p.y+forward*p.z)*scale);
            // 宽度UV位于发光纹理中部，避免身体大多数顶点在纹理透明边缘消失；明暗随视角表达立体轮廓。
            float shade=.60f+.40f*Clamp((p.y+2)/22.f,0,1);
            VertexAlpha(posed[i],.5f,.5f,.36f*shade,.62f*shade,.78f*shade,light);++vertex;
        }
        for(size_t i=0;i<phantomAsset.indices.size();++i)geometry->index(base+phantomAsset.indices[i]);
        // 刀光锚点取烘焙网格右手末端截面均值，不复制装备实体或抢占游戏角色动画。
        Vector3 hand=Vector3::ZERO;for(unsigned i=84;i<90;++i)hand+=posed[i];hand/=6.f;
        Vector3 blade=forward*cosf((progress-.5f)*2.3f)+right*sinf((progress-.5f)*2.3f);
        Ribbon(BoundFx(hand),BoundFx(hand+blade*scale*9),scale*.12f,light*1.5f,eye);
    }
    void Phantoms(const Vector3& eye){
        unsigned bodies=0;
        for(unsigned i=0;i<PHANTOM_PATHS;++i){
            const Slash& s=slashes[i*slashes.size()/PHANTOM_PATHS];float age=time-s.at;
            if(age<0||age>.68f)continue;float u=Clamp(age/.68f,0,1);
            Vector3 centre=facing*(s.centre*layoutScale),d=facing*(s.direction*s.length*layoutScale);
            Vector3 a=centre-d,b=centre+d,heading=b-a;
            for(unsigned echo=0;echo<PHANTOM_ECHOES&&bodies<PHANTOM_BODY_LIMIT;++echo){
                // 未出生的尾影跳过，不在路径起点堆四个相同人形；末尾每一层独立淡出。
                float v=u-float(echo)*.10f;if(v<0)continue;
                float light=sinf(Clamp(v,0,1)*3.14159265f)*.68f*(echo?(.44f/float(echo)):1.f);
                if(light<=.002f)continue;
                Phantom(BoundFx(a+(b-a)*v,AreaRadius()*.05f),v,light,heading,eye);++bodies;
            }
        }
    }
    void ShardPosition(unsigned id,Vector3& a,Vector3& b,Vector3& c) const {
        // 旧资源仍用三角数据载体，但含义为固定空间中的高光片区：无镜子实体、旋转或落地轨迹。
        const MirrorShard& s=shards[id];a=BoundFx(facing*(s.a*layoutScale));
        b=BoundFx(facing*(s.b*layoutScale));c=BoundFx(facing*(s.c*layoutScale));
    }
    void Glass(const Vector3& eye){
        // 不画闭合镜片边框；短促的视角高光沿斩痕出现，错位明暗让空间看似碎裂。
        // 此函数只保留原短促高光；连续背景错位由独立SpatialFracture承担，无实体镜片或下落。
        for(unsigned i=0;i<shards.size();++i){
            float age=time-shards[i].at;
            float appear=Clamp(age/.04f,0,1);
            float pulse=Clamp(1-age/.34f,0,1),remain=time<SHEATH?.07f:0.f;
            float fade=time<SHEATH?1.f:Clamp(1-(time-SHEATH)/.45f,0,1);
            Vector3 a,b,c;ShardPosition(i,a,b,c);Vector3 normal=(b-a).crossProduct(c-a),view=eye-(a+b+c)/3.f;
            float glint=.15f;if(normal.squaredLength()>.000001f&&view.squaredLength()>.000001f){normal.normalise();view.normalise();glint+=.55f*powf(fabsf(normal.dotProduct(view)),12.f);}
            // 保留零Alpha几何，保证蓄势/结束帧ManualObject段不为空，生命周期合同不变。
            // 源空间片区Alpha独立于每道裂痕闪光，有限生命周期统一按收刀消散。
            float sourceAlpha=Clamp(SourceCurve(4,time-CUT),0,1);
            TriangleFx(a,b,c,.42f+glint,appear*fade*(remain+.24f*pulse)*sourceAlpha);
        }
    }
    void OpticalVertex(const Vector3& p,float u,float v,float radius,float alpha=1.f,
                       const Vector3& normal=Vector3::UNIT_Y,float strength=0.f,float release=0.f,
                       bool wide=false,const Vector3& pivot=Vector3::ZERO,const Vector3& axis=Vector3::UNIT_Y,
                       const Ogre::Vector4& optical=Ogre::Vector4(-1.f,1.f,0.f,0.f),
                       const Vector3& reference=Vector3::ZERO){
        // 2.9.2保留UV4，并增加独立面枢轴/主表面法线；宽面整片用同一参照光线计算偏折。
        // 同时保留原逐顶点法线作前后面检测，避免把封闭薄网格两个面叠成灰玻璃。
        // COLOR.G仍是宽面标志。2.9.4追加TEXCOORD3：揭开进度/位移响应/退场进度/刀路坐标。
        // 揭开进度=-1为旧模式，shader严格走原响应。2.9.6追加TEXCOORD4：本顶点未偏折时的节点局部位置。
        // CPU参考位置经同一worldViewProjMatrix投影，FP反向映射当前片到出生位置，让片内画面也随几何偏转。
        // 旧模式忽略该通道；零Alpha失败占位同样写入全部五组UV，保证BeginUpdate与shader声明稳定。
        geometry->position(p);geometry->normal(normal);geometry->textureCoord(u,v,time,radius);
        geometry->textureCoord(pivot.x,pivot.y,pivot.z);geometry->textureCoord(axis.x,axis.y,axis.z);
        geometry->textureCoord(optical.x,optical.y,optical.z,optical.w);
        geometry->textureCoord(reference.x,reference.y,reference.z);
        geometry->colour(Clamp(strength,0,1),wide?1.f:0.f,Clamp(release,0,1),Clamp(alpha,0,1));
    }
    void LegacySpatialFracture(const Vector3& eye){
        const double submitBegin=Seconds();float radius=AreaRadius();Vector3 origin(0,.8f+radius*.28f,0);
        // 保留源空间朝向，不把每张网格转向相机。固定三张远到近排序，只有栈数组，不分配/复制材质。
        unsigned order[SOURCE_FACET_COUNT];float depth[SOURCE_FACET_COUNT];
        for(unsigned i=0;i<SOURCE_FACET_COUNT;++i){
            order[i]=i;const SourceFacetAsset& a=sourceFacets[i];
            depth[i]=(origin+facing*(a.pivot*radius)-eye).squaredLength();
        }
        for(unsigned i=1;i<SOURCE_FACET_COUNT;++i){
            unsigned id=order[i],j=i;while(j&&depth[order[j-1]]<depth[id]){order[j]=order[j-1];--j;}order[j]=id;
        }
        unsigned aliveCount=0;
        for(unsigned draw=0;draw<SOURCE_FACET_COUNT;++draw){
            unsigned id=order[draw];const SourceFacetAsset& a=sourceFacets[id];
            const Slash& slash=slashes[a.path];float age=time-slash.at;
            float death=SHEATH+.75f,phase=Clamp(age/(death-slash.at),0,1);
            float birth=Clamp(age/.075f,0,1);birth=birth*birth*(3-2*birth);
            float releaseAt=SHEATH+.024f*float(id),release=Clamp((time-releaseAt)/(death-releaseAt),0,1);
            // slashes原合同允许末刀恰在SHEATH；包络除数保底，避免有效边界数据产生0/0。
            float hold=FacetSample(facetEnvelopes[0],Clamp(age/std::max(SHEATH-slash.at,.001f),0,1));
            float endEnvelope=FacetSample(facetEnvelopes[1],release);
            // BG3中期/末段层作平滑交接；原Alpha键按各自峰值归一化，末键严格为0。
            // 两张切割面保留源NiTransformData形状；screen1短闪宽面保持源峰值几何，改用BG3持续包络。
            // 出生/退场均由独立剪辑秒驱动，未出生和尾部严格透明；该节奏适配不冒称源动画原样。
            float alpha=(age<0||time>=death)?0.f:birth*(hold*(1-release)+endEnvelope*release);
            // 立向宽面只随施放朝向旋转：固定世界位置/方向，保持源拓扑和相同出生退场时钟。
            // 非宽面仍走原NIF尺度/朝向；验证模式不复制网格、不改原有11段声明。
            if(settings.opticalProbeMode!=0&&id!=0)alpha=0.f;
            float strength=OpticalStrength(a.optical,age,death-slash.at),scale=FacetScale(a,phase);
            Vector3 axis=facing*(id==0?Vector3::UNIT_Z:a.axis);
            Vector3 pivot=(id==0?Vector3(0,.8f+radius*.40f,0):origin+facing*(a.pivot*radius))+axis*(radius*.025f*release);
            unsigned start=vertex;
            for(size_t j=0;j<a.positions.size();++j){
                Vector3 p=pivot+facing*(id==0?WideFacetPoint(a.positions[j])*radius:(a.positions[j]-a.pivot)*(radius*scale));
                Vector3 n=facing*(id==0?WideFacetNormal(a.normals[j]):a.normals[j]);
                OpticalVertex(p,a.uv[j].x,a.uv[j].y,radius,alpha,n,strength,release,id==0,pivot,axis);
            }
            for(size_t j=0;j<a.indices.size();++j)geometry->index(start+a.indices[j]);
            vertex+=static_cast<unsigned>(a.positions.size());if(alpha*strength>.001f)++aliveCount;
        }
        // 每次施放只记录首次有效一条；CPU提交耗时不冒称GPU耗时，清理由既有Finish/ReleaseGraphics承担。
        if(aliveCount&&!(fxStages&16)){
            fxStages|=16;std::ostringstream s;s<<"spatial_optics_active id="<<castId
                <<" revision=2.9.2_upright_facet_probe source_facets=3 alive="<<aliveCount
                <<" probe_mode="<<settings.opticalProbeMode<<" wide_width_radius=1.36 wide_height_radius=0.66 wide_centre_height_radius=0.40 wide_scale="<<wideFacetScale.x<<","<<wideFacetScale.y<<","<<wideFacetScale.z
                <<" camera_billboard=0 vertex_normals=source vertices=72 triangles=36 max_offset_pixels=36"
                <<" CPU_submit_ms="<<(Seconds()-submitBegin)*1000.0<<" GPU_ms=unmeasured lifetime_end="<<(SHEATH+.75f);
            Log(s.str());
        }
        // 每阶段仅一条CPU诊断；显示模式/宽面包络/源强度，不能冒称屏幕像素已可见或GPU计时。
        unsigned stage=time>=SHEATH+.10f?256u:(time>=CUT+.80f?128u:(time>=CUT+.10f?64u:0u));
        if(stage&&!(fxStages&stage)){
            fxStages|=stage;const SourceFacetAsset& a=sourceFacets[0];float age=time-slashes[a.path].at;
            std::ostringstream log;log<<"facet_probe_stage id="<<castId<<" stage="<<stage<<" mode="<<settings.opticalProbeMode
                <<" clip_time="<<time<<" wide_strength="<<OpticalStrength(a.optical,age,SHEATH+.75f-slashes[a.path].at)
                <<" CPU_alive="<<aliveCount<<" HDR_ready="<<refractionReady<<" GPU_visible=unmeasured";
            // 投影包围盒只是遮挡前几何上界，不代表通过深度/Alpha测试的实际像素数；每次施放最多三条。
            // 使用当前相机与特效节点坐标，区分远距离缩小、侧看退化和资源提交问题；不读回GPU。
            Ogre::Camera* camera=Render()->getCamera();
            const Ogre::Matrix4 vp=camera->getProjectionMatrix()*camera->getViewMatrix();
            float minX=FLT_MAX,minY=FLT_MAX,maxX=-FLT_MAX,maxY=-FLT_MAX;unsigned projected=0;
            float death=SHEATH+.75f,releaseAt=SHEATH;
            float release=Clamp((time-releaseAt)/(death-releaseAt),0,1);
            Vector3 axis=facing*Vector3::UNIT_Z,pivot=Vector3(0,.8f+AreaRadius()*.40f,0)+axis*(AreaRadius()*.025f*release);
            for(size_t j=0;j<a.positions.size();++j){
                Vector3 world=node->convertLocalToWorldPosition(pivot+facing*(WideFacetPoint(a.positions[j])*AreaRadius()));
                Ogre::Vector4 clip=vp*Ogre::Vector4(world.x,world.y,world.z,1.f);
                if(!Finite(clip.w)||clip.w<=.0001f)continue;
                float x=clip.x/clip.w,y=clip.y/clip.w;if(!Finite(x)||!Finite(y))continue;
                minX=std::min(minX,x);maxX=std::max(maxX,x);minY=std::min(minY,y);maxY=std::max(maxY,y);++projected;
            }
            float w=float(Render()->window->getWidth()),h=float(Render()->window->getHeight());
            float bx=projected?std::max(0.f,std::min(1.f,maxX)-std::max(-1.f,minX))*w*.5f:0.f;
            float by=projected?std::max(0.f,std::min(1.f,maxY)-std::max(-1.f,minY))*h*.5f:0.f;
            Vector3 ray=eye-pivot;ray.normalise();
            log<<" projected_vertices="<<projected<<" bbox_px="<<bx<<","<<by
                <<" bbox_viewport_fraction="<<(bx*by/std::max(w*h,1.f))
                <<" plane_view_abs_dot="<<fabs(axis.dotProduct(ray))<<" projection=pre_depth_pre_mask_bbox";Log(log.str());
        }
    }

    // 2.9.5五片分级布局：两大两中一小复用已验收screen1拓扑/UV/逆转置法线，不新增随机裂纹或亮线。
    // 1/2模式仍调用原单片实现；新模式只改变光学几何与剪辑秒时钟，不接触角色/伤害/世界时间。
    struct IndependentFacet {
        Vector3 pivot,axis,referencePivot;Quaternion rotation,referenceRotation;
        float size,alpha,strength,release,reveal,response;unsigned path;
    };
    Quaternion FacetRotation(float degrees,const Vector3& axis){
        float half=degrees*.00872664626f,s=sinf(half);
        return Quaternion(cosf(half),axis.x*s,axis.y*s,axis.z*s);
    }
    IndependentFacet IndependentFacetAt(unsigned id,float radius){
        // 每行：中心X/高度/中心Z（单位R）、等比尺寸、偏航/滚转、停留偏航/滚转增量、
        // 分离XZ（单位R）、俯仰及停留俯仰增量。俯仰互补避免大面都竖直而侧看时同时变窄。
        // 两大两中一小的尺寸平方和0.9403（旧0.9429），重新分配空间，不靠叠加面积/亮线提高强度。
        // Skyrim仍提供真实网格/遮罩，BG3仍提供hold/release；位置与三轴转动是Kenshi适配，非源旋转键。
        static const float profiles[INDEPENDENT_FACET_COUNT][12]={
            {-0.35f,0.37f,0.12f,0.55f,-32.f,-16.f,7.f,3.f,-0.065f,0.035f,25.f,-8.f},
            {0.3f,0.4f,-0.08f,0.57f,45.f,14.f,-8.f,-4.f,0.045f,-0.035f,32.f,-6.f},
            {-0.04f,0.54f,0.32f,0.38f,100.f,-22.f,9.f,-5.f,-0.04f,0.055f,-42.f,6.f},
            {0.02f,0.22f,-0.44f,0.34f,-95.f,20.f,-7.f,4.f,0.035f,-0.045f,-48.f,6.f},
            {-0.36f,0.23f,-0.26f,0.23f,36.f,-26.f,6.f,5.f,-0.04f,-0.025f,-55.f,8.f}
        };
        // 五片分别绑定现有96道刀路中的0/12/24/36/48：沿初斩顺序出生；保留原CSV三张及旧模式。
        static const unsigned paths[INDEPENDENT_FACET_COUNT]={0,12,24,36,48};
        const float* v=profiles[id];IndependentFacet f;f.path=paths[id];f.size=v[3];
        const SourceFacetAsset& a=sourceFacets[0];float at=slashes[f.path].at,age=time-at;
        // 五片退场间隔压到0.15剪辑秒（实际0.05秒），各片0.70；最后仍6.45<END=6.7。
        // 先分离后淡出；位置/旋转只跟剪辑时钟，不对齐摄像机，也不随帧随机变化。
        float releaseAt=SHEATH+FACET_RELEASE_INTERVAL*float(id),death=releaseAt+FACET_RELEASE_DURATION;
        f.release=Clamp((time-releaseAt)/(death-releaseAt),0,1);
        // 揭开时长0.45剪辑秒（实际0.15秒），仍投影对应刀路；FP用屏幕导数形成窄抗锯齿切口。
        // 揭开结束前不偏折，使刀路坐标稳定；0/1端点仍严格控制未出生/完全切开。
        f.reveal=Clamp(age/FACET_REVEAL_DURATION,0,1);
        float birth=Clamp(age/.075f,0,1);birth=birth*birth*(3-2*birth);
        // 各片在揭开后的剩余停留段前55%平滑完成一次偏折，再保持原最大角度直到收刀。
        // 稳住的是本片姿态/响应，HDR仍每帧更新、原强度曲线仍采样，不冻结片内世界或摄像机。
        // 后出生的片独立算时长；分母保留正数下界，收刀方向/幅度/退场截止仍按原合同。
        float bendDuration=std::max((SHEATH-at-FACET_REVEAL_DURATION)*FACET_BEND_FRACTION,.001f);
        float bend=Clamp((age-FACET_REVEAL_DURATION)/bendDuration,0,1);bend=bend*bend*(3-2*bend);
        // 五片响应独立且<=1，保持旧36像素上界及所有刀光/蓝雾颜色；不把适配响应称为源键。
        static const float responseEnd[INDEPENDENT_FACET_COUNT]={.95f,.82f,.70f,.78f,.64f};
        f.response=.28f+(responseEnd[id]-.28f)*bend;
        float separate=f.release*f.release*(3-2*f.release);
        // Y偏航×X俯仰×Z滚转：位置、法线及主表面轴共用这一正交旋转，保持折射/遮挡一致。
        // 等比缩放继续使用原逆转置法线；俯仰已在完整生命期检查球内/地面边界。
        Quaternion local=FacetRotation(v[4]+v[6]*bend+v[6]*separate,Vector3::UNIT_Y)
                        *FacetRotation(v[10]+v[11]*bend+v[11]*separate,Vector3::UNIT_X)
                        *FacetRotation(v[5]+v[7]*bend+v[7]*separate,Vector3::UNIT_Z);
        f.rotation=facing*local;f.axis=f.rotation*Vector3::UNIT_Z;
        // 出生参考面使用同一位置/三轴朝向/尺寸，仅去掉本片停留偏折和收刀分离。
        // 保存在节点局部坐标而不是旧帧屏幕坐标，镜头移动时双方同步投影，不产生跟屏拖影或读回缓存。
        f.referenceRotation=facing*(FacetRotation(v[4],Vector3::UNIT_Y)*FacetRotation(v[10],Vector3::UNIT_X)*FacetRotation(v[5],Vector3::UNIT_Z));
        f.referencePivot=facing*(Vector3(v[0],v[1],v[2])*radius)+Vector3(0,.8f,0);
        f.pivot=facing*(Vector3(v[0]+v[8]*separate,v[1]+.015f*separate,v[2]+v[9]*separate)*radius)
               +Vector3(0,.8f,0);
        float hold=FacetSample(facetEnvelopes[0],Clamp(age/std::max(SHEATH-at,.001f),0,1));
        float tail=FacetSample(facetEnvelopes[1],f.release);
        f.alpha=(age<0||time>=death)?0.f:birth*(hold*(1-f.release)+tail*f.release);
        f.strength=OpticalStrength(a.optical,age,death-at);return f;
    }
    // 2.9.8：沿已有刀路剪出不同斜边，仍复用Skyrim源网格/UV；轮廓是Kenshi适配，非原模组碎片数据。
    // 两个裁切平面固定在出生参考面的局部XY内，摄像机/中期偏折不重算方向，避免边缘游动或拓扑跳变。
    struct FacetClipPlane {Vector3 normal;float limit;unsigned path;bool fallback;};
    struct FacetClipVertex {Vector3 p,n,uv;};
    FacetClipPlane FacetContourPlane(unsigned id,unsigned edge,const IndependentFacet& f,const SourceFacetAsset& a){
        // 五片各沿绑定刀路及后第6条刀路裁切；保留系数根据真实screen1主面预检，保留约83%~86%面积。
        // 符号交错只选择裁去哪一角，不随机添裂纹；方向来自实际CSV，位置取源范围的有界比例。
        static const float retained[INDEPENDENT_FACET_COUNT][2]={{.90f,.76f},{.81f,.90f},{.91f,.77f},{.78f,.84f},{.82f,.82f}};
        FacetClipPlane plane;plane.path=(f.path+6u*edge)%static_cast<unsigned>(slashes.size());
        Vector3 direction=facing*slashes[plane.path].direction;
        Vector3 projected(direction.dotProduct(f.referenceRotation*Vector3::UNIT_X),direction.dotProduct(f.referenceRotation*Vector3::UNIT_Y),0);
        plane.fallback=projected.squaredLength()<.0000000001f;
        if(plane.fallback)projected=edge?Vector3::UNIT_Y:Vector3::UNIT_X;else projected.normalise();
        plane.normal=Vector3(-projected.y,projected.x,0);if((id+edge)&1u)plane.normal=-plane.normal;
        float lo=FLT_MAX,hi=-FLT_MAX;
        for(size_t j=0;j<a.positions.size();++j){float q=WideFacetPoint(a.positions[j]).dotProduct(plane.normal);lo=std::min(lo,q);hi=std::max(hi,q);}
        plane.limit=lo+(hi-lo)*retained[id][edge];return plane;
    }
    unsigned ClipFacetPolygon(const FacetClipVertex* input,unsigned count,const FacetClipPlane& plane,FacetClipVertex* output){
        // Sutherland-Hodgman裁凸多边形：三角形经两个半平面最多5点；8点栈缓冲有余量，无逐帧堆分配。
        // 交点同步插值位置/法线/UV；同一个局部点供当前面和出生参考面投影，保持五套UV传输合同。
        // 严格0/1交点不重复输出端点；空多边形返回0，不制造封口、背面发光或新的材质资源。
        if(!count)return 0;if(count>7u)throw std::runtime_error("Facet contour capacity exceeded");
        unsigned out=0;FacetClipVertex previous=input[count-1];float dp=previous.p.dotProduct(plane.normal)-plane.limit;
        for(unsigned j=0;j<count;++j){
            const FacetClipVertex& current=input[j];float dc=current.p.dotProduct(plane.normal)-plane.limit;
            if((dp<=0)!=(dc<=0)){
                float t=Clamp(dp/(dp-dc),0,1);
                if(t>0&&t<1){FacetClipVertex v;v.p=previous.p+(current.p-previous.p)*t;v.n=previous.n+(current.n-previous.n)*t;v.uv=previous.uv+(current.uv-previous.uv)*t;output[out++]=v;}
            }
            if(dc<=0)output[out++]=current;
            previous=current;dp=dc;
        }
        return out;
    }
    void IndependentSpatialFracture(const Vector3& eye){
        const double submitBegin=Seconds();float radius=AreaRadius();const SourceFacetAsset& a=sourceFacets[0];
        IndependentFacet facets[INDEPENDENT_FACET_COUNT];unsigned order[INDEPENDENT_FACET_COUNT];float depth[INDEPENDENT_FACET_COUNT];
        // 按当前已偏折/分离的实际枢轴排序；固定五实例、栈存储，不创建额外材质或背景捕获。
        for(unsigned i=0;i<INDEPENDENT_FACET_COUNT;++i){facets[i]=IndependentFacetAt(i,radius);order[i]=i;depth[i]=(facets[i].pivot-eye).squaredLength();}
        for(unsigned i=1;i<INDEPENDENT_FACET_COUNT;++i){unsigned id=order[i],j=i;while(j&&depth[order[j-1]]<depth[id]){order[j]=order[j-1];--j;}order[j]=id;}
        unsigned aliveCount=0,submittedVertices=0,submittedTriangles=0,contourFallbacks=0;
        for(unsigned draw=0;draw<INDEPENDENT_FACET_COUNT;++draw){
            unsigned id=order[draw];const IndependentFacet& f=facets[id];unsigned facetStart=vertex;
            FacetClipPlane planes[2]={FacetContourPlane(id,0,f,a),FacetContourPlane(id,1,f,a)};
            contourFallbacks+=unsigned(planes[0].fallback)+unsigned(planes[1].fallback);
            // 启动读取合同严格限制screen1为12三角形；每片固定12x8点栈空间，先裁一次，再提交同一结果。
            // 第一遍收集裁后范围，让揭开0..1横跨实际剩余轮廓；不延用被裁去角的投影极值。
            FacetClipVertex clipped[12][8];unsigned counts[12];Vector3 cutDirection=facing*slashes[f.path].direction;
            float cutMin=FLT_MAX,cutMax=-FLT_MAX;
            for(unsigned tri=0;tri<12u;++tri){
                FacetClipVertex input[8],middle[8];
                for(unsigned k=0;k<3u;++k){unsigned j=a.indices[tri*3u+k];input[k].p=WideFacetPoint(a.positions[j]);input[k].n=WideFacetNormal(a.normals[j]);input[k].uv=a.uv[j];}
                unsigned count=ClipFacetPolygon(input,3u,planes[0],middle);count=ClipFacetPolygon(middle,count,planes[1],clipped[tri]);
                if(count>5u)throw std::runtime_error("Invalid facet contour topology");counts[tri]=count;
                if(count<3u)continue;
                for(unsigned j=0;j<count;++j){float q=(f.rotation*clipped[tri][j].p).dotProduct(cutDirection);cutMin=std::min(cutMin,q);cutMax=std::max(cutMax,q);}
            }
            // 刀路垂直本片时仍回退局部X，裁切平面与揭开坐标均不对齐摄像机。
            if(cutMax-cutMin<.00001f){
                cutDirection=f.rotation*Vector3::UNIT_X;cutMin=FLT_MAX;cutMax=-FLT_MAX;
                for(unsigned tri=0;tri<12u;++tri)if(counts[tri]>=3u)for(unsigned j=0;j<counts[tri];++j){float q=(f.rotation*clipped[tri][j].p).dotProduct(cutDirection);cutMin=std::min(cutMin,q);cutMax=std::max(cutMax,q);}
            }
            float cutSpan=std::max(cutMax-cutMin,.00001f);
            for(unsigned tri=0;tri<12u;++tri){
                unsigned count=counts[tri];if(count<3u)continue;unsigned start=vertex;
                for(unsigned j=0;j<count;++j){
                    const FacetClipVertex& v=clipped[tri][j];Vector3 p=f.pivot+f.rotation*(v.p*(radius*f.size));
                    Vector3 n=f.rotation*v.n;if(n.squaredLength()>.0000000001f)n.normalise();else n=f.axis;
                    Vector3 reference=f.referencePivot+f.referenceRotation*(v.p*(radius*f.size));
                    float cut=Clamp(((f.rotation*v.p).dotProduct(cutDirection)-cutMin)/cutSpan,0,1);
                    OpticalVertex(p,v.uv.x,v.uv.y,radius,f.alpha,n,f.strength,f.release,true,f.pivot,f.axis,
                                  Ogre::Vector4(f.reveal,f.response,f.release,cut),reference);
                }
                // 凸裁切结果保留原绕序，扇形索引只使用本多边形顶点；源UV/薄侧面不跨三角形混接。
                for(unsigned j=1;j+1<count;++j){geometry->index(start);geometry->index(start+j);geometry->index(start+j+1);}
                vertex+=count;submittedTriangles+=count-2u;
            }
            submittedVertices+=vertex-facetStart;if(vertex>facetStart&&f.alpha*f.strength>.001f)++aliveCount;
        }
        if(aliveCount&&!(fxStages&16)){
            fxStages|=16;std::ostringstream log;log<<"spatial_optics_active id="<<castId
                <<" revision=2.9.8_slash_aligned_contours mode="<<settings.opticalProbeMode<<" instances="<<INDEPENDENT_FACET_COUNT<<" source=screen1 alive="<<aliveCount
                <<" vertices="<<submittedVertices<<" triangles="<<submittedTriangles<<" contour_planes_per_facet=2 contour_fallbacks="<<contourFallbacks<<" contour_reference=birth_xy slash_secondary_offset=6"
                <<" camera_billboard=0 HDR_copies_per_frame<=1 HDR_capture=before_optical_after_own_visuals content_mapping=reference_to_current overlap=nearest_snapshot_replacement"
                <<" CPU_submit_ms="<<(Seconds()-submitBegin)*1000.0<<" GPU_ms=unmeasured reveal_clip_seconds="<<FACET_REVEAL_DURATION<<" bend_remaining_fraction="<<FACET_BEND_FRACTION<<" release_interval_clip_seconds="<<FACET_RELEASE_INTERVAL<<" lifetime_end="<<(SHEATH+FACET_LIFETIME_TAIL);Log(log.str());
        }
        // 每次施放仍仅五阶段，每阶段每片一条（最多25条）：出生、五片停留、分离、交错淡出、尾片淡出。
        // CPU投影只是遮挡/遮罩前的几何上界；日志有界，不读回GPU，也不冒称实际可见像素。
        unsigned stage=time>=SHEATH+.85f?1024u:(time>=SHEATH+.40f?512u:
                      (time>=SHEATH+.10f?256u:(time>=CUT+1.65f?128u:(time>=CUT+.10f?64u:0u))));
        if(stage&&!(fxStages&stage)){
            fxStages|=stage;Ogre::Camera* camera=Render()->getCamera();const Ogre::Matrix4 vp=camera->getProjectionMatrix()*camera->getViewMatrix();
            float w=float(Render()->window->getWidth()),h=float(Render()->window->getHeight());
            for(unsigned id=0;id<INDEPENDENT_FACET_COUNT;++id){
                const IndependentFacet& f=facets[id];float minX=FLT_MAX,minY=FLT_MAX,maxX=-FLT_MAX,maxY=-FLT_MAX,maxWarp=0.f;unsigned projected=0;
                for(size_t j=0;j<a.positions.size();++j){
                    Vector3 world=node->convertLocalToWorldPosition(f.pivot+f.rotation*(WideFacetPoint(a.positions[j])*(radius*f.size)));
                    Ogre::Vector4 clip=vp*Ogre::Vector4(world.x,world.y,world.z,1.f);
                    if(!Finite(clip.w)||clip.w<=.0001f)continue;float x=clip.x/clip.w,y=clip.y/clip.w;if(!Finite(x)||!Finite(y))continue;
                    minX=std::min(minX,x);maxX=std::max(maxX,x);minY=std::min(minY,y);maxY=std::max(maxY,y);++projected;
                    // 有界CPU诊断：仅25条阶段日志，记录顶点参考映射幅度（未裁36px、未深度/遮罩测试），非GPU可见量。
                    Vector3 reference=node->convertLocalToWorldPosition(f.referencePivot+f.referenceRotation*(WideFacetPoint(a.positions[j])*(radius*f.size)));
                    Ogre::Vector4 refClip=vp*Ogre::Vector4(reference.x,reference.y,reference.z,1.f);
                    if(Finite(refClip.w)&&refClip.w>.0001f){
                        float dx=(refClip.x/refClip.w-x)*w*.5f,dy=(refClip.y/refClip.w-y)*h*.5f;
                        if(Finite(dx)&&Finite(dy))maxWarp=std::max(maxWarp,sqrtf(dx*dx+dy*dy));
                    }
                }
                float bx=projected?std::max(0.f,std::min(1.f,maxX)-std::max(-1.f,minX))*w*.5f:0.f;
                float by=projected?std::max(0.f,std::min(1.f,maxY)-std::max(-1.f,minY))*h*.5f:0.f;
                Vector3 ray=eye-f.pivot;if(ray.squaredLength()>.000001f)ray.normalise();else ray=Vector3::ZERO;
                std::ostringstream log;log<<"independent_facet_stage id="<<castId<<" stage="<<stage<<" facet="<<id<<" path="<<f.path
                    <<" clip_time="<<time<<" born_at="<<slashes[f.path].at<<" release_at="<<(SHEATH+FACET_RELEASE_INTERVAL*float(id))
                    <<" size="<<f.size<<" pivot="<<f.pivot.x<<","<<f.pivot.y<<","<<f.pivot.z
                    <<" axis="<<f.axis.x<<","<<f.axis.y<<","<<f.axis.z<<" alpha="<<f.alpha<<" strength="<<f.strength<<" release="<<f.release<<" reveal="<<f.reveal<<" response="<<f.response
                    <<" projected_vertices="<<projected<<" bbox_px="<<bx<<","<<by<<" bbox_viewport_fraction="<<(bx*by/std::max(w*h,1.f))
                    <<" plane_view_abs_dot="<<fabs(f.axis.dotProduct(ray))<<" reference_warp_vertex_max_px="<<maxWarp<<" warp_measure=source_pre_contour_pre_budget_pre_depth_pre_mask projection=source_pre_contour_pre_depth_pre_mask_bbox HDR_ready="<<refractionReady<<" GPU_visible=unmeasured";Log(log.str());
            }
        }
    }
    void SpatialFracture(const Vector3& eye){
        // 显式兼容已验收单片：模式3/4走独立五片，0/1/2仍保留原渲染路径与原源资源数量。
        if(settings.opticalProbeMode>=3)IndependentSpatialFracture(eye);else LegacySpatialFracture(eye);
    }

    void SourceQuad(const Vector3& a,const Vector3& b,const Vector3& c,const Vector3& d,
                    float r,float g,float bl,float alpha,float u0=0,float v0=0,float u1=1,float v1=1){
        // 新层都复用350圆裁剪和固定施放中心，Alpha来自原曲线并在像素shader再次乘DDS Alpha。
        VertexAlpha(a,u0,v0,r,g,bl,alpha);VertexAlpha(b,u1,v0,r,g,bl,alpha);
        VertexAlpha(c,u1,v1,r,g,bl,alpha);VertexAlpha(d,u0,v1,r,g,bl,alpha);
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);
        geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
    }
    void SourceSprite(const Vector3& p,float size,float stretch,float angle,float alpha,const Vector3& eye,
                      float r,float g,float b,unsigned tile=64){
        Vector3 view=eye-p;if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
        Vector3 right=view.crossProduct(Vector3::UNIT_Y);if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
        Vector3 up=right.crossProduct(view);up.normalise();
        Vector3 a=(right*cosf(angle)+up*sinf(angle))*size,z=(-right*sinf(angle)+up*cosf(angle))*(size*stretch);
        // 原烟尘是8x8 atlas，不可把64格整图当单个烟团；半纹素内缩避免相邻帧串色。
        float u0=0,v0=0,u1=1,v1=1;
        if(tile<64){float inset=.5f/512.f;u0=float(tile%8)/8+inset;v0=float(tile/8)/8+inset;u1=u0+.125f-2*inset;v1=v0+.125f-2*inset;}
        SourceQuad(p-a-z,p+a-z,p+a+z,p-a+z,r,g,b,alpha,u0,v0,u1,v1);
    }
    void SourceSlashes(const Vector3& eye,bool feather){
        unsigned before=vertex;float radius=AreaRadius();
        for(size_t i=0;i<slashes.size();++i){
            const Slash& s=slashes[i];float age=time-s.at;
            if(age<0||age>.95f)continue;
            Vector3 p=facing*(s.centre*layoutScale),d=facing*(s.direction*s.length*layoutScale);
            Vector3 side=d.crossProduct(eye-p);if(side.squaredLength()<.000001f)side=Vector3::UNIT_Y;side.normalise();
            // 弧形主体和多道弧形拖影使用ap05两张不同原图；保留原有96道线痕与六条平行余迹。
            float w=s.length*layoutScale*(feather?.19f:.115f);
            float birth=Clamp(age/.035f,0,1),fade=Clamp(1-age/(feather?.66f:.95f),0,1);
            float terminal=time<SHEATH?1.f:Clamp(1-(time-SHEATH)/.45f,0,1);
            float pulse=Clamp(SourceCurve(5,age),0,1);
            float alpha=birth*fade*terminal*(feather?.40f:(.65f+.35f*pulse));
            Vector3 shift=side*w*(feather?(1-fade)*.4f:0.f);p+=shift;side*=w;
            SourceQuad(p-d-side,p+d-side,p+d+side,p-d+side,.72f,.85f,1,alpha);
        }
        // 蓄势/结束保持透明占位段，禁止空ManualObject section改变索引和背景复制时点。
        if(vertex==before)SourceQuad(Vector3::ZERO,Vector3::ZERO,Vector3::ZERO,Vector3::ZERO,0,0,0,0);
        (void)radius;
    }
    float ParticleAngle(const Vector3& p,const Vector3& direction,const Vector3& eye) const {
        // SourceSprite的长轴为-right*sin+up*cos对应的局部z轴；把刀路投影到相机平面，避免沿世界轴错转。
        // 视线与刀路平行时采用零角度，不除以趋零向量；只计算视觉朝向，不触碰角色骨骼。
        Vector3 view=eye-p;if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
        Vector3 right=view.crossProduct(Vector3::UNIT_Y);if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
        Vector3 up=right.crossProduct(view);up.normalise();
        float x=direction.dotProduct(right),y=direction.dotProduct(up);
        return x*x+y*y<.000001f?0.f:atan2f(-x,y);
    }
    void SmokeSprite(const Vector3& p,float size,float stretch,float angle,float alpha,const Vector3& eye,float frame){
        // 专用烟雾输入：0..1局部UV/连续图集帧/范围半径，shader在同一64格内插值两帧。
        // 不改变SourceSprite的刀光/光屑合同；边界与透明度在自有像素程序再次软化。
        Vector3 view=eye-p;if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
        Vector3 right=view.crossProduct(Vector3::UNIT_Y);if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
        Vector3 up=right.crossProduct(view);up.normalise();
        Vector3 a=(right*cosf(angle)+up*sinf(angle))*size,z=(-right*sinf(angle)+up*cosf(angle))*(size*stretch);
        const Vector3 corners[]={p-a-z,p+a-z,p+a+z,p-a+z};const float us[]={0,1,1,0},vs[]={0,0,1,1};
        for(unsigned i=0;i<4;++i){
            geometry->position(BoundAtmosphere(corners[i]));geometry->textureCoord(us[i],vs[i],frame,AreaRadius());
            geometry->colour(.78f,.9f,1.f,((settings.opticalProbeMode==1||settings.opticalProbeMode==4)?0.f:Clamp(alpha,0,1)));
        }
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);
        geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
    }
    void SourceDust(const Vector3& eye){
        // 48条真实刀路各3个重叠软段，共144固定槽，全体由远到近排序，不逐条叠放造成透明互盖。
        // 1.65..1.90剪辑秒寿命=约0.55..0.63真实秒；收刀停发且END强制零Alpha，取消仍由原清理销毁。
        const unsigned count=144;HazeCell cells[count];float radius=AreaRadius();
        float age=time-CUT,end=Clamp((END-time)/(END-SHEATH),0,1);
        float fade=time<SHEATH?1.f:end*end*(3-2*end);
        // 连续雾承担主体气氛；刀路贴片仅作细尾烟，避免144个烟团再次像蓝色颗粒。
        // 2.7：144个旧尘烟槽只保留很淡的尾迹，防止细碎8x8图集主导主体烟雾。
        float opacity=age<0?0.f:(.006f+.010f*Clamp(SourceCurve(1,age),0,1))*fade;
        for(unsigned i=0;i<count;++i){
            unsigned path=i/3,part=i%3;const Slash& s=slashes[(path*2)%slashes.size()];
            Vector3 direction=facing*s.direction;if(direction.squaredLength()<.000001f)direction=Vector3::UNIT_X;direction.normalise();
            Vector3 side=direction.crossProduct(Vector3::UNIT_Y);if(side.squaredLength()<.000001f)side=Vector3::UNIT_Z;side.normalise();
            float life=1.65f+.25f*FxRandom(path,61),elapsed=std::max(0.f,std::min(time,SHEATH)-s.at);
            float born=s.at+floorf(elapsed/life)*life,local=std::max(0.f,time-born),u=Clamp(local/life,0,1);
            float along=-.48f+.96f*FxRandom(path,62);
            Vector3 p=facing*(s.centre*layoutScale)+direction*(s.length*layoutScale*along+radius*(.16f*u+.10f*(float(part)-1)));
            p+=side*(radius*.035f*sinf(u*4.71238898f+float(path))*(1-u))+Vector3::UNIT_Y*(radius*.06f*u);
            cells[i].p=BoundAtmosphere(p);cells[i].depth=(eye-cells[i].p).squaredLength();
            cells[i].size=radius*(.04f+.016f*FxRandom(path,63));cells[i].id=i;
        }
        std::sort(cells,cells+count);
        for(unsigned i=0;i<count;++i){
            unsigned id=cells[i].id,path=id/3;const Slash& s=slashes[(path*2)%slashes.size()];
            float life=1.65f+.25f*FxRandom(path,61),elapsed=std::max(0.f,std::min(time,SHEATH)-s.at);
            float born=s.at+floorf(elapsed/life)*life,local=std::max(0.f,time-born);
            float birth=Clamp(local/.22f,0,1),death=Clamp((life-local)/.65f,0,1);
            float envelope=time<s.at?0.f:birth*birth*(3-2*birth)*death*death*(3-2*death);
            // 独立连续帧带稳定id；相机排序不改生命时钟，16格/剪辑秒并在shader插值以减少跳帧。
            float frame=Clamp(local,0,3.f)*16.f+float(id%8);
            Vector3 direction=facing*s.direction;
            SmokeSprite(cells[i].p,cells[i].size,3.1f+.6f*FxRandom(path,64),
                ParticleAngle(cells[i].p,direction,eye),opacity*envelope,eye,frame);
        }
    }

    float SourceSmokeScale(float age,bool strip) const {
        // 直接采样本机NIF的200点烟带/64点烟丝尺寸序列，以归一化寿命线性插值。
        // 长度/寿命另外按350范围和三倍播放适配；绝不照抄Skyrim的巨大Bomb/Gravity数值。
        static const float band[200]={0.100000001f,0.114547454f,0.132351309f,0.15338777f,0.177528799f,0.204539135f,0.23406969f,0.265717685f,
            0.298984349f,0.333392501f,0.368424892f,0.403582335f,0.438519508f,0.472847074f,0.506326139f,0.538751781f,
            0.569975913f,0.599904835f,0.628495038f,0.655701041f,0.681520402f,0.706011474f,0.729174137f,0.751041055f,
            0.77165246f,0.791053772f,0.809314549f,0.826464951f,0.842538834f,0.857608914f,0.871692121f,0.884842873f,
            0.897097468f,0.908507705f,0.919077992f,0.928887784f,0.937928021f,0.946258724f,0.953886628f,0.960854948f,
            0.967182219f,0.972906232f,0.978034496f,0.982586741f,0.986602783f,0.990090311f,0.993066311f,0.995552301f,
            0.997567356f,0.999124646f,1.00023782f,1.00093794f,1.00126588f,1.00125849f,1.00094688f,1.00035775f,
            0.999513865f,0.998435438f,0.99714011f,0.995642066f,0.993956804f,0.992096364f,0.990070462f,0.987891197f,
            0.985563755f,0.983100355f,0.980506122f,0.977789879f,0.974957347f,0.972010732f,0.968959808f,0.96580857f,
            0.962560058f,0.959217012f,0.955788076f,0.952275395f,0.948680282f,0.945007324f,0.941261172f,0.937442064f,
            0.933554113f,0.929596961f,0.925578356f,0.921497762f,0.917353868f,0.913154483f,0.908902586f,0.904592037f,
            0.90023011f,0.895819604f,0.891358256f,0.886848629f,0.882292926f,0.877693534f,0.873052895f,0.868367791f,
            0.863645792f,0.858878016f,0.85407728f,0.849234641f,0.844357371f,0.839447439f,0.834500968f,0.829519391f,
            0.824504554f,0.819463909f,0.814387262f,0.809282064f,0.804149985f,0.798986316f,0.793798745f,0.788582444f,
            0.783338904f,0.778075695f,0.772781789f,0.767464697f,0.762125731f,0.75676626f,0.751381218f,0.745978177f,
            0.740552008f,0.735104084f,0.729635537f,0.724154115f,0.718648016f,0.713124871f,0.70758599f,0.702026069f,
            0.696452856f,0.690867484f,0.685264707f,0.679645538f,0.67401135f,0.668363214f,0.662702501f,0.657030344f,
            0.651341379f,0.645643413f,0.639931142f,0.634212434f,0.628481865f,0.622741044f,0.616990924f,0.61122632f,
            0.605462074f,0.599685967f,0.593899548f,0.588111103f,0.582315266f,0.576506913f,0.570700884f,0.564885676f,
            0.559069216f,0.553246975f,0.547420561f,0.541591704f,0.535762191f,0.529934049f,0.524102688f,0.518270135f,
            0.512438655f,0.506604195f,0.500775099f,0.494953662f,0.48913008f,0.483313233f,0.477499425f,0.471691579f,
            0.465892762f,0.460099965f,0.454316527f,0.448540211f,0.442780226f,0.437028974f,0.43129614f,0.425575018f,
            0.419869989f,0.414180636f,0.408512414f,0.402870625f,0.397245586f,0.391649276f,0.386083066f,0.380545139f,
            0.375043154f,0.369576782f,0.36414662f,0.358763218f,0.353429496f,0.348145694f,0.342922151f,0.337759137f,
            0.332671016f,0.327663422f,0.322745562f,0.317927688f,0.313225359f,0.308654547f,0.304239571f,0.300000012f};
        static const float wisp[64]={0.449999988f,0.460950077f,0.471965134f,0.483035922f,0.494152933f,0.505323648f,0.516543984f,0.527809203f,
            0.539120734f,0.550477743f,0.561882019f,0.573334575f,0.584832668f,0.596367002f,0.607958257f,0.619606674f,
            0.631302774f,0.643052101f,0.654849291f,0.666704178f,0.678614616f,0.690593302f,0.702640295f,0.714742124f,
            0.726914048f,0.739171624f,0.751502573f,0.763908327f,0.776405036f,0.78900826f,0.801704288f,0.81449312f,
            0.827416837f,0.840458572f,0.853642821f,0.866977274f,0.880481243f,0.894169927f,0.908067703f,0.922205985f,
            0.936620951f,0.951363206f,0.966504633f,0.982117176f,0.99833262f,1.01542115f,1.03359592f,1.05293834f,
            1.07346475f,1.0952692f,1.11840451f,1.14293659f,1.16890764f,1.19635832f,1.22525477f,1.255566f,
            1.28718174f,1.31986058f,1.35323274f,1.38666666f,1.41929746f,1.44998002f,1.47735965f,1.5f};
        const float* values=strip?band:wisp;unsigned count=strip?200:64;
        float x=Clamp(age,0,1)*float(count-1);unsigned i=unsigned(x);
        if(i>=count-1)return values[count-1];
        return values[i]+(values[i+1]-values[i])*(x-float(i));
    }
    float SourceSmokeAge(float begin,float life) const {
        // 2.8烟包单次出生并持续输运，不再floor循环回到刀路起点；三倍速下循环跳回尤其像闪烁颗粒。
        // 每个包独立寿命由调用者给出，收刀没有重新发射；剪辑秒不受世界时缓影响，END统一清理。
        if(time<begin||life<=0)return -1.f;
        return (time-begin)/life;
    }
    float SourceSmokeEnvelope(float age) const {
        if(age<0||age>=1||time>=END)return 0;
        // 参照BG3颜色/尺寸/发射分层：透明度仅控制柔入与末段消散，颜色单独由shader按年龄渐变。
        // 初斩后主烟形成，收刀冲击由位置和尺寸承担；不可重置年龄或在尾段反复生成新团。
        float birth=Clamp(age/.12f,0,1),death=Clamp((1-age)/.34f,0,1);
        float charge=Clamp((time-CUT)/.24f,0,1),tail=Clamp((time-SHEATH)/(END-SHEATH),0,1);
        return birth*birth*(3-2*birth)*death*death*(3-2*death)*(.32f+.68f*charge)*(1-tail*tail*tail);
    }
    void SourceSmokeVertex(const Vector3& p,float u,float v,unsigned shape,float alpha,float age){
        // 四分量UV合同：xy是单烟形局部UV，z=烟形索引*16+剪辑秒，w=伤害圆半径。
        // END=6.7<16，整个四边形共享shape/时钟，不串格；shader明确解包，不按动画翻页。
        // 不把四角夹回球面以免折叠；片元仍通过同一半球边界裁切，绝不影响医疗范围。
        geometry->position(p);geometry->textureCoord(u,v,float(shape%16)*16.f+time,AreaRadius());
        // 2.8保持既有颜色编码：shader用G解码平滑寿命，独立实现亮青蓝到较暗蓝的渐变。
        // Alpha只作柔入/消散，颜色不再二次相乘变黑；xy/shape*16+clock/半径合同保持不变。
        float old=Clamp(age,0,1),light=1-old*old*(3-2*old);
        geometry->colour(.42f+.34f*light,.68f+.27f*light,1.f,((settings.opticalProbeMode==1||settings.opticalProbeMode==4)?0.f:Clamp(alpha,0,1)));
    }
    void SourceSmokeQuad(const Vector3& a,const Vector3& b,const Vector3& c,const Vector3& d,
                         float u0,float u1,unsigned shape,float alpha,float age){
        SourceSmokeVertex(a,u0,0,shape,alpha,age);SourceSmokeVertex(b,u0,1,shape,alpha,age);
        SourceSmokeVertex(c,u1,1,shape,alpha,age);SourceSmokeVertex(d,u1,0,shape,alpha,age);
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);
        geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
    }
    // 复用已有的非const半球边界助手，不把此辅助绘制方法声明为const。
    Vector3 SourceSmokePoint(unsigned id,float along,float age) {
        const Slash& s=slashes[(id*2)%slashes.size()];
        Vector3 dir=facing*s.direction;if(dir.squaredLength()<.000001f)dir=Vector3::UNIT_X;dir.normalise();
        Vector3 side=dir.crossProduct(Vector3::UNIT_Y);
        if(side.squaredLength()<.000001f)side=Vector3::UNIT_Z;side.normalise();
        float radius=AreaRadius(),seed=6.2831853f*FxRandom(id,90);
        float release=Clamp((time-SHEATH)/.70f,0,1);release=release*release*(3-2*release);
        // 宽烟流沿真实刀路连续输运、卷起，年龄不再循环跳回；横向波相位沿整条UV连续，段间不跳。
        // 收刀只有一次向外分离/上浮，不增加物理粒子或影响角色；位置仍由同一半球助手约束。
        Vector3 p=facing*(s.centre*layoutScale)+dir*(s.length*layoutScale*(along*1.1f-.55f)+radius*.34f*age);
        p+=side*(radius*(.090f*sinf(along*6.f-time*1.65f+seed)*sinf(along*3.14159265f)
                               +.070f*sinf(age*3.f+seed)));
        p.y+=radius*(.035f+.13f*age+.036f*sinf(along*5.f+time*1.35f+seed));
        p+=p*(.10f*release)+Vector3::UNIT_Y*(radius*.045f*release);
        return BoundAtmosphere(p);
    }
    void SourceSmokeRibbons(const Vector3& eye){
        // 本机主烟为BSStripParticleSystem；这里重建其连续条带/尺寸生命周期，不冒称完整执行NIF。
        // 48条按中心深度远到近提交；0..8旧section保持，新section同样由既有Finish负责销毁。
        HazeCell bands[SMOKE_BANDS];float radius=AreaRadius();
        for(unsigned i=0;i<SMOKE_BANDS;++i){
            const Slash& s=slashes[(i*2)%slashes.size()];float age=SourceSmokeAge(s.at,std::max(.85f,(END-s.at)*(.90f+.08f*FxRandom(i,91))));
            bands[i].p=SourceSmokePoint(i,.5f,Clamp(age,0,1));bands[i].depth=(eye-bands[i].p).squaredLength();bands[i].id=i;
        }
        std::sort(bands,bands+SMOKE_BANDS);
        for(unsigned i=0;i<SMOKE_BANDS;++i){
            unsigned id=bands[i].id;const Slash& s=slashes[(id*2)%slashes.size()];
            // 2.8主体是沿刀路连续烟流；全半球Mist仍停用，烟带只按各自包络显露。
            float age=SourceSmokeAge(s.at,std::max(.85f,(END-s.at)*(.90f+.08f*FxRandom(id,91)))),alpha=.26f*SourceSmokeEnvelope(age);
            // 350范围下旧烟带太细/太透明；扩大连续烟体而非增加碎颗粒，固定48条/10段与排序不变。
            // 源尺寸曲线保留，但初期下限和收刀扩张独立控制；Alpha有界，禁止整体半球幕布。
            float release=Clamp((time-SHEATH)/.70f,0,1);release=release*release*(3-2*release);
            float width=radius*(.070f+.035f*FxRandom(id,92))*(.35f+.65f*SourceSmokeScale(age,true))*(1+.18f*release);
            unsigned shape=unsigned(FxRandom(id,93)*15.999f);
            for(unsigned j=0;j<SMOKE_SEGMENTS;++j){
                float u0=float(j)/float(SMOKE_SEGMENTS),u1=float(j+1)/float(SMOKE_SEGMENTS);
                Vector3 a=SourceSmokePoint(id,u0,Clamp(age,0,1)),b=SourceSmokePoint(id,u1,Clamp(age,0,1)),dir=b-a;
                if(dir.squaredLength()<.000001f)dir=facing*s.direction;
                Vector3 side=dir.crossProduct(eye-(a+b)*.5f);
                if(side.squaredLength()<.000001f)side=dir.crossProduct(Vector3::UNIT_Y);
                if(side.squaredLength()<.000001f)side=Vector3::UNIT_X;side.normalise();
                float w0=width*(.25f+.75f*sinf(u0*3.14159265f)),w1=width*(.25f+.75f*sinf(u1*3.14159265f));
                SourceSmokeQuad(a-side*w0,a+side*w0,b+side*w1,b-side*w1,u0,u1,shape,alpha,age);
            }
        }
    }
    Vector3 SourceWispPoint(unsigned id,float age) {
        float radius=AreaRadius(),sign=(id&1)?1.f:-1.f;
        float a=6.2831853f*FxRandom(id,100)+sign*(1.05f*age+.20f*time);
        float r=radius*(.14f+.53f*FxRandom(id,101)+.07f*sinf(age*3.f+float(id)));
        float release=Clamp((time-SHEATH)/.75f,0,1);release=release*release*(3-2*release);
        // 烟涡单包旋流并抬升，收刀再向外松开；保持中心留白、不同包独立相位，不铺满平面。
        // 由远到近排序与透明半球裁切保持；仅特效局部坐标，没有风场/碰撞/角色速度改动。
        Vector3 p(cosf(a)*r,.8f+radius*(.08f+.34f*FxRandom(id,102)+.20f*age),sinf(a)*r);
        p+=p*(.10f*release)+Vector3::UNIT_Y*(radius*.025f*release);
        return BoundAtmosphere(p);
    }
    void SourceSmokeWisps(const Vector3& eye){
        HazeCell cells[SMOKE_WISPS];float radius=AreaRadius();
        for(unsigned i=0;i<SMOKE_WISPS;++i){
            float begin=CUT+.80f*FxRandom(i,103),life=(END-begin)*(.78f+.16f*FxRandom(i,104)),age=SourceSmokeAge(begin,life);
            cells[i].p=SourceWispPoint(i,Clamp(age,0,1));cells[i].depth=(eye-cells[i].p).squaredLength();cells[i].id=i;
        }
        std::sort(cells,cells+SMOKE_WISPS);
        for(unsigned i=0;i<SMOKE_WISPS;++i){
            // 主蓝烟从初斩分批出生，停止循环复位；尾烟独立寿命，不能在收刀之后再次亮起。
            unsigned id=cells[i].id;float begin=CUT+.80f*FxRandom(id,103),life=(END-begin)*(.78f+.16f*FxRandom(id,104)),age=SourceSmokeAge(begin,life);
            // 2.8烟涡补充连续烟流之间的卷边，单包独立寿命；形状受共享低频密度场控制。
            float alpha=(.045f+.025f*FxRandom(id,105))*SourceSmokeEnvelope(age);
            // 低数量预算内的大尺度柔烟涡，沿原尺寸曲线扩张；不加烟团数量，收刀余气轻微膨胀。
            float release=Clamp((time-SHEATH)/.75f,0,1);release=release*release*(3-2*release);
            float size=radius*(.110f+.045f*FxRandom(id,106))*SourceSmokeScale(age,false)*(1+.15f*release);
            // 原烟丝旋转为.379253±.174533 rad/s，随机正负；图集切换原本关闭，因此每丝固定烟形。
            float angle=6.2831853f*FxRandom(id,107)+((id&1)?1.f:-1.f)*(.379253f+(.5f-FxRandom(id,108))*.349066f)*std::max(0.f,age)*life;
            Vector3 view=eye-cells[i].p;if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
            Vector3 right=view.crossProduct(Vector3::UNIT_Y);if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
            Vector3 up=right.crossProduct(view);up.normalise();
            Vector3 a=(right*cosf(angle)+up*sinf(angle))*size;
            Vector3 b=(-right*sinf(angle)+up*cosf(angle))*(size*(1.35f+.65f*FxRandom(id,109)));
            SourceSmokeQuad(cells[i].p-a-b,cells[i].p+a-b,cells[i].p+a+b,cells[i].p-a+b,0,1,unsigned(FxRandom(id,110)*15.999f),alpha,age);
        }
    }

    void SourceFlashes(const Vector3& eye){
        // 初斩/收刀脉冲各自一次，尾烟仍用独立粒子寿命；不改动画关键帧、伤害时刻或世界时间。
        // 原图Alpha与原曲线仍作细节，明确相位承担主体节奏；两张现有小范围光晕，拒绝半球闪白。
        float cutAge=time-CUT,releaseAge=time-SHEATH;
        float cut=cutAge<0?0.f:powf(Clamp(1-cutAge/.36f,0,1),2.f);
        float burst=releaseAge<0?0.f:powf(Clamp(1-releaseAge/.40f,0,1),2.f);
        float glow=releaseAge<0?0.f:powf(Clamp(1-releaseAge/.75f,0,1),2.f);
        float source=Clamp(SourceCurve(2,releaseAge),0,1);
        float r=AreaRadius(),spread=Clamp(releaseAge/.70f,0,1);spread=spread*spread*(3-2*spread);
        Vector3 p(0,.8f+r*.10f,0);
        SourceSprite(p,r*(.16f+.13f*spread),1,0,cut*.24f+burst*(.45f+.10f*source),eye,.22f,.64f,1);
        SourceSprite(p,r*(.20f+.28f*spread),.22f,.27f,glow*.22f*(1-spread),eye,.15f,.48f,.90f);
    }
    void SourceSparks(const Vector3& eye){
        unsigned before=vertex;float r=AreaRadius();
        // 128个固定槽沿实际刀路出生、随方向掠过并轻微卷曲；冷白短光丝与灰雾是独立层。
        // 寿命0.64..0.86剪辑秒即0.21..0.29真实秒，旧0.2剪辑秒只有0.067秒，远镜头很难辨认。
        // 收刀只重置同一预算的末次喷散，不追加实体；所有位置仍受350半球约束，结束不残留。
        for(unsigned i=0;i<128;++i){
            const Slash& s=slashes[i%slashes.size()];float at=time<SHEATH?s.at:SHEATH;
            float age=time-at-float(i%8)*.014f,life=.64f+.22f*FxRandom(i,71);
            if(age<0||age>life)continue;float u=age/life;
            Vector3 direction=facing*s.direction;if(direction.squaredLength()<.000001f)direction=Vector3::UNIT_X;direction.normalise();
            Vector3 side=direction.crossProduct(Vector3::UNIT_Y);if(side.squaredLength()<.000001f)side=Vector3::UNIT_Z;side.normalise();
            Vector3 p=facing*(s.centre*layoutScale)+direction*(s.length*layoutScale*(-.85f+1.70f*FxRandom(i,72)));
            p+=direction*(r*.13f*u)+side*(r*.025f*sinf(u*3.14159265f)*(i&1?1.f:-1.f));
            p+=Vector3::UNIT_Y*(r*.025f*u);p=BoundAtmosphere(p);
            float alpha=Clamp(age/.025f,0,1)*powf(Clamp(1-u,0,1),1.5f);
            SourceSprite(p,r*(.003f+.003f*FxRandom(i,73)),2.0f+4.0f*FxRandom(i,74),
                ParticleAngle(p,direction,eye),alpha*.70f,eye,.72f,.84f,1);
        }
        if(vertex==before)SourceQuad(Vector3::ZERO,Vector3::ZERO,Vector3::ZERO,Vector3::ZERO,0,0,0,0);
    }
    void StartLayer(unsigned index,const char* material){
        if(section)geometry->beginUpdate(index);else geometry->begin(material,Ogre::RenderOperation::OT_TRIANGLE_LIST,GROUP);
        vertex=0;
    }
    unsigned EndLayer(){if(!geometry->end())throw std::runtime_error("Empty VFX layer");return vertex;}

    Vector3 Joint(const std::string& name){
        // 实例骨骼局部坐标经角色节点缩放/旋转变成场景坐标，再减去特效节点的场景位置。
        // 不猜测角色逻辑位置的浮动原点约定；与 Draw 使用同一节点基准。
        Vector3 scenePos=animation->node->convertLocalToWorldPosition(skeleton->getBone(name)->_getDerivedPosition());
        return scenePos-node->_getDerivedPositionUpdated();
    }
    void Draw(){
        Renderer* r=Render();
        // 借当前可见角色的场景节点换算固定施放中心，避免直接使用绝对世界位置。
        // 特效节点挂根节点下，世界转局部后再写；后面的 Joint 和相机也使用同一场景基准。
        Character* casterObject=Resolve();if(!CharacterReady(casterObject))throw std::runtime_error("Caster unavailable for VFX centre");
        // 保持施放时的逻辑中心anchor：当前场景节点位置加世界差向量，抵消浮动原点。
        // 旧版容许2单位角色位移时，光带会跟随角色而伤害仍在anchor，造成边缘不一致。
        Vector3 casterScene=animation->node->_getDerivedPositionUpdated()+(anchor-casterObject->getPosition());
        Ogre::SceneNode* root=scene->getRootSceneNode();
        node->setPosition(root->convertWorldToLocalPosition(casterScene));
        Vector3 effectScene=node->_getDerivedPositionUpdated();
        Vector3 eye=r->getCamera()->getDerivedPosition()-effectScene;
        StartLayer(0,"JCE/Glow");
        // 地面圆半径与资产布局缩放分开；96条裂痕中心、长度和宽度使用同一拟合系数。
        // 裂痕先脉冲亮起，空间停留时保留弱痕；收刀按各道固定相位消退，不挤成持续亮线笼。
        float widthScale=layoutScale/30.f;
        for(size_t i=0;i<slashes.size();++i){const Slash& s=slashes[i];float age=time-s.at;
            if(age<0||time>=END)continue;
            // 2.8初斩短亮、停留降低线笼感；收刀再短亮后按各道固定相位分离消退。
            // 不修改斩击位置/96条资产或医疗触发，仅改变光的包络，给连续烟体和空间片区留下对比。
            float pulse=powf(Clamp(1-age/.28f,0,1),2.f),intensity=.24f+.76f*pulse;
            if(time>=SHEATH){
                float release=Clamp((time-SHEATH-.004f*float(i%17))/.58f,0,1);
                float fade=1-release*release*(3-2*release);
                intensity=(.35f+.65f*Clamp(1-(time-SHEATH)/.18f,0,1))*fade;
            }
            Vector3 p=facing*(s.centre*layoutScale),d=facing*(s.direction*s.length*layoutScale);
            Ribbon(p-d,p+d,.18f*widthScale,intensity*.6f,eye);Ribbon(p-d,p+d,.035f*widthScale,intensity*2,eye);
            SlashAfterimages(s,unsigned(i),.18f*widthScale,intensity,eye);
        }
        // 唯一地面范围圈从演出开始固定为伤害半径，收刀后只淡出，不伸缩成另一种范围。
        // 圈依旧位于施放地平面上方0.8单位并遵守世界深度；坡地遮挡不是伤害范围变小。
        float areaRadius=AreaRadius(),ringWidth=.1f*widthScale;
        float boundaryLight=time<SHEATH?(time<CUT?.4f:.7f):Clamp(1-(time-SHEATH)/.65f,0,1);
        GroundRing(areaRadius,ringWidth,boundaryLight);
        // 独立视觉刀/鞘；不强行修改真实装备，角色已有武器可能与它同时显示。
        Vector3 left=Joint("Bip01 L Hand");
        Vector3 right=Joint("Bip01 R Hand");
        Vector3 blade=facing*Vector3(-.8f,-.2f,.3f);blade.normalise();
        Ribbon(left,left+blade*7,.14f,.65f,eye);
        if(time>=DRAW&&time<SHEATH){Ribbon(right,right+blade*7,.12f,1.5f,eye);Ribbon(right,right+blade*7,.025f,3,eye);}
        else Ribbon(left-blade*.8f,left,.25f,.9f,eye);
        // 掠过16条真实路径的持刀幻影；空间碎裂仅为下一材质段的瞬态光影，没有边框/落地碎片。
        unsigned total=EndLayer();
        StartLayer(1,"JCE/Mist");Mist(eye);total+=EndLayer();
        StartLayer(2,"JCE/Glass");Glass(eye);Phantoms(eye);total+=EndLayer();
        // 折射优先级低于其他自有段；独立模式五片复用原NIF，失败保留同声明零Alpha占位。
        StartLayer(3,refractionReady?"JCE/Refraction":"JCE/Glass");
        if(refractionReady)SpatialFracture(eye);
        else{
            // 中途HDR复制失败后仍用NORMAL/四分量UV和零Alpha占位；不能回退到TriangleFx的两分量布局。
            // BeginUpdate必须与上一帧顶点声明一致；此路径不访问已禁用材质的任何uniform。
            float radius=AreaRadius();
            OpticalVertex(Vector3::ZERO,0,0,radius,0.f);OpticalVertex(Vector3::UNIT_X,1,0,radius,0.f);
            OpticalVertex(Vector3::UNIT_Y,0,1,radius,0.f);
            geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);vertex+=3;
        }
        total+=EndLayer();
        // 追加原纹理层，保留0..3既有section和首段背景复制时点。总预算含透明占位四边形。
        StartLayer(4,"JCE/SourceBlade");SourceSlashes(eye,false);total+=EndLayer();
        StartLayer(5,"JCE/SourceFeather");SourceSlashes(eye,true);total+=EndLayer();
        StartLayer(6,"JCE/SourceDust");SourceDust(eye);total+=EndLayer();
        StartLayer(7,"JCE/SourceFlash");SourceFlashes(eye);total+=EndLayer();
        StartLayer(8,"JCE/SourceSpark");SourceSparks(eye);total+=EndLayer();
        // 追加9/10两个固定段，不挪折射监听器的0..8索引；共用同一节点、半径和清理生命周期。
        StartLayer(9,"JCE/SourceSmokeRibbon");SourceSmokeRibbons(eye);total+=EndLayer();
        StartLayer(10,"JCE/SourceSmokeWisp");SourceSmokeWisps(eye);total+=EndLayer();
        if(total>VFX_VERTEX_LIMIT)throw std::runtime_error("VFX vertex budget exceeded");
        vertex=total;section=true;
        // 只记录每个阶段首次到达，不按碎片/粒子逐帧刷日志；可判断是否真正提交三层。
        if(!(fxStages&1)){fxStages|=1;std::ostringstream s;s<<"vfx_layers_ready id="<<castId
            <<" layers=11 source_textures=7 source_curves=8 phantom_mesh_vertices="<<phantomAsset.vertices<<" refraction="<<refractionReady<<" phantom_paths="<<PHANTOM_PATHS<<" phantom_echoes="<<PHANTOM_ECHOES<<" slash_echoes="<<SLASH_ECHOES
            <<" optics_revision=2.9.8_slash_aligned_contours optics_curves=9 optics_planes=0 optics_facets="<<(settings.opticalProbeMode>=3?INDEPENDENT_FACET_COUNT:(settings.opticalProbeMode==0?SOURCE_FACET_COUNT:1u))<<" max_offset_pixels=36 layer_order="<<(settings.opticalProbeMode>=3?"visuals_then_refraction_snapshot":"refraction_then_visuals")<<" particle_revision=2.8_single_birth_broad_smoke smoke_bands=48 smoke_segments=10 smoke_wisps=96 smoke_shapes=16 smoke_clock=clip_seconds dust_paths=48 dust_slots=144 spark_slots=128 fog_slices="<<MIST_SLICES<<" atmosphere=along_path_smoke_no_global_mist glow_energy=alpha_times_two cloud_noise=authored27 fog_step="<<(2.f/float(MIST_SLICES))<<" fog_density_clock=clip_seconds palette=2.8_age_cyan_to_blue facets="<<shards.size()<<" vertices="<<vertex;Log(s.str());}
        if(time>=CUT&&!(fxStages&2)){fxStages|=2;Log("vfx_phase: spatial_fracture id="+Number(castId));}
        if(time>=SHEATH&&!(fxStages&4)){fxStages|=4;Log("vfx_phase: spatial_dissolve id="+Number(castId));}
        // 五片总退场尾段保持1.30，只影响自有特效清空诊断，不延迟原END后的世界时间恢复。
        if(time>=SHEATH+(settings.opticalProbeMode>=3?FACET_LIFETIME_TAIL:.75f)&&!(fxStages&8)){fxStages|=8;Log("vfx_phase: spatial_regions_cleared id="+Number(castId));}
        // 每次施放仅一次主烟包诊断；计数是CPU存活包，不冒称实际可见像素，无逐粒子/逐帧日志。
        if(time>=CUT+.75f&&!(fxStages&32)){
            fxStages|=32;unsigned aliveBands=0,aliveWisps=0;
            for(unsigned i=0;i<SMOKE_BANDS;++i){
                const Slash& s=slashes[(i*2)%slashes.size()];
                float a=SourceSmokeAge(s.at,std::max(.85f,(END-s.at)*(.90f+.08f*FxRandom(i,91))));
                if(SourceSmokeEnvelope(a)>.001f)++aliveBands;
            }
            for(unsigned i=0;i<SMOKE_WISPS;++i){
                float born=CUT+.80f*FxRandom(i,103),life=(END-born)*(.78f+.16f*FxRandom(i,104));
                if(SourceSmokeEnvelope(SourceSmokeAge(born,life))>.001f)++aliveWisps;
            }
            std::ostringstream s;s<<"vfx_smoke_packets id="<<castId<<" phase=hold bands="<<aliveBands<<" wisps="<<aliveWisps
                <<" age_reset=0 ribbon_alpha_cap=0.26 wisp_alpha_cap=0.07 global_mist=disabled";Log(s.str());
        }
        // 更新后的有限包围盒也用于诊断；不使用无限 AABB 或改其他物体的可见性。
        if(queueCalls==0&&time>1&&!queueWarning){queueWarning=true;Log("vfx_waiting_for_queue_callback id="+Number(castId));}

    }
    void Tick(GameWorld* w){
        double now=Seconds();
        if(active&&w!=world){Finish("world_replaced",false);world=w;return;}world=w;
        // 即使演出已经结束，暂停解除或恢复失败后的后续帧仍清偿时间恢复债务。
        if(speedRestorePending)RestoreTime("resume_retry");
        // 单键上升沿，不再要求 Ctrl/Shift；下面的输入模式/编辑框门槛继续防止输入文字时施放。
        bool combo=Foreground()&&(GetAsyncKeyState(int(settings.castKey))&0x8000);
        bool edge=combo&&!wasKey;wasKey=combo;
        // 只在施放键上升沿记录，不按帧刷日志；可分辨没收到输入与前置条件拒绝。
        if(edge){std::ostringstream s;s<<"cast_key_detected vk="<<settings.castKey;Log(s.str());}
        if(edge){
            // 新输入先于旧演出的时间线结算；覆盖不能补算旧演出尚未发生的伤害。
            const char* blocked=!w->player?"player_unavailable":
                w->isLoadingFromASaveGame()?"loading":w->isPaused()?"paused":!key?"input_unavailable":
                !key->controlEnabled?"controls_disabled":key->gameMode!=InputHandler::GLOBAL?"non_global_input_mode":
                (GetAsyncKeyState(VK_ESCAPE)&0x8000)?"escape_held":Editing()?"text_editing":0;
            if(blocked){
                Log(std::string("cast_blocked: ")+blocked);
                if(!active)return;
            }else{
                if(active){
                    std::ostringstream s;s<<"cast_restart_requested id="<<castId<<" t="<<time<<" damage_done="<<damageDone;Log(s.str());
                    // 完整恢复骨骼/武器/世界速度并释放音效与图形，再获取新演出的快照。
                    // 已结算的伤害不回滚；wasKey保持按键状态，长按不会逐帧重启。
                    Finish("restarted_by_key");
                }
                Character* c=w->player->selectedCharacter.getCharacter();
                try{Begin(c,now);}catch(const std::exception& e){Log(std::string("cast_rejected: ")+e.what());Finish("begin_failed");}
                return;
            }
        }
        if(active){
            if(w->isLoadingFromASaveGame()){Finish("loading");return;}
            // 分别记录暂停/失焦/按Esc/输入失效，便于确认时间恢复延后是否符合玩家操作。
            const char* cancel=w->isPaused()?"cancelled_pause":!Foreground()?"cancelled_focus":
                (GetAsyncKeyState(VK_ESCAPE)&0x8000)?"cancelled_escape":(!key||!key->controlEnabled)?"cancelled_input":0;
            if(cancel){Finish(cancel);return;}
            Character* c=Resolve();const char* blocked=CasterBlockedReason(c);
            if(blocked){Finish(blocked);return;}
            if(!SameAnimation(c)){Finish("caster_animation_changed");return;}
            // 伤害以U键时的快照为准：不因AI收鞘、缓存清空或用户卸下/换装武器而撤销。
            // 已在上面检查角色、世界和加载状态；跨帧仅保留数值快照与serial hand，不读旧武器指针。
            if(!SameRenderer()){Finish("scene_replaced");return;}
            if(fabs(w->getFrameSpeedMultiplier()-settings.slow)>.00005f){Finish("speed_changed_externally");return;}
            if((c->getPosition()-anchor).squaredLength()>4){Finish("caster_moved");return;}
            double elapsed=now-beginning;
            // 卡顿跨过多个事件时依序处理，只触发一次；过久停顿取消，禁止回来补一刀。
            // time 是剪辑秒，必须除回倍率再与真实间隔比较，否则加速后会漏检卡顿。
            if(elapsed-double(time)/PLAYBACK_RATE>1.5){Finish("frame_stall");return;}
            time=float(elapsed*PLAYBACK_RATE);
            if(!poseSeen&&elapsed>.5){Finish("pose_hook_not_observed");return;}
            Pose(animation);
            if(!cutDone&&time>=CUT){cutDone=true;}
            // Damage可因每击资格失效立即Finish；中断后本帧不得继续绘制或重复访问已释放状态。
            if(!damageDone&&time>=SHEATH){Damage();if(!active)return;}
            if(time>=END){Finish("completed");return;}
            Draw();
            if(now-lastSummary>=2){lastSummary=now;std::ostringstream s;s<<"cast_progress id="<<castId<<" t="<<time<<" pose_calls="<<poseCalls<<" queue_calls="<<queueCalls<<" render_calls="<<renderCalls<<" vertices="<<vertex;Log(s.str());}
            return;
        }

    }
};
Runtime* runtime=0;
typedef void(__fastcall* FrameFn)(GameWorld*,float);
typedef void(__fastcall* PoseFn)(AnimationClass*,float);
FrameFn originalFrame=0;PoseFn originalPose=0;
void __fastcall PoseHook(AnimationClass* a,float dt){
    if(!InterlockedCompareExchange(&ready,0,0)){originalPose(a,dt);return;}
    // 非施法者直接通过；只为受控角色串行化原生变换与姿势覆盖。
    if(InterlockedCompareExchangePointer(&poseOwner,0,0)!=a){originalPose(a,dt);return;}
    Guard lock(gate);
    originalPose(a,dt);
    if(GetCurrentThreadId()!=DWORD(InterlockedCompareExchange(&frameThread,0,0))){
        if(runtime->active&&!runtime->wrongThreadNoted){runtime->wrongThreadNoted=true;std::ostringstream s;s<<"pose_thread_mismatch expected="<<frameThread<<" actual="<<GetCurrentThreadId();Log(s.str());}
        return;
    }
    if(runtime->active&&a==runtime->animation){try{runtime->Pose(a,true);}catch(const std::exception& e){Log(std::string("pose_error: ")+e.what());runtime->Finish("pose_error");}}
}
void __fastcall FrameHook(GameWorld* w,float dt){
    originalFrame(w,dt);
    if(!InterlockedCompareExchange(&ready,0,0))return;
    LONG previousThread=InterlockedCompareExchange(&frameThread,LONG(GetCurrentThreadId()),0);
    Guard lock(gate);
    // 首次回调证明钩子链实际到达；之后不加空闲逐帧日志。
    if(!previousThread){std::ostringstream s;s<<"frame_hook_seen thread="<<GetCurrentThreadId();Log(s.str());}
    try{runtime->Tick(w);}catch(const std::exception& e){Log(std::string("runtime_error: ")+e.what());runtime->Finish("runtime_error");}
}
} // namespace JCE

// RE_Kenshi 使用 GetProcAddress 查找 ?startPlugin@@YAXXZ（C++ 无参 void __cdecl）。
// 不能使用 extern "C"：它会仅导出 startPlugin，加载器找不到入口而无法初始化。
__declspec(dllexport) void startPlugin(){
    using namespace JCE;
    if(InterlockedCompareExchange(&started,1,0))return;
    InitializeCriticalSection(&gate);QueryPerformanceFrequency(&frequency);
    wchar_t path[32768];HMODULE self=0;
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(&startPlugin),&self))return;
    DWORD n=GetModuleFileNameW(self,path,32768);if(n==0||n>=32768)return;
    directory.assign(path,n);directory=directory.substr(0,directory.find_last_of(L"\\/")+1);
    Guard lock(gate);
    try{
        skin.Load();LoadAssets();runtime=new Runtime();runtime->settings.Load();
        // 两个绑定均使用声明中的成员函数地址，避免在插件里维护字符串函数签名。
        intptr_t frame=NativeAddress(&GameWorld::_NV_mainLoop_GPUSensitiveStuff,"frame");
        // 本机 Human::update 先调用基类，再重置自身标记；不能把基类返回当成完整人形入口结束。
        // 控制点改到整个入口返回后，减少原生顺序依赖；并未把该标记重置认定为旧版抽动的已证实原因。
        intptr_t pose=NativeAddress(&AnimationClassHuman::_NV_update,"pose");
        if(!frame||!pose)throw std::runtime_error("Native function binding unavailable");
        KenshiLib::HookStatus h1=KenshiLib::AddHook(frame,reinterpret_cast<void*>(&FrameHook),&originalFrame);
        KenshiLib::HookStatus h2=KenshiLib::AddHook(pose,reinterpret_cast<void*>(&PoseHook),&originalPose);
        if(h1!=KenshiLib::SUCCESS||h2!=KenshiLib::SUCCESS||!originalFrame||!originalPose)throw std::runtime_error("Hook installation incomplete; plugin remains inactive");
        InterlockedExchange(&ready,1);
        // 启动日志输出实际生效键值，修改 ini 后必须重启游戏才能读取。
        std::ostringstream s;s<<"plugin_ready; single VK="<<runtime->settings.castKey<<" casts (85=U); Escape cancels; resources=11; source_vfx=ap05_textures_curves_strips; animation=ap05_HKX_retarget; version=2.9.11-dev";Log(s.str());
    }catch(const std::exception& e){Log(std::string("plugin_disabled: ")+e.what());ErrorLog(std::string("JudgementCutEnd: ")+e.what());}
}
