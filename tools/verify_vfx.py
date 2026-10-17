"""1.1.1特效与正式基线核验：数学/资源/JS解释运行，不编译C++或安装。"""
from pathlib import Path
import ast,hashlib,importlib.util,json,math,re,struct,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def main():
    spec=importlib.util.spec_from_file_location('existing_verify',ROOT/'tools'/'verify.py')
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);old_result=base.main()
    check('original regression suite',old_result['static_passed'])
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig')
    frozen=ROOT/'releases'/'1.0.0';manifest=json.loads((frozen/'release-manifest.json').read_text('utf8'))
    check('formal 1.0 release tag and original build marker',manifest['release']=='1.0.0' and manifest['internal_source_and_dll_marker']=='0.3.0')
    check('every frozen source/runtime hash preserved',all(hashlib.sha256((frozen/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest['files']))
    with zipfile.ZipFile(frozen.parent/'JudgementCutEnd-1.0.0.zip') as z:
        check('formal ZIP CRC',z.testzip() is None)
        check('formal ZIP payload equals frozen directory',all(hashlib.sha256(z.read('JudgementCutEnd-1.0.0/'+x['path'])).hexdigest()==x['sha256'] for x in manifest['files']))
    reference=(frozen/'source'/'JudgementCutEnd.cpp').read_text('utf-8-sig')
    def region(t,start,end):return t[t.index(start):t.index(end,t.index(start))]
    check('all damage, 350 boundary, native stagger logic byte-equivalent',region(cpp,'    float AreaRadius()','    unsigned vertex;')==region(reference,'    float AreaRadius()','    unsigned vertex;'))
    check('bounded root pose uses snapshot and retained skin publication',all(x in cpp for x in ('SampleTranslation(', 'poseHeightScale','RefreshSkin();')) and 'createAnimation(' not in cpp)
    # 时间修复是显式允许的Tick差异；仍逐字比对输入、伤害时点和其余时间线。
    tick=region(cpp,'    void Tick(','Runtime* runtime=0;')
    tick=tick.replace('        // 即使演出已经结束，暂停解除或恢复失败后的后续帧仍清偿时间恢复债务。\n        if(speedRestorePending)RestoreTime("resume_retry");\n','')
    tick=tick.replace('            // 分别记录暂停/失焦/按Esc/输入失效，便于确认时间恢复延后是否符合玩家操作。\n            const char* cancel=w->isPaused()?"cancelled_pause":!Foreground()?"cancelled_focus":\n                (GetAsyncKeyState(VK_ESCAPE)&0x8000)?"cancelled_escape":(!key||!key->controlEnabled)?"cancelled_input":0;\n            if(cancel){Finish(cancel);return;}',
        '            if(w->isPaused()||!Foreground()||(GetAsyncKeyState(VK_ESCAPE)&0x8000)||!key||!key->controlEnabled){Finish("cancelled_pause_focus_or_escape");return;}')
    check('input and real timeline unchanged except reviewed time restoration',tick==region(reference,'    void Tick(','Runtime* runtime=0;'))
    assets=ROOT/'package'/'JudgementCutEnd'/'assets'
    for name in ('jce_sequence.wav','jce_sequence_fast.wav','jce_glow.tga'):
        check('unchanged animation/audio/base glow '+name,(assets/name).read_bytes()==(frozen/'source'/'package'/'JudgementCutEnd'/'assets'/name).read_bytes())
    old=[[float(v) for v in l.split()] for l in (frozen/'source'/'package'/'JudgementCutEnd'/'assets'/'slashes.csv').read_text('utf8').splitlines()[1:]]
    rows=[[float(v) for v in l.split()] for l in (assets/'slashes.csv').read_text('utf8').splitlines()[1:]]
    check('same 96 geometric slash paths and lifetimes',len(rows)==96 and all(a[:7]==b[:7] and a[8]==b[8] for a,b in zip(old,rows)))
    check('spread births inside cut to sheath',all(2.35<=s[7]<=4.55<5.15 for s in rows) and all(a[7]<b[7] for a,b in zip(rows,rows[1:])))
    selected=[rows[i*len(rows)//16] for i in range(16)]
    check('16 distinct moving paths with full phantom lifetime before damage',len(set(tuple(s[:7]) for s in selected))==16 and all(s[7]+.68<5.15 for s in selected))
    glass=(assets/'jce_shards.csv').read_text('utf8').splitlines()
    shards=[[float(x) for x in l.split()] for l in glass[1:]]
    check('192 independent optical facets from all 96 slashes',glass[0]=='JCESHARDS 1 192' and len(shards)==192 and all(s[9]==rows[i//2][7] for i,s in enumerate(shards)))
    check('bounded finite nondegenerate fragment assets',all(len(s)==10 and all(math.isfinite(x) for x in s) and max(math.dist(s[j:j+3],[0,0,0]) for j in (0,3,6))<8 for s in shards))
    for name,size in (('jce_mist.tga',128),('jce_glass.tga',64)):
        b=(assets/name).read_bytes();w,h=struct.unpack_from('<HH',b,12)
        check('valid 32-bit top-left TGA '+name,w==h==size and b[2]==2 and b[16]==32 and b[17]==0x28 and len(b)==18+w*h*4)
    mist=(assets/'jce_mist.tga').read_bytes()[18:]
    check('neutral RGB texture with transparent alpha rim and cloud noise',mist[0]==255 and mist[3]==0 and mist[128*64*4+64*4+3]>0 and len(set(mist[3::4]))>100 and len(set(mist[::4]))==1)
    material=(assets/'jce.material').read_text('utf8')
    check('three separate existing shader-compatible materials',all('material '+s in material for s in ('JCE/Glow','JCE/Mist','JCE/Glass')) and material.count('depth_write off')==4 and material.count('depth_check on')==4 and 'scene_blend alpha_blend' in material)
    for name in re.findall(r'^\s*texture\s+(\S+)',material,re.M):check('material texture exists '+name,(assets/name).is_file())
    check('new shard loader validates count and corruption before hooks',r'assets\\jce_shards.csv' in cpp and 'count!=192' in cpp and 'Invalid mirror shard' in cpp and cpp.index('skin.Load();LoadAssets();')<cpp.index('KenshiLib::AddHook(frame'))
    check('preserved base sections and extended source layer callback coverage',all(s in cpp for s in ('StartLayer(0,"JCE/Glow")','StartLayer(1,"JCE/Mist")','StartLayer(2,"JCE/Glass")','rend==geometry->getSection(i)','unsigned i=0;i<FX_SECTIONS;++i','StartLayer(3,refractionReady?')))
    check('unique graphical object retained and cleanup still owns all sections',cpp.count('scene->createManualObject()')==1 and cpp.count('scene->destroyManualObject(geometry)')==1 and 'scene->removeRenderObjectListener(this)' in cpp)
    check('new layers use existing graphics API and no cloned gameplay entities',all(s not in region(cpp,'    Vector3 BoundFx','    Vector3 Joint') for s in ('createEntity','shareSkeletonInstanceWith','new Character','addWound','setFrameSpeedMultiplier','setPosition(')))
    check('per-cast diagnostic stage flags bounded',all(s in cpp for s in ('fxStages=0','fxStages&1','fxStages&2','fxStages&4','fxStages&8','if(logLines++>=4096)return')))
    # 按最坏情况所有96裂痕/32幻影同时可见，严格统计函数写入顶点与索引上界。
    # 保留既有最坏32幻影预算；追加96主体+96弧形残迹+48atlas雾片+2闪光+128光屑。
    # 原4层预算独立保留，新增透明占位段的上界由同层最大数量覆盖。
    source_quads=96+96+48+2+128
    vertices=96*56+128*4+32*(256+4)+12+576*4+168*4+192*6+source_quads*4
    indices=96*84+128*6+32*(320*3+6)+18+576*6+168*6+192*6+source_quads*6
    check('hard bounded geometry',vertices==19828 and vertices<32768 and indices<49152 and 'VFX_VERTEX_LIMIT=32768' in cpp and 'VFX_INDEX_LIMIT=49152' in cpp)
    stripped=re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'','',cpp,flags=re.S)
    stack=[];pairs={')':'(',']':'[','}':'{'}
    for c in stripped:
        if c in '([{':stack.append(c)
        elif c in pairs:assert stack and stack.pop()==pairs[c]
    check('C++ delimiter structure',not stack)
    js=re.search(r'<script>(.*?)</script>',(ROOT/'preview'/'index.html').read_text('utf8'),re.S).group(1)
    node=r'C:\Program Files\nodejs\node.exe'
    r=subprocess.run([node,'--check'],input=js,encoding='utf8',capture_output=True)
    check('preview JavaScript syntax',r.returncode==0)
    # 运行自有离线算法而非模拟/修改游戏。Canvas桩校验所有绘制坐标有限，固定空间片区/半球圆界使用真实预览函数。
    harness="""
const vm=require('node:vm');let operations=0;
function finite(args){for(let x of args)if(typeof x==='number'&&!Number.isFinite(x))throw Error('nonfinite drawing position');}
let ctx={createImageData(w,h){return{data:new Uint8ClampedArray(w*h*4)}}};
for(let n of ['putImageData','fillRect','beginPath','moveTo','lineTo','closePath','fill','stroke','arc','save','restore','translate','rotate','drawImage','clip'])ctx[n]=function(...args){finite(args);operations++;};
let canvas={width:560,height:500,clientWidth:560,clientHeight:500,getContext(){return ctx},setPointerCapture(){}},controls={focus:{checked:false},seek:{},ghost:{checked:true},mist:{checked:true},mirrors:{checked:true},phase:{},clock:{},play:{},restart:{}};
let context={URLSearchParams,location:{search:""},console,Math,Uint8ClampedArray,performance:{now:()=>0},devicePixelRatio:1,window:{},requestAnimationFrame(){},document:{querySelector(s){return s==='canvas'?canvas:controls[s.slice(1)]},createElement(){return {width:128,height:128,getContext(){return ctx}}}}};vm.createContext(context);
vm.runInContext(SOURCE,context);
let result=vm.runInContext('(()=>{let checked=0,hazeChecked=0,stationary=0,visiblePaths=new Set;window.JCE_PREVIEW.setTime(0);let initial=DATA.shards.map((s,i)=>shardPosition(i));for(let tt=0;tt<=6.7001;tt+=.05){window.JCE_PREVIEW.setTime(tt);for(let i=0;i<DATA.shards.length;i++){let p=shardPosition(i);for(let j=0;j<3;j++){let v=p[j];if(!v.every(Number.isFinite)||Math.hypot(v[0],v[2])>350.0001)throw Error("facet boundary");if(v.some((x,k)=>Math.abs(x-initial[i][j][k])>.000001))throw Error("falling mirror");checked++;}stationary++;}let cells=fogCells();if(cells.length!==168)throw Error("missing regular haze cells");for(let cell of cells){let v=boundAtmosphere(cell.p);if(v[1]<.8||Math.hypot(v[0],v[1]-.8,v[2])>350.00001)throw Error("haze hemisphere");hazeChecked++;}for(let i=0;i<16;i++){let age=tt-DATA.slashes[i*6][7];if(age>=0&&age<.68)visiblePaths.add(i);}}if(visiblePaths.size!==16)throw Error("missing phantom");return {facet_vertices_checked:checked,phantom_paths:visiblePaths.size,stationary_facet_frames:stationary,haze_cells_checked:hazeChecked};})()',context);
console.log(JSON.stringify({...result,draw_operations:operations}));
"""
    r=subprocess.run([node,'-'],input=harness.replace('SOURCE',json.dumps(js)),encoding='utf8',capture_output=True)
    check('preview finite coordinates, fixed spatial glints, full hemisphere haze, 16 phantom events',r.returncode==0)
    model=json.loads(r.stdout)
    # 源码开发后仍保留用户上次安装的1.1.0成品；不能把已安装版本误当作正式1.0冻结DLL。
    status=json.loads((ROOT/'docs/task-status.json').read_text('utf8'))
    # 外部用户已编译1.1.1，编译目录与仍安装的1.1.0分别按已记录身份核验；不伪称新源码已编译。
    check('observed build and unchanged package/installed DLL identities',hashlib.sha256((ROOT.parent/'bin/Release/JudgementCutEnd.dll').read_bytes()).hexdigest()==status['observed_build_artifact']['sha256'] and all(hashlib.sha256(p.read_bytes()).hexdigest()==status['dll_sha256'] for p in (ROOT/'package/JudgementCutEnd/JudgementCutEnd.dll',Path(r'D:\steam\steamapps\common\Kenshi\mods\JudgementCutEnd\JudgementCutEnd.dll'))))
    check('no falling or outlined mirrors in runtime drawing','ShardEdges(' not in cpp and 'Motes(' not in cpp and all(x not in region(cpp,'    void ShardPosition(','    void StartLayer(') for x in ('Quaternion spin','centre.y=','flat[','Ribbon(')))
    check('all 96 paths emit six delayed sweep echoes','SLASH_ECHOES=6' in cpp and 'SlashAfterimages(s,unsigned(i)' in cpp and 'echo<=SLASH_ECHOES' in cpp and 'delayed=age-.025f*echo' in cpp)
    check('six trail births complete for last slash before sheath',max(s[7] for s in rows)+6*.025+.05<5.15)
    check('grey continuous shell and ordered volumetric lattice',all(x in cpp for x in ('rings=12,sectors=48','level<7','ring<3','j<8','std::sort(cells,cells+count)','geometry->colour(.48f,.50f,.54f','BoundAtmosphere')) and 'scene_blend alpha_blend' in material.split('material JCE/Mist')[1].split('material JCE/Glass')[0])
    check('no local class template in v100 sorting','struct HazeCell' in cpp and 'HazeCell cells[MIST_CLOUDS]' in cpp and 'struct Cell' not in cpp)
    check('bounded four phantom echoes','PHANTOM_ECHOES=4' in cpp and 'echo<PHANTOM_ECHOES' in cpp)
    check('optical additive blend honors vertex alpha','scene_blend src_alpha one' in material.split('material JCE/Glass')[1])
    check('end-of-cast optical light clears in place','time>=SHEATH+.45f' in cpp and 'spatial_glints_cleared' in cpp and 'debris_landed' not in cpp)
    for p in (ROOT/'tools').glob('*.py'):ast.parse(p.read_text('utf8'))
    return {'static_passed':True,'base_check_count':len(old_result['checks']),'vfx_check_count':len(checks),'checks':checks,'geometry_upper_bound':{'vertices':vertices,'indices':indices},'preview_model':model,'compiled':False,'game_tested':False,'frozen_release':'1.0.0','development_version':'2.1.0-dev'}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
