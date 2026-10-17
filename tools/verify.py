"""仅解析与数学检查，不调用编译器、不安装资源到游戏。"""
from pathlib import Path
import ast, hashlib, importlib.util, json, math, re, struct, sys, wave
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"package/JudgementCutEnd"
checks=[]
def check(name,condition):
    checks.append({"name":name,"passed":bool(condition)})
    if not condition:raise AssertionError(name)
def main():
    for p in (ROOT/"tools").glob("*.py"):ast.parse(p.read_text("utf8"));check("Python AST "+p.name,True)
    project=ET.parse(ROOT/"JudgementCutEnd.vcxproj").getroot();ns={"p":"http://schemas.microsoft.com/developer/msbuild/2003"}
    check("v100 ABI",project.find(".//p:PlatformToolset",ns).text=="v100")
    # VC100 的成员函数取址与库桩地址合同；优化配置必须与链接器一起生效。
    check("whole program optimization enabled",project.find(".//p:WholeProgramOptimization",ns).text=="true")
    check("LTCG and nonincremental linking",project.find(".//p:LinkTimeCodeGeneration",ns).text=="UseLinkTimeCodeGeneration" and project.find(".//p:LinkIncremental",ns).text=="false")
    check("only own C++ translation unit",[p.attrib["Include"] for p in project.findall(".//p:ClCompile[@Include]",ns)]==["JudgementCutEnd.cpp"])
    links=project.find(".//p:AdditionalDependencies",ns).text
    check("all import libraries configured",all(x in links for x in ("KenshiLib.lib","OgreMain_x64.lib","MyGUIEngine_x64.lib","winmm.lib")))
    dep=ROOT.parent.parent/"1.Dependencies/KenshiLib_0.5.0"
    check("existing dependencies",all((dep/"Libraries"/f).exists() for f in ("KenshiLib.lib","OgreMain_x64.lib","MyGUIEngine_x64.lib")))
    # Boost 的自动链接指令来自头文件，即使 AdditionalDependencies 不显式列出也必须可找到。
    library_path=project.find(".//p:LibraryPath",ns).text
    check("Boost autolink search path", "$(BoostDir)\\stage\\lib" in library_path)
    boost=ROOT.parent.parent/"1.Dependencies/boost_1_60_0/stage/lib"
    check("all four Boost autolink libraries present",all((boost/("libboost_"+name+"-vc100-mt-1_60.lib")).is_file() for name in ("thread","system","date_time","chrono")))
    check("manifest single entry",json.loads((PKG/"RE_Kenshi.json").read_text('utf8'))=={"Plugins":["JudgementCutEnd.dll"]})
    ET.parse(PKG/"_JudgementCutEnd.info")
    mod=(PKG/"JudgementCutEnd.mod").read_bytes();v,n,r=struct.unpack_from('<III',mod);check("zero-record mod header",v==17 and r==1 and n==len(mod)-16)
    pos=12
    for _ in range(2):n=struct.unpack_from('<I',mod,pos)[0];pos+=4;mod[pos:pos+n].decode('utf8');pos+=n
    check("no game data record",mod[pos:]==b'\0'*26)
    data=json.loads((ROOT/"preview/scene.json").read_text('utf8'));lines=(PKG/"assets/jce.clip").read_text('utf8').splitlines();i=1;tracks={}
    while i<len(lines):
        assert lines[i].startswith('BONE ');name=lines[i][5:];i+=1;keys=[]
        while lines[i]!='END':
            k=lines[i].split();assert k[0]=='KEY';keys.append([float(v) for v in k[1:]]);i+=1
        i+=1;tracks[name]=keys
    check("track count matches contract",len(tracks)==int(lines[0].split()[3])==23)
    check("track names distinct",len(tracks)==lines.count('END'))
    for name,keys in tracks.items():
        check("frames finite, ordered, normalized: "+name,len(keys)==403 and keys[0][0]==0 and keys[-1][0]==6.7 and all(a[0]<b[0] for a,b in zip(keys,keys[1:])) and all(all(math.isfinite(x) for x in row) and abs(sum(x*x for x in row[1:5])-1)<1e-6 for row in keys))
        index=next(b['id'] for b in data['bones'] if b['name']==name)
        check("preview/runtime identical: "+name,all(max(abs(x-y) for x,y in zip(row[1:5],frame['delta'][index]))<1e-7 for row,frame in zip(keys,data['frames'])))
    # 除四元数规范外，还检查关键帧角速度，直接阻止再次交付“规范但突然跳 44°”的资源。
    max_step=0
    for keys in tracks.values():
        for previous,current in zip(keys,keys[1:]):
            dot=min(1,abs(sum(x*y for x,y in zip(previous[1:5],current[1:5]))))
            max_step=max(max_step,math.degrees(2*math.acos(dot)))
    check("all bone steps under 12 degrees at 60 Hz",max_step<12.001)
    check("full humanoid parent chain controlled",all(name in tracks for name in ("Bip01","Bip01 Pelvis","Bip01 L Thigh","Bip01 R Thigh","Bip01 L Clavicle","Bip01 R Clavicle","Bip01 Neck")))
    # HTML 与运行时资源同源；检测重制资源后遗漏更新预览的情况。
    embedded=next(row for row in (ROOT/"preview/index.html").read_text("utf8").splitlines() if row.startswith("const DATA="))
    check("embedded HTML equals scene data",json.loads(embedded[len("const DATA="):].rstrip(";"))==data)
    # 骨架与动画数学：每帧骨长必须不变、足部不能漂移；不能把预览正常当作实机通过。
    spec=importlib.util.spec_from_file_location('author_assets',ROOT/'tools/author_assets.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    bones=data['bones'];rest=module.world(bones,[b['orientation'] for b in bones]);max_length_error=0;foot_drift=0;hand_motion=0;floor_error=0
    foot_ids=[b["id"] for b in bones if b["name"] in ("Bip01 L Foot","Bip01 R Foot","Bip01 L Toe0","Bip01 R Toe0","Bip01 L Toe0Nub","Bip01 R Toe0Nub")]
    floor=min(rest[k][0][1] for k in foot_ids)
    for frame in data['frames']:
        local=[module.qmul(b['orientation'],q) for b,q in zip(bones,frame['delta'])];wp=module.world(bones,local)
        dy=frame['translation'][0][1]
        wp=[([p[0],p[1]+dy,p[2]],q) for p,q in wp]
        floor_error=max(floor_error,abs(min(wp[k][0][1] for k in foot_ids)-floor))
        for b,(p,q) in zip(bones,wp):
            assert all(math.isfinite(x) for x in (*p,*q))
            if b['parent']>=0:
                length=math.dist(p,wp[b['parent']][0]);ref=math.sqrt(sum(x*x for x in b['position']));max_length_error=max(max_length_error,abs(length-ref))
            if 'Foot' in b['name']:foot_drift=max(foot_drift,math.dist(p,rest[b['id']][0]))
        hand_motion=max(hand_motion,math.dist(wp[28][0],rest[28][0]))
    check("bone lengths preserved",max_length_error<1e-5);check("lowest foot stays on floor with no horizontal root travel",floor_error<1e-5 and all(f["translation"][0][0]==f["translation"][0][2]==0 for f in data["frames"]));check("nontrivial draw/sheath movement",hand_motion>4)
    layout=(PKG/'assets/slashes.csv').read_text('utf8').splitlines();rows=[[float(v) for v in s.split()] for s in layout[1:]]
    check("96 independent stable slashes",len(rows)==96 and all(len(s)==9 and all(math.isfinite(x) for x in s) and abs(sum(x*x for x in s[3:6])-1)<1e-5 and 2.35<=s[7]<=4.55 and 0<s[8]<=3 for s in rows))
    tga=(PKG/'assets/jce_glow.tga').read_bytes();w,h=struct.unpack_from('<HH',tga,12);check("TGA dimensions and size",w==256 and h==32 and len(tga)==18+w*h*4)
    with wave.open(str(PKG/'assets/jce_sequence.wav'),'rb') as wav:check("WAV full timeline",wav.getnchannels()==1 and wav.getsampwidth()==2 and abs(wav.getnframes()/wav.getframerate()-6.7)<1e-5)
    shaders=(module.GAME/'data/materials/forward/basic.program').read_text('utf8');compositor=(module.GAME/'data/materials/compositors/main.compositor').read_text('utf8');material=(PKG/'assets/jce.material').read_text('utf8')
    check("game shader contract",all(x in shaders and x in material for x in ('Basic_Coloured_Texture_VP','Basic_Texture_FP')))
    check("HDR queue exists",'rq_first 82' in compositor and re.search(r'rq_last\s+85',compositor))
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig')
    # 防止头文件路径拼错被行为/PE检查遗漏；只检查本项目直接引用的本地依赖头，
    # 标准库与Windows SDK由用户的v100环境解析，此处不伪装为完整预处理或编译。
    local_headers=re.findall(r'(?m)^#include <((?:kenshi|core|ogre|mygui)/[^>]+)>',cpp)
    check("all direct local dependency headers exist",
          bool(local_headers) and all((dep/"Include"/name).is_file() for name in local_headers) and
          "kenshi/combat/CombatClass.h" in local_headers)
    # RE_Kenshi 的入口消费方要求 C++ 修饰名；源检查防止重新引入 C 导出，成品由安装器查 PE 表。
    check("RE_Kenshi C++ entry contract",re.search(r'(?m)^__declspec\(dllexport\) void startPlugin\(\)',cpp) is not None and 'extern "C" __declspec(dllexport) void startPlugin' not in cpp)
    ini=dict(line.split('=',1) for line in (PKG/"JudgementCutEnd.ini").read_text("utf8").splitlines() if '=' in line and not line.startswith(('#',';')))
    check("single U default and configurable VK input",ini.get('CastKeyVK')=='85' and "castKey('U')" in cpp and 'GetAsyncKeyState(int(settings.castKey))' in cpp and all(x not in cpp for x in ('GetAsyncKeyState(VK_CONTROL)','GetAsyncKeyState(VK_SHIFT)')))
    check("bounded input and first callback diagnostics",all(x in cpp for x in ('if(edge){','cast_key_detected vk=','cast_blocked: ','if(!previousThread)','frame_hook_seen thread=','logLines++>=4096')))
    installer=(ROOT/"tools/Stage-LocalMod.ps1").read_text("utf-8-sig")
    check("installation validates export before copying",installer.index("$exports = @(Get-PeExportNames") < installer.index("Copy-BackedFile $compiledDll") and "$exports -cnotcontains '?startPlugin@@YAXXZ'" in installer)
    # 上升沿模型覆盖持键不重复、松开可重试、失去前台不触发；宿主按键仍须实机验证。
    def edges(states):
        previous=False;count=0
        for foreground,vk in states:
            current=foreground and vk
            count+=current and not previous;previous=current
        return count
    check("hotkey hold/release/focus state boundaries",edges([(True,True)]*120)==1 and edges([(False,True)]*120)==0 and edges([(True,False)]*120)==0 and edges([(True,True),(True,False),(True,True)])==2)
    check("single key retains text and input gates",all(x in cpp for x in ('Editing()?"text_editing"','key->gameMode!=InputHandler::GLOBAL','w->isPaused()?"paused"')))
    # 前置声明不能构造 Damages 或读取 GameData 字段，必须包含实际类型定义。
    check("native damage types fully included",all("#include <kenshi/"+name+">" in cpp and (dep/"Include/kenshi"/name).is_file() for name in ("Damages.h","GameData.h")))
    check("no skeleton resource mutation",all(x not in cpp for x in ('createAnimation(','removeAnimation(','addLinkedSkeletonAnimationSource(')))
    # 两个_NV目标来自完整类型的成员函数地址；label只能用于日志，绝不参与Windows目标导出查询。
    check("native binding and one hook per entry",cpp.count('KenshiLib::AddHook(')==2 and 'NativeAddress(&GameWorld::_NV_mainLoop_GPUSensitiveStuff,"frame")' in cpp and 'NativeAddress(&AnimationClassHuman::_NV_update,"pose")' in cpp and '#include <kenshi/Animation/AnimationClassHuman.h>' in cpp)
    # SDK读首字，不要求成员指针总长等于void*；桩校验仍在SDK调用前，不能回退到修饰名查询。
    check("member stub address guarded before SDK resolution",all(x in cpp for x in ('sizeof(method)<sizeof(stub)','std::memcpy(&stub,&method,sizeof(stub))','GetProcAddress(library,"FUNC_BEGIN")','GetProcAddress(library,"FUNC_END")','address<begin||address>=end','KenshiLib::GetRealAddress(method)')) and cpp.index('address<begin||address>=end')<cpp.index('KenshiLib::GetRealAddress(method)') and 'GetProcAddress(library,exportedName)' not in cpp and 'NativeAddress("?' not in cpp)
    check("one medical call site in single deferred damage batch",cpp.count('medical.addWound(')==1 and cpp.index('damageDone=true')<cpp.index('medical.addWound('))
    check("targets revalidate by handle",'targets[i].getCharacter()' in cpp and 'ProtectedPlayer(v)||!c->isEnemy(v,true)' in cpp)
    check("scope serializes only caster",'InterlockedCompareExchangePointer(&poseOwner,0,0)!=a' in cpp)
    # 手动提交绕过的仅是本效果 CPU 剔除；自动路径关闭，GPU 深度、主相机/阴影过滤及注销必须同时存在。
    check("manual render submission and camera/shadow isolation",all(x in cpp for x in ("postFindVisibleObjects","Ogre::SceneManager::IRS_NONE","current!=Render()->getCamera()","geometry->setVisible(false)","geometry->_updateRenderQueue(","notifyRenderSingleObject","scene->removeRenderObjectListener(this)","scene->removeListener(this)")))
    check("material supported and scene coordinates explicit",all(x in cpp for x in ("mat->load()","mat->getBestTechnique()","animation->node->_getDerivedPositionUpdated()","root->convertWorldToLocalPosition(casterScene)")) and "anchor-origin" not in cpp)
    # 同一相机多次回调也只能在粒子队列到达后每帧提交一次。
    check("render phase filter and per-frame deduplication",all(x in cpp for x in ("current->isRenderedRq(83)","lastQueuedFrame==frame","lastQueuedFrame=frame","getNextFrameNumber()")))
    audio=json.loads((ROOT/"docs/audio-provenance.json").read_text("utf8"))
    check("reference audio source hashes verified",len(audio["sources"])==5 and all(hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()==item["sha256"] for item in audio["sources"]))
    check("world/pose restoration",all(x in cpp for x in ('setFrameSpeedMultiplier(previousSpeed)','setManuallyControlled(false)','destroyManualObject(geometry)','destroySceneNode(node)','pose_restore_skin_error')))
    # 用户已明确移除镜头控制，旧 ini=1 也不能再次开启；相机仅用于渲染和朝向光带。
    check("free camera including legacy config",ini.get('CinematicCamera')=='0' and 'config_ignored CinematicCamera; free camera only' in cpp and all(x not in cpp for x in ('cameraOwned','camera->setPosition','camera->setOrientation','camera->lookAt')))
    # 数据流检查包含主身体身份、衣物独立蒙皮消费者、临时开关异常恢复和四次诊断上限。
    check("instance skin publication and ownership",all(x in cpp for x in ('skin.skeleton(animation->body)==skeleton','Visible body/skeleton mismatch','skin.sharing(body)','skeleton->_notifyManualBonesDirty();','entities[i]->_updateAnimation();','~StateUpdateGuard(){skin.setSkip(entity,previous);}','poseDiagnostics<4','pose_skin_published','matrix_error=')))
    # 0.2.1 头文件/运行库布局不一致；新增 cache 后八个接口均使用真实 DLL 导出且在钩子前绑定。
    bindings=re.findall(r'OgreExport<\w+>\("([^"]+)"\)',cpp)
    check("eight native skin interfaces bound before hooks",len(bindings)==8 and cpp.index('skin.Load();')<cpp.index('KenshiLib::AddHook(') and 'GetProcAddress(library,name)' in cpp)
    check("no incompatible Entity inline accesses",all(x not in cpp for x in ('->getSkeleton()','->isInitialised()','->getSkeletonInstanceSharingSet()','->getSkipAnimationStateUpdate()','->setSkipAnimationStateUpdate(','->_getBoneMatrices()','->_getNumBoneMatrices()')))
    pose_cpp=cpp.split('    void Pose(AnimationClass* a,bool observed=false){',1)[1].split('    void Collect()',1)[0]
    check("transform then skin publication ordering",pose_cpp.index('skeleton->_updateTransforms();')<pose_cpp.index('RefreshSkin();') and 'const Ogre::Matrix4* actual=skin.matrices(body);' in pose_cpp)
    # 读取本机 PE 导出及关键分支字节，防止把 vanilla OGRE 的调用顺序当成本机实现。
    # 此检查仅适用当前运行库；不执行或改写 DLL，也不调用编译器。
    native=(module.GAME/'OgreMain_x64.dll').read_bytes()
    pe=struct.unpack_from('<I',native,60)[0];opt=pe+24
    sections=struct.unpack_from('<H',native,pe+6)[0];table=opt+struct.unpack_from('<H',native,pe+20)[0]
    def offset(rva):
        for i in range(sections):
            s=table+40*i;va,size,raw=struct.unpack_from('<III',native,s+12)
            if va<=rva<va+size:return raw+rva-va
        raise AssertionError('unmapped native RVA')
    export=offset(struct.unpack_from('<I',native,opt+112)[0])
    count=struct.unpack_from('<I',native,export+24)[0]
    funcs,names,ordinals=(offset(x) for x in struct.unpack_from('<III',native,export+28))
    exports={}
    for i in range(count):
        at=offset(struct.unpack_from('<I',native,names+4*i)[0])
        name=native[at:native.index(b'\0',at)].decode('ascii')
        ordinal=struct.unpack_from('<H',native,ordinals+2*i)[0]
        exports[name]=struct.unpack_from('<I',native,funcs+4*ordinal)[0]
    check("all eight native OGRE exports present",all(name in exports for name in bindings))
    cache_rva=exports['?cacheBoneMatrices@Entity@Ogre@@IEAA_NXZ']
    update_rva=exports['?updateAnimation@Entity@Ogre@@IEAAXXZ']
    cache_code=native[offset(cache_rva):offset(cache_rva)+175]
    update_code=native[offset(update_rva):offset(update_rva)+128]
    check("local native skip bypasses updateAnimation cache call",bytes.fromhex('80 BB D8 02 00 00 00 75 08 48 8B CB E8') in update_code)
    check("explicit native cache skips replay but writes matrices",bytes.fromhex('80 BB D8 02 00 00 00 75 2D') in cache_code and bytes.fromhex('FF 90 F8 01 00 00') in cache_code)
    refresh=cpp.split('    unsigned RefreshSkin(){',1)[1].split('    void Pose(',1)[0]
    check("explicit cache precedes world matrices with guarded skip",refresh.index('StateUpdateGuard guard(')<refresh.index('skin.cache(entities[i])')<refresh.index('skeleton->_notifyManualBonesDirty();entities[i]->_updateAnimation();'))
    # 模型同时覆盖旧 skip 导致的冻结、同帧缓存、身体/衣物以及异常开关恢复；不称为游戏验收。
    def publish(frame,cache_frame,skip,explicit):
        cached='old_pose';world='old_pose';replayed=False;dirty=True
        if explicit:
            if frame!=cache_frame or dirty:
                replayed=not skip and frame!=cache_frame
                cached='native_old_pose' if replayed else 'new_pose'
                cache_frame=frame;dirty=False
            dirty=True
        if dirty:
            if not skip:cached='native_old_pose' if frame!=cache_frame else 'new_pose'
            world=cached
        return cached,world,replayed
    check("old skip freezes while explicit cache publishes across frames",all(publish(frame,cached,True,False)[1]=='old_pose' and publish(frame,cached,True,True)==('new_pose','new_pose',False) for frame,cached in ((30,30),(31,30))))
    check("body and sharing consumers each receive pose without replay",all(publish(31,30,True,True)[1]=='new_pose' for _ in range(8)))
    check("bone local positions owned and restored",all(x in cpp for x in ('b.previousPosition=b.bone->getPosition();','bones[i].bone->setPosition(bones[i].previousPosition);','position_drift_corrected=')) and cpp.count('bones[i].bone->setPosition(bones[i].previousPosition);')==1 and 'bones[i].previousPosition+SampleTranslation(clip[i],time)*(weight*poseHeightScale)' in cpp)
    # 403 帧下每次模拟外部累加，再重申快照，所有骨长与根位置保持；退出恢复同一快照。
    initial=[tuple(b['position']) for b in bones];current=list(initial);max_drift=0
    for frame in data['frames']:
        current=[(p[0],p[1],p[2]+.4) for p in current]
        max_drift=max(max_drift,max(math.dist(a,b) for a,b in zip(current,initial)))
        current=list(initial)
        check_pose=module.world([dict(b,position=list(pos)) for b,pos in zip(bones,current)],[module.qmul(b['orientation'],q) for b,q in zip(bones,frame['delta'])])
        assert all(math.isfinite(x) for pose in check_pose for x in pose[0])
    check("local translation accumulation reset for entire cast",current==initial and .39<max_drift<.41)
    check("radius directly 350 with compatible larger clamp",ini['Radius']=='350' and 'Settings():radius(350)' in cpp and 'radius=Clamp(v,5,1000)' in cpp)
    # 持续刀痕合同只约束Draw的主刀光循环；短寿命光屑可独立按life停止，不能全文件禁止。
    draw=cpp.split('    void Draw(){',1)[1].split('    void Tick(',1)[0]
    check("fitted slash and ring widths with persistent cracks",all(x in draw for x in ('float widthScale=layoutScale/30.f;','.18f*widthScale','.035f*widthScale','.1f*widthScale','if(age<0||time>=END)continue;')) and 'age>life' not in draw)
    # HDR 增益是浮点着色器 uniform；顶点颜色保持归一化，不能用字节溢出伪造亮度。
    hlsl=(module.GAME/'data/materials/forward/basic.hlsl').read_text('utf8')
    glsl=(module.GAME/'data/materials/forward/basic.frag').read_text('utf8')
    check("fourfold HDR gain supported by both game shader variants",'param_named colour float4 4 4 4 1' in material and 'colour * input.colour' in hlsl and 'colour * vColour' in glsl and 'geometry->colour(Clamp(r,0,1),Clamp(g,0,1),Clamp(b,0,1),1)' in cpp)
    # 保持几何预算，不因五倍半径放大循环数；场景填充率仍可能上升，需实机测性能。
    check("expanded VFX retains bounded geometry",96*56+128*4+64*110+12+576*4+168*4+192*3<32768 and 'geometry->estimateVertexCount(VFX_VERTEX_LIMIT)' in cpp and 'VFX_VERTEX_LIMIT=32768' in cpp)
    # 0.3.0：Radius直接是水平圆半径；按朝向拟合裂痕，不能再用资产系数放大伤害。
    norm=lambda p:math.sqrt(sum(x*x for x in p))
    horizontal=lambda p:math.hypot(p[0],p[2])
    endpoints=[[s[i]+sign*s[3+i]*s[6] for i in range(3)] for s in rows for sign in (-1,1)]
    check("circle radius fixed independent of VFX extent",
          "float AreaRadius() const {return settings.radius;}" in cpp and "effectRadiusScale" not in cpp)
    check("rotated endpoints and half width determine per cast VFX scale",
          all(x in cpp for x in ("FitSlashLayout();","facing*(s.centre-s.direction*s.length)",
          "facing*(s.centre+s.direction*s.length)","sqrtf(a.x*a.x+a.z*a.z)",
          "layoutScale=AreaRadius()/envelope;","s.centre*layoutScale","s.direction*s.length*layoutScale")))
    check("candidate margin and exact XZ circle used for damage",
          "getObjectsWithinSphere(list,anchor,AreaRadius()+.01f" in cpp and
          "distanceSquared=delta.x*delta.x+delta.z*delta.z" in cpp and
          "distanceSquared<=radius*radius" in cpp)
    # 旋转（含倾斜）/半宽/极限半径联合验证；旋转后端点先拟合，光带相机朝向不改变半宽上界。
    for axis,angle in (((0,1,0),0),((0,1,0),90),((1,0,0),35),((0,0,1),-40)):
        q=module.axis(axis,angle);rotated=[module.rotate(q,p) for p in endpoints]
        envelope=max(1,max(horizontal(p)+.18/30 for p in rotated))
        for radius in (5,150,350,1000):
            scale=radius/envelope
            check("all 96 projected slashes fit radius/rotation "+str((radius,axis,angle)),
                  len(rotated)==192 and all(horizontal(p)*scale+.18*scale/30<=radius+1e-7 for p in rotated))
            width=.1*scale/30;inner=max(0,radius-2*width)
            ring_vertices=[(math.cos(i*math.pi/64)*r,.8,math.sin(i*math.pi/64)*r)
                           for i in range(128) for r in (inner,radius)]
            check("ground annulus outer exactly circle "+str((radius,axis,angle)),
                  all(horizontal(p)<=radius+1e-7 for p in ring_vertices) and
                  all(abs(horizontal(p)-radius)<1e-7 for p in ring_vertices[1::2]))
    check("circle boundary included while outside rejected regardless of height",
          horizontal((350,500,0))<=350 and horizontal((350.01,0,0))>350 and
          horizontal((0,10000,0))<=350 and not math.isfinite(horizontal((float("nan"),0,0))))
    check("only fixed horizontal boundary circle no expanding alternate ring",
          "GroundRing(areaRadius,ringWidth,boundaryLight);" in cpp and
          "for(unsigned i=0;i<128;++i)" in cpp and "radius-2*width" in cpp and
          "ringRadius" not in cpp and "outerRing" not in cpp and "area_shape=horizontal_circle" in cpp)
    check("visible and logical centres share fixed anchor across origin shifts",
          "animation->node->_getDerivedPositionUpdated()+(anchor-casterObject->getPosition())" in cpp)
    anchor=(100,50,-70);current=(101,50,-69)
    for origin in ((0,0,0),(10000,-300,7000),(-100000,500,400)):
        scene_current=tuple(a-b for a,b in zip(current,origin))
        scene_anchor=tuple(a+b-c for a,b,c in zip(scene_current,anchor,current))
        check("floating origin cancellation "+str(origin),
              scene_anchor==tuple(a-b for a,b in zip(anchor,origin)))
    damage_area=cpp.split("    void Damage(){",1)[1].split("    unsigned vertex",1)[0]
    check("current enemies collected once at damage not early cut",
          cpp.count("Collect();")==1 and "Collect();" in damage_area and
          damage_area.index("damageDone=true")<damage_area.index("Collect();")<damage_area.index("medical.addWound("))
    check("all in area enemies independent of legacy MaxTargets",
          'else if(k=="MaxTargets"&&v!=0)' in cpp and "settings.maxTargets" not in cpp and
          "for(unsigned i=0;i<list.size();++i)" in cpp)
    check("fixed boundary ring remains in geometry budget",
          "GroundRing(areaRadius,ringWidth,boundaryLight);" in cpp and 96*8+128*4+9*14*4+12<8192)
    check("all target damage with bounded diagnostic detail",
          "if(hitDiagnostics++<16)" in damage_area and
          "++applied;" in damage_area and "logLines++>=4096" in cpp)
    # 以目标当前身份/敌对/位置筛选：超过32人仍全覆盖；友军、玩家、离圈、无效对象不命中。
    population=[(i,True,False,(float(i),0,0),True) for i in range(100)]
    population += [(200,False,False,(0,0,0),True),(201,True,True,(0,0,0),True),
                   (202,True,False,(351,0,0),True),(203,True,False,(0,0,0),False)]
    def area_ids(population):
        return list(dict.fromkeys(i for i,enemy,player,pos,valid in population
                    if valid and enemy and not player and horizontal(pos)<=350))
    check("100 enemies covered while neutral player outside invalid rejected",area_ids(population)==list(range(100)))
    initial=[(1,True,False,(0,0,0),True),(2,True,False,(351,0,0),True)]
    final=[(1,True,False,(351,0,0),True),(2,True,False,(0,0,0),True)]
    check("entrant hit and leaver skipped at commit",area_ids(initial)==[1] and area_ids(final)==[2])
    # 三倍时钟跨层合同：剪辑仍 6.7 秒，真实时间/音效/卡顿保持各自单位，冷却已取消。
    check("threefold runtime clock preserves real stall deadline",all(x in cpp for x in (
        "const float PLAYBACK_RATE=3.f;","time=float(elapsed*PLAYBACK_RATE);",
        "elapsed-double(time)/PLAYBACK_RATE>1.5","!poseSeen&&elapsed>.5")) and "elapsed-time>1.5" not in cpp)
    preview=(ROOT/"preview/index.html").read_text("utf8")
    check("preview clock threefold, clip contract preserved","t+(now-last)/1000*3" in preview and "(t/3).toFixed(2)" in preview and data["duration"]==6.7)
    check("preview shares radius and fitted slash projection",
          all(x in preview for x in ("const AREA_RADIUS=350;","const LAYOUT_SCALE=AREA_RADIUS/SLASH_ENVELOPE;",
          "x=>x*LAYOUT_SCALE","groundRing(AREA_RADIUS", "radius-2*width")))
    fast_spec=importlib.util.spec_from_file_location('author_fast_audio',ROOT/'tools/author_fast_audio.py')
    fast_module=importlib.util.module_from_spec(fast_spec)
    # author_fast_audio 复用 author_assets 的备份写入器；这里仅调用纯 render，不运行 main/put。
    sys.modules["author_assets"]=module;fast_spec.loader.exec_module(fast_module)
    rendered,fast_evidence=fast_module.render()
    fast=PKG/"assets/jce_sequence_fast.wav"
    check("fast soundtrack reproducible without changing source sounds",fast.read_bytes()==rendered and
        json.loads((ROOT/"docs/fast-audio-provenance.json").read_text("utf8"))==fast_evidence)
    with wave.open(str(fast),"rb") as wav:
        check("fast PCM keeps pitch rate and exact threefold duration",
              (wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes())==(1,2,44100,98490))
    check("sound cues align to clip divided by three within one sample",all(
        abs(cue["real_at"]-cue["clip_at"]/3)<=1/44100 and cue["peak_before_mix"]>.001
        for cue in fast_evidence["sources"]) and fast_evidence["peak"]<=.900001)
    check("runtime plays synchronized fast soundtrack","assets\\\\jce_sequence_fast.wav" in cpp and "assets\\\\jce_sequence.wav" not in cpp)
    check("per slash 100 percent overrides legacy 44 multiplier",ini.get("DamageMultiplier")=="1" and
        "damageMultiplier(1)" in cpp and 'else if(k=="DamageMultiplier"&&v!=1)' in cpp and
        "per_slash_100_percent" in cpp and "damageMultiplier=Clamp" not in cpp and "CutDamage" not in ini and "BluntDamage" not in ini and
        "config_ignored legacy fixed damage" in cpp and "Damages d(settings.cutDamage" not in cpp)
    check("complete native weapon stats headers",all("#include <kenshi/"+h+">" in cpp for h in ("CharStats.h","Gear.h")))
    damage_cpp=cpp.split("    void Damage(){",1)[1].split("    unsigned vertex",1)[0]
    check("per target formula before fresh single slash native medical calls",
          damage_cpp.count("SnapshotDamageFor(v)")==1 and "d.multiply(" not in damage_cpp and
          damage_cpp.index("for(size_t i=0")<damage_cpp.index("SnapshotDamageFor(v)")<
          damage_cpp.index("for(unsigned strike=0;strike<strikeCount;++strike)")<
          damage_cpp.index("Damages d(base);")<damage_cpp.index("medical.addWound("))
    check("hit count derives from current 96 VFX rows",
          len(rows)==96 and "const unsigned strikeCount=unsigned(slashes.size())" in damage_cpp and
          all(s[7]<5.15 for s in rows))
    check("reaction requested once after inner hit loop with aggregated body counts",
          damage_cpp.count("Stagger(targets[i]")==1 and
          damage_cpp.index("medical.addWound(")<damage_cpp.index("Stagger(targets[i]") and
          "++bodyHits[part->stringID]" in damage_cpp and "landed_hits=" in damage_cpp and "bodyparts=" in damage_cpp)
    check("each strike resolves caster target and world before medical call",
          all(x in damage_cpp for x in ("Character* currentCaster=Resolve();v=targets[i].getCharacter();",
          "CasterBlockedReason(currentCaster)","Finish(reason);return;","target_dead_invalid_or_left_area")))
    stagger_cpp=cpp.split("    const char* Stagger(",1)[1].split("    void Damage(){",1)[0]
    check("large native reaction with honest race fallback",
          all(x in stagger_cpp for x in ("chooseStumbleAnim(part,origin,true)","chooseStumbleAnim(part,origin,false)",
          "race_has_no_stumble_animation","large_stumble_requested","small_stumble_fallback",
          "a->startStumble(reaction);combat->_getHit(CUT_DEFAULT,response,c,true)")))
    check("no extra medical damage HP writes or timer writes for stagger",
          "medical.addWound(" not in stagger_cpp and "extraStun=" not in stagger_cpp and
          "stumbleTimer=" not in cpp and "whenCanStopStumble=" not in cpp and
          "stumbleForce=" not in cpp and "Damages response(0,force,0,1,0)" in stagger_cpp)
    check("stagger guards KO death prone and bounds force",
          all(x in stagger_cpp for x in ("v->isDead()","v->_NV_isUnconcious()",
          "v->_NV_getProneState()!=PS_NORMAL","1000000.0","landedForce*settings.staggerForceMultiplier")) and
          ini["StaggerForceMultiplier"]=="8" and "staggerForceMultiplier=Clamp(v,1,100)" in cpp)
    # 回归检查：U键通过原生装备选择/拔刀建立数值快照；后续换装不能撤销伤害。
    prepare=cpp.split("    void PrepareWeapon(Character* c){",1)[1].split("    void RestoreWeapon",1)[0]
    finish=cpp.split("    void Finish(",1)[1].split("    unsigned RefreshSkin",1)[0]
    begin=cpp.split("    void Begin(",1)[1].split("    void ReleaseGraphics",1)[0]
    check("weapon only required at visual begin","Equip a melee weapon" not in cpp and
          "PrepareWeapon(c);" in begin and begin.index("MakeResources();")<begin.index("PrepareWeapon(c);") and
          "caster_requires_equipped_melee_weapon" in begin and "weapon_damage_snapshot_not_ready" in begin and "throw " not in prepare)
    check("native preferred equipped weapon selected without backpack search",all(x in cpp for x in (
          "human->_NV_getThePreferredWeapon()","weapon->getCategory()!=SKILL_UNARMED",
          "human->_NV_drawWeapon(weapon,weapon->inventorySection)")) and "stats->setWeapon(" not in cpp)
    check("damage requires prepared U key numeric snapshot",all(x in cpp for x in (
          "damageArmed=drawOK&&CaptureDamageSnapshot(c)","SameHand(castWeapon,cached->getHandle())",
          "SameHand(castWeapon,preferred->getHandle())","(!damageArmed||!castDamage.valid)",
          "equipment_change_after_begin=ignored")) and "cast_damage_disarmed:" not in cpp)
    check("only plugin drawn same weapon restored",all(x in cpp for x in (
          "if(!drewWeapon||CasterBlockedReason(c))return;",
          "human->_NV_getCurrentWeapon()==owned","human->_NV_sheatheWeapon()",
          "weapon_restore_skipped: ownership_changed")) and
          "RestoreWeapon(c);" in finish and "damageArmed=false;drewWeapon=false;" in finish)
    # 新快照验证覆盖完整源代码合同；不再保留“换装撤销”的旧模型。
    from verify_damage_snapshot import validate_snapshot_source
    for name,passed in validate_snapshot_source(cpp):check(name,passed)
    # 实际 KenshiLib 桩表 -> 本机 RVA 表 -> 可执行文件，只读确认原生拔刀调用 setWeapon。
    def pe_map(data):
        pe=struct.unpack_from("<I",data,60)[0];o=pe+24
        st=o+struct.unpack_from("<H",data,pe+20)[0];count=struct.unpack_from("<H",data,pe+6)[0]
        def at(rva):
            for i in range(count):
                va,size,raw=struct.unpack_from("<III",data,st+i*40+12)
                if va<=rva<va+size:return raw+rva-va
            raise AssertionError("unmapped game/library RVA")
        exp=at(struct.unpack_from("<I",data,o+112)[0]);names_count=struct.unpack_from("<I",data,exp+24)[0]
        fa,na,oa=[at(v) for v in struct.unpack_from("<III",data,exp+28)];result={}
        for i in range(names_count):
            start=at(struct.unpack_from("<I",data,na+i*4)[0])
            name=data[start:data.index(b"\0",start)].decode("ascii")
            ix=struct.unpack_from("<H",data,oa+i*2)[0];result[name]=struct.unpack_from("<I",data,fa+ix*4)[0]
        return at,result
    lib=(module.GAME/"KenshiLib.dll").read_bytes();lib_at,lib_ex=pe_map(lib)
    rvas=(module.GAME/"RE_Kenshi/RVAs/Steam_1.0.65.br").read_bytes()
    game=(module.GAME/"kenshi_x64.exe").read_bytes();game_at,_=pe_map(game)
    def native_rva(name):
        stub=lib_ex[name];first=lib_ex["FUNC_BEGIN"]
        assert first<=stub<lib_ex["FUNC_END"] and (stub-first)%6==0
        assert lib[lib_at(stub):lib_at(stub)+2]==b"\xff\x25"
        return struct.unpack_from("<I",rvas,(stub-first)//6*4)[0]
    wound=native_rva("?addWound@MedicalSystem@@QEAAPEAVGameData@@_NW4CutDirection@@AEAVDamages@@AEAHPEAVRootObject@@AEAW4Enum@AttackDirection@@PEAVHarpoon@@@Z")
    wound_code=game[game_at(wound):game_at(wound)+0x360]
    check("native default body part selection uses dynamic weighted anatomy",
          wound==0x64fe40 and all(bytes.fromhex(x) in wound_code for x in
          ("F3 0F 10 77 38","F3 0F 59 77 3C","F3 0F 58 CE","83 F8 01")))
    check("native cumulative weighted draw resolves random float thunk",
          game[game_at(0x650163)]==0xe8 and
          0x650163+5+struct.unpack_from("<i",game,game_at(0x650163)+1)[0]==0x4b80d and
          game[game_at(0x4b80d)]==0xe9 and
          0x4b80d+5+struct.unpack_from("<i",game,game_at(0x4b80d)+1)[0]==0x9b0db0)
    check("native spatial query ignores caller count uses full results",
          native_rva("?getObjectsWithinSphere@GameWorld@@QEAAXAEAV?$lektor@PEAVRootObject@@@@AEBVVector3@Ogre@@MW4itemType@@HPEAVRootObject@@@Z")==0x785660 and
          game[game_at(0x78568f):game_at(0x78568f)+8]==bytes.fromhex("C7 44 24 28 FF FF FF 7F"))
    # 原生名字虽称Sphere，两种SpacialCell实际读取X/Z，不读取Y。
    # 检验网格分派和距离机器码；原生严格<，插件用0.01候选余量后自己<=350过滤。
    check("native sphere delegates to horizontal spatial grid",
          native_rva("?getObjects@ZoneSpacialGrid@@QEBAHAEBVVector3@Ogre@@MHAEAV?$lektor@PEAVRootObject@@@@H@Z")==0x9fe340 and
          game[game_at(0x25d7e)]==0xe9 and
          0x25d7e+5+struct.unpack_from("<i",game,game_at(0x25d7e)+1)[0]==0x9fe340)
    for rva in (0x9fa5e3,0x9fb737):
        distance_code=game[game_at(rva):game_at(rva)+40]
        check("native candidate XZ-only distance "+hex(rva),
              all(bytes.fromhex(x) in distance_code for x in
                  ("F3 41 0F 10 0E","F3 41 0F 10 46 08","F3 0F 5C 40 08","F3 0F 5C 08",
                   "F3 0F 59 C0","F3 0F 59 C9","F3 0F 58 C1")))
    draw=native_rva("?_NV_drawWeapon@CharacterHuman@@QEAA_NPEAVItem@@V?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@@Z")
    setter=native_rva("?setWeapon@CharStats@@QEAAXPEAVWeapon@@@Z")
    preferred=native_rva("?_NV_getThePreferredWeapon@CharacterHuman@@QEAAPEAVWeapon@@XZ")
    current=native_rva("?_NV_getCurrentWeapon@CharacterHuman@@QEAAPEAVWeapon@@XZ")
    sheath=native_rva("?_NV_sheatheWeapon@CharacterHuman@@QEAAXXZ")
    has=native_rva("?hasWeapon@CharStats@@QEBA_NXZ")
    dc=game[game_at(draw):game_at(draw)+0x385];destinations=[]
    for i in range(len(dc)-5):
        if dc[i]!=0xe8:continue
        dest=draw+i+5+struct.unpack_from("<i",dc,i+1)[0]
        try:
            off=game_at(dest)
            if game[off]==0xe9:dest=dest+5+struct.unpack_from("<i",game,off+1)[0]
        except AssertionError:continue
        destinations.append(dest)
    check("native human draw really populates combat cache",setter in destinations)
    check("native weapon accessors and sheath exports map",all(v>0 for v in (preferred,current,sheath)) and
          "CharacterHuman.h" in cpp and game[game_at(current):game_at(current)+8]==b"\x48\x8b\x81\xd8\x06\x00\x00\xc3")
    check("hasWeapon is cache hand test not inventory search",
          game[game_at(has):game_at(has)+7]==b"\x83\xb9\x10\x02\x00\x00\x0b")
    # 手柄重载虚函数 ABI 回归：不经 C++ 的重载槽排序，显式调用原生非虚比较。
    check("all owned weapon and target equality uses native nonvirtual hand API",
          "bool SameHand(const hand& a,const hand& b){return a._NV_operator_equal(b);}" in cpp and
          "SameHand(targets[j],h)" in cpp and "std::find(targets" not in cpp and "castWeapon==" not in cpp)
    ctor=native_rva("??0hand@@QEAA@XZ");cc=game[game_at(ctor):game_at(ctor)+7]
    assert cc[:3]==b"\x48\x8d\x05"
    vt=ctor+7+struct.unpack_from("<i",cc,3)[0]
    entries=struct.unpack_from("<QQQ",game,game_at(vt));targets_native=[]
    for absolute in entries:
        rva=absolute-0x140000000;off=game_at(rva)
        assert game[off]==0xe9
        targets_native.append(rva+5+struct.unpack_from("<i",game,off+1)[0])
    eq_hand=native_rva("?_NV_operator_equal@hand@@QEBA_NAEBV1@@Z")
    eq_bool=native_rva("?_NV_operator_equal@hand@@QEBA_N_N@Z")
    check("game hand slot zero is bool and slot one is hand equality",
          targets_native[:2]==[eq_bool,eq_hand] and eq_bool!=eq_hand)
    code=game[game_at(eq_hand):game_at(eq_hand)+60]
    check("native equality compares type container containerSerial index serial",
          all(op in code for op in (b"\x44\x8b\x42\x08",b"\x39\x42\x0c",b"\x39\x41\x10",
                                     b"\x39\x42\x14",b"\x39\x42\x18")))
    def same_fields(a,b):
        if a[0]==b[0]==11:return True
        return all(x==y for x,y in zip(a,b))
    handle=(2,0,0,223874,1155273472)
    check("same handle passes and each stale identity component fails",
          same_fields(handle,handle) and all(not same_fields(handle,tuple(v+1 if j==i else v
          for j,v in enumerate(handle))) for i in range(5)))
    duplicate_inputs=[handle,handle,(2,0,0,223875,1),handle];unique=[]
    for h in duplicate_inputs:
        if not any(same_fields(h,v) for v in unique):unique.append(h)
    check("repeated target identity commits only once",len(unique)==2)
    check("cooldown removed even for legacy nonzero settings",
          ini["Cooldown"]=="0" and 'else if(k=="Cooldown"&&v!=0)' in cpp and
          "cooldown_removed" in cpp and all(x not in cpp for x in
          ("nextAllowed","settings.cooldown","cooldown(15)","cast_blocked: already_active")))
    tick=cpp.split("    void Tick(",1)[1].split("\n};",1)[0]
    restart=tick.index('Finish("restarted_by_key");')
    begin_pos=tick.index('Begin(c,now);')
    check("new key replaces old cast before pending timeline damage",
          tick.index("if(edge){",tick.index("cast_key_detected")) < restart < begin_pos < tick.index("Damage();"))
    check("input remains rising edge across cleanup and restart",
          "bool edge=combo&&!wasKey;wasKey=combo;" in tick and
          "wasKey=" not in finish and "wasKey=" not in begin)
    check("restart uses existing common input safety gates",
          all(x in tick[:restart] for x in ('"loading"','"paused"','"controls_disabled"',
              '"non_global_input_mode"','"text_editing"','"escape_held"')) and
          "if(!active)return;" in tick[:restart])
    check("restart restores owned state before new snapshots",
          all(x in finish for x in ("setManuallyControlled(false)","RestoreWeapon(c)",
              "RestoreTime(reason,validWorld)","PlaySoundW(0,0,0)","ReleaseGraphics(validScene)",
              "bones.clear();targets.clear();ghosts.clear()","caster.setNull();castWeapon.setNull()")) and
          all(x in begin for x in ("beginning=now","cutDone=damageDone=false","targets.clear()",
              "ghosts.clear()","poseSeen=false")))

    # 生命周期模型覆盖旧结算点被新输入抢占、已结算伤害保留，以及长按/资源所有权。
    # 只模拟接口合同；不能替代宿主 C++ 或真实游戏验收。
    def replay(rows):
        active=False;was_key=False;origin=0;cast=0;done=False;hits=[];ends=[];live=0;peak=0
        for now,down,allowed in rows:
            edge=down and not was_key;was_key=down
            if edge and allowed:
                if active:ends.append((cast,"restart"));live-=1
                active=True;origin=now;cast+=1;done=False;live+=1;peak=max(peak,live)
                continue
            if active:
                clip=(now-origin)*3
                if clip>=5.15 and not done:hits.append(cast);done=True
                if clip>=6.7:active=False;live-=1;ends.append((cast,"completed"))
        return cast,hits,ends,live,peak
    rows=[(0,True,True),(.1,False,True),(1.8,True,True),(1.9,False,True),
          (3.6,False,True),(3.7,False,True),(4.1,False,True)]
    r=replay(rows)
    check("restart wins on old damage boundary, only replacement hits",
          r[0]==2 and r[1]==[2] and r[2]==[(1,"restart"),(2,"completed")] and r[3:]==(0,1))
    r=replay([(0,True,True),(.1,False,True),(1.8,False,True),(1.9,True,True),
              (2,False,True),(3.7,False,True),(4.2,False,True)])
    check("committed damage remains once per cast after replacement",r[1]==[1,2] and r[3:]==(0,1))
    r=replay([(0,True,True),(1.8,True,True),(2.3,True,True),(2.4,False,True),(2.41,True,True)])
    check("held key does not replay, release allows immediate no cooldown cast",
          r[0]==2 and r[1]==[1] and r[2]==[(1,"completed")] and r[3:]==(1,1))
    for phase in (.2,.9,1.6):
        r=replay([(0,True,True),(.05,False,True),(phase,True,True),
                  (phase+.05,False,True),(phase+1.8,False,True),(phase+2.3,False,True)])
        check("restart at clip phase "+str(phase),r[1]==[2] and r[3:]==(0,1))
    r=replay([(0,True,True),(.1,False,True),(1,True,False),(1.8,False,True),(2.3,False,True)])
    check("blocked editing input does not replace current cast",r[0]==1 and r[1]==[1] and r[3:]==(0,1))
    rows=[(0,True,True)]
    for i in range(1,101):rows.extend([(i*.1-.01,False,True),(i*.1,True,True)])
    rows.extend([(11.8,False,True),(12.3,False,True)])
    r=replay(rows)
    check("100 replacements retain one owner and no old queued hits",
          r[0]==101 and r[1]==[101] and len(r[2])==101 and r[3:]==(0,1))
    check("finite base and returned reaction channels validated",
          "ValidDamage(base)" in damage_cpp and "if(ValidDamage(d))" in damage_cpp and all(x in cpp for x in
          ("Finite(d.cut)","Finite(d.blunt)","Finite(d.pierce)","Finite(d.extraStun)",
           "Finite(d.bleedMult)","Finite(d.armourPenetration)")))
    check("bounded hit diagnostics expose base anatomy batch and reaction",
          all(x in damage_cpp for x in ("base_cut=","base_blunt=","base_pierce=","base_stun=",
          "bleed_mult=","armour_penetration=","requested_hits=","landed_hits=","stagger=","stagger_force=")))
    # 独立参数副本模型：护甲的引用修改不能串到下一击；死亡停止、不同目标保持独立。
    # 这是入口合同模型，不执行宿主原生选择/HP/反应。
    def batch(base,armour,die_after=None):
        parts=[0]*7;arguments=[];total=0
        for strike in range(96):
            if die_after is not None and strike>=die_after:break
            d=list(base);arguments.append(tuple(d));parts[strike%7]+=1
            d[0]*=armour
            total+=sum(d[:4])
        return parts,arguments,total
    base=(10,4,2,3,1.2,-.1)
    parts,args,total=batch(base,.5)
    check("96 independent fresh parameters retain bleed and penetration",
          len(args)==sum(parts)==96 and all(x==base for x in args) and total==96*14)
    check("one target armour changes do not affect another target",
          batch(base,.2)[2]==96*11 and batch(base,.5)[2]==96*14)
    check("early death ends remaining hits and zero hits no reaction",
          sum(batch(base,.5,3)[0])==3 and sum(batch(base,.5,0)[0])==0 and
          "hits?Stagger(" in damage_cpp)
    # 原生导出+特定版本机器码验证，防止依赖头里的旧RVA被当作本机入口。
    def code_at(rva,size):return game[game_at(rva):game_at(rva)+size]
    check("native large stumble selector export and big flag filter",
          native_rva("?chooseStumbleAnim@AnimationClass@@QEAAPEAVAnimationData@@PEAVGameData@@W4CutOrigination@@_N@Z")==0x51e990 and
          bytes.fromhex("44 38 BF 4C 01 00 00") in code_at(0x51e990,0x160))
    check("native stumble start and combat reaction force exports",
          native_rva("?startStumble@AnimationClass@@QEAAXPEAVAnimationData@@@Z")==0x51fa00 and
          native_rva("?_getHit@CombatClass@@QEAAXW4CutDirection@@AEBVDamages@@PEAVRootObject@@_N@Z")==0x664a00 and
          bytes.fromhex("F3 0F 11 83 2C 01 00 00") in code_at(0x664a00,0xa4))
    check("native target reaction accessors match current game",
          native_rva("?getCombatClass@Character@@QEBAPEAVCombatClass@@XZ")==0x5c8820 and
          native_rva("?_NV_getProneState@Character@@QEBA?AW4ProneState@@XZ")==0x5c7380 and
          native_rva("?_NV_isUnconcious@Character@@QEBA_NXZ")==0x5c9380 and
          native_rva("?getAttackOriginationDirection@Character@@QEAA?AW4CutOrigination@@PEAV1@@Z")==0x435260)
    check("block timer is constant so no promised forced duration",
          native_rva("?calculateStumbleBlockTimer@CharStats@@QEAAMM@Z")==0x8853e0 and
          code_at(0x8853e0,9)[:4]==bytes.fromhex("F3 0F 10 05") and code_at(0x8853e0,9)[8]==0xc3)
    # 小状态模型验证一次性结算、卡顿取消与用户变速所有权规则；该模型不执行宿主 C++。
    def timeline(times):
        events=[];cut=damage=False;previous=0
        for t in times:
            if t-previous>1.5:events.append('cancel');break
            previous=t
            clip_time=t*3
            if clip_time>=2.35 and not cut:cut=True;events.append('cut')
            if clip_time>=5.15 and not damage:damage=True;events.append('damage')
            if clip_time>=6.7:events.append('finish');break
        return events
    check("sheath commits once at multiple FPS",all(timeline([i/fps for i in range(int(7*fps))])==['cut','damage','finish'] for fps in (15,30,60,144)))
    check("long stall cancels before deferred damage",timeline([0,.1,1.7])==['cancel'])
    check("short stall orders crossing events",timeline([i*.4 for i in range(18)])==['cut','damage','finish'])
    check("threefold real cut sheath end boundaries",all(timeline([i/fps for i in range(math.ceil(6.7/3*fps)+1)])==['cut','damage','finish'] for fps in (15,30,60,144)))
    text_ext={'.cpp','.md','.ps1','.py','.html','.json','.info','.vcxproj','.sln','.ini','.material','.clip','.csv'}
    for p in ROOT.rglob('*'):
        if p.is_file() and p.suffix in text_ext:
            b=p.read_bytes();text=b.decode('utf-8-sig');assert not any(x in text for x in ('\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf')),(p,'mojibake')
            assert b'\n' not in b.replace(b'\r\n',b''), (p,'mixed/LF newlines')
    check("UTF-8 Chinese and CRLF verified",True)
    return {'static_passed':True,'checks':checks,'metrics':{'bone_length_error':max_length_error,'foot_drift':foot_drift,'right_hand_motion':hand_motion,'frames':403,'tracks':23,'max_single_frame_rotation_degrees':max_step},'compiled':False,'game_tested':False}
if __name__=='__main__':
    result=main();print(json.dumps(result,ensure_ascii=False,indent=2))
