"""2.6跨层审计：比较正式2.5与双备份、资源声明和边界模型；不编译或启动游戏。"""
from pathlib import Path
import ast,hashlib,json,math,re
from verify_particles import body,masked
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clamp(x):return max(0,min(1,x))
def smooth(x):x=clamp(x);return x*x*(3-2*x)
def main():
    checks=[]
    def check(n,v):
        checks.append({'name':n,'passed':bool(v)})
        if not v:raise AssertionError(n)
    baseline=json.loads((ROOT/'docs/bg3-design-2.6/baseline.json').read_text('utf-8'))
    for rel,m in baseline['files'].items():
        for directory in baseline['backups']:
            p=Path(directory)/'E/KenshiProject/2.Projects/JudgementCutEnd'/rel
            check('original backup hash '+str(p),digest(p)==m['sha256'])
    old=(Path(baseline['backups'][0])/'E/KenshiProject/2.Projects/JudgementCutEnd/JudgementCutEnd.cpp').read_text('utf-8-sig')
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig')
    allowed=['void SpatialFracture(','float SourceSmokeEnvelope(','void SourceSmokeVertex(','void SourceSmokeQuad(',
        'Vector3 SourceSmokePoint(','void SourceSmokeRibbons(','Vector3 SourceWispPoint(','void SourceSmokeWisps(',
        'void SourceFlashes(','void Draw(']
    normalized=cpp
    for signature in allowed:normalized=normalized.replace(body(normalized,signature),body(old,signature))
    check('entire C++ outside VFX scope equals 2.5',normalized.replace('2.6.0-dev','2.5.0-dev')==old)
    for signature in ['void Begin(','void Finish(','void Tick(','void Damage(','void Pose(','void RestoreTime(',
        'void Collect(','void FitSlashLayout(','void ReleaseGraphics(','void ReleaseRefraction(',
        'void CaptureBackground(','void MakeResources(','float SourceSmokeAge(','float SourceSmokeScale(']:
        check('protected function identity '+signature,body(cpp,signature)==body(old,signature))
    changed='\n'.join(body(cpp,n) for n in allowed)
    check('no C++11 additions',not re.search(r'\b(nullptr|constexpr|thread_local|auto)\b',masked(changed)))
    check('UV shape clock radius transport','float(shape%16)*16.f+time,AreaRadius()' in body(cpp,'void SourceSmokeVertex('))
    check('age passed to four corners',body(cpp,'void SourceSmokeQuad(').count('shape,alpha,age)')==4)
    for n in ['void SourceSmokeRibbons(','void SourceSmokeWisps(']:check('age producer '+n,',alpha,age);' in body(cpp,n))
    optics=(A/'jce_refraction.hlsl').read_text('utf-8');program=(A/'jce_refraction.program').read_text('utf-8')
    check('CPU lifecycle vectors','"cutLife"+Number(i),Ogre::Vector4(' in cpp and 'i<OPTICAL_PLANES' in body(cpp,'void SpatialFracture('))
    for i in range(8):check('cutLife contract '+str(i),bool(re.search(r'\bcutLife'+str(i)+r'\b',optics)) and 'param_named cutLife%d float4 0 0 0 0'%i in program)
    check('lifecycle vectors actually consumed',all(t in optics for t in ['saturate(lives[i].z)','saturate(lives[i].x)','saturate(lives[i].y)','saturate(weight)']))
    check('one HDR sample and bounded displacement',optics.count('sceneCopy.Sample(')==1 and '1080.0*20,10,28' in optics and 'if(magnitude>pixels)' in optics)
    check('refraction guards and hemisphere',all(t in optics for t in ['if(strength<=0)','if(boundary<=0)','smoothstep(.975,1,length(sphere))','smoothstep(0,.01,sphere.y)']))
    fog=(A/'jce_atmosphere.hlsl').read_text('utf-8');smoke=body(fog,'float4 jce_source_smoke_shape(')
    check('continuous shared field','+shape*' not in smoke and 'clock*.42+q.y*.48' in smoke)
    check('two noise samples plus atlas and palette',smoke.count('fogNoise.Sample(')==2 and smoke.count('smokeAtlas.Sample(')==1 and smoke.count('fogPalette.Sample(')==1)
    check('smoke guards','if(input.colour.a<=0)' in smoke and 'if(boundary<=0)' in smoke and 'saturate(alpha)' in smoke)
    check('atlas shape and half texel inset',all(t in smoke for t in ['clamp(floor(input.texCoord.z/16),0,15)','tile*.25+.5/512','(.25-1.0/512)']))
    for shape in range(16):
        for clock in [0,2.35,5.15,6.7]:
            packed=shape*16+clock
            check('UV shape '+str(shape)+' time '+str(clock),int(packed//16)==shape and abs(packed-shape*16-clock)<1e-5)
    declarations={}
    for p in A.glob('*.program'):
        s=p.read_text('utf-8')
        for kind,name in re.findall(r'(vertex|fragment)_program\s+(\S+)\s+hlsl',s):
            check('unique program '+name,name not in declarations);declarations[name]=p
        for source in re.findall(r'\bsource\s+(\S+)',s):check('shader exists '+source,(A/source).is_file())
        for entry in re.findall(r'\bentry_point\s+(\S+)',s):check('entry '+entry,any(re.search(r'\b'+re.escape(entry)+r'\s*\(',h.read_text('utf-8')) for h in A.glob('*.hlsl')))
    for p in [A/'jce.material',A/'jce_source.material']:
        for name in re.findall(r'(?:vertex|fragment)_program_ref\s+(JCE/\S+)',p.read_text('utf-8')):check('material link '+name,name in declarations)
    for name in ['JCE/MistBase26_FP','JCE/SourceSmokeRibbon26_FP','JCE/SourceSmokeWisp26_FP','JCE/Refraction26_FP']:check('versioned shader '+name,name in declarations)
    for rel in baseline['files']:
        p=ROOT/rel;s=p.read_text(baseline['files'][rel]['encoding']);m=masked(s)
        check('encoding CRLF '+rel,not any(x in s for x in ['\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf']) and b'\n' not in p.read_bytes().replace(b'\r\n',b''))
        if p.suffix in ['.cpp','.hlsl','.program','.material']:check('delimiters '+rel,all(m.count(l)==m.count(r) for l,r in [('(',')'),('{','}'),('[',']')]))
    # 数值模型只核对出生与退场边界，不声称执行了shader或C++。
    rows=[[float(x) for x in l.split()] for l in (A/'slashes.csv').read_text('utf-8').splitlines()[1:]]
    check('96 actual slashes',len(rows)==96)
    for i in range(8):
        at=rows[i*12][7];release_at=5.15+.018*i;denominator=5.60-release_at
        check('positive release interval '+str(i),denominator>0)
        samples=[]
        for t in [at-.1,at,at+.055,5.15,release_at,5.60,6.7]+[6.7*j/1000 for j in range(1001)]:
            release=clamp((t-release_at)/denominator);alive=smooth((t-at)/.055)*(1-smooth(release));pulse=math.sin(release*math.pi)
            samples.append(alive);assert 0<=alive<=1 and -1e-12<=pulse<=1
            if t<=at or t>=5.60:assert abs(alive)<1e-10
        check('cut lifecycle bounded with zero endpoints '+str(i),max(samples)>0)
    check('fixed slots and sections',all(t in cpp for t in ['SMOKE_BANDS=48','SMOKE_SEGMENTS=10','SMOKE_WISPS=96','MIST_SLICES=32','OPTICAL_PLANES=8','FX_SECTIONS=11']))
    meta=json.loads((A/'vfx-2.6.0.json').read_text('utf-8'));check('2.5 geometry budget',meta['geometry']['vertex_upper_bound']==19096<32768 and meta['geometry']['index_upper_bound']==46788<49152)
    check('BG3 original assets not copied',meta['bg3_assets_copied'] is False)
    archive=ROOT/'releases/JudgementCutEnd-2.5.0-release.zip'
    check('formal2.5 ZIP unchanged',digest(archive)=='ee5c0ae63b136003887372c3a25b43df69d72cfbd933eb352bdd569257396f65')
    check('installed DLL unchanged',digest(Path(r'D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd\JudgementCutEnd.dll'))=='3ed7242398a930cde9c6b40e79a63866cb19c15a7a94a1f681cb1fec9db44892')
    entries=json.loads((ROOT/'releases/2.5.0/manifest.json').read_text('utf-8-sig'))
    installed=0;original=0
    for item in entries:
        rel=item['path']
        if rel.startswith('installed-mod/JudgementCutEnd/assets/'):
            p=Path(r'D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd')/rel[len('installed-mod/JudgementCutEnd/'):]
            check('installed asset unchanged '+p.name,digest(p)==item['sha256']);installed+=1
        if rel.startswith('source/package/JudgementCutEnd/assets/'):
            p=ROOT/rel[len('source/'):];relative=p.relative_to(ROOT).as_posix()
            if relative not in baseline['files']:check('other source asset unchanged '+p.name,digest(p)==item['sha256']);original+=1
    check('archive asset comparisons nonempty',installed>10 and original>10)
    for p in (ROOT/'tools').glob('*.py'):ast.parse(p.read_text('utf-8'))
    check('Python syntax parsed',True)
    return {'static_passed':True,'check_count':len(checks),'checks':checks,'compiled':False,'game_tested':False,
        'installed_new_revision':False,'source_version':'2.6.0-dev','limitations':['文本和数学检查不能代替C++编译及HLSL运行','烟带面积和额外噪声采样的GPU开销待测量']}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
