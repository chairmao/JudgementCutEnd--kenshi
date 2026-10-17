from pathlib import Path
import json,hashlib,datetime,re,math,struct
ROOT=Path(r'E:\KenshiProject\2.Projects\JudgementCutEnd')
ASSETS=ROOT/'package/JudgementCutEnd/assets'
STAMP='JudgementCutEnd-AssetPort-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
AUDIT=ROOT/'docs'/STAMP
AUDIT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(rel,data,role,where,changes):
    p=ROOT/rel;old=p.read_bytes() if p.exists() else None
    backups=[];enc='binary'
    if isinstance(data,str):
        bom=old is not None and old.startswith(b'\xef\xbb\xbf')
        if old is not None:
            t=old.decode('utf-8-sig');assert '\n' not in t.replace('\r\n',''),str(p)
        data=data.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8')
        if bom:data=b'\xef\xbb\xbf'+data
        t=data.decode('utf-8-sig')
        assert not any(s in t for s in ['\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf']),str(p)
        enc='UTF-8 '+('BOM' if bom else 'no BOM')+' / CRLF'
    if old==data:return
    if old is not None:
        assert len(old)<=20*1024*1024
        for base in [Path(r'D:\CodexBackups'),Path(r'E:\AIWorkSpace\_backups')]:
            b=base/STAMP/p.drive[0]/Path(*p.parts[1:]);b.parent.mkdir(parents=True,exist_ok=True)
            with b.open('xb') as f:f.write(old)
            assert b.read_bytes()==old
            backups.append(str(b))
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('wb' if old is not None else 'xb') as f:f.write(data)
    assert p.read_bytes()==data
    report={'File':str(p),'Role':role,'Code location':where,'Before':hashlib.sha256(old).hexdigest() if old is not None else 'absent','Changes':changes,'Reasons':'用户授权实际HKX重定向、人物网格残影和空间裂光升级','After':sha(p),'Impact':'仅JudgementCutEnd项目与自有资源；保持350范围、96次伤害、U覆盖重施放与时间恢复','Validation':'即时字节读回；编码/中文/换行扫描；后续集中静态核验','Safety':{'backups':backups,'encoding':enc},'Unresolved':'禁止代编译；新动画及渲染需用户编译后游戏验收'}
    with (AUDIT/(str(len(list(AUDIT.glob('*.json')))).zfill(3)+'-'+p.name+'.json')).open('xb') as f:f.write((json.dumps(report,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8'))
    print(json.dumps(report,ensure_ascii=False))

"""将 ap05 的真实 Skyrim SE HKX 动作重定向至 Kenshi；不编译 DLL、不写游戏目录。"""
import argparse,sys,importlib.util
from pathlib import Path
# 工作域解码器是 PyNifly GPL-3.0 源码，不要求 Blender 或机器全局安装。
def main(decoder):
    # 已核验的解码器按SHA固定，防止远端main变动造成无法复现的静默改写。
    expected={'anim_fo4.py': '9b46fb0dfe48710f0333ec89a50019d79592063b40844d6175961d8065257d67', 'anim_skyrim.py': '8f308511882dd4aeb0d47b7e9698cce9ab4ad238eae99bdd47bec2e08139266a'}
    assert all(sha(decoder/name)==h for name,h in expected.items()), 'Decoder checksum mismatch'
    sys.path.insert(0,str(decoder))
    from anim_skyrim import load_skyrim_animation,load_skyrim_skeleton
    spec=importlib.util.spec_from_file_location('jce_math',ROOT/'tools/author_assets.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    animPath=m.SOURCE/'Meshes/actors/character/animations/dynamicanimationreplacer/_CustomConditions/10004905/combatidlea.hkx'
    skelPath=Path(r'E:\skyrimspecialedition\mods\XP32 Maximum Skeleton Special Extended\meshes\actors\character\character assets\skeleton.hkx')
    # 解码器校验版本/压缩类型。必须显式匹配骨名；242轨道中只用标准人形，忽略发饰/衣物扩展骨。
    a=load_skyrim_animation(str(animPath));s=load_skyrim_skeleton(str(skelPath))
    assert a.blend_hint==0 and a.num_frames==211 and abs(a.duration-7)<.001
    assert len(a.bone_names)==a.num_tracks==len(a.tracks)
    names={n:i for i,n in enumerate(a.bone_names)};sn={n:i for i,n in enumerate(s.bones)}
    b=m.skeleton(m.GAME/'data/character/meshes/male_skeleton/male_skeleton.skeleton')
    female=m.skeleton(m.GAME/'data/character/meshes/female_skeleton/female_skeleton.skeleton')
    bn={x['name']:x['id'] for x in b};rest=m.world(b,[x['orientation'] for x in b])
    mapping={'Bip01':'NPC COM [COM ]','Bip01 Pelvis':'NPC Pelvis [Pelv]',
      'Bip01 Spine':'NPC Spine [Spn0]','Bip01 Spine1':'NPC Spine1 [Spn1]','Bip01 Spine2':'NPC Spine2 [Spn2]',
      'Bip01 Neck':'NPC Neck [Neck]','Bip01 Head':'NPC Head [Head]'}
    for side in ['L','R']:
        for dst,src in [('Thigh','Thigh [%sThg]'),('Calf','Calf [%sClf]'),('Foot','Foot [%sft ]'),
          ('Toe0','Toe0 [%sToe]'),('Clavicle','Clavicle [%sClv]'),('UpperArm','UpperArm [%sUar]'),
          ('Forearm','Forearm [%sLar]'),('Hand','Hand [%sHnd]')]:
            mapping['Bip01 '+side+' '+dst]='NPC '+side+' '+(src%side)
    # 只要求控制的23根标准骨存在，不要求装饰/牙齿骨名或顺序相同。
    assert set(mapping).issubset({x['name'] for x in female})
    assert len(mapping)==23 and all(n in sn and n in names for n in mapping.values())
    # 只使用真实 binding/annotation 对应的标准骨。该 HKX binding 是空表，注释轨道给出每条骨名。
    assert not a.track_to_bone_indices
    def qw(x):return m.qnorm((x[3],*x[:3]))
    sr=[]
    for i,p in enumerate(s.reference_pose):
        q=qw(p.rotation);pos=tuple(p.translation);parent=s.parents[i]
        if parent>=0:pp,pq=sr[parent];q=m.qmul(pq,q);pos=m.vadd(pp,m.rotate(pq,pos))
        sr.append((pos,q))
    # 两套骨架不仅向上轴不同：Skyrim左股骨位于-X，Kenshi左股骨位于+X。
    # 先把Z向上转为Y向上，再绕Y旋转180度，同时对齐左右与前向；仍是纯旋转，禁止镜像。
    # 只转-90度X会把左右颠倒，并使弯腰、颈部和手腕的旋转平面落到错误一侧。
    C=m.qmul(m.axis((0,1,0),180),m.axis((1,0,0),-90))
    ci=m.qi(C)
    sourceLeft=m.rotate(C,m.vsub(sr[sn[mapping['Bip01 L Thigh']]][0],sr[sn[mapping['Bip01 R Thigh']]][0]))
    targetLeft=m.vsub(rest[bn['Bip01 L Thigh']][0],rest[bn['Bip01 R Thigh']][0])
    assert m.dot(m.unit(sourceLeft),m.unit(targetLeft))>.99, 'Anatomical left/right mismatch'
    assert m.dot(m.rotate(C,(0,0,1)),(0,1,0))>.99999, 'Up axis mismatch'
    # 只沿显式的解剖链校准主轴，不能用序列里的第一个子骨骼：Spine2先列出的
    # 子骨是L Clavicle而非Neck，会把胸部主轴错误扭向肩膀，继而由颈/头补偿这个错误。
    # 多分支骨盆、末端头/手/脚趾保留自身滚转基准；不沿装饰骨、下颌或道具重新定向。
    aim={'Bip01 Spine':'Bip01 Spine1','Bip01 Spine1':'Bip01 Spine2',
         'Bip01 Spine2':'Bip01 Neck','Bip01 Neck':'Bip01 Head'}
    for side in ['L','R']:
        for aa,bb in [('Thigh','Calf'),('Calf','Foot'),('Foot','Toe0'),
                      ('Clavicle','UpperArm'),('UpperArm','Forearm'),('Forearm','Hand')]:
            aim['Bip01 '+side+' '+aa]='Bip01 '+side+' '+bb
    primary={i:None for i in range(len(b))}
    for aa,bb in aim.items():
        assert b[bn[bb]]['parent']==bn[aa], 'Unexpected target hierarchy'
        primary[bn[aa]]=bn[bb]
    offsets={}
    for dst,src in mapping.items():
        i=bn[dst];j=sn[src];child=primary[i];target=rest[i][1]
        if child is not None and b[child]['name'] in mapping and i>1:
            sj=sn[mapping[b[child]['name']]]
            # 对齐解剖主轴，同时保留目标骨的滚转基准；不能直接拷贝两种骨架局部四元数。
            td=m.vsub(rest[child][0],rest[i][0]);sd=m.rotate(C,m.vsub(sr[sj][0],sr[j][0]))
            target=m.qmul(m.from_to(td,sd),target)
        offsets[i]=m.qmul(m.qi(sr[j][1]),m.qmul(ci,target))
    def slerp(x,y,u):
        dot=m.dot(x,y)
        if dot<0:y=tuple(-v for v in y);dot=-dot
        if dot>.9995:return m.qnorm(m.lerp(x,y,u))
        angle=math.acos(max(-1,min(1,dot)));return tuple((p*math.sin((1-u)*angle)+q*math.sin(u*angle))/math.sin(angle) for p,q in zip(x,y))
    frames=[];sourceRange=[float('inf'),float('-inf')];maxFootError=0
    floor=min(rest[i][0][1] for i in [4,5,6,9,10,11])
    for f in range(403):
        t=f/60;sf=t*30;lo=min(int(sf),a.num_frames-2);u=sf-lo;sw=[]
        for j,name in enumerate(s.bones):
            if name in names:
                tr=a.tracks[names[name]];pos=m.lerp(tr.translations[lo],tr.translations[lo+1],u)
                q=slerp(qw(tr.rotations[lo]),qw(tr.rotations[lo+1]),u)
            else:pos=s.reference_pose[j].translation;q=qw(s.reference_pose[j].rotation)
            parent=s.parents[j]
            if parent>=0:pp,pq=sw[parent];pos=m.vadd(pp,m.rotate(pq,pos));q=m.qmul(pq,q)
            sw.append((pos,q))
        sourceRange=[min(sourceRange[0],sw[4][0][1]),max(sourceRange[1],sw[4][0][1])]
        local=[];targetW=[]
        for i,bone in enumerate(b):
            parent=bone['parent']
            if bone['name'] in mapping:
                desired=m.qmul(m.qmul(C,sw[sn[mapping[bone['name']]]][1]),offsets[i])
                q=desired if parent<0 else m.qmul(m.qi(targetW[parent]),desired)
            else:q=bone['orientation'];desired=q if parent<0 else m.qmul(targetW[parent],q)
            local.append(m.qnorm(q));targetW.append(m.qnorm(desired))
        wp=m.world(b,local)
        # 不导入瞬移根运动。仅根据双脚最低点补偿根骨竖直高度，使蹲姿仍在地面上。
        dy=floor-min(wp[i][0][1] for i in [4,5,6,9,10,11])
        assert abs(dy)<12
        delta=[m.qnorm(m.qmul(m.qi(x['orientation']),q)) for x,q in zip(b,local)]
        positions=[[0,dy,0] if i==0 else [0,0,0] for i in range(len(b))]
        frames.append({'t':round(t,8),'delta':[[round(v,9) for v in q] for q in delta],
                       'translation':[[round(v,8) for v in p] for p in positions]})
        maxFootError=max(maxFootError,abs(min(wp[i][0][1]+dy for i in [4,5,6,9,10,11])-floor))
    # 原HKX在隐藏/瞬移阶段存在很大的瞬时姿态切换。去掉水平瞬移后直接显示会造成肢体甩动。
    # 对目标骨旋转做双向角速度限制，再重算地面补偿；不把源动画的瞬移视觉当作普通步行动作。
    rawMax=0.
    for prev,cur in zip(frames,frames[1:]):
        rawMax=max(rawMax,max(math.degrees(2*math.acos(min(1,abs(m.dot(x,y))))) for x,y in zip(prev['delta'],cur['delta'])))
    def limited(sequence):
        out=[sequence[0]]
        for q in sequence[1:]:
            angle=math.degrees(2*math.acos(min(1,abs(m.dot(out[-1],q)))))
            out.append(slerp(out[-1],q,min(1,12./max(angle,.000001))))
        return out
    for i in range(len(b)):
        raw=[frame['delta'][i] for frame in frames];fw=limited(raw);bw=limited(raw[::-1])[::-1]
        filtered=limited([slerp(x,y,.5) for x,y in zip(fw,bw)])
        for frame,q in zip(frames,filtered):frame['delta'][i]=[round(v,9) for v in m.qnorm(q)]
    maxFootError=0.
    for frame in frames:
        local=[m.qmul(bone['orientation'],q) for bone,q in zip(b,frame['delta'])];wp=m.world(b,local)
        dy=floor-min(wp[i][0][1] for i in [4,5,6,9,10,11]);assert abs(dy)<12
        frame['translation'][0]=[0,round(dy,8),0]
        maxFootError=max(maxFootError,abs(min(wp[i][0][1]+dy for i in [4,5,6,9,10,11])-floor))
    text=['JCECLIP 2 6.7 23']
    for bone in b:
        if bone['name'] not in mapping:continue
        i=bone['id'];text.append('BONE '+bone['name'])
        for f in frames:text.append('KEY '+' '.join(format(v,'.9f') for v in [f['t'],*f['delta'][i],*f['translation'][i]]))
        text.append('END')
    put('package/JudgementCutEnd/assets/jce.clip','\n'.join(text)+'\n','动画资源','JCECLIP v2 producer','真实 HKX 23骨映射；403关键帧；位置通道仅根骨竖直补偿')
    # 固定拓扑人形网格：立体躯干/四肢/头与长衣摆，随真实重定向姿态运动。无NPC/共享动画缓存。
    meshParts=[(1,14,1.2,.7),(16,17,.55,.45),(17,18,.42,.36),(26,27,.55,.45),(27,28,.42,.36),
      (2,3,.75,.60),(3,4,.53,.46),(7,8,.75,.60),(8,9,.53,.46),(20,22,.70,.70)]
    vertices=[];triangles=[];bindings=[]
    # 三个椭圆截面的连续曲面；每段18顶点/24三角，法向光照在离线烘焙中生成。
    for aa,bb,w,d in meshParts:
        start=len(bindings)
        for ring,u in enumerate([0,.5,1]):
            radius=[.55,1,.45][ring]
            for k in range(6):bindings.append((aa,bb,u,w*radius*math.cos(k*math.pi/3),d*radius*math.sin(k*math.pi/3)))
        for ring in range(2):
            for k in range(6):
                x=start+ring*6+k;y=start+ring*6+(k+1)%6
                triangles.extend([(x,y,y+6),(x,y+6,x+6)])
    # 衣摆三条连贯曲面，短时间拖尾只影响视觉网格，不参与伤害/碰撞。
    for side in [-1,1]:
        start=len(bindings)
        for u in [0,.5,1]:
            for v in [-1,0,1]:bindings.append((1,1,u,side*(1.1+u*.9),v*.6))
        for r in range(2):
            for k in range(2):
                x=start+r*3+k;triangles.extend([(x,x+1,x+4),(x,x+4,x+3)])
    assert len(bindings)<=256 and len(triangles)<=320
    for frame in frames:
        local=[m.qmul(bone['orientation'],q) for bone,q in zip(b,frame['delta'])];wp=m.world(b,local)
        result=[]
        for aa,bb,u,w,d in bindings:
            pa,qa=wp[aa];pb,qb=wp[bb];base=m.lerp(pa,pb,u)
            # 骨架平面轴来自该骨旋转；退化衣摆额外沿后下方垂落，朝向跟随骨盆。
            side=m.rotate(qa,(0,1,0));front=m.rotate(qa,(0,0,1))
            if aa==bb==1:
                base=m.vadd(pa,m.rotate(qa,(-u*7,0,-u*1.5)))
            result.append([round(v,7) for v in m.vadd(m.vadd(m.vadd(base,m.vmul(side,w)),m.vmul(front,d)),frame['translation'][0])])
        vertices.append(result)
    binary=bytearray(struct.pack('<8sIIIff',b'JCEPHM2\0',len(frames),len(bindings),len(triangles),60.,6.7))
    for tri in triangles:binary.extend(struct.pack('<3H',*tri))
    for frame in vertices:
        for xyz in frame:binary.extend(struct.pack('<3f',*xyz))
    put('package/JudgementCutEnd/assets/jce_phantom.bin',bytes(binary),'幻影网格资源','JCEPHM2 bounded frames','198顶点/256三角立体人形与衣摆；实际HKX姿态烘焙，无实体克隆')
    scene=json.loads((ROOT/'preview/scene.json').read_text('utf8'));scene['frames']=frames
    scene['phantom']={'triangles':triangles,'frames':vertices,'frame_rate':60,'sample_interval':[2.1,2.6]}
    scene['animation_source']='ap05 HKX retarget; root horizontal travel removed; floor correction'
    put('preview/scene.json',json.dumps(scene,ensure_ascii=False,separators=(',',':'))+'\n','离线预览数据','same animation and mesh','离线预览与实际资源同源；不称为游戏验证')
    h=(ROOT/'preview/index.html').read_text('utf8')
    h=re.sub(r'(?m)^const DATA=.*$',lambda _: 'const DATA='+json.dumps(scene,ensure_ascii=False,separators=(',',':'))+';',h)
    put('preview/index.html',h,'离线预览','embedded DATA','同步实际HKX动作和网格资源')
    provenance={'animation_source':str(animPath),'animation_sha256':sha(animPath),'skeleton_source':str(skelPath),'skeleton_sha256':sha(skelPath),
      'decoder':{'name':'PyNifly','url':'https://github.com/BadDogSkyrim/PyNifly','license':'GPL-3.0',
       'files':{name:sha(decoder/name) for name in ['anim_fo4.py','anim_skyrim.py']}},
      'coordinate_alignment':{'up':'Skyrim +Z -> Kenshi +Y','left':'Skyrim -X -> Kenshi +X','forward':'Skyrim +Y -> Kenshi +Z','quaternion_wxyz':C,'anatomical_aim':aim},
      'source_duration':a.duration,'source_frames':a.num_frames,'source_tracks':a.num_tracks,
      'binding':'empty binding identity with annotation bone names; explicit standard humanoid names',
      'mapping':mapping,'events':[{'time':x.time,'text':x.text} for x in a.annotations],
      'source_horizontal_COM_range':sourceRange,'raw_max_bone_step_degrees':rawMax,'retarget_velocity_cap_clip_degrees_per_second':720,'horizontal_root_motion_removed':True,'maximum_floor_error':maxFootError,
      'output_frames':403,'output_tracks':23,'output_clip_sha256':sha(ASSETS/'jce.clip'),
      'phantom':{'vertices':len(bindings),'triangles':len(triangles),'sha256':sha(ASSETS/'jce_phantom.bin'),'origin':'independent authored generic humanoid, NOT caster equipment clone'},
      'license_note':'HKX由ap05制作；作者允许非商业修改/跨游戏转换并要求署名；未将原版第三方贴图标为原创或CC0'}
    put('docs/retarget-provenance.json',json.dumps(provenance,ensure_ascii=False,indent=2)+'\n','重定向证据','source and output hashes','保留源文件身份、事件、骨映射、根位移处理和来源限制')
    print(json.dumps({'retargeted':True,'source_frames':a.num_frames,'output_frames':403,'phantom_vertices':len(bindings),'phantom_triangles':len(triangles)},ensure_ascii=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--decoder',type=Path,required=True)
    main(parser.parse_args().decoder)
