"""从用户本机ap05资源移植纹理和关联曲线；不编译、不安装、不改源模组。"""
from pathlib import Path
import json,hashlib,math
from PIL import Image
import inspect_skyrim_vfx as nif
ROOT=Path(__file__).resolve().parents[1]
SOURCE=nif.SOURCE
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract_curve(file,target):
    parsed=nif.parse(SOURCE/'Meshes/effects/AP05'/file)
    blocks={b['index']:b for b in parsed['parsed_blocks']}
    matches=[]
    # 只使用sequence中实际绑定到有效材质target的Alpha控制器，拒绝孤立/废弃关键帧。
    for seq in blocks.values():
        if seq['type']!='NiControllerSequence':continue
        for c in seq['controlled_blocks']:
            ctl=blocks.get(c['controller'],{})
            if ctl.get('type')!='BSEffectShaderPropertyFloatController' or ctl['target']!=target or ctl['variable']!=5:continue
            it=blocks[c['interpolator']];data=blocks[it['data']]
            assert data['type']=='NiFloatData' and data['interpolation'] in (1,2)
            assert 0<seq['frequency']<=4 and ctl['frequency']==1 and ctl['phase']==0
            matches.append({'nif':file,'nif_sha256':parsed['sha256'],'sequence':seq['index'],
                'controller':ctl['index'],'target':target,'node':c['node'],'frequency':seq['frequency'],
                'interpolator':it['index'],'data':data['index'],'interpolation':data['interpolation'],'keys':data['keys']})
    assert len(matches)==1,(file,target)
    return matches[0]
def evaluate(c,t):
    # NifSkope官方插值定义：区间左点Backward和右点Forward是归一化区间切线，不再乘秒长。
    # 小于0或超出最后键时归零，属于本插件有限演出生命周期；原键和切线逐项保留。
    keys=c['keys'];t*=c['frequency']
    if t<0 or t>keys[-1]['time']:return 0.
    if t<=keys[0]['time']:return keys[0]['value']
    for a,b in zip(keys,keys[1:]):
        if t<=b['time']:
            u=(t-a['time'])/(b['time']-a['time'])
            if c['interpolation']==1:return a['value']+(b['value']-a['value'])*u
            return (2*u**3-3*u*u+1)*a['value']+(-2*u**3+3*u*u)*b['value']+(u**3-2*u*u+u)*a.get('backward',0)+(u**3-u*u)*b.get('forward',0)
    return keys[-1]['value']
def main():
    # 使用项目既有安全写入器：UTF-8/CRLF与中文检查、每个覆盖文件双备份、逐文件报告。
    source=(ROOT/'tools/author_port.py').read_text('utf8').split('"""')[0]
    source=source.replace("STAMP='JudgementCutEnd-AssetPort-'","STAMP='JudgementCutEnd-SkyrimVFXAssets-'")
    source=source.replace('用户授权实际HKX重定向、人物网格残影和空间裂光升级','用户授权本机原模组特效移植，保留来源哈希')
    source=source.replace('禁止代编译；新动画及渲染需用户编译后游戏验收','新C++消费端须用户编译Release|x64，实机未验证')
    scope={};exec(source,scope);put=scope['put']
    specs=[('screen_flash','JCE030ScreenFx.nif',107),('screen_veil','JCE030ScreenFx.nif',110),
        ('finish_glow','JCE040Finish.nif',108),('finish_halo','JCE040Finish.nif',120),
        ('fracture_alpha','JCE030CutAllActi.nif',188),('cut_flash','JCE030CutAllActi.nif',106)]
    curves=[dict(name=name,**extract_curve(file,target)) for name,file,target in specs]
    text='JCEFXCURVES 1 6\n'
    for c in curves:
        text+='CURVE %s %d %.9g %d\n'%(c['name'],c['interpolation'],c['frequency'],len(c['keys']))
        for k in c['keys']:text+='KEY '+' '.join('%.9g'%k.get(n,0) for n in ('time','value','backward','forward'))+'\n'
    put('package/JudgementCutEnd/assets/jce_source_curves.csv',text,'运行时源曲线','6条原Alpha曲线及归一化切线','按实际引用导出，禁止按文件中出现顺序猜测用途')
    textures=[]
    for local,ref in [('jce_source_blade09.dds','4905/blade_effect09.dds'),
        ('jce_source_blade08.dds','4905/blade_effect08.dds'),
        ('jce_source_dust.dds','fxsmokepuffanim01dark.dds'),
        ('jce_source_flash.dds','FXGlowSpotLinear.dds'),
        ('jce_source_spark.dds','fxspark.dds')]:
        p=SOURCE/'textures/effects/zjc'/ref;b=p.read_bytes()
        with Image.open(p) as im:size=im.size;mode=im.mode
        assert b[:4]==b'DDS ' and max(size)<=2048
        put('package/JudgementCutEnd/assets/'+local,b,'本机源纹理','只读源DDS逐字节复制','保留原像素、压缩格式和Alpha，不把原图替换成随机生成纹理')
        textures.append({'source':str(p),'source_sha256':digest(p),'output':local,'output_sha256':hashlib.sha256(b).hexdigest(),'dimensions':size,'mode':mode})
    program="""// 原纹理专用shader；只在本插件资源组使用，不覆盖游戏Basic_*程序。
fragment_program JCE/SourceTexture_FP hlsl
{
    source jce_source_texture.hlsl
    entry_point jce_source_texture_fp
    target ps_4_0
    default_params
    {
        param_named hdrGain float 1
        param_named grayscale float 0
    }
}
"""
    shader="""// 同原有Basic_Coloured_Texture_VP接口；HDR增益独立于归一化顶点颜色。
// 透明度同时乘原DDS Alpha与演出曲线，防止演出前后零Alpha仍发光。
Texture2D sourceTexture : register(t0);
SamplerState sourceSampler : register(s0);
uniform float hdrGain;
uniform float grayscale;
struct JCE_SOURCE_FRAGMENT {float4 pos:SV_Position;float4 colour:COLOR;float4 texCoord:TEXCOORD0;};
float4 jce_source_texture_fp(JCE_SOURCE_FRAGMENT input):SV_Target {
    float4 source=sourceTexture.Sample(sourceSampler,input.texCoord.xy);
    float mask=dot(source.rgb,float3(.2126,.7152,.0722));
    float3 colour=lerp(source.rgb,mask.xxx,saturate(grayscale));
    return float4(colour*input.colour.rgb*hdrGain,source.a*input.colour.a);
}
"""
    put('package/JudgementCutEnd/assets/jce_source_texture.program',program,'专用shader声明','JCE/SourceTexture_FP','独立HDR增益，不改变游戏公用程序')
    put('package/JudgementCutEnd/assets/jce_source_texture.hlsl',shader,'专用源纹理shader','DX11像素输入合同','同时保留源纹理Alpha和顶点Alpha，按材质选择中性灰转译')
    mat=''
    for name,tex,gain,gray,blend in [('SourceBlade','blade09',3,0,'src_alpha one'),
        ('SourceFeather','blade08',1.6,0,'src_alpha one'),('SourceDust','dust',1,0,'alpha_blend'),
        ('SourceFlash','flash',3,0,'src_alpha one'),('SourceSpark','spark',4,1,'src_alpha one')]:
        mat+=f"""// 本机ap05原纹理层；亮度按Kenshi HDR适配，非照搬Skyrim数值。
material JCE/{name}
{{
    technique
    {{
        pass
        {{
            vertex_program_ref Basic_Coloured_Texture_VP {{}}
            fragment_program_ref JCE/SourceTexture_FP
            {{
                param_named hdrGain float {gain}
                param_named grayscale float {gray}
            }}
            lighting off
            depth_write off
            depth_check on
            cull_hardware none
            scene_blend {blend}
            texture_unit
            {{
                texture jce_source_{tex}.dds
                tex_address_mode clamp
                filtering bilinear
            }}
        }}
    }}
}}
"""
    put('package/JudgementCutEnd/assets/jce_source.material',mat,'五个独立材质层','刀光、残迹、烟尘、闪光、光屑','保留灰色整体半球，在其内部按原纹理叠加空间效果')
    report={'version':'1.2.1-dev','textures':textures,'curves':curves,'atlas':{'texture':'jce_source_dust.dds','columns':8,'rows':8,'source':'原纹理64格可视核对','fps_adapter':20},
        'event_mapping':{'cut_source':2.334,'cut_runtime':2.35,'finish_source':5.134,'finish_runtime':5.15,'playback_rate':3},
        'render_layers':9,'base_layers_preserved':4,'new_layers':['SourceBlade','SourceFeather','SourceDust','SourceFlash','SourceSpark'],
        'runtime_dll_required':'1.2.1-dev','local_test_assets_only':True,
        'limitations':['原NIF几何/发射器模拟未完整移植；用固定96路径和48雾片适配',
            '烟尘atlas播放速率与HDR增益为Kenshi适配参数，不声称与Skyrim一致',
            'Spark采用灰度强度加蓝白色，尚未完整实现原palette着色语义',
            '原BSLightingShader屏幕效果仍以本插件既有空间HDR副本折射实现，无全屏接管',
            '不代编译；不可把旧DLL与1.2.1资源验收状态混淆'],
        'format_reference':nif.SCHEMA,'interpolation_reference':'https://github.com/niftools/nifskope/blob/develop/src/gl/glcontroller.cpp',
        'credits':'原资源：ap05、elysees等；原模组含Bethesda/FO4纹理。仅本机测试，不声明可公开再分发。'}
    put('package/JudgementCutEnd/assets/vfx-1.2.1.json',json.dumps(report,ensure_ascii=False,indent=2)+'\n','移植来源清单','源哈希、curve引用及明确适配项','区分精确复制、准确曲线读取和Kenshi适配行为')
    return report
if __name__=='__main__':main()
