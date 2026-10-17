"""2.2蓝色氤氲：仅生成本项目源码/材质/纹理，不编译、不部署、不写原Skyrim资源。"""
from pathlib import Path
from PIL import Image
import ast,datetime,hashlib,io,json,math,re,sys
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'package/JudgementCutEnd/assets'
STAMP='JudgementCutEnd-BlueFog-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
AUDIT=ROOT/'docs'/STAMP
BASELINE_CPP='61f10be1a013bfe06c0075a79b9359d4cb30a5bf425dcd5af70f7dc3b1993e33'
def digest(b):return hashlib.sha256(b).hexdigest()
def text(p):return p.read_bytes().decode('utf-8-sig').replace('\r\n','\n')
def put(rel,data,role,where,before,change,reason,impact):
    # 每个旧文件先双备份且逐字节读回；文本仅接受原UTF-8/CRLF，不静默转换其它编码。
    p=ROOT/rel;old=p.read_bytes() if p.exists() else None
    bom=bool(old and old.startswith(b'\xef\xbb\xbf'));encoding='binary';backups=[]
    if isinstance(data,str):
        if old is not None:
            original=old.decode('utf-8-sig')
            assert '\n' not in original.replace('\r\n',''),p
        data=data.replace('\r\n','\n').replace('\n','\r\n').encode('utf8')
        if bom:data=b'\xef\xbb\xbf'+data
        new=data.decode('utf-8-sig')
        assert not any(x in new for x in ['\ufffd','\u951f\u65a4\u62f7','\u951f','\u00c3','\u00c2','\u00ef\u00bb\u00bf','\u00e5','\u00e6','\u00e7','\u00e8','\x3f\x3f\x3f']),p
        encoding='UTF-8 '+('BOM' if bom else 'no BOM')+' / CRLF'
    if old==data:return
    if old is not None:
        assert len(old)<=20*1024*1024,p
        for base in [Path(r'D:\CodexBackups'),Path(r'E:\AIWorkSpace\_backups')]:
            dest=base/STAMP/p.drive[0]/Path(*p.parts[1:])
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(old)
            assert dest.read_bytes()==old,dest
            backups.append(str(dest))
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('wb' if old is not None else 'xb') as f:f.write(data)
    assert p.read_bytes()==data
    if isinstance(data,bytes) and p.suffix in ['.cpp','.hlsl','.program','.material','.json','.md','.py']:
        new=data.decode('utf-8-sig')
        if old is not None:
            important=re.findall(r'[\u4e00-\u9fff]{4,}',old.decode('utf-8-sig'))
            # 被改区允许注释更新；未改区的中文由完整源码/材质保护区核验，而不是盲修原文。
        assert '\n' not in new.replace('\r\n','')
        if p.suffix=='.py':ast.parse(new)
    report={'File':str(p),'Role':role,'Code location':where,'Before':before,'Changes':change,
        'Reasons':reason,'After':digest(data),'Impact':impact,
        'Validation':'立即字节读回与编码/中文检查通过；见随后verify_blue_fog.py，未运行编译器',
        'Safety':{'backups':backups,'encoding':encoding,'before_sha256':digest(old) if old else None},
        'Unresolved':'[MISSING] 游戏实际shader加载、透明排序/性能与最终观感；用户Release|x64编译后验收'}
    reportPath=AUDIT/(str(len(list(AUDIT.glob('*-file.json')))).zfill(3)+'-'+p.name+'-file.json')
    with reportPath.open('xb') as f:f.write((json.dumps(report,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf8'))
    print(json.dumps({'file':str(p),'report':str(reportPath),'backed_up':len(backups),'encoding':encoding},ensure_ascii=False))
def replace_once(source,old,new):
    assert source.count(old)==1,old[:100]
    return source.replace(old,new,1)
def main():
    cppPath=ROOT/'JudgementCutEnd.cpp';assert digest(cppPath.read_bytes())==BASELINE_CPP,'Source changed; review first'
    AUDIT.mkdir()
    # 先固定所有现有包文件和外部DLL身份；正式版/游戏安装在本任务中全程只读。
    baseline={'stamp':STAMP,'source_sha256':BASELINE_CPP,'files':{},
        'installed':{},'formal':{},'external_dll':{},'video':r'E:\QQdata\1009E7~1.MP4',
        'video_frames':r'D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCEVideoReview-20261008-115041-8f2a3a'}
    for p in [cppPath,*sorted((ROOT/'package/JudgementCutEnd').rglob('*'))]:
        if p.is_file():baseline['files'][str(p.relative_to(ROOT))]=digest(p.read_bytes())
    game=Path(r'D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd')
    for p in sorted((ROOT/'package/JudgementCutEnd').rglob('*')):
        if p.is_file():
            rel=p.relative_to(ROOT/'package/JudgementCutEnd');q=game/rel
            if q.exists():baseline['installed'][str(q)]=digest(q.read_bytes())
    for name in ['JudgementCutEnd-1.0.0.zip','JudgementCutEnd-2.0.0-release.zip']:
        p=ROOT/'releases'/name;baseline['formal'][str(p)]=digest(p.read_bytes())
    p=ROOT.parent/'bin/Release/JudgementCutEnd.dll';baseline['external_dll'][str(p)]=digest(p.read_bytes())
    # 本机NIF直接核验原烟雾确实引用该渐变；这里仅复用色表，不宣称完整还原Skyrim渲染器。
    sys.path.insert(0,str(ROOT/'tools'));import inspect_skyrim_vfx as nif
    parsed=nif.parse(nif.SOURCE/'Meshes/effects/AP05/JCE030CutAllActi.nif')
    smoke=[b for b in parsed['parsed_blocks'] if b.get('palette_texture','').lower().endswith('gradshockdisintegrate.dds')]
    assert len(smoke)==1 and smoke[0]['source_texture'].lower().endswith('fxsmokesoftsub.dds')
    palette=nif.SOURCE/smoke[0]['palette_texture'].replace('\\','/')
    assert palette.exists()
    baseline['skyrim_palette']={'path':str(palette),'sha256':digest(palette.read_bytes()),'nif':parsed['file'],
        'nif_sha256':parsed['sha256'],'block':smoke[0],'mapping':'中间行按密度采样；18%源色表 + 冷蓝基色适配，非Skyrim原渲染公式'}
    with (AUDIT/'baseline.json').open('xb') as f:f.write((json.dumps(baseline,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf8'))
    cpp=text(cppPath);oldcpp=cpp
    cpp=cpp.replace('2.1.0-dev','2.2.0-dev')
    cpp=replace_once(cpp,'// 特效对象/顶点硬预算；16幻影路径、80云团、128微粒、48镜面/192碎片，没有永久实体。\nconst unsigned PHANTOM_PATHS=16, PHANTOM_ECHOES=4, SLASH_ECHOES=6, MIST_CLOUDS=168;',
        '// 蓝雾采用96个宽软云层和48条刀路各3段烟流；无半球壳、无永久实体。\n// 顶点/索引硬预算仍沿用32768/49152；其他幻影、刀光与光屑数量不变。\nconst unsigned PHANTOM_PATHS=16, PHANTOM_ECHOES=4, SLASH_ECHOES=6, MIST_CLOUDS=96;')
    lo=cpp.index('    void HazeVertex(');hi=cpp.index('    void SlashAfterimages(',lo)
    newmist="""    void HazeVertex(const Vector3& p,float u,float v,float alpha){
        // 自有雾shader的TEXCOORD0四分量为局部UV/剪辑秒/范围半径；顶点程序还传施放局部位置。
        // 时间只用于雾的缓慢流动，仍随现有三倍演出时间轴；不读写世界速度、不按帧查材质。
        geometry->position(BoundAtmosphere(p));geometry->textureCoord(u,v,time,AreaRadius());
        geometry->colour(.82f,.91f,1.f,Clamp(alpha,0,1));
    }
    void HazeQuad(const Vector3& a,const Vector3& b,const Vector3& c,const Vector3& d,float alpha){
        HazeVertex(a,0,0,alpha);HazeVertex(b,1,0,alpha);
        HazeVertex(c,1,1,alpha);HazeVertex(d,0,1,alpha);
        geometry->index(vertex);geometry->index(vertex+1);geometry->index(vertex+2);
        geometry->index(vertex);geometry->index(vertex+2);geometry->index(vertex+3);vertex+=4;
    }
    void Mist(const Vector3& eye){
        // 取消576面封闭壳：大软云片互相重叠形成体积感，像素按局部半径柔化边缘，不出现硬罩子。
        // 这里只是有界视觉近似；96槽深度排序、每帧栈持有，不生成实体或分配堆内存。
        float rise=Clamp((time-.5f)/1.4f,0,1),end=Clamp((END-time)/(END-SHEATH),0,1);
        float phase=rise*rise*(3-2*rise)*(time<SHEATH?1.f:end*end*(3-2*end));
        HazeCell cells[MIST_CLOUDS];unsigned count=0;float radius=AreaRadius();
        for(unsigned level=0;level<6;++level)for(unsigned ring=0;ring<2;++ring)for(unsigned j=0;j<8;++j){
            unsigned id=count;float h=.08f+.145f*level,r=sqrtf(1-h*h)*(.20f+.42f*ring);
            float angle=(float(j)+.5f*(level&1)+.19f*ring)*.78539816f+time*.018f;
            Vector3 p(cosf(angle)*radius*r,.8f+radius*h,sinf(angle)*radius*r);
            p+=Vector3(sinf(time*.28f+id*.73f)*radius*.018f,sinf(time*.22f+id)*radius*.012f,
                cosf(time*.24f+id*.51f)*radius*.018f);
            cells[count].p=BoundAtmosphere(p);cells[count].depth=(eye-cells[count].p).squaredLength();
            cells[count].size=radius*(.22f+.04f*FxRandom(id,91));cells[count].id=id;++count;
        }
        std::sort(cells,cells+count);
        for(unsigned i=0;i<count;++i){
            Vector3 p=cells[i].p,view=eye-p;if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
            Vector3 right=view.crossProduct(Vector3::UNIT_Y);if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
            Vector3 up=right.crossProduct(view);up.normalise();right*=cells[i].size;up*=cells[i].size*.85f;
            HazeQuad(p-right-up,p+right-up,p+right+up,p-right+up,phase*.115f);
        }
    }
"""
    cpp=cpp[:lo]+newmist+cpp[hi:]
    lo=cpp.index('    void SourceDust(');hi=cpp.index('    void SourceFlashes(',lo)
    newdust="""    void SmokeSprite(const Vector3& p,float size,float stretch,float angle,float alpha,const Vector3& eye,float frame){
        // 专用烟雾输入：0..1局部UV/连续图集帧/范围半径，shader在同一64格内插值两帧。
        // 不改变SourceSprite的刀光/光屑合同；边界与透明度在自有像素程序再次软化。
        Vector3 view=eye-p;if(view.squaredLength()<.000001f)view=Vector3::UNIT_Z;view.normalise();
        Vector3 right=view.crossProduct(Vector3::UNIT_Y);if(right.squaredLength()<.000001f)right=Vector3::UNIT_X;right.normalise();
        Vector3 up=right.crossProduct(view);up.normalise();
        Vector3 a=(right*cosf(angle)+up*sinf(angle))*size,z=(-right*sinf(angle)+up*cosf(angle))*(size*stretch);
        const Vector3 corners[]={p-a-z,p+a-z,p+a+z,p-a+z};const float us[]={0,1,1,0},vs[]={0,0,1,1};
        for(unsigned i=0;i<4;++i){
            geometry->position(BoundAtmosphere(corners[i]));geometry->textureCoord(us[i],vs[i],frame,AreaRadius());
            geometry->colour(.78f,.9f,1.f,Clamp(alpha,0,1));
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
        float opacity=age<0?0.f:(.16f+.20f*Clamp(SourceCurve(1,age),0,1))*fade;
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
"""
    cpp=cpp[:lo]+newdust+cpp[hi:]
    cpp=replace_once(cpp,'particle_revision=2.1_streams dust_slots=48 spark_slots=128 haze_cells=',
        'particle_revision=2.2_blue_wisps dust_paths=48 dust_slots=144 spark_slots=128 haze_cells=')
    cpp=replace_once(cpp,'atmosphere=grey_hemisphere facets=','atmosphere=blue_soft_clouds palette=ap05_gradshock facets=')
    put('JudgementCutEnd.cpp',cpp,'RE_Kenshi主线程演出生产端','HazeVertex/HazeQuad/Mist/SmokeSprite/SourceDust与版本/首次日志',
        '168小灰雾片+576壳面；48个短寿命烟团',
        '96宽软底雾；144重叠烟流；四分量UV输送时间/半径；版本2.2.0-dev',
        '实机4.4/10秒雾稀薄；旧顶点灰色、独立小片与密度收紧阻碍连续氤氲',
        '仅VFX生产与自有shader合同；保持9段索引和首段背景复制，其他游戏逻辑逐字校验')
    # 噪声是可复现的周期低频场，不使用随机逐帧亮点；RGBA存两个独立平滑密度场。
    def hash_value(x,y,seed,n):
        v=((x%n)*374761393+(y%n)*668265263+seed*1442695041)&0xffffffff
        v=((v^(v>>13))*1274126177)&0xffffffff
        return ((v^(v>>16))&65535)/65535
    def noise(x,y,n,seed):
        x*=n;y*=n;ix=math.floor(x);iy=math.floor(y);u=x-ix;v=y-iy
        u=u*u*(3-2*u);v=v*v*(3-2*v)
        a=hash_value(ix,iy,seed,n);b=hash_value(ix+1,iy,seed,n)
        c=hash_value(ix,iy+1,seed,n);d=hash_value(ix+1,iy+1,seed,n)
        return (a*(1-u)+b*u)*(1-v)+(c*(1-u)+d*u)*v
    im=Image.new('RGBA',(256,256));pixels=[]
    for y in range(256):
        for x in range(256):
            values=[]
            for seed in [17,41]:
                v=sum(w*noise(x/256,y/256,n,seed) for n,w in [(3,.64),(5,.28),(9,.08)])
                values.append(round(255*v))
            pixels.append((values[0],values[1],128,255))
    im.putdata(pixels);buf=io.BytesIO();im.save(buf,format='TGA')
    put('package/JudgementCutEnd/assets/jce_fog_noise.tga',buf.getvalue(),'周期低频密度纹理','256² RGBA / R和G两个平滑场',
        '无连续密度场','可复现3/5/9频率云场，wrap采样，只有8%细尺度',
        '大雾片内部需缓慢变化而非固定颗粒','仅自有雾shader；无每帧CPU纹理生成')
    put('package/JudgementCutEnd/assets/jce_source_fog_palette.dds',palette.read_bytes(),'本机ap05色表资源',
        'JCE030CutAllActi.nif烟雾材质palette引用','原烟雾渐变未在本插件实际采样',
        '原DDS逐字节复制；来源NIF和纹理SHA写入baseline','提供蓝紫颜色层次',
        '仅烟雾材质使用；原模组文件只读，18%混合为Kenshi适配而非完全照搬')
    shader="""// 蓝雾仅作用于本插件两种自有材质；不修改游戏全屏雾、曝光、共享shader或深度资源。
// VP沿用本机basic.hlsl的POSITION/COLOR/TEXCOORD0与worldviewproj_matrix合同，另传施放局部位置。
// 半径/时钟由各四边形的四分量UV输送；不依赖按帧改材质或游戏全局时间。
struct JCE_FOG_FRAGMENT {
    float4 pos : SV_Position;
    float4 colour : COLOR;
    float4 texCoord : TEXCOORD0;
    float3 localPosition : TEXCOORD1;
};
JCE_FOG_FRAGMENT jce_fog_vp(float4 pos : POSITION,float4 colour : COLOR,float4 texCoord : TEXCOORD0,
                           uniform float4x4 worldViewProjMatrix) {
    JCE_FOG_FRAGMENT o;
    o.pos=mul(worldViewProjMatrix,pos);
    o.colour=colour;o.texCoord=texCoord;o.localPosition=pos.xyz;
    return o;
}
Texture2D fogNoise : register(t0);
SamplerState noiseSampler : register(s0);
Texture2D fogPalette : register(t1);
SamplerState paletteSampler : register(s1);
Texture2D smokeAtlas : register(t2);
SamplerState atlasSampler : register(s2);
float jce_fog_edge(float2 uv) {
    // 四边形内用平方椭圆柔边，四边完全透明；保留低密度细节，不做稠密轮廓提取。
    float2 p=uv*2-1;
    float edge=saturate(1-dot(p,p));
    return edge*edge;
}
float jce_fog_boundary(float3 q) {
    // 底部只需不穿地，侧/顶部在半径的末18%柔和淡出；半径来自同一AreaRadius生产端。
    return (1-smoothstep(.82,1,length(q)))*smoothstep(0,.025,q.y);
}
float3 jce_fog_colour(float density) {
    // 原色表中间行按密度采样，再与冷蓝基色分层；避免把原暗紫直接当成灰烟或冲白HDR。
    float3 original=fogPalette.Sample(paletteSampler,float2(.14+.64*saturate(density),.5)).rgb;
    float3 blue=lerp(float3(.24,.43,.66),float3(.56,.78,.96),saturate(density));
    return lerp(blue,original*float3(.80,.98,1),.18);
}
float4 jce_mist_fp(JCE_FOG_FRAGMENT input) : SV_Target {
    // 未出生/结束的固定占位片仍提交几何，但零Alpha立即返回，不进行雾纹理采样。
    if(input.colour.a<=0)return float4(0,0,0,0);
    float radius=max(input.texCoord.w,.001);
    float3 q=(input.localPosition-float3(0,.8,0))/radius;
    float clock=input.texCoord.z;
    // 两个低频场缓慢错向平移，第二层受第一层柔和扭曲；无高频散点和逐帧随机闪烁。
    float2 uv0=q.xz*.75+q.y*float2(.35,-.21)+clock*float2(.022,-.018);
    float4 first=fogNoise.Sample(noiseSampler,uv0);
    float2 uv1=q.xy*1.4+q.z*float2(.27,.16)+(first.rg-.5)*.11+clock*float2(-.016,.024);
    float density=.68*first.r+.32*fogNoise.Sample(noiseSampler,uv1).g;
    float alpha=input.colour.a*jce_fog_edge(input.texCoord.xy)*jce_fog_boundary(q)*(.38+.62*density);
    return float4(jce_fog_colour(density)*input.colour.rgb,saturate(alpha));
}
float4 jce_smoke_frame(float frame,float2 uv) {
    // 每格64px/原图512px；半纹素内缩后再采样，插值也不能跨格或串到其它帧。
    float tile=fmod(floor(frame),64);
    float2 cell=float2(fmod(tile,8),floor(tile/8));
    float2 atlasUV=cell*.125+.5/512+saturate(uv)*(.125-1.0/512);
    return smokeAtlas.Sample(atlasSampler,atlasUV);
}
float4 jce_smoke_fp(JCE_FOG_FRAGMENT input) : SV_Target {
    // 未出生/结束的固定占位片仍提交几何，但零Alpha立即返回，不进行雾纹理采样。
    if(input.colour.a<=0)return float4(0,0,0,0);
    float radius=max(input.texCoord.w,.001);
    float3 q=(input.localPosition-float3(0,.8,0))/radius;
    float frame=max(0,input.texCoord.z);
    float4 first=jce_smoke_frame(frame,input.texCoord.xy);
    float4 second=jce_smoke_frame(frame+1,input.texCoord.xy);
    float4 source=lerp(first,second,frac(frame));
    // 恢复原Alpha低密度细丝，平方根只适度提升薄烟；原Alpha为零时仍严格透明。
    float wisps=.56*source.a+.44*sqrt(saturate(source.a));
    float noise=fogNoise.Sample(noiseSampler,q.xz*1.65+q.y*.32+frame*float2(.0015,-.001)).r;
    float alpha=wisps*input.colour.a*jce_fog_edge(input.texCoord.xy)*jce_fog_boundary(q)*(.72+.28*noise);
    float density=saturate(.38+.42*source.a+.20*noise);
    return float4(jce_fog_colour(density)*input.colour.rgb*1.12,saturate(alpha));
}
"""
    put('package/JudgementCutEnd/assets/jce_atmosphere.hlsl',shader,'独立VP/底雾/烟流shader',
        'jce_fog_vp / jce_mist_fp / jce_smoke_fp','灰底雾与硬化烟团分开且无源渐变',
        '局部连续云场、半球柔边、原图集双帧插值、低密度细丝、蓝紫渐变',
        '仅换RGB无法获得氤氲形态','新增本插件着色器；3次底雾采样/4次烟流采样；真实GPU支持未验证')
    program="""// 与本机Ogre HLSL路径一致；矩阵自动参数名必须是worldviewproj_matrix。
vertex_program JCE/Fog_VP hlsl
{
    source jce_atmosphere.hlsl
    entry_point jce_fog_vp
    target vs_4_0
    default_params
    {
        param_named_auto worldViewProjMatrix worldviewproj_matrix
    }
}
fragment_program JCE/Mist_FP hlsl
{
    source jce_atmosphere.hlsl
    entry_point jce_mist_fp
    target ps_4_0
}
fragment_program JCE/Smoke_FP hlsl
{
    source jce_atmosphere.hlsl
    entry_point jce_smoke_fp
    target ps_4_0
}
"""
    put('package/JudgementCutEnd/assets/jce_atmosphere.program',program,'Ogre程序声明',
        '独立vs_4_0/ps_4_0三个入口','无蓝雾专用程序','局部位置VP与两种FP独立入口',
        'RGBA/UV/时钟/半径需明确跨层合同','不覆盖Basic或JCE/SourceTexture_FP，无共享参数副作用')
    def pass_text(fp,atlas=False):
        return """    technique
    {
        pass
        {
            vertex_program_ref JCE/Fog_VP {}
            fragment_program_ref JCE/"""+fp+""" {}
            // 普通透明混合保留背景与蓝色层次；写深度关闭，世界深度检测/双面保持。
            lighting off
            depth_write off
            depth_check on
            cull_hardware none
            scene_blend alpha_blend
            texture_unit
            {
                texture jce_fog_noise.tga
                tex_address_mode wrap
                filtering bilinear
            }
            texture_unit
            {
                texture jce_source_fog_palette.dds
                tex_address_mode clamp
                filtering bilinear
            }
"""+("""            texture_unit
            {
                texture jce_source_dust.dds
                tex_address_mode clamp
                filtering bilinear
            }
""" if atlas else '')+"""        }
    }
"""
    material=text(A/'jce.material');start=material.index('// JCE_VFX110_BEGIN');end=material.index('material JCE/Glass',start)
    replacement='// 蓝雾2.2：本层只绘制96个宽软云片，局部噪声与蓝紫色表替代灰色半球壳。\nmaterial JCE/Mist\n{\n'+pass_text('Mist_FP')+'}\n'
    material=material[:start]+replacement+material[end:]
    put('package/JudgementCutEnd/assets/jce.material',material,'底雾材质绑定','仅JCE/Mist',
        'Basic灰雾单纹理','绑定专用Fog_VP/Mist_FP与低频场/源色表',
        '背景雾灰色且形态单调','Glow/Glass/Refraction材质逐字保持')
    material=text(A/'jce_source.material')
    start=material.index('material JCE/SourceDust');end=material.index('// 本机ap05原纹理层',start)
    replacement='material JCE/SourceDust\n{\n'+pass_text('Smoke_FP',True)+'}\n'
    material=material[:start]+replacement+material[end:]
    put('package/JudgementCutEnd/assets/jce_source.material',material,'烟流材质绑定','仅JCE/SourceDust',
        'SourceTexture_FP启用dustDetail稠密轮廓','绑定专用Fog_VP/Smoke_FP和噪声/源色表/原烟图集',
        '低密度薄烟需要恢复及连续帧插值','其余刀光/拖尾/闪光/光屑材质逐字保持')
    metadata={'revision':'2.2-blue-wisps-r1','source_version':'2.2.0-dev','audit':str(AUDIT),
        'source_palette':baseline['skyrim_palette'],'video_observation':'4.4/10秒刀光淡蓝、空间雾稀薄零碎；不是对新版本的实机证明',
        'layers':9,'clouds':96,'shell_quads':0,'dust_paths':48,'dust_segments_per_path':3,'dust_slots':144,
        'dust_lifetime_clip_seconds':[1.65,1.90],'playback_rate':3,'clock_units':'clip seconds',
        'noise_texture':'jce_fog_noise.tga','noise_octaves':[[3,.64],[5,.28],[9,.08]],'noise_seed':[17,41],
        'base_cloud_alpha':.115,'smoke_alpha_before_atlas_max':.36,'boundary_fade_normalized':[.82,1],
        'estimated_max_vertices':17620,'estimated_max_indices':44286,
        'shader_sample_counts':{'Mist':3,'Smoke':4},'native_compiled':False,'shader_compiled':False,
        'game_tested':False,'installed':False,'notes':['雾层为有界透明近似，不是真体积光线积分','新素材与新DLL必须成套部署','不代编译、不写游戏/正式版']}
    put('package/JudgementCutEnd/assets/vfx-2.2.0.json',json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',
        '资源修订说明','2.2蓝雾合同与来源','无本修订说明','记录来源、预算、时钟、静态与实机状态',
        '避免新资源与旧DLL混装或把静态通过当成实机通过','仅说明文档，不参与游戏配置')
    baseline['changed_existing']=['JudgementCutEnd.cpp','package/JudgementCutEnd/assets/jce.material','package/JudgementCutEnd/assets/jce_source.material']
    # 基线只在新建后追加独立结果，不覆盖baseline。
    put('docs/blue-fog-2.2-task.json',json.dumps({'audit':str(AUDIT),'baseline':str(AUDIT/'baseline.json'),
        'source_version':'2.2.0-dev','resource_revision':'2.2-blue-wisps-r1','changed_existing':baseline['changed_existing'],
        'compiled':False,'game_tested':False,'installed':False},ensure_ascii=False,indent=2)+'\n',
        '本轮任务状态','新建2.2任务记录','无','保存不可变基线入口与待编译状态','静态审计需要原版身份','不影响旧版本实机状态')
    print('READY '+str(AUDIT))
if __name__=='__main__':main()
