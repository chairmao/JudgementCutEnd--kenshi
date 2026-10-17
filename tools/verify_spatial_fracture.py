"""空间切裂2.5只读跨层验证：原曲线、受保护代码、资源、队列和数值边界；不编译。"""
from pathlib import Path
import ast, hashlib, importlib.util, json, math, re
import verify_particles as utility
import inspect_spatial_refraction as reference
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets'
def text(p):return p.read_bytes().decode('utf-8-sig').replace('\r\n','\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sample(curve,t):
    # 只核验导出关键帧的物理边界和原曲线比例；不把这个离线采样器当成C++或GPU执行。
    keys=curve['keys']
    if t<keys[0]['time'] or t>keys[-1]['time']:return 0
    for a,b in zip(keys,keys[1:]):
        if t<=b['time']:
            u=(t-a['time'])/(b['time']-a['time'])
            if curve['interpolation']==1:return a['value']+(b['value']-a['value'])*u
            return (2*u**3-3*u*u+1)*a['value']+(-2*u**3+3*u*u)*b['value']+(u**3-2*u*u+u)*a.get('backward',0)+(u**3-u*u)*b.get('forward',0)
    return keys[-1]['value']
def main():
    checks=[]
    def check(name,passed):
        checks.append({'name':name,'passed':bool(passed)})
        if not passed:raise AssertionError(name)
    task=json.loads((ROOT/'docs/spatial-fracture-2.5-task.json').read_text('utf8'))
    baseline=json.loads(Path(task['baseline']).read_text('utf8'))
    backup=Path(baseline['backups'][0])/'E/KenshiProject/2.Projects/JudgementCutEnd'
    old=text(backup/'JudgementCutEnd.cpp');cpp=text(ROOT/'JudgementCutEnd.cpp')
    for b in baseline['backups']:
        check('original CPP backed up '+b,sha(Path(b)/'E/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp')==baseline['files']['JudgementCutEnd.cpp'])
    protected=['void RestoreTime(','void Begin(','void Finish(','void Tick(','void Damage(','void Pose(',
               'void Collect(','bool InArea(','void FitSlashLayout(','void GroundRing(','void SourceSparks(',
               'void MakeResources(','void ReleaseGraphics(','void CaptureBackground(','void PrepareRefraction(',
               'void ReleaseRefraction(','void PrepareWeapon(','void RestoreWeapon(','bool SameDamageWeapon(',
               'void SourceSmokeRibbons(','void SourceSmokeWisps(','void SourceDust(','void Mist(',
               'void Phantoms(','void SlashAfterimages(','float SourceCurve(','intptr_t NativeAddress(']
    for sig in protected:check('unchanged complete function '+sig,utility.body(cpp,sig)==utility.body(old,sig))
    # 去掉唯一授权的新增块并替回渲染函数，逐字核对剩余整个CPP，避免片段测试遗漏旁支。
    normalized=cpp.replace('2.5.0-dev','2.4.0-dev')
    normalized=normalized.replace('#include <ogre/OgreManualObject.h>\n// 独立光学层需要明确绘制优先级；只调用本机DLL已有的公开非内联队列接口。\n#include <ogre/OgreRenderQueue.h>\n#include <ogre/OgreVector4.h>','#include <ogre/OgreManualObject.h>')
    normalized=normalized.replace('// 保留全部11个段索引；按独立优先级排序，背景副本在首个自有段绘制前抓取。','// 四个既有层索引保留；五个原纹理层追加，不改变背景副本的首段抓取时点。')
    normalized=normalized.replace('const unsigned FX_SECTIONS=11;\n// 原NIF的八组切割折射 + 一组大范围折射；强度键保持独立，空间拓扑按实际刀路适配。\nconst unsigned OPTICAL_PLANES=8;','const unsigned FX_SECTIONS=9;')
    normalized=normalized.replace('// 原烟带48条×10段、烟丝96个固定槽不变；折射改为单覆盖面，总上界19096顶点/46788索引。','// 原烟带48条×10段、烟丝96个固定槽；新增2304顶点/3456索引，总上界19668/47358。')
    start=normalized.index('\n\n// 独立强度数据不复用Alpha曲线。');end=normalized.index('\nvoid LoadAssets()',start)
    normalized=normalized[:start]+normalized[end:]
    start=normalized.index('    // 九条原RefractionStrength曲线');end=normalized.index('    // 独立只读人形网格烘焙：',start)
    normalized=normalized[:start]+normalized[end:]
    start=normalized.index('    void OpticalVertex(');end=normalized.index('    void SourceQuad(',start)
    normalized=normalized[:start]+normalized[end:]
    for sig in ['virtual void postFindVisibleObjects(','virtual void notifyRenderSingleObject(','void Draw(','void Glass(']:
        normalized=normalized.replace(utility.body(normalized,sig),utility.body(old,sig))
    check('entire CPP identity outside authorized optical/queue/version changes',normalized==old)
    check('C++03 compatibility no new lambdas/auto/nullptr',not re.search(r'\b(auto|nullptr|constexpr)\b',utility.masked(utility.body(cpp,'void SpatialFracture('))))
    check('C++ and HLSL bracket balance',all(utility.masked(t).count('{')==utility.masked(t).count('}') for t in [cpp,text(A/'jce_refraction.hlsl')]))
    check('shader export entry contract',all(x in text(A/'jce_refraction.program') for x in ['entry_point jce_refraction_vp','target vs_4_0','entry_point jce_refraction_fp','target ps_4_0']))
    shader=text(A/'jce_refraction.hlsl');program=text(A/'jce_refraction.program')
    for i in range(8):
        check('all cut plane/state uniforms declared and default zero '+str(i),
              all('cut'+kind+str(i) in shader and 'param_named cut'+kind+str(i)+' float4 0 0 0 0' in program for kind in ['Plane','State']))
    check('CPP scalar/vector uniform names and float4 ABI',all(x in cpp for x in ['"cutPlane"+Number(i)','"cutState"+Number(i)','"screenState"','Ogre::Vector4']))
    check('public SDK vector and UV overloads exist',all(x in text(ROOT.parent.parent/'1.Dependencies/KenshiLib_0.5.0/Include/ogre/OgreGpuProgramParams.h') for x in ['setNamedConstant(const String& name, const Vector4& vec)']) and 'virtual void textureCoord(Real x, Real y, Real z, Real w);' in text(ROOT.parent.parent/'1.Dependencies/KenshiLib_0.5.0/Include/ogre/OgreManualObject.h'))
    check('local position and pivot VP->FP contract',all(x in shader for x in ['localPosition : TEXCOORD1','pivot : TEXCOORD2','o.localPosition=pos.xyz','mul(worldViewProjMatrix,pos)','sceneCopy : register(t1)','sceneSampler : register(s1)']))
    check('pixel hemisphere and zero lifecycle guards',all(x in shader for x in ['if(strength<=0)','if(boundary<=0)','length(sphere)','smoothstep(0,.01,sphere.y)','captureValid']))
    material=text(A/'jce.material');old_material=text(backup/'package/JudgementCutEnd/assets/jce.material')
    for name in ['Glow','Mist','Glass']:
        def segment(t):
            at=t.index('material JCE/'+name);q=utility.masked(t);a=q.index('{',at);dep=1;j=a+1
            while dep:dep+=(q[j]=='{')-(q[j]=='}');j+=1
            return t[at:j]
        check('preserved material '+name,segment(material)==segment(old_material))
    check('Refraction VP and texture1 copy slot preserved','vertex_program_ref JCE/Refraction_VP {}' in material and material[material.index('material JCE/Refraction'):].count('texture_unit')==2)
    check('all material textures exist',all((A/t).is_file() for file in A.glob('*.material') for t in re.findall(r'^\s*texture (\S+)',text(file),re.M)))
    check('public queue priority SDK and real DLL export','void addRenderable(Renderable* pRend, uint8 groupID, ushort priority);' in text(ROOT.parent.parent/'1.Dependencies/KenshiLib_0.5.0/Include/ogre/OgreRenderQueue.h') and b'?addRenderable@RenderQueue@Ogre@@QEAAXPEAVRenderable@2@EG@Z\0' in Path(r'D:\steam\steamapps\common\Kenshi\OgreMain_x64.dll').read_bytes())
    order=sorted(range(11),key=lambda i:100 if i==3 else (101+i if i<3 else 100+i))
    check('queue optics before fog, blade, phantom and all smoke',order==[3,0,1,2,4,5,6,7,8,9,10])
    notify=utility.body(cpp,'virtual void notifyRenderSingleObject(')
    check('first actual owned render captures once with all11 sections','CaptureBackground();' in notify and 'if(rend==geometry->getSection(0))' not in notify and 'FX_SECTIONS=11' in cpp and 'if(captureFrame==frame)return' in cpp)
    result=reference.inspect()
    check('source evidence byte/data identity',result==json.loads((ROOT/'docs/spatial-refraction-source-2.5.json').read_text('utf8')))
    check('runtime9 curve bytes equal exact original extraction',text(A/'jce_optics.csv')==reference.curve_text(result))
    check('nine independent source shapes/curves',len(result['meshes'])==len(result['curves'])==9 and sum(b['vertices_count'] for b in result['meshes'])==216)
    ratios=[float(x.rstrip('f')) for x in re.search(r'const float bandRatio\[\]=\{([^}]+)',cpp).group(1).split(',')]
    meshes={m['name']:m for m in result['meshes']}
    check('runtime band widths match original mesh ratios',all(abs(ratios[i]-(meshes['slash'+str(i+1)]['local_max'][1]-meshes['slash'+str(i+1)]['local_min'][1])/(meshes['slash'+str(i+1)]['local_max'][2]-meshes['slash'+str(i+1)]['local_min'][2]))<1e-7 for i in range(8)))
    for c in result['curves']:
        values=[sample(c,c['keys'][-1]['time']*i/1000) for i in range(1001)]
        check('finite nonnegative bounded original curve '+c['name'],all(math.isfinite(v) and -.00001<=v<=c['peak']+.00001 for v in values) and abs(values[-1])<1e-6 and sample(c,.9)>.64)
    # 这是算法边界数值检查，不宣称调用实际GPU；用极端分辨率/位移检查限幅与采样域。
    for width,height in [(640,480),(1920,1080),(2560,1440),(4096,4096)]:
        cap=max(10,min(28,min(width,height)/1080*20))
        for x,y in [(0,0),(80,50),(-1000,500),(1e-12,-1e-12)]:
            n=math.hypot(x,y);x,y=(x*cap/n,y*cap/n) if n>cap else (x,y)
            check('finite bounded pixel displacement '+str((width,height,x,y)),math.isfinite(x+y) and math.hypot(x,y)<=28.000001)
    rows=[[float(v) for v in l.split()] for l in text(A/'slashes.csv').splitlines()[1:]]
    check('8 unique actual slash paths and births before sheath',len(set(i*len(rows)//8 for i in range(8)))==8 and all(2.35<=rows[i*len(rows)//8][7]<5.15 for i in range(8)))
    check('world clock and duration untouched','PLAYBACK_RATE=3.f' in cpp and 'SHEATH=5.15f, END=6.7f' in cpp and 'SHEATH+.45f-slash.at' in cpp)
    check('optical draw ends before animation/end cleanup',5.15+.45<6.7 and 'age>=duration' in utility.body(cpp,'float OpticalStrength('))
    draw=utility.body(cpp,'void Draw(');fallback=draw[draw.index('else{\n            // 中途HDR复制失败'):draw.index('total+=EndLayer();',draw.index('else{\n            // 中途HDR复制失败'))]
    check('late refraction failure keeps float4 UV and zero alpha',fallback.count('OpticalVertex(')==3 and fallback.count('radius,0.f)')==3 and 'TriangleFx' not in utility.masked(fallback))
    check('zero fallback does not access disabled uniforms','setNamedConstant' not in fallback and 'getFragmentProgramParameters' not in fallback)
    # 相机俯视/斜视的真实刀路投影产生多个片区；使用资源数值核验，不能当作实际GPU画面。
    def dot(a,b):return sum(x*y for x,y in zip(a,b))
    def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    def unit(a):
        n=math.sqrt(dot(a,a));return tuple(x/n for x in a) if n>1e-9 else (1,0,0)
    envelope=max([1]+[max(math.hypot(s[0]-s[3]*s[6],s[2]-s[5]*s[6]),math.hypot(s[0]+s[3]*s[6],s[2]+s[5]*s[6]))+.18/30 for s in rows])
    for eye in [(0,800,0),(0,550,650),(600,400,-500)]:
        centre=(0,.8+350*.28,0);view=unit(tuple(a-b for a,b in zip(eye,centre)))
        right=unit(cross(view,(0,1,0)));up=unit(cross(right,view))
        planes=[]
        for i in range(8):
            s=rows[i*len(rows)//8];n=unit(cross(s[3:6],view));p=tuple(v*350/envelope for v in s[:3]);planes.append((n,-dot(n,p)/350))
        cells=set();covered=0
        for ix in range(-40,41):
            for iy in range(-40,41):
                p=tuple(centre[k]+right[k]*350*ix/40+up[k]*350*iy/40 for k in range(3))
                if p[1]<.8 or math.dist(p,(0,.8,0))>350:continue
                q=tuple(v/350 for v in p);cells.add(sum((1<<i) for i,(n,w) in enumerate(planes) if dot(n,q)+w>=0));covered+=1
        check('actual slash partitions visible hemisphere '+str(eye),covered>1000 and len(cells)>=10)
    check('strict startup loader remains before hooks',cpp.index('skin.Load();LoadAssets();')<cpp.index('KenshiLib::AddHook(frame') and all(x in cpp for x in ['count!=9','keys>128','Optics curve must dissolve to zero','Unexpected optics fields']))
    check('no new graphics resource per draw',all(x not in utility.body(cpp,'void SpatialFracture(') for x in ['createManual','createEntity','new ','ifstream','setFrameSpeedMultiplier','addWound']))
    previous=json.loads((A/'vfx-2.4.0.json').read_text('utf8'))
    vertices=previous['vertex_upper_bound']-192*3+4;indices=previous['index_upper_bound']-192*3+6
    check('strict vertex/index budgets improve',vertices==19096 and indices==46788 and vertices<32768 and indices<49152)
    allowed={str(Path(rel)) for rel in task['changed_existing']}
    check('all existing non-approved files unchanged',all(sha(ROOT/rel)==h for rel,h in baseline['files'].items() if str(Path(rel)) not in allowed))
    check('installed files, DLLs, formal/special archives and source NIF unchanged',all(sha(Path(p))==h for p,h in baseline['protected'].items()))
    for path in [ROOT/r for r in task['changed_existing']]+[ROOT/'tools/inspect_spatial_refraction.py',Path(__file__)]:
        b=path.read_bytes();s=b.decode('utf-8-sig')
        check('encoding and Chinese readable '+str(path.relative_to(ROOT)),b'\n' not in b.replace(b'\r\n',b'') and not any(x in s for x in ['\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf','\x3f\x3f\x3f']))
    check('CPP BOM preserved',(ROOT/'JudgementCutEnd.cpp').read_bytes().startswith(b'\xef\xbb\xbf'))
    for path in (ROOT/'tools').glob('*.py'):ast.parse(text(path),filename=str(path))
    check('all Python tools AST parse no bytecode/compiler',True)
    return {'passed':True,'check_count':len(checks),'checks':checks,'native_compile_run':False,'shader_compile_run':False,
            'game_tested':False,'installed_new_revision':False,'source_version':'2.5.0-dev','vertex_upper_bound':vertices,
            'index_upper_bound':indices,'limitations':['验证不执行C++/HLSL，像素算术/队列适配需实机验证','Kenshi空间/时钟适配不等于原NIF引擎逐像素执行']}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
