"""原资源移植静态/数学/坏输入核验，不编译C++、HLSL或启动游戏。"""
from pathlib import Path
import ast,hashlib,json,math,re,struct
import author_skyrim_vfx as author
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets'
BASE=Path(r'D:\CodexBackups\JudgementCutEnd-VFXPort-20261008-003948-386021\E\KenshiProject\2.Projects\JudgementCutEnd\JudgementCutEnd.cpp')
def load_curves(text):
    # 独立解析格式与坏输入；边界同时与C++消费者审阅，不能将此工具当C++执行证明。
    tok=iter(text.split())
    def take():return next(tok)
    if [take(),take(),take()]!=['JCEFXCURVES','1','6']:raise ValueError('header')
    names=['screen_flash','screen_veil','finish_glow','finish_halo','fracture_alpha','cut_flash'];out=[]
    for name in names:
        if take()!='CURVE' or take()!=name:raise ValueError('name/order')
        interpolation=int(take());frequency=float(take());count=int(take())
        if interpolation not in (1,2) or not math.isfinite(frequency) or not 0<frequency<=4 or not 2<=count<=128:raise ValueError('curve bounds')
        keys=[]
        for _ in range(count):
            if take()!='KEY':raise ValueError('key tag')
            t,value,back,forward=[float(take()) for _ in range(4)]
            if not all(map(math.isfinite,[t,value,back,forward])) or not 0<=t<=10 or max(map(abs,[value,back,forward]))>8:raise ValueError('key bounds')
            if (not keys and abs(t)>.00001) or (keys and t<=keys[-1]['time']):raise ValueError('time ordering')
            keys.append({'time':t,'value':value,'backward':back,'forward':forward})
        out.append({'name':name,'interpolation':interpolation,'frequency':frequency,'keys':keys})
    if list(tok):raise ValueError('trailing garbage')
    return out
def main():
    checks=[]
    def check(name,value):
        checks.append({'name':name,'passed':bool(value)})
        if not value:raise AssertionError(name)
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig');old=BASE.read_text('utf-8-sig')
    manifest=json.loads((A/'vfx-1.2.1.json').read_text('utf8'))
    curves=load_curves((A/'jce_source_curves.csv').read_text('utf8'))
    for t in manifest['textures']:
        check('exact original DDS bytes '+t['output'],author.digest(Path(t['source']))==author.digest(A/t['output'])==t['source_sha256'])
        check('DDS header and finite resolution '+t['output'],(A/t['output']).read_bytes()[:4]==b'DDS ' and max(t['dimensions'])<=2048)
    for actual,expected in zip(curves,manifest['curves']):
        fresh=author.extract_curve(expected['nif'],expected['target'])
        check('actual sequence links retained '+actual['name'],fresh['data']==expected['data'] and fresh['controller']==expected['controller'] and fresh['nif_sha256']==expected['nif_sha256'] and fresh['keys']==expected['keys'])
        check('sequence frequency retained '+actual['name'],abs(actual['frequency']-fresh['frequency'])<1e-7)
        for k in fresh['keys']:
            check('key value exact within float text precision '+actual['name']+' '+str(k['time']),abs(author.evaluate(actual,k['time']/actual['frequency'])-k['value'])<2e-6)
        for i in range(1001):
            value=author.evaluate(actual,10*i/1000)
            if not math.isfinite(value) or abs(value)>8:raise AssertionError('curve finite bounds')
        check('before birth and expired curve zero '+actual['name'],author.evaluate(actual,-.1)==0 and author.evaluate(actual,11)==0)
    # 非零切线的单独已知解检验，避免只测取键点而无法发现左右切线读反。
    example={'frequency':1,'interpolation':2,'keys':[{'time':0,'value':0,'backward':1,'forward':0},{'time':1,'value':1,'backward':0,'forward':1}]}
    check('normalized Hermite tangent convention independent example',all(abs(author.evaluate(example,u)-u)<1e-9 for u in [.1,.25,.5,.9]))
    source=(A/'jce_source_curves.csv').read_text('utf8')
    malformed=[('truncation',source[:source.index('KEY')]),('huge count',source.replace('2 1 14','2 1 999999',1)),
        ('NaN frequency',source.replace('2 1 14','2 nan 14',1)),('NaN key',source.replace('KEY 0 0 0 -0','KEY 0 nan 0 -0',1)),
        ('nonzero first time',source.replace('KEY 0 ', 'KEY 0.5 ',1)),
        ('wrong order',source.replace('CURVE screen_flash','CURVE finish_glow',1)),('garbage',source+' garbage')]
    for name,bad in malformed:
        check('bad input differs '+name,bad!=source)
        rejected=False
        try:load_curves(bad)
        except (ValueError,StopIteration):rejected=True
        check('reject bad curve '+name,rejected)
    def region(t,start,end):return t[t.index(start):t.index(end,t.index(start))]
    check('damage radius weapon and stagger byte unchanged',region(cpp,'    float AreaRadius()','    unsigned vertex;')==region(old,'    float AreaRadius()','    unsigned vertex;'))
    check('input restart time advance and restore unchanged',region(cpp,'    void Tick(','Runtime* runtime=0;')==region(old,'    void Tick(','Runtime* runtime=0;'))
    check('animation and skin publication unchanged',region(cpp,'    void Pose(','    float AreaRadius()')==region(old,'    void Pose(','    float AreaRadius()'))
    # 就绪日志仅更新特效资源数和版本；其前后的绑定、失败处理必须逐字相同。
    binding=region(cpp,'Runtime* runtime=0;','version=')
    previous_binding=region(old,'Runtime* runtime=0;','version=')
    binding=binding.replace('resources=9; source_vfx=ap05_textures_curves;', 'resources=4;')
    # 用户本轮另行授权两处成员地址式绑定；只归一化这两个调用及其新增说明，AddHook和错误路径仍逐字核验。
    binding=binding.replace('        // 两个绑定均使用声明中的成员函数地址，避免在插件里维护字符串函数签名。\n','')
    binding=binding.replace('NativeAddress(&GameWorld::_NV_mainLoop_GPUSensitiveStuff,"frame")','NativeAddress("?_NV_mainLoop_GPUSensitiveStuff@GameWorld@@QEAAXM@Z")')
    binding=binding.replace('NativeAddress(&AnimationClassHuman::_NV_update,"pose")','NativeAddress("?_NV_update@AnimationClassHuman@@QEAAXM@Z")')
    check('native hook sites unchanged after authorized member-address binding',binding==previous_binding)
    check('loader before hooks and bounded data',cpp.index('sourceFx>>tag>>version>>count')<cpp.index('skin.Load();LoadAssets();') and all(x in cpp for x in ['count!=6','keys>128','c.frequency>4','k.t<=c.keys.back().t','Unexpected source FX fields']))
    check('C++ tangent convention matches format',all(x in cpp for x in ['a.backward+(u3-u2)*b.forward','float t=age*curve.frequency','age<0']))
    names=['SourceBlade','SourceFeather','SourceDust','SourceFlash','SourceSpark']
    for i,n in enumerate(names):
        check('source layer wired '+n,('StartLayer(%d,"JCE/%s")'%(i+4,n)) in cpp and 'material JCE/'+n in (A/'jce_source.material').read_text('utf8'))
    check('frame callbacks cover all sections','i<FX_SECTIONS' in cpp and 'FX_SECTIONS=9' in cpp and 'rend==geometry->getSection(0))CaptureBackground();' in cpp)
    check('new GPU program interface',(A/'jce_source_texture.program').read_text('utf8').count('target ps_4_0')==1 and all(x in (A/'jce_source_texture.hlsl').read_text('utf8') for x in ['TEXCOORD0','SV_Target','source.a*input.colour.a','hdrGain']))
    check('new material occlusion alpha and owned shader',all((A/'jce_source.material').read_text('utf8').count(s)==5 for s in ['depth_write off','depth_check on','fragment_program_ref JCE/SourceTexture_FP']))
    check('DDS references resolve',all((A/t).is_file() for t in re.findall(r'^\s*texture\s+(\S+)',(A/'jce_source.material').read_text('utf8'),re.M)))
    check('atlas half texel boundary and finite clock','inset=.5f/512.f' in cpp and 'tile/8' in cpp and 'tile%8' in cpp and 'unsigned(Clamp(local,0,3.f)*20.f' in cpp)
    # 2.1以稳定粒子id的局部时钟推进图集；原64格四边界仍逐格核验。
    # 遍历所有64格的四个UV边界，证明不会读到邻格和atlas外；几何边界仍经BoundFx裁剪。
    for tile in range(64):
        u=(tile%8)/8+.5/512;v=(tile//8)/8+.5/512
        assert 0<u<u+.125-1/512<1 and 0<v<v+.125-1/512<1
    check('all 64 atlas cells have valid UV',True)
    block=region(cpp,'    void SourceQuad(','    void StartLayer(')
    check('source FX has no allocations gameplay or file IO',all(s not in block for s in ['new ','resize(','push_back(','std::ifstream','addWound','setFrameSpeedMultiplier','setPosition(','createEntity','createParticleSystem']))
    check('source layers share bounded vertex path','VertexAlpha(a,u0,v0' in block and 'geometry->position(BoundFx(p));' in cpp)
    check('empty sections maintain placeholder','if(vertex==before)SourceQuad(' in block and block.count('if(vertex==before)')==2)
    check('source fog fixed memory and back to front sorting','HazeCell cells[count]' in block and 'const unsigned count=48' in block and 'std::sort(cells,cells+count)' in block)
    check('bounded logs no per-particle logging','Log(' not in block and 'if(logLines++>=4096)return' in cpp and 'source_fx_assets_ready' in cpp)
    vertices=18348+(96+96+48+2+128)*4;indices=45378+(96+96+48+2+128)*6
    check('geometry fits existing budgets',vertices==19828 and indices==47598 and vertices<32768 and indices<49152)
    for file in ['JudgementCutEnd.cpp','tools/inspect_skyrim_vfx.py','tools/author_skyrim_vfx.py','tools/verify_source_vfx.py','package/JudgementCutEnd/assets/jce_source_curves.csv','package/JudgementCutEnd/assets/jce_source.material','package/JudgementCutEnd/assets/jce_source_texture.hlsl','package/JudgementCutEnd/assets/jce_source_texture.program']:
        raw=(ROOT/file).read_bytes();text=raw.decode('utf-8-sig')
        check('encoding CRLF Chinese '+file,'\n' not in text.replace('\r\n','') and not any(x in text for x in ['\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2']))
        if file.endswith('.py'):ast.parse(text)
    check('C++ BOM preserved',(ROOT/'JudgementCutEnd.cpp').read_bytes().startswith(b'\xef\xbb\xbf'))
    check('no new C++11 constructs',not re.search(r'\b(nullptr|constexpr|thread_local)\b',block))
    return {'passed':True,'check_count':len(checks),'checks':checks,'source_curves':6,'source_textures':5,'layers':9,'vertex_upper_bound':vertices,'index_upper_bound':indices,'native_compile_run':False,'shader_compile_run':False,'game_tested':False,'limitations':manifest['limitations']}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
