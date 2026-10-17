"""淡蓝资源修订静态验证；不编译C++/HLSL，不启动游戏。"""
from pathlib import Path
import hashlib,json,math,re
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(text):
    return '\n'.join(line.strip() for line in re.sub(r'//[^\n]*','',text).splitlines() if line.strip())
def block(text,name):
    start=text.index('material JCE/'+name);end=text.find('\nmaterial JCE/',start+1)
    return text[start:] if end==-1 else text[start:end]
def main():
    evidence=json.loads((ROOT/'docs/pale-blue-20261008.json').read_text('utf8'));checks=[]
    def check(name,result):
        checks.append({'name':name,'passed':bool(result)})
        if not result:raise AssertionError(name)
    before=evidence['before']
    check('entire C++ byte unchanged',digest(ROOT/'JudgementCutEnd.cpp')==before['cpp_sha256'])
    check('DLL has not been recompiled or replaced',digest(ROOT/'package/JudgementCutEnd/JudgementCutEnd.dll')==before['dll_sha256'])
    for source in evidence['sources']:check('original Skyrim NIF identity '+Path(source['file']).name,digest(Path(source['file']))==source['sha256'])
    cut=evidence['sources'][0]
    check('direct original blue particle RGB',any(b['type']=='BSEffectShaderProperty' and b['index']==113 and all(abs(a-b)<1e-6 for a,b in zip(b['base_color'][:3],[.14610514,.62186617,1])) for b in cut['materials']))
    shader=(A/'jce_source_texture.hlsl').read_text('utf8')
    original=before['files']['jce_source_texture.hlsl']['text']
    normalized=shader.replace('uniform float3 colourTint;','').replace('*colourTint','')
    check('shader only RGB colourTint extension; alpha and dust logic unchanged',clean(normalized)==clean(original))
    check('no extra texture sampling or UV modification',shader.count('sourceTexture.Sample(')==1 and 'sourceTexture.Sample(sourceSampler,input.texCoord.xy)' in shader)
    program=(A/'jce_source_texture.program').read_text('utf8')
    normalized=re.sub(r'\s*param_named colourTint float3 1 1 1','',program)
    check('shader missing tint default backward compatible white',clean(normalized)==clean(before['files']['jce_source_texture.program']['text']))
    material=(A/'jce_source.material').read_text('utf8');old=before['files']['jce_source.material']['text']
    normalized=re.sub(r'^\s*param_named colourTint float3[^\n]*\n','',material,flags=re.M)
    for name,palette in evidence['palettes'].items():
        current=block(material,name);previous=block(old,name)
        check('palette RGB transported '+name,'param_named colourTint float3 '+' '.join(str(x) for x in palette['tint']) in current)
        values=palette['tint']
        check('blue ordering and finite bounded tint '+name,all(math.isfinite(x) and 0<x<=1 for x in values) and values[0]<values[1]<values[2])
        oldgain=re.search(r'param_named hdrGain float ([0-9.]+)',previous).group(1)
        part=block(normalized,name)
        replaced=re.sub(r'param_named hdrGain float [0-9.]+','param_named hdrGain float '+oldgain,part)
        check('material only colour and gain changed '+name,clean(replaced)==clean(previous))
        check('HDR gain finite and not increased '+name,0<palette['gain']<=float(oldgain))
    base=(A/'jce.material').read_text('utf8');previous=before['files']['jce.material']['text']
    for name in ['Mist','Refraction']:check('grey atmosphere or scene refraction fully untouched '+name,clean(block(base,name))==clean(block(previous,name)))
    for name,palette in [('Glow','4 4 4 1'),('Glass','1 1 1 1')]:
        normalized=re.sub(r'param_named colour float4 [0-9. ]+','param_named colour float4 '+palette,block(base,name))
        check('base material only RGB gain changed '+name,clean(normalized)==clean(block(previous,name)))
    # 基础单层中性纹理/现有顶点色经过曝光映射仍应偏蓝；这是数学检查，不是Kenshi最终tone-map证明。
    vertices={'SourceBlade':[.72,.85,1],'SourceFeather':[.72,.85,1],'SourceDust':[.65,.68,.73],'SourceFlash':[.78,.87,1],'SourceSpark':[.72,.84,1]}
    for name,palette in evidence['palettes'].items():
        for intensity in [.05,.25,.5,1]:
            rgb=[v*c*palette['gain']*intensity for v,c in zip(vertices[name],palette['tint'])]
            mapped=[x/(1+x) for x in rgb]
            assert all(math.isfinite(x) for x in mapped) and mapped[0]<mapped[1]<mapped[2]
        check('sampled layer remains pale blue over intensity range '+name,True)
    # 其他资产沿用原2.1当前安装或正式2.0内容；本次只修改上述四个颜色资源。
    check('original DDS/clip/path/audio byte unchanged',all(digest(p)==digest(Path(r'D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd\assets')/p.name) for p in A.iterdir() if p.is_file() and p.name not in before['files']))
    for name,h in evidence['after'].items():
        check('recorded resource exact identity '+name,digest(A/name)==h)
        raw=(A/name).read_bytes();text=raw.decode('utf8')
        check('UTF8 no BOM CRLF and readable Chinese '+name,not raw.startswith(b'\xef\xbb\xbf') and '\n' not in text.replace('\r\n','') and not any(s in text for s in ['\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf']))
    status=json.loads((ROOT/'docs/task-status.json').read_text('utf8'))
    check('formal2 ZIP unchanged',digest(Path(status['formal_release']['zip']))==status['formal_release']['zip_sha256'])
    check('2.1 DLL resource contract remains compatible',b'version=2.1.0-dev' in (ROOT/'package/JudgementCutEnd/JudgementCutEnd.dll').read_bytes() and not evidence['dll_recompile_required'])
    return {'passed':True,'check_count':len(checks),'checks':checks,'resource_revision':evidence['resource_revision'],'cpp_changed':False,'dll_recompile_required':False,'native_compile_run':False,'shader_compile_run':False,'game_tested':False}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
