"""真实HKX来源、只读网格、坏资源与局部HDR回收核验；不调用编译器。"""
from pathlib import Path
import hashlib,json,math,struct,re,importlib.util
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'package/JudgementCutEnd/assets';checks=[]
def check(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    if not ok:raise AssertionError(name)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_mesh(b):
    # 独立格式检查用于截断/溢出用例；源代码连接另行核验，不冒充C++执行。
    if len(b)<28:raise ValueError('short header')
    magic,f,v,n,fps,d=struct.unpack_from('<8sIIIff',b)
    if (magic,f,v,n)!=(b'JCEPHM2\0',403,198,256) or not math.isfinite(fps) or abs(fps-60)>.001 or not math.isfinite(d) or abs(d-6.7)>.001:raise ValueError('header')
    if len(b)!=28+n*6+f*v*12:raise ValueError('length')
    idx=struct.unpack_from('<'+str(n*3)+'H',b,28)
    if any(i>=v for i in idx):raise ValueError('index')
    xyz=list(struct.iter_unpack('<3f',b[28+n*6:]))
    if any(not all(math.isfinite(x) for x in p) or math.sqrt(sum(x*x for x in p))>50 for p in xyz):raise ValueError('position')
    return f,v,n,idx,xyz
def rejected(b):
    try:read_mesh(b)
    except (ValueError,struct.error):return True
    return False
def main():
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig');p=json.loads((ROOT/'docs/retarget-provenance.json').read_text('utf8'))
    check('actual source HKX and XPMSSE skeleton identity',all(digest(Path(p[k]))==p[k.replace('_source','_sha256')] for k in ('animation_source','skeleton_source')))
    check('source normal animation, actual 211 frames and 242 tracks',p['source_frames']==211 and p['source_tracks']==242 and p['source_duration']==7)
    check('retarget 23 named bones at 60 Hz',len(p['mapping'])==23 and p['output_tracks']==23 and p['output_frames']==403)
    check('clip and phantom hashes match producer record',digest(A/'jce.clip')==p['output_clip_sha256'] and digest(A/'jce_phantom.bin')==p['phantom']['sha256'])
    decoder=Path(r'D:\CodexWorkSpace\Sessions\20261002-235652-kenshi-crash-407794f2\Task-JCEAssetPort-20261007')
    check('offline GPL decoder files pinned',all(digest(decoder/name)==h for name,h in p['decoder']['files'].items()))
    check('root horizontal travel removed and vertical floor correction explicit',p['horizontal_root_motion_removed'] and p['maximum_floor_error']<1e-6 and p['retarget_velocity_cap_clip_degrees_per_second']==720)
    check('source drawing and sheath event times recorded',any('Draw' in x['text'] and abs(x['time']-2.1)<.01 for x in p['events']) and any('Sheath' in x['text'] for x in p['events']))
    b=(A/'jce_phantom.bin').read_bytes();f,v,n,indices,xyz=read_mesh(b)
    check('mesh valid exact bounded topology and allocation',f==403 and v==198 and n==256 and len(b)<1024*1024)
    scene=json.loads((ROOT/'preview/scene.json').read_text('utf8'))
    check('binary topology equals preview',list(zip(*[iter(indices)]*3))==[tuple(t) for t in scene['phantom']['triangles']])
    check('all baked binary vertices equal preview within float precision',all(max(abs(x-y) for x,y in zip(pos,scene['phantom']['frames'][i//v][i%v]))<3e-6 for i,pos in enumerate(xyz)))
    for name,bad in [('empty',b''),('header truncated',b[:20]),('end truncated',b[:-1]),('extra data',b+b'\0'),('wrong magic',b'X'+b[1:])]:
        check('reject '+name,rejected(bad))
    for name,offset,fmt,value in [('huge frame allocation',8,'I',2**32-1),('huge vertex allocation',12,'I',2**32-1),('invalid triangle index',28,'H',198),('nonfinite vertex',28+n*6,'f',math.nan),('huge vertex',28+n*6,'f',1000),('NaN fps',20,'f',math.nan)]:
        bad=bytearray(b);struct.pack_into('<'+fmt,bad,offset,value);check('reject '+name,rejected(bad))
    check('runtime validates mesh dimensions before allocation',cpp.index('phantomAsset.frames!=403')<cpp.index('phantomAsset.positions.resize(') and 'Invalid phantom asset length' in cpp)
    check('v1 compatible and v2 root-only positions',all(s in cpp for s in ('(version!=1&&version!=2)','if(clipVersion==2)','tr.name!="Bip01"','Unexpected keyframe fields')))
    check('baked sample stable at last frame and bounded simultaneous bodies','Vector3 posed[256]' in cpp and 'bodies<PHANTOM_BODY_LIMIT' in cpp and 'PHANTOM_BODY_LIMIT=32' in cpp and 'phantomAsset.frames-2' in cpp)
    check('zero alpha fallback keeps material section nonempty','else TriangleFx(Vector3::ZERO,Vector3::UNIT_X,Vector3::UNIT_Y,0,0)' in cpp)
    capture=cpp.split('    void CaptureBackground(){')[1].split('    void MakeResources(){')[0]
    check('copy before own section and once per frame','rend==geometry->getSection(0))CaptureBackground();' in cpp and 'if(captureFrame==frame)return;' in capture)
    check('copy source is bound RTV, destination independent','OMGetRenderTargets(1,&view.p,0)' in capture and 'destination==texture.p' in capture and 'CopyResource(destination,texture.p)' in capture)
    check('copy rejects format dimensions arrays mip multisample changes',all(s in capture for s in ('src.Width!=dst.Width','src.Height!=dst.Height','src.Format!=dst.Format','src.MipLevels!=dst.MipLevels','src.ArraySize!=1','dst.ArraySize!=1','src.SampleDesc.Count!=1','dst.SampleDesc.Count!=1','src.SampleDesc.Quality!=dst.SampleDesc.Quality')))
    check('shader SRV state restored in render callback',capture.index('PSGetShaderResources')<capture.index('PSSetShaderResources(1,1,&none)')<capture.index('CopyResource(')<capture.index('PSSetShaderResources(1,1,&old.p)'))
    check('no CPU readback or global camera/compositor edits',all(s not in cpp for s in ('D3D11_USAGE_STAGING','captureContext->Map','addWorkspace(','setListener(this)','getCompositorManager2()')))
    check('getter COM refs owned and immediate context released','~ComOwned(){if(p)p->Release();}' in cpp and 'captureContext->Release();captureContext=0;' in cpp)
    release=cpp.split('    void ReleaseRefraction(){')[1].split('    void PrepareRefraction(){')[0]
    check('own texture removed even after material reset error','refraction_material_release_error' in release and 'Ogre::ResourceManager::remove(Ogre::String("JCE/SceneCopy"))' in release and 'background.setNull();' in release)
    check('render copy disabled independently on capture failure','refractionReady=false;' in capture and 'captureValid",0.f' in capture)
    hlsl=(A/'jce_refraction.hlsl').read_text('utf8');prog=(A/'jce_refraction.program').read_text('utf8')
    check('own HLSL interface matches existing coloured vertex program','SV_Position' in hlsl and 'TEXCOORD0' in hlsl and 'register(t1)' in hlsl and 'source jce_refraction.hlsl' in prog and 'target ps_4_0' in prog and 'viewport_size' in prog)
    check('captured viewport projection and bounded pixel distortion','input.pos.xy*viewport.zw' in hlsl and '*8.0*viewport.zw' in hlsl and 'captureValid' in hlsl)
    stage=(ROOT/'tools/Stage-LocalMod.ps1').read_text('utf-8-sig')
    check('version gate before copying old DLL',stage.index('DLL version does not match')<stage.index('Copy-BackedFile $compiledDll'))
    check('current source version marker 2.1.0','version=2.1.0-dev' in cpp and 'resources=9' in cpp)
    # 源码已进入2.1.0，用户上次编译的1.2.1（正式2.0）只作为历史产物核验；两者不可混同。
    # 本验证器仍不会代编译。资源可独立更新，因此DLL当前不意味着动画资源已经部署。
    status=json.loads((ROOT/'docs/task-status.json').read_text('utf8'))
    check('source version recorded independently of user build',status['source_version']=='2.1.0-dev')
    if status.get('compiled'):
        check('user native artifact identity recorded without agent compilation',
              not status['last_user_compilation']['agent_ran_compiler'] and
              digest(Path(status['observed_build_artifact']['path']))==status['observed_build_artifact']['sha256'])
    # 整个变更域文本都严格UTF-8，保留BOM与CRLF；既有历史文档不自动修复。
    targets=[ROOT/'JudgementCutEnd.cpp',ROOT/'tools/author_port.py',ROOT/'tools/verify_port.py',ROOT/'tools/verify.py',ROOT/'tools/verify_vfx.py',ROOT/'tools/Stage-LocalMod.ps1',ROOT/'preview/index.html',ROOT/'preview/scene.json']+list(A.glob('jce_refraction.*'))
    for path in targets:
        raw=path.read_bytes();t=raw.decode('utf-8-sig')
        check('encoding and Chinese '+path.name,'\n' not in t.replace('\r\n','') and not any(s in t for s in ['\ufffd','\u951f\u65a4\u62f7','\u00c3','\u00c2','\u00ef\u00bb\u00bf']))
    return {'passed':True,'checks':checks,'check_count':len(checks),'compiled':False,'game_tested':False,'mesh_bytes':len(b),'source_version':'2.1.0-dev'}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
