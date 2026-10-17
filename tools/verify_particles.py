"""2.1粒子与正式2.0回归：只读资源/静态/数值核验，不编译或启动游戏。"""
from pathlib import Path
import ast,hashlib,json,math,re,zipfile
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def masked(text):
    # 保持字符位置，忽略注释/字符串内的括号，提取函数时不把字符串里的符号当代码。
    return re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',lambda m:' '*len(m.group()),text,flags=re.S)
def body(text,signature):
    start=text.index(signature);m=masked(text);a=m.index('{',start);depth=1;i=a+1
    while depth:
        if m[i]=='{':depth+=1
        elif m[i]=='}':depth-=1
        i+=1
    return text[start:i]
def rand(i,salt):
    n=(i*374761393+salt*668265263+1100)&0xffffffff
    n=((n^(n>>13))*1274126177)&0xffffffff
    return ((n^(n>>16))&65535)/65535
def clamp(x,a=0,b=1):return max(a,min(b,x))
def main():
    checks=[]
    def check(name,result):
        checks.append({'name':name,'passed':bool(result)})
        if not result:raise AssertionError(name)
    f=ROOT/'releases/2.0.0';manifest=json.loads((f/'release-manifest.json').read_text('utf8'))
    formal=json.loads((ROOT/'docs/formal-release-2.0.0-clean.json').read_text('utf8'))
    check('formal2 tag and exact original DLL',manifest['release']=='2.0.0' and manifest['original_internal_version']=='1.2.1-dev' and digest(f/'mod/JudgementCutEnd.dll')==manifest['dll_sha256'])
    check('every formal2 manifest file unchanged',all(digest(f/x['path'])==x['sha256'] for x in manifest['files']))
    check('formal2 archive identity',digest(Path(formal['zip']))==formal['zip_sha256'])
    with zipfile.ZipFile(formal['zip']) as z:
        check('formal2 archive CRC and no IDE cache',z.testzip() is None and len(z.namelist())==len(manifest['files'])+1 and all('/.vs/' not in x for x in z.namelist()))
        check('formal2 archive all listed byte hashes',all(hashlib.sha256(z.read('JudgementCutEnd-2.0.0/'+x['path'])).hexdigest()==x['sha256'] for x in manifest['files']))
    for folder in formal['special_backups']:
        check('special release copy byte identity '+folder,digest(Path(folder)/Path(formal['zip']).name)==formal['zip_sha256'])
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig');old=(f/'source/JudgementCutEnd.cpp').read_text('utf-8-sig')
    # 不只检查伤害关键词：逐字锁定真实医疗调用、U输入、骨骼、时间恢复、清理和所有刀光生产者。
    protected=['bool SameDamageWeapon(','void PrepareWeapon(','void RestoreWeapon(','void ReleaseRefraction(',
        'void PrepareRefraction(','void CaptureBackground(','void MakeResources(','void RestoreTime(','void Begin(',
        'void ReleaseGraphics(','void Finish(','unsigned RefreshSkin(','void Pose(','float AreaRadius(',
        'void FitSlashLayout(','bool InArea(','void Collect(','void Damage(','void Ribbon(','void GroundRing(',
        'Vector3 BoundFx(','Vector3 BoundAtmosphere(','void SlashAfterimages(','void Phantom(','void Phantoms(',
        'void ShardPosition(','void Glass(','void SourceQuad(','void SourceSprite(','void SourceSlashes(',
        'void SourceFlashes(','void StartLayer(','void Tick(','intptr_t NativeAddress(']
    for name in protected:check('formal2 protected function byte identity '+name,body(cpp,name)==body(old,name))
    # Draw只有一条每次施放首次资源日志新增粒子版本；所有原刀光提交调用与阶段顺序保持逐字相同。
    normalized=body(cpp,'void Draw(').replace(' particle_revision=2.1_streams dust_slots=48 spark_slots=128','')
    check('formal2 draw and all slash section submission unchanged',normalized==body(old,'void Draw('))
    for asset in A.iterdir():
        if asset.is_file() and asset.name not in ['jce_source_texture.hlsl','jce_source_texture.program','jce_source.material']:
            check('original asset unchanged '+asset.name,asset.read_bytes()==(f/'mod/assets'/asset.name).read_bytes())
    material=(A/'jce_source.material').read_text('utf8');previous=(f/'mod/assets/jce_source.material').read_text('utf8')
    for name,next_name in [('SourceBlade','SourceFeather'),('SourceFeather','SourceDust'),('SourceFlash','SourceSpark')]:
        segment=lambda x:x.split('material JCE/'+name)[1].split('material JCE/'+next_name)[0]
        check('unmodified knife/flash material '+name,segment(material)==segment(previous))
    check('unmodified spark material',material.split('material JCE/SourceSpark')[1]==previous.split('material JCE/SourceSpark')[1])
    shader=(A/'jce_source_texture.hlsl').read_text('utf8');program=(A/'jce_source_texture.program').read_text('utf8')
    check('new parameter producer transport consumer',all(x in shader for x in ['uniform float dustDetail;','if(dustDetail>.5)','float detail=1;']) and 'param_named dustDetail float 0' in program and material.count('param_named dustDetail float 1')==1)
    check('shader does not add samples or alter UV/texture',shader.count('sourceTexture.Sample(')==1 and 'input.texCoord.xy)' in shader and 'source.a*input.colour.a*detail' in shader)
    check('finite local tile clock and stable sorted particle id',all(x in cpp for x in ['unsigned id=cells[i].id','cells[i].id=i','Clamp(local,0,3.f)*20.f','const unsigned count=48']))
    fog=body(cpp,'void Mist(');dust=body(cpp,'void SourceDust(');spark=body(cpp,'void SourceSparks(')
    check('background shell and cloud opacity reduced','phase*.055f' in fog and 'phase*.045f' in fog and '.15f+.015f' in fog)
    check('strict fixed geometry budget preserved','i<128' in spark and 'const unsigned count=48' in dust and 'MIST_CLOUDS=168' in cpp and 19828<32768 and 47598<49152)
    check('no gameplay IO entity allocation or logging in particle loops',not any(token in dust+spark+body(cpp,'float ParticleAngle(') for token in ['new ','resize(','push_back(','Log(','std::ifstream','setPosition(','createEntity','createParticleSystem','addWound','getByName(']))
    check('no C++11 syntax introduced',not re.search(r'\b(nullptr|constexpr|thread_local|auto)\b',masked(dust+spark)))
    check('spark layer transparent placeholder retained','if(vertex==before)SourceQuad(' in spark)
    # 全部粒子在不同帧率的三倍时间轴上采样寿命、停发和透明度；不是C++或GPU运行证明。
    rows=[[float(x) for x in line.split()] for line in (A/'slashes.csv').read_text('utf8').splitlines()[1:]]
    visible_dust=set();visible_sparks=set();dust_max_alpha=0;dust_cleared=True;spark_cleared=True
    for fps in [15,30,60,144]:
        seen=0
        for frame in range(math.ceil(6.7/3*fps)+1):
            t=min(6.7,3*frame/fps)
            for i in range(48):
                at=rows[i*2][7];life=1.10+.17*rand(i,61)
                elapsed=max(0,min(t,5.15)-at);born=at+math.floor(elapsed/life)*life;local=max(0,t-born)
                envelope=0 if t<at else clamp(local/.10)*clamp((life-local)/.35)
                tile=int(clamp(local,0,3)*20+i%8)%64
                if envelope>0:visible_dust.add(i)
                assert math.isfinite(envelope) and 0<=envelope<=1 and 0<=tile<64
                # 停止发射后不会重启；最晚5.15+1.27结束，早于整个演出6.7。
                if t>=6.42 and envelope>0:dust_cleared=False
            for i in range(128):
                at=rows[i%96][7] if t<5.15 else 5.15
                age=t-at-(i%8)*.014;life=.64+.22*rand(i,71)
                alpha=0 if age<0 or age>life else clamp(age/.025)*clamp(1-age/life)**1.5
                if alpha>0:seen+=1;visible_sparks.add(i)
                if t>=6.108 and alpha>0:spark_cleared=False
        check('spark emissions sampled at real fps '+str(fps),seen>0)
    check('all independent dust and spark slots visible during full timeline',len(visible_dust)==48 and len(visible_sparks)==128)
    check('dust and spark fade out before end; no post-cast residual',dust_cleared and spark_cleared)
    check('light fragment visible life at least 3.2 times old',min((.64+.22*rand(i,71))/.2 for i in range(128))>=3.2)
    for tile in range(64):
        u=(tile%8)/8+.5/512;v=(tile//8)/8+.5/512
        assert 0<u<u+.125-1/512<1 and 0<v<v+.125-1/512<1
    check('no DDS atlas neighbor sample or out of bounds',True)
    # 旋转相机仅换排序，稳定粒子ID不能改变自身寿命/图集帧；重合深度亦不依赖数组序号。
    local=.314
    identity={i:(1.10+.17*rand(i,61),int(local*20+i%8)%64) for i in range(48)}
    for sequence in [list(range(48)),list(reversed(range(48))),sorted(range(48),key=lambda i:rand(i,81))]:
        check('sort keeps atlas identity '+str(sequence[:3]),all(identity[i]==(1.10+.17*rand(i,61),int(local*20+i%8)%64) for i in sequence))
    # shader灰底门限只压低Alpha，范围0..1；其他材料dustDetail=0恒为2.0颜色/Alpha。
    for n in range(1001):
        a=n/1000;u=clamp((a-.025)/(.32-.025));core=u*u*(3-2*u)
        detail=.25+.75*core
        assert 0<=a*detail<=a<=1
    check('shader dust alpha bounded and no additive grey fog brightening',True)
    for rel in ['JudgementCutEnd.cpp','tools/verify_particles.py','tools/verify_port.py','tools/verify_vfx.py','tools/verify_source_vfx.py','package/JudgementCutEnd/assets/jce_source_texture.hlsl','package/JudgementCutEnd/assets/jce_source_texture.program','package/JudgementCutEnd/assets/jce_source.material']:
        raw=(ROOT/rel).read_bytes();text=raw.decode('utf-8-sig')
        check('encoding Chinese CRLF '+rel,'\n' not in text.replace('\r\n','') and not any(s in text for s in ['\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf']))
        if rel.endswith('.py'):ast.parse(text)
    check('C++ BOM preserved',(ROOT/'JudgementCutEnd.cpp').read_bytes().startswith(b'\xef\xbb\xbf'))
    status=json.loads((ROOT/'docs/task-status.json').read_text('utf8'))
    check('source current development pending user compile',status['source_version']=='2.1.0-dev' and not status['compiled'])
    game=Path(status['installed_directory'])
    check('installed DLL still exact formal2 runtime',digest(game/'JudgementCutEnd.dll')==manifest['dll_sha256'])
    check('installed resources untouched by particle development',all(digest(game/x['path'].removeprefix('mod/'))==x['sha256'] for x in manifest['files'] if x['path'].startswith('mod/')))
    return {'passed':True,'check_count':len(checks),'checks':checks,'native_compile_run':False,'shader_compile_run':False,'game_tested':False,'formal_release':'2.0.0','source_version':'2.1.0-dev','vertices_upper':19828,'indices_upper':47598,'limitations':['数值模型与源码审阅不证明GPU观感或性能','最终需用户Release|x64编译并游戏验收']}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
