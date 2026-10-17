"""制作1.1.1原创雾/镜片资源；不编译、不安装，不依赖外部环境。"""
from pathlib import Path
import datetime,json,hashlib,math,random,struct
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'package'/'JudgementCutEnd'/'assets'
def write(path,data,role):
    # 资源复现也遵守双备份；纯字节相同则不覆盖，不重复写已有告警/审计。
    if isinstance(data,str):
        assert not any(x in data for x in ('\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf'))
        data=data.replace('\r\n','\n').replace('\n','\r\n').encode('utf8')
    if path.exists() and path.read_bytes()==data:return
    before=path.read_bytes() if path.exists() else None
    stamp='JudgementCutEnd-VFXAssets-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backups=[]
    if before is not None:
        assert len(before)<=20*1024*1024
        if path.suffix in ('.csv','.material','.json','.html'):
            before.decode('utf-8');assert not before.startswith(b'\xef\xbb\xbf')
            assert b'\n' not in before.replace(b'\r\n',b'')
        for base in (Path(r'D:\CodexBackups'),Path(r'E:\AIWorkSpace\_backups')):
            backup=base/stamp/path.drive.rstrip(':')/Path(*path.parts[1:])
            backup.parent.mkdir(parents=True,exist_ok=True)
            with backup.open('xb') as f:f.write(before)
            assert backup.read_bytes()==before;backups.append(str(backup))
    with path.open('wb' if before is not None else 'xb') as f:f.write(data)
    assert path.read_bytes()==data
    report={'File':str(path),'Role':role,'Code location':'完整特效资源','Before':'已双备份' if before is not None else '不存在','Changes':'确定性重现1.1.1特效资产','Reasons':'灰色整体气氛与瞬态空间裂光，不改原动画/音频','After':'资源已生成','Impact':'仅JudgementCutEnd分发包','Validation':'逐字节读回一致，文本UTF-8/CRLF/中文扫描','Safety':{'backups':backups,'encoding':'文本UTF-8无BOM/CRLF；TGA保持二进制'},'Unresolved':'需用户编译/实机验证'}
    audit=ROOT/'docs'/stamp;audit.mkdir()
    with (audit/'file-report.json').open('xb') as f:f.write((json.dumps(report,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf8'))
    print(json.dumps({'file':str(path),'report':str(audit/'file-report.json')},ensure_ascii=False))
def noise(x,y,seed):
    # 稳定整点哈希，不依赖进程随机种子；雾纹理按多频率叠加，不做逐帧随机闪烁。
    def h(a,b):
        n=(a*374761393+b*668265263+seed*1442695041)&0xffffffff
        n=((n^(n>>13))*1274126177)&0xffffffff
        return ((n^(n>>16))&65535)/65535
    i,j=math.floor(x),math.floor(y);u,v=x-i,y-j;u=u*u*(3-2*u);v=v*v*(3-2*v)
    return (h(i,j)*(1-u)+h(i+1,j)*u)*(1-v)+(h(i,j+1)*(1-u)+h(i+1,j+1)*u)*v
def tga(w,h,pixel):
    body=bytearray()
    for y in range(h):
        for x in range(w):body.extend(pixel(x/(w-1),y/(h-1)))
    return struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,w,h,32,0x28)+body
def main():
    rows=[[float(x) for x in l.split()] for l in (OUT/'slashes.csv').read_text('utf8').splitlines()[1:]]
    assert len(rows)==96
    # 保留全部位置/方向/长度与96次伤害合同；将出痕铺满斩击段，让16个掠影有可见演出时间。
    for i,s in enumerate(rows):s[7]=2.35+2.2*i/95
    write(OUT/'slashes.csv','JCESLASH 1 96\n'+'\n'.join(' '.join('%.7f'%x for x in s) for s in rows)+'\n','96裂痕时序，16幻影共享对应路径')
    def mist(u,v):
        # 中性灰RGB保持均匀；软边与噪声放Alpha，供普通透明混合，不再发光成蓝色粒子。
        r=math.hypot((u-.5)*2,(v-.5)*2)
        fall=max(0,1-r*r)**1.35
        n=sum(noise(u*f,v*f,k+13)*w for k,(f,w) in enumerate(((3,.5),(7,.3),(15,.15),(31,.05))))
        alpha=int(255*fall*(.60+.40*n))
        return (255,255,255,alpha)
    write(OUT/'jce_mist.tga',tga(128,128,mist),'中性灰雾Alpha噪声纹理，软边不发蓝光')
    def glass(u,v):
        # 不强调玻璃边框；高光穿过三角片时只有柔和、断续的光学片区。
        r=math.hypot((u-.5)*2,(v-.5)*2)
        diagonal=math.exp(-((u+v-1.0)*7)**2)
        alpha=int(255*max(0,1-r*r)*(.25+.75*diagonal))
        return(255,255,255,alpha)
    write(OUT/'jce_glass.tga',tga(64,64,glass),'软边瞬态空间高光纹理，无镜片边框')
    rng=random.Random(1110);triangles=[]
    # 每道真实斩痕关联两个独立斜向片区；不再拼成48个四边形镜子。
    for s in rows:
        direction=s[3:6];side=[-direction[2],0,direction[0]]
        n=math.sqrt(sum(x*x for x in side)) or 1;side=[x/n for x in side]
        for echo in range(2):
            centre=[s[k]+direction[k]*s[6]*rng.uniform(-.35,.35)+side[k]*(echo-.5)*.02 for k in range(3)]
            w=rng.uniform(.045,.11);h=rng.uniform(.05,.13)
            a=[centre[k]-side[k]*w for k in range(3)]
            b=[centre[k]+side[k]*w+direction[k]*.05 for k in range(3)]
            c=[centre[k]+side[k]*w*.15-direction[k]*.03+(h if k==1 else 0) for k in range(3)]
            triangles.append([*a,*b,*c,s[7]])
    write(OUT/'jce_shards.csv','JCESHARDS 1 192\n'+'\n'.join(' '.join('%.7f'%x for x in t) for t in triangles)+'\n','96道斩痕关联192个独立瞬态光区，固定空间坐标，无下落')
    material=(OUT/'jce.material').read_text('utf8')
    if '// JCE_VFX110_BEGIN' in material:material=material.split('// JCE_VFX110_BEGIN')[0].rstrip()+'\n'
    material+='''\n// JCE_VFX110_BEGIN：三个独立材质段：灰雾Alpha混合、刀痕/空间裂光加法混合；不修改公共着色器。
material JCE/Mist
{
    technique
    {
        pass
        {
            vertex_program_ref Basic_Coloured_Texture_VP {}
            fragment_program_ref Basic_Texture_FP { param_named colour float4 1 1 1 1 }
            lighting off
            depth_write off
            depth_check on
            cull_hardware none
            scene_blend alpha_blend
            texture_unit { texture jce_mist.tga tex_address_mode clamp colour_op modulate }
        }
    }
}
material JCE/Glass
{
    technique
    {
        pass
        {
            vertex_program_ref Basic_Coloured_Texture_VP {}
            fragment_program_ref Basic_Texture_FP { param_named colour float4 1 1 1 1 }
            lighting off
            depth_write off
            depth_check on
            cull_hardware none
            // 乘源Alpha再叠加光，确保零Alpha帧没有高光；纯add会忽略顶点Alpha。
            scene_blend src_alpha one
            texture_unit { texture jce_glass.tga tex_address_mode clamp colour_op modulate }
        }
    }
}
'''
    # OGRE脚本按换行识别属性，不能将多个texture_unit属性放同一行。
    material=material.replace('fragment_program_ref Basic_Texture_FP { param_named colour float4 1 1 1 1 }','fragment_program_ref Basic_Texture_FP\n            {\n                param_named colour float4 1 1 1 1\n            }').replace('fragment_program_ref Basic_Texture_FP { param_named colour float4 1 1 1 1 }','fragment_program_ref Basic_Texture_FP\n            {\n                param_named colour float4 1 1 1 1\n            }')
    for name in ('mist','glass'):
        material=material.replace('texture_unit { texture jce_'+name+'.tga tex_address_mode clamp colour_op modulate }','texture_unit\n            {\n                texture jce_'+name+'.tga\n                tex_address_mode clamp\n                colour_op modulate\n            }')
    write(OUT/'jce.material',material,'保留Glow，新建Mist/Glass独立材质')
    write(OUT/'vfx-1.1.1.json',json.dumps({'version':'1.1.1-dev','slashes':96,'slash_echoes':6,'phantom_paths':16,'phantom_echoes':4,'mist_clouds':168,'motes':0,'hemisphere_shell_quads':576,'physical_mirrors':False,'falling_fragments':False,'spatial_facets':192,'shards':192,'sections':['JCE/Glow','JCE/Mist','JCE/Glass'],'damage_changed':False,'assets':'原创确定性制作；不是DMC原始模型/着色器资源'},ensure_ascii=False,indent=2)+'\n','特效资产/运行预算清单')
    # 预览是资源的消费者：发布CSV后按已舍入的实际数值同步两份载体，避免重跑制作工具后时序分叉。
    scene=ROOT/'preview'/'scene.json';preview=ROOT/'preview'/'index.html'
    data=json.loads(scene.read_text('utf8'))
    data['slashes']=[[float(x) for x in line.split()] for line in (OUT/'slashes.csv').read_text('utf8').splitlines()[1:]]
    data['shards']=[[float(x) for x in line.split()] for line in (OUT/'jce_shards.csv').read_text('utf8').splitlines()[1:]]
    payload=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    write(scene,payload+'\n','同源预览数据，保留原骨骼轨道并同步特效')
    text=preview.read_text('utf8');lines=text.splitlines()
    assert sum(line.startswith('const DATA=') for line in lines)==1
    lines=[('const DATA='+payload+';') if line.startswith('const DATA=') else line for line in lines]
    write(preview,'\n'.join(lines)+'\n','保持预览渲染逻辑，同步内嵌特效数据')

if __name__=='__main__':main()
