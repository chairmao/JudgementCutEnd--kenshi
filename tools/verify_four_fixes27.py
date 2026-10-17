"""2.7四项视觉修正：源码边界、材质合同、颜色/低频/密度/输运模型；不编译或启动游戏。"""
from pathlib import Path
import ast,hashlib,json,math,re
import numpy as np
from PIL import Image
from verify_particles import body,masked
from generate_cloud_field27 import field
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return p.read_text('utf-8-sig')
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def main():
    checks=[];metrics={}
    def check(name,result):
        checks.append({'name':name,'passed':bool(result)})
        if not result:raise AssertionError(name)
    baseline=json.loads(read(ROOT/'docs/four-fixes-2.7/baseline.json'))
    old_root=Path(baseline['backups'][0])/'E/KenshiProject/2.Projects/JudgementCutEnd'
    for rel,item in baseline['files'].items():
        for backup in baseline['backups']:
            check('backup '+backup+' / '+rel,digest(Path(backup)/'E/KenshiProject/2.Projects/JudgementCutEnd'/rel)==item['sha256'])
    cpp=read(ROOT/'JudgementCutEnd.cpp');old=read(old_root/'JudgementCutEnd.cpp')
    # 整文件归一化比较：授权五个VFX函数及版本以外，所有代码、注释、契约逐字保持。
    allowed=['void Vertex(','void SourceDust(','void SourceSmokeRibbons(','void SourceSmokeWisps(','void Draw(']
    normalized=cpp
    for sig in allowed:normalized=normalized.replace(body(cpp,sig),body(old,sig),1)
    check('complete C++ scope limited to five VFX functions and version',normalized.replace('2.7.0-dev','2.6.0-dev')==old)
    protected=['void Begin(','void Finish(','void Tick(','void Damage(','void Pose(','void RestoreTime(',
       'void Collect(','void FitSlashLayout(','void ReleaseGraphics(','void ReleaseRefraction(',
       'void PrepareRefraction(','void CaptureBackground(','void MakeResources(','void Ribbon(',
       'void GroundRing(','void Mist(','void HazeVertex(','void SourceQuad(','void SourceSprite(']
    for sig in protected:check('protected unchanged '+sig,body(cpp,sig)==body(old,sig))
    # 字符串屏蔽保留原长度，日志字数变动会留下不同空白；去空白后逐token比较。
    check('Draw only revision log changed',re.sub(r'\s+','',masked(body(cpp,'void Draw(')))==re.sub(r'\s+','',masked(body(old,'void Draw('))))
    vertex=body(cpp,'void Vertex(')
    check('only Ribbon and GroundRing use energy Vertex',len(re.findall(r'\bVertex\(',cpp))==1+len(re.findall(r'\bVertex\(',body(cpp,'void Ribbon(')))+len(re.findall(r'\bVertex\(',body(cpp,'void GroundRing('))))
    check('energy producer shared RGB peak and alpha half',all(x in vertex for x in ['std::max(r,std::max(g,b))','r*inverse','g*inverse','b*inverse','energy*.5f']))
    shader=read(A/'jce_source_texture.hlsl');glow=body(shader,'float4 jce_glow27_fp(');source=body(shader,'float4 jce_source_texture_fp(')
    material=read(A/'jce.material');source_material=read(A/'jce_source.material');glow_mat=body(material,'material JCE/Glow')
    check('Glow decodes alpha once and returns zero for zero energy',all(x in glow for x in ['saturate(input.colour.a)*2','if(energy<=0)return float4(0,0,0,0)','hdrGain*energy']))
    check('Glow energy in RGB and ONE ONE blend','scene_blend add' in glow_mat and 'scene_blend src_alpha' not in glow_mat and 'light/(1+.45*peak),0' in glow)
    check('ordinary source alpha not decoded','source.a*input.colour.a*detail' in source and 'input.colour.a)*2' not in source)
    check('shared scalar HDR compression','light/=1+.35*peak' in source and 'light/(1+.45*peak)' in glow)
    check('old vertex white saturation reproduced',np.array_equal(np.clip(np.array([.65,.85,1])*1.6,0,1),[1,1,1]))
    for brightness in [0,.05,.4,.8,1.6,2]:
        raw=np.array([.65,.85,1])*brightness;energy=max(raw);rgb=raw/energy if energy>1e-6 else raw*0
        light=rgb*np.array([.25,.82,1])*1.35*(np.clip(energy*.5,0,1)*2);light/=1+.45*max(light)
        check('Glow hue/zero energy '+str(brightness),np.all(np.isfinite(light)) and (np.all(light==0) if brightness==0 else np.allclose(light/light[2],[.1625,.697,1])))
    metrics['maximum_single_glow_rgb']=light.tolist()
    # 逐program读取实际entry point/默认uniform，避免只替换文件名而消费者仍旧。
    programs={}
    for file in A.glob('*.program'):
        text=read(file)
        for match in re.finditer(r'(?:vertex|fragment)_program\s+(JCE/\S+)\s+hlsl',text):
            block=body(text,match.group());name=match.group(1)
            check('unique program '+name,name not in programs);programs[name]=block
            src=re.search(r'\bsource\s+(\S+)',block).group(1);entry=re.search(r'\bentry_point\s+(\S+)',block).group(1);hlsl=read(A/src)
            check('entry exists '+name,bool(re.search(r'\b'+re.escape(entry)+r'\s*\(',hlsl)))
            for param,kind in re.findall(r'param_named\s+(\w+)\s+(float(?:[234])?)\b',block):
                # 同类型uniform可逗号连续声明，按声明列表读取，不能只匹配首个变量。
                declarations=re.findall(r'\buniform\s+'+kind+r'\s+([^;)]+)[;)]',hlsl)
                check('uniform '+name+' / '+param,any(param in re.findall(r'\b\w+\b',decl) for decl in declarations))
    for file in A.glob('*.material'):
        for ref in re.findall(r'(?:vertex|fragment)_program_ref\s+(JCE/\S+)',read(file)):check('material resolves '+file.name+' / '+ref,ref in programs)
    check('Glow material owns new program','fragment_program_ref JCE/Glow27_FP' in glow_mat)
    check('Glow uniform defaults match',all(x in programs['JCE/Glow27_FP'] and x in glow_mat for x in ['hdrGain float 1.35','colourTint float3 0.25 0.82 1']))
    atmosphere=read(A/'jce_atmosphere.hlsl');refraction=read(A/'jce_refraction.hlsl')
    cloud=body(atmosphere,'float4 jce_cloud_field(');mist=body(atmosphere,'float4 jce_mist_fp(');aux=body(atmosphere,'float4 jce_source_smoke_shape(')
    for name in ['Mist','SourceSmokeRibbon','SourceSmokeWisp']:
        mat=body(material if name=='Mist' else source_material,'material JCE/'+name)
        check('low frequency repeat texture '+name,all(x in mat for x in ['texture jce_cloud_field27.tga','tex_address_mode wrap','filtering trilinear']))
    check('two field noise samples',cloud.count('fogNoise.Sample(')==2)
    check('volume and aux share local density field','jce_cloud_field(q,input.texCoord.z)' in mist and 'jce_cloud_field(q,clock)' in aux)
    check('continuous blue palette has no gray palette read','Sample' not in body(atmosphere,'float3 jce_fog_colour('))
    check('soft density / weak atlas / edge transparency',all(x in aux for x in ['smoothstep(.20,.76,field.x)','(.92+.08*sourceAlpha)','ends*cross','interior*interior']))
    check('fixed atlas and half texel',all(x in aux for x in ['floor(input.texCoord.z/16)','tile*.25+.5/512','(.25-1.0/512)']))
    check('atlas mip remains disabled',source_material.count('filtering linear linear none')>=2)
    check('legacy dust algorithm unchanged',body(atmosphere,'float4 jce_smoke_fp(')==body(read(old_root/'package/JudgementCutEnd/assets/jce_atmosphere.hlsl'),'float4 jce_smoke_fp('))
    check('dust/ribbon/wisp lower weighting','.006f+.010f*Clamp(SourceCurve(1,age),0,1)' in body(cpp,'void SourceDust(') and '.18f*SourceSmokeEnvelope' in body(cpp,'void SourceSmokeRibbons(') and '.025f+.020f' in body(cpp,'void SourceSmokeWisps('))
    check('slice normalized Beer Lambert alpha','step=2.f/float(MIST_SLICES)' in body(cpp,'void Mist(') and 'phase*step' in body(cpp,'void Mist(') and 'opticalDepth=.95*input.colour.a*boundary*density' in mist and '1-exp(-opticalDepth)' in mist)
    for density in [0,.1,.5,1]:
        for count in [16,32,64]:check('density model '+str((density,count)),abs(math.exp(-.95*2/count*density)**count-math.exp(-.95*2*density))<1e-12)
    metrics['uniform_path_alpha_old']=1-math.exp(-.16*2);metrics['uniform_path_alpha_new']=1-math.exp(-.95*2)
    check('denser volume remains bounded',0<metrics['uniform_path_alpha_old']<metrics['uniform_path_alpha_new']<1)
    for u,v in [(0,.5),(1,.5),(.5,0),(.5,1)]:
        interior=16*u*(1-u)*v*(1-v);ends=smooth(0,.12,u)*(1-smooth(.88,1,u));cross=1-smooth(.30,1,abs(v*2-1))
        check('four edges transparent '+str((u,v)),interior**2==0 and ends*cross==0)
    data=np.array(Image.open(A/'jce_cloud_field27.tga'));expected=np.rint(field()*255).astype(np.uint8)
    check('RGBA 512 periodic texture reproducible',data.shape==(512,512,4) and np.array_equal(data,expected))
    check('new texture hash',digest(A/'jce_cloud_field27.tga')=='7fa310bae0be51285107ab3b4e7cc839c81f23b0b871b6e277e2e50371b45db1')
    # wrap接缝梯度须与内部相当；周期采样不重复终点，不能强求首尾像素相等。
    for axis in [0,1]:
        d=data.astype(float);edge=np.take(d,0,axis=axis)-np.take(d,-1,axis=axis)
        check('periodic seam gradient '+str(axis),np.max(np.abs(edge))<=np.max(np.abs(np.diff(d,axis=axis)))+1)
    freq=np.fft.fftfreq(512)*512;yy,xx=np.meshgrid(freq,freq,indexing='ij');high=(np.abs(xx)>=16)|(np.abs(yy)>=16)
    for channel in range(4):
        v=data[:,:,channel]/255.;power=np.abs(np.fft.fft2(v-v.mean()))**2;ratio=float(power[high].sum()/power.sum());metrics['high_frequency_fraction_'+str(channel)]=ratio
        check('pixel grain power bounded '+str(channel),ratio<.0001)
    # 实际TGA周期双线性采样与HLSL公式对应；仅验证连续输运，不声称GPU实机流动。
    tex=data/255.
    def sample(uv):
        pos=np.mod(uv,1)*512-.5;lo=np.floor(pos).astype(int);f=pos-lo
        return sum(tex[(lo[:,1]+dy)%512,(lo[:,0]+dx)%512]*((f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1]))[:,None] for dy in [0,1] for dx in [0,1])
    rng=np.random.default_rng(27);q=rng.uniform(-.65,.65,(400,3));q[:,1]=rng.uniform(.1,.7,400)
    def density_at(clock):
        angle=clock*.38+q[:,1]*.45;sn=np.sin(angle);cs=np.cos(angle);rolled=np.stack([q[:,0]*cs-q[:,2]*sn,q[:,0]*sn+q[:,2]*cs],axis=1)
        uv=rolled*np.array([.66,1.02])+q[:,1,None]*np.array([.28,-.31]);first=sample(uv+clock*np.array([.12,-.09]))
        second=sample(uv[:,::-1]*np.array([.88,.62])+(first[:,1:3]-.5)*.28+clock*np.array([-.105,.13]))
        return smooth(.2,.76,.62*first[:,0]+.38*second[:,1])
    motion=float(np.mean(np.abs(density_at(2.5)-density_at(2.8))));tiny=float(np.mean(np.abs(density_at(2.5)-density_at(2.5001))))
    check('density flows across .3 clip second',motion>.015);check('density continuous across tiny time increment',tiny<.001)
    metrics['flow_mean_delta_0_3_clip_seconds']=motion;metrics['flow_mean_delta_0_0001_clip_seconds']=tiny
    check('one scene copy sample',refraction.count('sceneCopy.Sample(')==1)
    check('local cold multiplier','float3(.42,.68,.94)' in refraction)
    # 注释长度可变，忽略注释后的token序列比较精确锁定唯一的冷暗系数改动。
    old_ref=read(old_root/'package/JudgementCutEnd/assets/jce_refraction.hlsl')
    tokens=lambda x:re.sub(r'\s+','',masked(x))
    check('refraction only cold multiplier code changed',tokens(refraction).replace('float3(.42,.68,.94)','float3(.94,.975,1.015)')==tokens(old_ref))
    meta=json.loads(read(A/'vfx-2.7.0.json'))
    check('fixed geometry budget unchanged',meta['geometry']['vertex_upper_bound']==19096 and meta['geometry']['index_upper_bound']==46788 and meta['gpu']['extra_geometry']==0)
    check('metadata does not claim compilation or game test',not meta['compiled'] and not meta['game_tested'] and not meta['installed'])
    installed=Path(r'D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd')
    check('installed DLL remains verified 2.6',digest(installed/'JudgementCutEnd.dll')=='e990ba24148e48113620023427f95db173ba117db9127ca4394b620784dc8c99')
    for rel,item in baseline['files'].items():
        if '/assets/' in rel:check('installed asset unchanged '+Path(rel).name,digest(installed/'assets'/Path(rel).name)==item['sha256'])
    check('formal 2.5 frozen archive unchanged',digest(ROOT/'releases/JudgementCutEnd-2.5.0-release.zip')=='ee5c0ae63b136003887372c3a25b43df69d72cfbd933eb352bdd569257396f65')
    files=[ROOT/rel for rel in baseline['files'] if rel!='docs/task-status.json']+[ROOT/'tools/generate_cloud_field27.py',Path(__file__)]
    for file in files:
        raw=file.read_bytes();text=read(file)
        check('encoding '+file.name,raw.startswith(b'\xef\xbb\xbf')==(file.suffix=='.cpp'))
        check('CRLF '+file.name,b'\n' not in raw.replace(b'\r\n',b''))
        check('Chinese preserved '+file.name,not any(x in text for x in ['\ufffd','\u951f\u65a4\u62f7','\u951f','\u00c3','\u00c2','\u00ef\u00bb\u00bf','\u00e5','\u00e6','\u00e7','\u00e8']))
        if file.suffix=='.py':ast.parse(text);check('Python syntax '+file.name,True)
        else:check('balanced delimiters '+file.name,all(masked(text).count(a)==masked(text).count(b) for a,b in [('(',')'),('{','}'),('[',']')]))
    return {'static_passed':True,'check_count':len(checks),'checks':checks,'metrics':metrics,'compiled':False,'game_tested':False,'performance_measured':False,
       'limits':'源码合同与数值模型；未代替HLSL编译、GPU混合/曝光/性能和游戏验收'}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
