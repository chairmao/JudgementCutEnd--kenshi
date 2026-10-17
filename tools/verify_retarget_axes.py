
"""独立核对重定向的解剖方向及源数据误差；只读检查，不编译或运行游戏。"""
from pathlib import Path
import sys,importlib.util,json,math,hashlib,ast
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    m=module('assets_math',ROOT/'tools/author_assets.py')
    d=Path(r'D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCEAssetPort-20261007')
    sys.path.insert(0,str(d))
    from anim_skyrim import load_skyrim_animation,load_skyrim_skeleton
    p=json.loads((ROOT/'docs/retarget-provenance.json').read_text('utf8'))
    a=load_skyrim_animation(p['animation_source']);s=load_skyrim_skeleton(p['skeleton_source'])
    b=m.skeleton(m.GAME/'data/character/meshes/male_skeleton/male_skeleton.skeleton')
    female=m.skeleton(m.GAME/'data/character/meshes/female_skeleton/female_skeleton.skeleton')
    scene=json.loads((ROOT/'preview/scene.json').read_text('utf8'))
    oldPath=Path(r'D:\CodexBackups\JudgementCutEnd-AssetPort-20261008-001338-262981\E\KenshiProject\2.Projects\JudgementCutEnd\preview\scene.json')
    old=json.loads(oldPath.read_text('utf8'));checks=[];metrics=[]
    def check(n,ok):
        checks.append({'name':n,'passed':bool(ok)})
        if not ok:raise AssertionError(n)
    C=tuple(p['coordinate_alignment']['quaternion_wxyz'])
    # 从左右股骨的世界位置验证左右，不以工具注释或文件名推测朝向。
    rest=m.world(b,[x['orientation'] for x in b]);sr=[]
    for i,pose in enumerate(s.reference_pose):
        q=m.qnorm((pose.rotation[3],*pose.rotation[:3]));pos=pose.translation;parent=s.parents[i]
        if parent>=0:pp,pq=sr[parent];q=m.qmul(pq,q);pos=m.vadd(pp,m.rotate(pq,pos))
        sr.append((pos,q))
    sn={n:i for i,n in enumerate(s.bones)};an={n:i for i,n in enumerate(a.bone_names)}
    left=m.rotate(C,m.vsub(sr[sn['NPC L Thigh [LThg]']][0],sr[sn['NPC R Thigh [RThg]']][0]))
    check('source anatomical left aligns actual target left',m.dot(m.unit(left),m.unit(m.vsub(rest[2][0],rest[7][0])))>.99)
    check('source up becomes target up',m.dot(m.rotate(C,(0,0,1)),(0,1,0))>.99999)
    axes=[m.rotate(C,v) for v in [(1,0,0),(0,1,0),(0,0,1)]]
    check('pure right-handed rotation, no reflection',m.dot(m.cross(axes[0],axes[1]),axes[2])>.99999)
    aim=p['coordinate_alignment']['anatomical_aim']
    check('chest uses neck, never first clavicle',aim['Bip01 Spine2']=='Bip01 Neck')
    check('terminal head is not realigned to eye/jaw/hair','Bip01 Head' not in aim)
    # 直接从源HKX恢复标准骨父子世界变换，以原头骨+Y面向、+Z顶部对照Kenshi头骨-Z面向、+X顶部。
    # 只检查拔刀前稳定阶段，瞬移/隐藏阶段的滤波误差另行保留，不能让容错掩盖基本轴错误。
    def error(x,y):return math.degrees(math.acos(max(-1,min(1,m.dot(m.unit(x),m.unit(y))))))
    for t in [.5,1,1.5,2,2.1]:
        f=round(t*30);sw=[]
        for j,n in enumerate(s.bones):
            pose=s.reference_pose[j];pos=pose.translation;q=m.qnorm((pose.rotation[3],*pose.rotation[:3]))
            if n in an:
                tr=a.tracks[an[n]];pos=tr.translations[f];q=m.qnorm((tr.rotations[f][3],*tr.rotations[f][:3]))
            parent=s.parents[j]
            if parent>=0:pp,pq=sw[parent];q=m.qmul(pq,q);pos=m.vadd(pp,m.rotate(pq,pos))
            sw.append((pos,q))
        sourceQ=m.qmul(C,sw[sn['NPC Head [Head]']][1]);row={'clip_time':t}
        for label,sc in [('before',old),('after',scene)]:
            frame=sc['frames'][round(t*60)]
            w=m.world(b,[m.qmul(x['orientation'],q) for x,q in zip(b,frame['delta'])])
            row[label]={'face_error_deg':error(m.rotate(w[21][1],(0,0,-1)),m.rotate(sourceQ,(0,1,0))),
                        'top_error_deg':error(m.rotate(w[21][1],(1,0,0)),m.rotate(sourceQ,(0,0,1)))}
        check('source face direction preserved at '+str(t),row['after']['face_error_deg']<2)
        check('source head top direction preserved at '+str(t),row['after']['top_error_deg']<2)
        metrics.append(row)
    check('actual clip hash matches generation',hashlib.sha256((ROOT/'package/JudgementCutEnd/assets/jce.clip').read_bytes()).hexdigest()==p['output_clip_sha256'])
    floor=min(rest[i][0][1] for i in [4,5,6,9,10,11]);maxFloor=0;maxStep=0
    for k,frame in enumerate(scene['frames']):
        check('finite normalized rotations frame '+str(k),all(all(math.isfinite(v) for v in q) and abs(sum(v*v for v in q)-1)<1e-7 for q in frame['delta']))
        w=m.world(b,[m.qmul(x['orientation'],q) for x,q in zip(b,frame['delta'])])
        maxFloor=max(maxFloor,abs(min(w[i][0][1]+frame['translation'][0][1] for i in [4,5,6,9,10,11])-floor))
        check('root-only vertical position '+str(k),frame['translation'][0][0]==frame['translation'][0][2]==0 and all(v==[0,0,0] for v in frame['translation'][1:]))
        if k:
            maxStep=max(maxStep,max(math.degrees(2*math.acos(min(1,abs(m.dot(x,y))))) for x,y in zip(scene['frames'][k-1]['delta'],frame['delta'])))
    check('floor compensation retained',maxFloor<1e-6)
    check('no instant 180-degree local frame jump',maxStep<=12.00001)
    check('controlled bones exist in standard female skeleton',set(p['mapping']).issubset({x['name'] for x in female}))
    for file in ['tools/author_port.py','tools/inspect_skyrim_vfx.py','tools/verify_retarget_axes.py']:
        raw=(ROOT/file).read_bytes();txt=raw.decode('utf-8-sig');ast.parse(txt)
        check('syntax encoding Chinese '+file,'\n' not in txt.replace('\r\n','') and '\ufffd' not in txt and '\u951f\u65a4\u62f7' not in txt)
    nif=module('nif_reader',ROOT/'tools/inspect_skyrim_vfx.py')
    for raw,fmt in [(b'\0','I'),(b'\xff\xff\xff\x7f','str')]:
        caught=False
        try:
            reader=nif.Reader(raw);reader.string() if fmt=='str' else reader.read(fmt)
        except ValueError:caught=True
        check('NIF reader rejects malformed '+fmt,caught)
    return {'passed':True,'check_count':len(checks),'checks':checks,'head_direction_comparison':metrics,
            'max_local_step_deg':maxStep,'max_floor_error':maxFloor,'native_compilation_run':False,'game_tested':False,
            'limitations':['标准男女骨架静态检查；凯瑟琳实机头部/面部蒙皮验收仍未完成','原动画本身在瞬移和回身阶段包含身体转向；不以钳制头部替代重定向']}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
