"""2.2蓝色氤氲：只读跨层/几何/生命周期/资源保护核验；不编译、不运行游戏。"""
from pathlib import Path
from PIL import Image
import ast,hashlib,json,math,re
import verify_particles as previous
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p):return p.read_bytes().decode('utf-8-sig').replace('\r\n','\n')
def smooth(a,b,x):
    u=max(0,min(1,(x-a)/(b-a)));return u*u*(3-2*u)
def clamp(x):return max(0,min(1,x))
def norm(v):return math.sqrt(sum(x*x for x in v))
def plus(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(v,s):return tuple(x*s for x in v)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):return mul(v,1/norm(v)) if norm(v)>1e-6 else (1,0,0)
def bound(p,r):
    p=(p[0],max(.8,p[1]),p[2]);v=(p[0],p[1]-.8,p[2]);n=norm(v)
    return plus(mul(v,min(1,r/n)) if n>1e-6 else v,(0,.8,0))
def material_segment(s,name):
    at=s.index('material JCE/'+name);m=previous.masked(s);a=m.index('{',at);depth=1;i=a+1
    while depth:
        depth+=(m[i]=='{')-(m[i]=='}');i+=1
    return s[at:i]
def main():
    checks=[]
    def check(name,result):
        checks.append({'name':name,'passed':bool(result)})
        if not result:raise AssertionError(name)
    task=json.loads((ROOT/'docs/blue-fog-2.2-task.json').read_text('utf8'))
    baseline=json.loads(Path(task['baseline']).read_text('utf8'));stamp=baseline['stamp']
    backup=Path(r'D:\CodexBackups')/stamp/'E/KenshiProject/2.Projects/JudgementCutEnd'
    cpp=text(ROOT/'JudgementCutEnd.cpp');old=text(backup/'JudgementCutEnd.cpp')
    check('cpp exact original backed up to two roots',digest(backup/'JudgementCutEnd.cpp')==baseline['source_sha256'] and
        digest(Path(r'E:\AIWorkSpace\_backups')/stamp/'E/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp')==baseline['source_sha256'])
    # 去掉仅获授权的雾函数区域/数量/有界首日志/版本变更，整份剩余源码必须与旧版逐字相同。
    normalized=cpp.replace('2.2.0-dev','2.1.0-dev')
    start=normalized.index('    void HazeVertex(');end=normalized.index('    void SlashAfterimages(',start)
    oldstart=old.index('    void HazeVertex(');oldend=old.index('    void SlashAfterimages(',oldstart)
    normalized=normalized[:start]+old[oldstart:oldend]+normalized[end:]
    start=normalized.index('    void SmokeSprite(');end=normalized.index('    void SourceFlashes(',start)
    oldstart=old.index('    void SourceDust(');oldend=old.index('    void SourceFlashes(',oldstart)
    normalized=normalized[:start]+old[oldstart:oldend]+normalized[end:]
    intro='// 蓝雾采用96个宽软云层和48条刀路各3段烟流；无半球壳、无永久实体。\n// 顶点/索引硬预算仍沿用32768/49152；其他幻影、刀光与光屑数量不变。\n'
    normalized=normalized.replace(intro,'// 特效对象/顶点硬预算；16幻影路径、80云团、128微粒、48镜面/192碎片，没有永久实体。\n')
    normalized=normalized.replace('MIST_CLOUDS=96','MIST_CLOUDS=168')
    normalized=normalized.replace('particle_revision=2.2_blue_wisps dust_paths=48 dust_slots=144 spark_slots=128 haze_cells=',
        'particle_revision=2.1_streams dust_slots=48 spark_slots=128 haze_cells=')
    normalized=normalized.replace('atmosphere=blue_soft_clouds palette=ap05_gradshock facets=','atmosphere=grey_hemisphere facets=')
    check('complete source identity outside authorized VFX/log/version regions',normalized==old)
    for sig in ['void RestoreTime(','void Begin(','void Finish(','void Tick(','void Damage(','void Pose(',
        'void MakeResources(','void ReleaseGraphics(','void CaptureBackground(','void PrepareRefraction(',
        'void Collect(','bool InArea(','void FitSlashLayout(','void GroundRing(','void SourceSprite(',
        'void SourceSparks(','intptr_t NativeAddress(']:
        check('protected full function '+sig,previous.body(cpp,sig)==previous.body(old,sig))
    for name in ['jce.material','jce_source.material']:
        now=text(A/name);before=text(backup/'package/JudgementCutEnd/assets'/name)
        protected=['Glow','Glass','Refraction'] if name=='jce.material' else ['SourceBlade','SourceFeather','SourceFlash','SourceSpark']
        for seg in protected:check('unmodified material '+seg,material_segment(now,seg)==material_segment(before,seg))
    allowed={str(Path(p)) for p in task['changed_existing']}
    for rel,h in baseline['files'].items():
        if rel not in allowed:check('existing package/source unchanged '+rel,digest(ROOT/rel)==h)
    for group in ['installed','formal','external_dll']:
        check('all '+group+' artifacts unchanged',all(digest(Path(p))==h for p,h in baseline[group].items()))
    pal=baseline['skyrim_palette']
    check('original palette copied byte-for-byte and source still unchanged',digest(A/'jce_source_fog_palette.dds')==pal['sha256']==digest(Path(pal['path'])))
    check('original NIF still unchanged',digest(Path(pal['nif']))==pal['nif_sha256'])
    shader=text(A/'jce_atmosphere.hlsl');program=text(A/'jce_atmosphere.program')
    check('shader brackets balanced after masking',sum(c=='{' for c in previous.masked(shader))==sum(c=='}' for c in previous.masked(shader)))
    check('source C++ braces balanced after masking',sum(c=='{' for c in previous.masked(cpp))==sum(c=='}' for c in previous.masked(cpp)))
    vp=previous.body(shader,'JCE_FOG_FRAGMENT jce_fog_vp(')
    check('local-space VP matrix and texture-clock pass-through contract',all(x in vp for x in ['mul(worldViewProjMatrix,pos)','o.texCoord=texCoord','o.localPosition=pos.xyz']) and
        'param_named_auto worldViewProjMatrix worldviewproj_matrix' in program and 'float4 texCoord : TEXCOORD0' in shader)
    check('SDK provides exact four-component textureCoord virtual overload','virtual void textureCoord(Real x, Real y, Real z, Real w);' in text(ROOT.parent.parent/'1.Dependencies/KenshiLib_0.5.0/Include/ogre/OgreManualObject.h'))
    for entry,target in [('jce_fog_vp','vs_4_0'),('jce_mist_fp','ps_4_0'),('jce_smoke_fp','ps_4_0')]:
        check('program actual entry '+entry,'entry_point '+entry in program and 'target '+target in program and entry+'(' in shader)
    for name,fp,atlas in [('Mist','Mist_FP',False),('SourceDust','Smoke_FP',True)]:
        s=material_segment(text(A/('jce.material' if name=='Mist' else 'jce_source.material')),name)
        check('own shader material '+name,'vertex_program_ref JCE/Fog_VP' in s and 'fragment_program_ref JCE/'+fp in s)
        textures=re.findall(r'^\s*texture (\S+)',s,re.M)
        check('texture register order '+name,textures==['jce_fog_noise.tga','jce_source_fog_palette.dds']+(['jce_source_dust.dds'] if atlas else []))
        check('texture existence '+name,all((A/t).exists() for t in textures))
        check('world depth and normal alpha '+name,all(t in s for t in ['depth_write off','depth_check on','scene_blend alpha_blend','cull_hardware none']))
    check('explicit sampler slots 0/1/2','register(t0)' in shader and 'register(t1)' in shader and 'register(t2)' in shader and
        all('register(s'+str(i)+')' in shader for i in range(3)))
    check('no density cutoff or dustDetail in new smoke',all(x not in shader for x in ['clip(','dustDetail','smoothstep(.025,.32']))
    check('strict zero-alpha early exits',shader.count('if(input.colour.a<=0)return float4(0,0,0,0);')==2)
    check('no game/scene depth read or fullscreen postprocess',all(x not in shader for x in ['SV_Depth','discard','sceneTexture','depthTexture','RWTexture']))
    fog=previous.body(cpp,'void Mist(');dust=previous.body(cpp,'void SourceDust(');smoke=previous.body(cpp,'void SmokeSprite(')
    check('fixed cloud producer matches 96 slots','MIST_CLOUDS=96' in cpp and all(x in fog for x in ['level<6','ring<2','j<8']) and 6*2*8==96)
    check('halfball shell producer removed',all(x not in fog for x in ['sectors','rings=12','true)']))
    check('144 stable sorted stream segment slots','const unsigned count=144' in dust and 'unsigned path=i/3,part=i%3' in dust and 'unsigned id=cells[i].id,path=id/3' in dust)
    check('mist four-component UV clock/radius','geometry->textureCoord(u,v,time,AreaRadius());' in cpp)
    check('smoke four-component UV frame/radius','geometry->textureCoord(us[i],vs[i],frame,AreaRadius());' in smoke)
    check('particle loops no allocation IO medical calls logging or material lookup',
        not any(x in fog+dust+smoke for x in ['new ','resize(','push_back(','Log(','std::ifstream','getByName(','createEntity','addWound']))
    check('v100 loops no C++11 constructs',not re.search(r'\b(nullptr|constexpr|thread_local|auto)\b',previous.masked(fog+dust+smoke)))
    old_v=96*56+128*4+32*(256+4)+12+576*4+168*4+192*6+(96+96+48+2+128)*4
    old_i=96*84+128*6+32*(320*3+6)+18+576*6+168*6+192*6+(96+96+48+2+128)*6
    new_v=old_v-576*4-72*4+96*4;new_i=old_i-576*6-72*6+96*6
    check('conservative geometry budget',old_v==19828 and old_i==47598 and new_v==17620 and new_i==44286 and new_v<32768 and new_i<49152)
    rows=[[float(x) for x in line.split()] for line in text(A/'slashes.csv').splitlines()[1:]]
    check('96 real slash records',len(rows)==96)
    # 使用原曲线和真实资产抽样，包括最后一刻、最小/最大半径、低帧率、俯视相机和与刀路重合的视线。
    visible=set();max_alpha=0;sample_count=0;last_emission_stable=True
    for fps in [15,30,60,144]:
        for frame in range(math.ceil(6.7/3*fps)+1):
            t=min(6.7,3*frame/fps)
            fade=1 if t<5.15 else smooth(0,1,clamp((6.7-t)/(6.7-5.15)))
            for id in range(144):
                path=id//3;at=rows[path*2][7];life=1.65+.25*previous.rand(path,61)
                elapsed=max(0,min(t,5.15)-at);born=at+math.floor(elapsed/life)*life;local=max(0,t-born)
                birth=smooth(0,1,clamp(local/.22));death=smooth(0,1,clamp((life-local)/.65))
                alpha=0 if t<at else .36*fade*birth*death
                if alpha>1e-7:visible.add(id)
                assert 0<=alpha<=.3600001 and math.isfinite(alpha)
                if t==6.7:assert alpha==0
                if t>=5.15:
                    b=at+math.floor(max(0,5.15-at)/life)*life
                    last_emission_stable &= abs(b-born)<1e-9
                max_alpha=max(max_alpha,alpha);sample_count+=1
        check('lifecycle real fps '+str(fps),True)
    check('all 144 independent segments become visible',len(visible)==144)
    check('no post-sheath new birth; END no remaining alpha',last_emission_stable and max_alpha<=.36)
    corner_count=0
    for radius in [1,30,350,5000]:
        scale=radius/max(1,max(max(math.hypot(s[0]-s[3]*s[6],s[2]-s[5]*s[6]),math.hypot(s[0]+s[3]*s[6],s[2]+s[5]*s[6]))+.18/30 for s in rows))
        for t in [0,2.35,3,4.2,5.15,6.4,6.7]:
            for path in range(48):
                s=rows[path*2];d=unit(s[3:6]);side=unit(cross(d,(0,1,0)));life=1.65+.25*previous.rand(path,61)
                at=s[7];born=at+math.floor(max(0,min(t,5.15)-at)/life)*life;u=clamp(max(0,t-born)/life)
                for part in range(3):
                    p=plus(mul(s[:3],scale),mul(d,s[6]*scale*(-.48+.96*previous.rand(path,62))+radius*(.16*u+.10*(part-1))))
                    p=plus(p,plus(mul(side,radius*.035*math.sin(u*4.71238898+path)*(1-u)),(0,radius*.06*u,0)))
                    p=bound(p,radius);size=radius*(.04+.016*previous.rand(path,63));stretch=3.1+.6*previous.rand(path,64)
                    for eye in [(0,radius*2,0),(radius*2,.8,0),plus(p,mul(d,2*radius)),p]:
                        v=plus(eye,mul(p,-1));view=unit(v) if norm(v)>1e-6 else (0,0,1)
                        right=unit(cross(view,(0,1,0)));up=unit(cross(right,view))
                        x=sum(a*b for a,b in zip(d,right));y=sum(a*b for a,b in zip(d,up));angle=0 if x*x+y*y<1e-6 else math.atan2(-x,y)
                        a=mul(plus(mul(right,math.cos(angle)),mul(up,math.sin(angle))),size)
                        z=mul(plus(mul(right,-math.sin(angle)),mul(up,math.cos(angle))),size*stretch)
                        for aa,zz in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                            corner=bound(plus(p,plus(mul(a,aa),mul(z,zz))),radius)
                            assert all(math.isfinite(x) for x in corner) and corner[1]>=.8 and norm((corner[0],corner[1]-.8,corner[2]))<=radius+1e-6
                            corner_count+=1
    check('perspective/overhead/path-aligned/degenerate eyes keep finite bounded smoke corners',True)
    # Alpha形状边缘、半球边缘与色表映射数值界；模型不能代替游戏GPU验收。
    for u in [0,.01,.25,.5,.75,.99,1]:
        for v in [0,.01,.25,.5,.75,.99,1]:
            edge=clamp(1-((2*u-1)**2+(2*v-1)**2))**2
            if u in [0,1] or v in [0,1]:assert edge==0
            assert 0<=edge<=1
    check('all quad edges transparent with soft interior',True)
    for distance in [0,.4,.81,.82,.9,.999,1,1.01,2]:
        b=1-smooth(.82,1,distance)
        assert 0<=b<=1
        if distance>=1:assert b==0
    check('hemisphere fade at same 350 radius, no hard exterior',True)
    for a in [i/1000 for i in range(1001)]:
        wisps=.56*a+.44*math.sqrt(a)
        assert a<=wisps<=1 and math.isfinite(wisps)
    check('low-density smoke retained; original zero alpha stays zero',True)
    for cell in range(64):
        for u in [0,.1,.5,.9,1]:
            for v in [0,.1,.5,.9,1]:
                x=cell%8*.125+.5/512+u*(.125-1/512)
                y=cell//8*.125+.5/512+v*(.125-1/512)
                assert cell%8*.125<x<(cell%8+1)*.125 and cell//8*.125<y<(cell//8+1)*.125
        nxt=(cell+1)%64;assert 0<=nxt<64
    check('both interpolated atlas frames inside original 64 cells',True)
    im=Image.open(A/'jce_fog_noise.tga').convert('RGBA')
    check('bounded low-frequency RG noise field',im.size==(256,256) and im.getextrema()[2]==(128,128) and im.getextrema()[3]==(255,255))
    seam=max(max(abs(im.getpixel((0,y))[ch]-im.getpixel((255,y))[ch]) for y in range(256)) for ch in [0,1])
    seam=max(seam,max(max(abs(im.getpixel((x,0))[ch]-im.getpixel((x,255))[ch]) for x in range(256)) for ch in [0,1]))
    check('periodic noise bilinear seam is smooth',seam<=4)
    palim=Image.open(A/'jce_source_fog_palette.dds').convert('RGB')
    for d in [i/100 for i in range(101)]:
        p=palim.getpixel((round((.14+.64*d)*(palim.width-1)),palim.height//2))
        b=[.24+(.56-.24)*d,.43+(.78-.43)*d,.66+(.96-.66)*d]
        c=[.82*b[k]+.18*p[k]/255*[.8,.98,1][k] for k in range(3)]
        assert all(0<=x<=1 for x in c) and c[2]>c[1]>c[0]
    check('palette adaptation retains blue/green/red separation without HDR clipping',True)
    changed=[ROOT/'JudgementCutEnd.cpp',ROOT/'tools/author_blue_fog.py',ROOT/'tools/verify_blue_fog.py',
        *[A/x for x in ['jce_atmosphere.hlsl','jce_atmosphere.program','jce.material','jce_source.material','vfx-2.2.0.json']]]
    for p in changed:
        raw=p.read_bytes();s=raw.decode('utf-8-sig')
        check('encoding CRLF readable Chinese '+p.name,'\n' not in s.replace('\r\n','') and not any(x in s for x in ['\ufffd','\u951f\u65a4\u62f7','\u951f','\u00c3','\u00c2','\u00ef\u00bb\u00bf','\u00e5','\u00e6','\u00e7','\u00e8','\x3f\x3f\x3f']))
        if p.suffix=='.py':ast.parse(s)
    check('CPP BOM preserved',(ROOT/'JudgementCutEnd.cpp').read_bytes().startswith(b'\xef\xbb\xbf'))
    check('all new shader/material references resolve',all((A/x).exists() for x in ['jce_atmosphere.hlsl','jce_fog_noise.tga','jce_source_fog_palette.dds','jce_source_dust.dds']))
    check('new source cannot pass old binary deployment guard','version=2.2.0-dev' in cpp and b'version=2.2.0-dev' not in (ROOT.parent/'bin/Release/JudgementCutEnd.dll').read_bytes())
    return {'passed':True,'check_count':len(checks),'checks':checks,'native_compile_run':False,'shader_compile_run':False,
        'installed':False,'game_tested':False,'source_version':'2.2.0-dev','resource_revision':'2.2-blue-wisps-r1',
        'conservative_geometry':{'vertices':new_v,'indices':new_i,'previous_vertices':old_v,'previous_indices':old_i},
        'lifecycle_samples':sample_count,'bounded_smoke_corners':corner_count,'noise_seam_max_byte_difference':seam,
        'limitations':['未运行C++/HLSL编译器','模型与文本检查不能证明实际GPU行为/透明排序/帧率/最终视觉']}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
