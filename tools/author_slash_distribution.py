"""只重排认可2.8版的刀光和配套裂光；不编译、不安装、不读取或写入游戏目录。"""
from pathlib import Path
import argparse, datetime, hashlib, json, math

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "package" / "JudgementCutEnd" / "assets"
BASELINE = ROOT / "releases" / "JudgementCutEnd-2.8.0-accepted-20261009-195356-a0a960" / "source"
BASELINE_SLASH_SHA = "5c8f81088a29825fef2ddcac97d4093789cc447b89aff9915029888b33e20214"


def dot(a, b): return sum(x*y for x, y in zip(a, b))
def add(a, b): return [x+y for x, y in zip(a, b)]
def mul(a, n): return [x*n for x in a]
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def norm(a): return math.sqrt(dot(a, a))
def unit(a): return mul(a, 1/norm(a))
def digest(data): return hashlib.sha256(data).hexdigest()


def read_rows(path, header, count, columns):
    lines=path.read_bytes().decode("utf-8").splitlines()
    assert lines[0]==header
    rows=[[float(v) for v in line.split()] for line in lines[1:]]
    assert len(rows)==count and all(len(row)==columns and all(math.isfinite(v) for v in row) for row in rows)
    return rows


def layout_scale(rows):
    # 与运行时FitSlashLayout保持同一端点XZ包围算法；只计算资产，没有修改原生钩子。
    # 保留原最长端点可稳定全局系数，避免顺带放大幻影、空间切面和光带宽度。
    extent=1.0
    for s in rows:
        for sign in (-1, 1):
            p=add(s[:3], mul(s[3:6], sign*s[6]))
            extent=max(extent, math.hypot(p[0],p[2])+.18/30)
    return 350/extent


def redistribute(old):
    rows=[row[:] for row in old]; scale=layout_scale(old)
    extrema=[max(math.hypot(s[0]+k*s[3]*s[6],s[2]+k*s[5]*s[6]) for k in (-1,1)) for s in old]
    protected=set(range(0,96,6)) | {max(range(96),key=lambda i:extrema[i])}
    # 16条幻影包含8条折射切面；它们和原最长端点逐字段保留，稳定现有演出与全局拟合系数。
    candidates=[i for i in range(96) if i not in protected]
    changed=[candidates[j*len(candidates)//48] for j in range(48)]
    outer=[i for j,i in enumerate(changed) if j%3!=2]
    bridges=[i for j,i in enumerate(changed) if j%3==2]
    angles=[]
    for order,index in enumerate(outer):
        # 32条外围交错长弦：中心距离随弦夹角变化约224..317，不摆成同一内圆围栏。
        # 空间顺序与出生顺序错开；高度/倾角只按稳定编号生成，禁止逐帧随机闪动。
        theta=2*math.pi*((order*13)%32)/32+.41
        phi=math.radians(36.5625+13*math.sin(order*2.39996))
        reach=346+.5*math.sin(order*1.7); rho=reach*math.cos(phi); half=reach*math.sin(phi)
        centre=[rho*math.cos(theta),65+105*(.5+.5*math.sin(order*2.39996)),rho*math.sin(theta)]
        delta=[-half*math.sin(theta),half*.13*math.sin(order*1.13),half*math.cos(theta)]
        rows[index][:7]=mul(centre,1/scale)+unit(delta)+[norm(delta)/scale]
        angles.extend(((theta-phi)%(2*math.pi),(theta+phi)%(2*math.pi)))
    for order,index in enumerate(bridges):
        # 16条贯穿长斩按剩余端点最大角空隙补边；不用同一个极端端点缩放后误认整个外环已满。
        # 每道横向偏离中心45..80单位，避免十几道直线在施法者位置拼成廉价放射星芒。
        ordered=sorted(angles)
        gaps=[(ordered[(j+1)%len(ordered)]-value)%(2*math.pi) for j,value in enumerate(ordered)]
        gap=max(range(len(gaps)),key=lambda j:gaps[j])
        target=(ordered[gap]+gaps[gap]*.5)%(2*math.pi); angles.append(target)
        reach=343+.8*math.sin(order*1.1)
        offset=(45+35*(.5+.5*math.sin(order*2.1)))*(1 if order%2==0 else -1)
        far=math.sqrt(reach*reach-offset*offset); theta=target-math.atan2(offset,far)
        near=-65-15*math.sin(order*2.3); rho=(far+near)/2; half=(far-near)/2
        centre=[rho*math.cos(theta)-offset*math.sin(theta),70+70*(.5+.5*math.cos(order*2.39996)),rho*math.sin(theta)+offset*math.cos(theta)]
        delta=[half*math.cos(theta),half*.19*math.sin(order*1.6),half*math.sin(theta)]
        # 先按世界单位构形，再转换回原CSV归一化中心/单位方向/半长度；时序与寿命不写入。
        rows[index][:7]=mul(centre,1/scale)+unit(delta)+[norm(delta)/scale]
    rows=[[round(v,7) for v in s] for s in rows]
    assert len(outer)==32 and len(bridges)==16 and layout_scale(rows)==scale
    assert all(rows[i]==old[i] for i in protected)
    assert all(s[7:]==old[i][7:] for i,s in enumerate(rows))
    return rows, changed, sorted(protected)


def rotate(v, old_direction, new_direction):
    # 最小旋转只改变配对光区朝向，不放大旧三角片面积；反向刀路使用正交轴180度回退。
    a=unit(old_direction); b=unit(new_direction); axis=cross(a,b); sine=norm(axis); cosine=max(-1,min(1,dot(a,b)))
    if sine<1e-9:
        if cosine>0:return v[:]
        axis=unit(cross(a,[1,0,0] if abs(a[0])<.8 else [0,1,0]))
        return add(mul(axis,2*dot(axis,v)),mul(v,-1))
    axis=mul(axis,1/sine)
    return add(add(mul(v,cosine),mul(cross(axis,v),sine)),mul(axis,dot(axis,v)*(1-cosine)))


def companion_glints(old, new, glints, changed):
    result=[row[:] for row in glints]
    for index in changed:
        for echo in range(2):
            row=glints[index*2+echo]; updated=[]
            # 两个对应裂光分布到刀路两侧段上，保留形状和出生时间；不是新增实体碎镜。
            anchor=add(new[index][:3],mul(new[index][3:6],new[index][6]*(-.48 if echo==0 else .48)))
            for offset in (0,3,6):
                local=add(row[offset:offset+3],mul(old[index][:3],-1))
                updated+=add(anchor,rotate(local,old[index][3:6],new[index][3:6]))
            result[index*2+echo]=[round(v,7) for v in updated]+[row[9]]
    return result


def table(header, rows):
    return (header+"\r\n"+"\r\n".join(" ".join("%.7f"%v for v in row) for row in rows)+"\r\n").encode("utf-8")


def report_write(path, content, role, region, reason, audit):
    before=path.read_bytes() if path.exists() else None; backups=[]
    if before==content:return
    # 数据资源与预览原本UTF-8无BOM；原字节备份并保留已有CRLF（含HTML既有CRCRLF），不全文件改换行。
    if before is not None:
        assert len(before)<=20*1024*1024 and not before.startswith(b"\xef\xbb\xbf")
        before.decode("utf-8");assert b"\n" not in before.replace(b"\r\n",b"")
        for base in (Path(r"D:\CodexBackups"),Path(r"E:\AIWorkSpace\_backups")):
            target=base/audit.name/path.drive.rstrip(":")/Path(*path.parts[1:]);target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==before
            else:
                with target.open("xb") as out:out.write(before)
            backups.append(str(target))
    decoded=content.decode("utf-8")
    for bad in ("\ufffd","锟斤拷","ï»¿"):
        assert bad not in decoded
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("wb" if before is not None else "xb") as out:out.write(content)
    assert path.read_bytes()==content
    entry={"File":str(path),"Role":role,"Code location":region,"Before":"认可2.8布局/对应预览" if before is not None else "新建",
           "Changes":reason,"Reasons":"350外围中心线稀疏，保留16幻影/8切面以及原时序，补足外环贯穿",
           "After":"2.8.1外围布局资源；运行时继续使用2.8 DLL","Impact":"原格式、计数、伤害、U重播、时钟和材质契约不变；透明像素覆盖可能增加",
           "Validation":"写回字节/UTF-8/换行/中文检查通过；几何审计另见verification.json",
           "Safety":{"backups":backups,"encoding":"UTF-8无BOM，保留既有换行"},"Unresolved":"未编译、未部署、未做实机视觉和GPU测试"}
    target=audit/("file-report-"+path.name+".json")
    if target.exists():raise RuntimeError("拒绝覆盖已有逐文件报告")
    with target.open("xb") as out:out.write((json.dumps(entry,ensure_ascii=False,indent=2)+"\r\n").replace("\r\n","\n").replace("\n","\r\n").encode("utf-8"))
    print(json.dumps({"file":str(path),"report":str(target)},ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--audit",type=Path,required=True);parser.add_argument("--apply",action="store_true");args=parser.parse_args()
    assert args.audit.is_dir()
    old_asset=BASELINE/"package/JudgementCutEnd/assets/slashes.csv"
    assert digest(old_asset.read_bytes())==BASELINE_SLASH_SHA,"固定认可版输入身份不匹配"
    old=read_rows(old_asset,"JCESLASH 1 96",96,9)
    glints=read_rows(BASELINE/"package/JudgementCutEnd/assets/jce_shards.csv","JCESHARDS 1 192",192,10)
    rows,changed,protected=redistribute(old); shards=companion_glints(old,rows,glints,changed)
    csv=table("JCESLASH 1 96",rows);glass=table("JCESHARDS 1 192",shards)
    # 正式格式没有注释字段，算法说明放在此制作器及独立清单，避免C++流提取被注释打断。
    manifest={"source_version":"2.8.0-dev","resource_revision":"2.8.1-outer-slash-layout-r1","native_cpp_changed":False,
              "dll_recompile_required":False,"installed":False,"game_tested":False,"bg3_assets_copied":False,
              "slash_count":96,"changed_paths":changed,"protected_paths":protected,"outer_chords":32,"inner_to_outer_cuts":16,
              "paired_glint_count":192,"timing_changed":False,"global_layout_scale":layout_scale(rows),
              "files":{"slashes.csv":digest(csv),"jce_shards.csv":digest(glass)},
              "accepted_baseline":str(BASELINE),"design":"32外围交错长斩+16内外贯穿；保留48原路径、全部出生/寿命、16幻影和8折射取样路径",
              "performance_note":"顶点/索引/路径数量不变；刀光延长会增加透明像素覆盖，实际帧耗未测试"}
    if not args.apply:
        print(json.dumps(manifest,ensure_ascii=False,indent=2));return
    for name, content in (("slashes.csv",csv),("jce_shards.csv",glass)):
        current=(ASSETS/name).read_bytes(); accepted=(BASELINE/"package/JudgementCutEnd/assets"/name).read_bytes()
        assert current in (accepted,content),"发现未授权并发资源变化："+name
    report_write(ASSETS/"slashes.csv",csv,"运行时96刀光布局","48条中心/方向/半长度","32外围长弦和16贯穿斩；保持其余48路径及全部出现时间/寿命",args.audit)
    report_write(ASSETS/"jce_shards.csv",glass,"192个配对光学片区","重排刀路关联的96个三角片","跟随48条新刀路重新定位/旋转；保持192数量、其余片区与时间",args.audit)
    # 浏览器预览只同步路径数据，旧预览没有最新雾/折射shader，不能当实机视觉验证。
    scene_path=ROOT/"preview/scene.json";scene=json.loads(scene_path.read_bytes().decode("utf-8"));old_scene=json.loads(json.dumps(scene))
    scene["slashes"]=rows;scene["shards"]=shards
    html_path=ROOT/"preview/index.html";html=html_path.read_bytes().decode("utf-8");start=html.index("const DATA=")+len("const DATA=")
    embedded,consumed=json.JSONDecoder().raw_decode(html[start:]);assert embedded==old_scene,"预览JSON与内嵌数据不同"
    compact=json.dumps(scene,ensure_ascii=False,separators=(",",":"))
    scene_bytes=(compact+"\r\n").encode("utf-8")
    report_write(scene_path,scene_bytes,"几何预览数据","slashes与shards数组","仅同步新刀路/对应光区；骨骼动画与其他预览参数保留",args.audit)
    html_bytes=(html[:start]+compact+html[start+consumed:]).encode("utf-8")
    report_write(html_path,html_bytes,"浏览器独立几何预览","const DATA内嵌数组","仅同步同一份刀路数据，脚本/中文/原换行保持",args.audit)
    report_write(ASSETS/"vfx-2.8.1.json",(json.dumps(manifest,ensure_ascii=False,indent=2)+"\r\n").replace("\r\n","\n").replace("\n","\r\n").encode("utf-8"),"资源身份清单","2.8.1资源修订","记录两项CSV哈希、制作范围与未部署状态，DLL身份仍2.8.0-dev",args.audit)


if __name__=="__main__":main()
