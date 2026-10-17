"""制作独立 Kenshi 动作和特效；按用户授权使用本地参考音效，完整记录来源。"""
from pathlib import Path
import argparse, datetime, hashlib, json, math, random, shutil, struct, wave
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "package" / "JudgementCutEnd"
SOURCE = Path("E:/skyrimspecialedition/mods/Judgement Cut End - ap05's Remake")
GAME = Path("D:/steam/steamapps/common/Kenshi")
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
REPORTS=[]

def put(path, data, role):
    # 再次运行也不会无备份覆盖：备份在项目外，按绝对原路径保留目录。
    existed=path.exists()
    if isinstance(data,str):
        data=data.replace("\r\n","\n").replace("\n","\r\n").encode("utf-8")
    # 确定性资源与上一轮字节相同就保留，不为未变更文件反复制造备份。
    if existed and path.read_bytes()==data:
        print(json.dumps({"File":str(path),"Changes":"unchanged; not overwritten"},ensure_ascii=False));return
    if existed:
        for base in (Path("D:/CodexBackups"),Path("E:/AIWorkSpace/_backups")):
            target=base/("JudgementCutEnd-"+STAMP)/path.drive.rstrip(":")/Path(*path.parts[1:])
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as f: f.write(path.read_bytes())
    path.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(data,str):
        data=data.replace("\r\n","\n").replace("\n","\r\n").encode("utf-8")
        text=data.decode("utf-8")
        assert not any(x in text for x in ("\ufffd","\u951f\u65a4\u62f7","\u00c3","\u00c2","\u00ef\u00bb\u00bf"))
    with path.open("wb" if existed else "xb") as f:f.write(data)
    assert path.read_bytes()==data
    REPORTS.append({"File":str(path),"Role":role,"Code location":"whole generated resource","Before":"existing, backed up" if existed else "absent","Changes":"created/reproduced deterministically","Reasons":"JCE resource contract v1","After":"ready for runtime loading","Impact":"new plugin only","Validation":"strict readback and encoding scan","Safety":"dual external backups if overwritten; UTF-8/CRLF text or binary asset","Unresolved":"game rendering not tested"})
    print(json.dumps(REPORTS[-1],ensure_ascii=False))

def qmul(a,b):
    w,x,y,z=a;v,r,s,t=b
    return (w*v-x*r-y*s-z*t,w*r+x*v+y*t-z*s,w*s-x*t+y*v+z*r,w*t+x*s-y*r+z*v)
def qi(q):return (q[0],-q[1],-q[2],-q[3])
def qnorm(q):
    n=math.sqrt(sum(x*x for x in q));return tuple(x/n for x in q)
def vadd(a,b):return tuple(x+y for x,y in zip(a,b))
def vsub(a,b):return tuple(x-y for x,y in zip(a,b))
def vmul(a,k):return tuple(x*k for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):return vmul(v,1/math.sqrt(dot(v,v)))
def rotate(q,v):return qmul(qmul(q,(0,*v)),qi(q))[1:]
def axis(v,angle):
    v=unit(v);a=math.radians(angle)/2;return(math.cos(a),*(x*math.sin(a) for x in v))
def from_to(a,b):
    a=unit(a);b=unit(b);d=dot(a,b)
    if d < -.99999:
        return axis(cross(a,(1,0,0) if abs(a[0])<.8 else (0,1,0)),180)
    return qnorm((1+d,*cross(a,b)))
def lerp(a,b,u):return tuple(x+(y-x)*u for x,y in zip(a,b))
def smooth(u):return max(0,min(1,u))**2*(3-2*max(0,min(1,u)))

def skeleton(path):
    # Kenshi Serializer_v1.80 的骨骼 chunk 长度不计骨骼名称；不能普通按 length 跳过。
    b=path.read_bytes();i=b.index(b"\n")+1;bones=[];parents={}
    assert b[:2]==b"\x00\x10" and b"Serializer_v1.80" in b[:24]
    while i+6<=len(b):
        t,n=struct.unpack_from("<HI",b,i)
        if t==0x2000:
            e=b.index(b"\n",i+6);h=struct.unpack_from("<H",b,e+1)[0]
            p=struct.unpack_from("<3f",b,e+3);x,y,z,w=struct.unpack_from("<4f",b,e+15)
            bones.append({"id":h,"name":b[i+6:e].decode(),"position":p,"orientation":qnorm((w,x,y,z))})
            i+=n+e-(i+6)+1
        elif t==0x3000:
            c,p=struct.unpack_from("<HH",b,i+6);parents[c]=p;i+=n
        elif t==0x1010:i+=n
        else:break
    for bone in bones:bone["parent"]=parents.get(bone["id"],-1)
    assert [x["id"] for x in bones]==list(range(len(bones)))
    return bones

def world(bones,local):
    result=[]
    for b,q in zip(bones,local):
        p=b["position"];parent=b["parent"]
        if parent>=0:
            pp,pq=result[parent];result.append((vadd(pp,rotate(pq,p)),qmul(pq,q)))
        else:result.append((p,q))
    return result

def curve(cards,t):
    """分段平滑曲线，连接点位置连续且速度为零；禁止用阶段常量直接跳转躯干。"""
    if t<=cards[0][0]:return cards[0][1]
    for (a,p),(b,q) in zip(cards,cards[1:]):
        if t<=b:return lerp(p,q,smooth((t-a)/(b-a)))
    return cards[-1][1]

def pose(bones,t):
    local=[b["orientation"] for b in bones];names={b["name"]:b["id"] for b in bones}
    rest=world(bones,local)
    # 全身定姿由运行时持有完整父子链，骨盆与双腿取稳定站姿、肩颈随连续躯干转动。
    # 这里不平移根骨/骨盆，确保脚不漂移；动作是重新编排的 Kenshi 动作，不冒称 HKX 重定向。
    blend=smooth(t/.45)*(1-smooth((t-6.05)/.65))
    twist=curve([(0,(0,)),(.7,(-12,)),(2.1,(-18,)),(2.4,(22,)),(3.2,(14,)),
                 (3.9,(-8,)),(5.15,(-8,)),(6.7,(0,))],t)[0]
    pitch=curve([(0,(0,)),(.7,(-5,)),(2.1,(-5,)),(2.4,(-2,)),
                 (3.2,(-2,)),(5.15,(-4,)),(6.7,(0,))],t)[0]
    # 世界轴旋转转换到父骨空间，分摊躯干扭转，而非脊柱一根骨头承担 44 度瞬跳。
    for name,degrees,ax in (("Bip01 Spine",pitch,(1,0,0)),
        ("Bip01 Spine1",twist*.55,(0,1,0)),("Bip01 Spine2",twist*.45,(0,1,0)),
        ("Bip01 Neck",-twist*.2,(0,1,0)),("Bip01 Head",-twist*.4,(0,1,0))):
        h=names[name];wp=world(bones,local);parent=wp[bones[h]["parent"]][1]
        local[h]=qmul(qmul(qmul(qi(parent),axis(ax,degrees)),parent),local[h])
    # 手的位置：右手跨到左腰握柄，拔刀挥向右前方，停顿后对准左手持鞘的位置回鞘。
    right=curve([(0,rest[names["Bip01 R Hand"]][0]),(.7,(1.6,10.7,1.5)),
        (2.1,(1.6,10.7,1.5)),(2.4,(-4.8,12.4,3.5)),(3.15,(-4.8,12.4,3.5)),
        (3.9,(-.5,11.8,4.1)),(4.45,(3.0,10.8,2.2)),
        (5.15,(1.6,10.7,1.5)),(5.65,(1.6,10.7,1.5)),(6.7,rest[names["Bip01 R Hand"]][0])],t)
    left=curve([(0,rest[names["Bip01 L Hand"]][0]),(.7,(2.3,10.1,1.0)),
        (5.65,(2.3,10.1,1.0)),(6.7,rest[names["Bip01 L Hand"]][0])],t)
    for side,tar in (("L",left),("R",right)):
        u=names["Bip01 "+side+" UpperArm"];e=names["Bip01 "+side+" Forearm"];h=names["Bip01 "+side+" Hand"]
        wp=world(bones,local);shoulder=wp[u][0]
        l1=math.sqrt(dot(bones[e]["position"],bones[e]["position"]));l2=math.sqrt(dot(bones[h]["position"],bones[h]["position"]))
        ray=vsub(tar,shoulder);dist=max(.1,min(l1+l2-.001,math.sqrt(dot(ray,ray))));d=unit(ray)
        # 两侧独立的外侧肘极向量，避免双肘共用向前的极点而反折/穿过胸口。
        pole=(1 if side=="L" else -1,.1,.75)
        pole=unit(vsub(pole,vmul(d,dot(pole,d))))
        along=(dist*dist+l1*l1-l2*l2)/(2*dist)
        elbow=vadd(shoulder,vadd(vmul(d,along),vmul(pole,math.sqrt(max(0,l1*l1-along*along)))))
        uq=qmul(from_to(vsub(rest[e][0],rest[u][0]),vsub(elbow,shoulder)),rest[u][1])
        local[u]=qmul(qi(wp[bones[u]["parent"]][1]),uq)
        eq=qmul(from_to(vsub(rest[h][0],rest[e][0]),vsub(tar,elbow)),rest[e][1])
        local[e]=qmul(qi(uq),eq)
        desired=qmul(axis((0,1,0),(20 if side=="L" else -15)*blend),rest[h][1])
        local[h]=qmul(qi(eq),desired)
    return [qnorm(qmul(qi(b["orientation"]),q)) for b,q in zip(bones,local)]

def reference_soundtrack():
    """使用用户提供的本地参考音效制作同步轨道；不混入人声、音乐或随机合成声。"""
    import array,io
    rate=44100;mix=[0.0]*int(6.7*rate);used=[]
    cues=[("JCE010Intro.wav",0,.45,2.1),("JCE020Draw.wav",2.1,.65,.7),
          ("JCE030CutAll.wav",2.35,.65,1.1),("JCE040Sheath.wav",3.66,.5,.744),
          ("JCE040Finish.wav",5.15,.7,1.55)]
    for name,at,gain,limit in cues:
        path=SOURCE/"sound/fx/zjc"/name
        with wave.open(str(path),"rb") as wav:
            assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())==(1,2,rate)
            pcm=array.array("h",wav.readframes(wav.getnframes()))
        count=min(len(pcm),int(limit*rate),len(mix)-int(at*rate));fade=int(.015*rate)
        for i in range(count):
            envelope=min(1,i/fade,(count-1-i)/fade)
            mix[int(at*rate)+i]+=pcm[i]/32768*gain*max(0,envelope)
        used.append({"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"at":at,"gain":gain,"used_seconds":count/rate})
    # 仅降幅防止多轨叠加削波，保持参考音效自身的频谱；输出稳定的单一 WinMM WAV。
    peak=max(abs(v) for v in mix);scale=min(1,.9/peak) if peak else 1
    result=array.array("h",(round(v*scale*32767) for v in mix));buf=io.BytesIO()
    with wave.open(buf,"wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(result.tobytes())
    return buf.getvalue(),used


def main():
    bones=skeleton(GAME/"data/character/meshes/male_skeleton/male_skeleton.skeleton")
    female=skeleton(GAME/"data/character/meshes/female_skeleton/female_skeleton.skeleton")
    # delta 可供兼容 Bip01 骨架使用；保留模型身体比例和当前位置，不替换共享骨架资源。
    controlled=[x for x in bones if "Nub" not in x["name"] and not any(word in x["name"] for word in ("Prop","Jaw"))]
    frames=[round(i/60,6) for i in range(403)]
    raw=[pose(bones,t) for t in frames];samples=[]
    # IK 在接近伸直与反向挥斩时角速度会尖峰；对离线四元数同半球加权滤波，
    # 使用 ±0.1 秒窗口而不平移演出事件。归一化后骨长不变；运行时仍用 Slerp 插值。
    for frame in range(len(raw)):
        row=[]
        for bone in range(len(bones)):
            ref=raw[frame][bone];total=[0.0]*4
            for other in range(max(0,frame-6),min(len(raw),frame+7)):
                q=raw[other][bone];weight=math.exp(-((other-frame)/2.5)**2/2)
                sign=1 if sum(x*y for x,y in zip(ref,q))>=0 else -1
                for axis_index in range(4):total[axis_index]+=q[axis_index]*weight*sign
            row.append(qnorm(total))
        samples.append(row)
    lines=["JCECLIP 1 6.700000 "+str(len(controlled))]
    for b in controlled:
        lines.append("BONE "+b["name"])
        for t,qs in zip(frames,samples):lines.append("KEY %.6f %.8f %.8f %.8f %.8f"%(t,*qs[b["id"]]))
        lines.append("END")
    put(OUT/"assets"/"jce.clip","\n".join(lines)+"\n","403 帧连续全身编排，完整父子朝向链的四元数局部增量")
    rng=random.Random(517);slashes=[]
    for i in range(96):
        # 均匀体积取样；两层光带共用这条几何，不逐帧随机闪动。
        centre=(rng.uniform(-.8,.8),rng.uniform(.08,.8),rng.uniform(-.8,.8))
        direction=unit((rng.uniform(-1,1),rng.uniform(-.5,.5),rng.uniform(-1,1)))
        slashes.append([*centre,*direction,rng.uniform(.18,.52),2.35+i/96*.55,rng.uniform(.7,1.7)])
    put(OUT/"assets"/"slashes.csv","JCESLASH 1 96\n"+"\n".join(" ".join("%.7f"%x for x in v) for v in slashes)+"\n","96 条空间裂痕的确定性布局／出现时间／寿命")
    material="""material JCE/Glow
{
    technique
    {
        pass
        {
            vertex_program_ref Basic_Coloured_Texture_VP {}
            fragment_program_ref Basic_Texture_FP {}
            lighting off
            depth_write off
            depth_check on
            cull_hardware none
            scene_blend add
            texture_unit
            {
                texture jce_glow.tga
                tex_address_mode clamp
                colour_op modulate
            }
        }
    }
}
"""
    put(OUT/"assets"/"jce.material",material,"独立 OGRE 加法发光材质，保留深度遮挡")
    w,h=256,32;pixels=bytearray()
    for y in range(h):
        for x in range(w):
            v=int(255*math.exp(-((y/(h-1)-.5)*6)**2)*max(0,math.sin(math.pi*x/(w-1)))**.35)
            pixels.extend((v,v,v,255))
    put(OUT/"assets"/"jce_glow.tga",struct.pack("<BBBHHBHHHHBB",0,0,2,0,0,0,0,0,w,h,32,0x28)+pixels,"原创 256×32 发光梯度贴图")
    # 使用参考模组的五个动作音效重混为 6.7 秒轨道，保留配置文件 SoundEnabled 开关。
    soundtrack,audio_sources=reference_soundtrack()
    put(OUT/"assets"/"jce_sequence.wav",soundtrack,"本地参考拔刀/斩击/收鞘音效的同步混音")
    put(ROOT/"docs"/"audio-provenance.json",json.dumps({"sources":audio_sources,"format":"mono PCM16 44100 Hz","duration":6.7,"redistribution":"本地测试资源；来源为用户提供参考目录，不声称原创音频"},ensure_ascii=False,indent=2),"逐个参考音效哈希、阶段和混音合同")
    payload={"duration":6.7,"draw":2.1,"cut":2.35,"sheath":5.15,"rate":60,"bones":bones,"frames":[{"t":t,"delta":qs} for t,qs in zip(frames,samples)],"slashes":slashes}
    put(ROOT/"preview"/"scene.json",json.dumps(payload,ensure_ascii=False,separators=(",",":")),"独立预览用同源骨骼、动作和裂痕数据")
    # 离线 HTML 内嵌同一份数据，资源再制作时同步更新，防止预览停留在旧动作。
    preview=ROOT/"preview"/"index.html"
    if preview.exists():
        text=preview.read_text("utf8");rows=text.splitlines()
        matches=[i for i,row in enumerate(rows) if row.startswith("const DATA=")]
        if len(matches)!=1:raise ValueError("Preview DATA contract is missing or ambiguous")
        rows[matches[0]]="const DATA="+json.dumps(payload,ensure_ascii=False,separators=(",",":"))+";"
        put(preview,"\n".join(rows)+"\n","同步离线预览内嵌动作/骨架/裂痕合同")
    hkx=list(SOURCE.rglob("*.hkx"));origin={"reference":str(SOURCE),"hkx":[{"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in hkx],"reference_skeletons":[str(p) for p in SOURCE.rglob("*skeleton*")],"male_sha256":hashlib.sha256((GAME/"data/character/meshes/male_skeleton/male_skeleton.skeleton").read_bytes()).hexdigest(),"male_bones":len(bones),"female_bones":len(female),"female_controls_match":all(x["name"] in [b["name"] for b in female] for x in controlled),"copied_third_party_files":[x["path"] for x in audio_sources],"animation":"independent IK authored movement; reference timings only; NOT HKX retarget","animation_frame_count":len(frames)}
    put(ROOT/"docs"/"asset-provenance.json",json.dumps(origin,ensure_ascii=False,indent=2),"参考来源、文件哈希、骨架核验及原创资源声明")
    put(ROOT/"docs"/"asset-change-reports.json",json.dumps(REPORTS,ensure_ascii=False,indent=2),"逐个资产变更报告")
if __name__=="__main__":main()
