"""精确读取本地SSE折射网格与九条强度曲线；只读原资源，不依赖或执行Skyrim。"""
from pathlib import Path
import importlib.util, json, hashlib, math, argparse
SOURCE=Path("E:/skyrimspecialedition/mods/Judgement Cut End - ap05's Remake/Meshes/effects/AP05/JCE030CutRefraction.nif")
SCHEMA="https://github.com/niftools/nifxml/blob/develop/nif.xml"

def inspect(path=SOURCE):
    # 基本浮点/sequence解析复用现有工具；新增几何解析限定SSE100并消费完整块，禁止按字节碰巧匹配。
    spec=importlib.util.spec_from_file_location('source_nif',Path(__file__).with_name('inspect_skyrim_vfx.py'))
    nif=importlib.util.module_from_spec(spec);spec.loader.exec_module(nif)
    raw=path.read_bytes();parsed=nif.parse(path);by={b['index']:b for b in parsed['parsed_blocks']}
    r=nif.Reader(raw[raw.index(b'\n')+1:])
    version,endian,user,count,bs=[r.read(f) for f in ('I','B','I','I','I')]
    if (version,endian,user,bs)!=(0x14020007,1,12,100):raise ValueError('Not SSE100')
    for _ in range(3):r.string('B')
    types=[r.string() for _ in range(r.read('H'))]
    indices=[r.read('H') for _ in range(count)];sizes=[r.read('I') for _ in range(count)]
    ns=r.read('I');r.read('I');strings=[r.string() for _ in range(ns)]
    for _ in range(r.read('I')):r.read('I')
    def name(i):
        if i==0xffffffff:return ''
        if i>=len(strings):raise ValueError('Bad name')
        return strings[i]
    def group(q,dim):
        n=q.read('I');itype=q.read('I') if n else 0
        if n>128 or (n and itype not in (1,2)):raise ValueError('Unsupported key group')
        keys=[]
        for _ in range(n):
            k={'time':q.read('f'),'value':q.read(str(dim)+'f')}
            if itype==2:k.update(forward=q.read(str(dim)+'f'),backward=q.read(str(dim)+'f'))
            keys.append(k)
        return {'interpolation':itype,'keys':keys}
    meshes=[];nodes=[];transforms=[]
    for index,(ti,size) in enumerate(zip(indices,sizes)):
        if ti>=len(types) or size>len(r.data)-r.pos:raise ValueError('Block range')
        data=r.data[r.pos:r.pos+size];r.pos+=size;t=types[ti];q=nif.Reader(data)
        if t in ('BSFadeNode','NiNode','BSTriShape'):
            item={'index':index,'type':t,'name':name(q.read('I'))}
            n=q.read('I')
            if n>10000:raise ValueError('Extra data')
            item.update(extra=[q.read('i') for _ in range(n)],controller=q.read('i'),flags=q.read('I'),
                        translation=q.read('3f'),rotation=q.read('9f'),scale=q.read('f'),collision=q.read('i'))
            if t!='BSTriShape':
                n=q.read('I')
                if n>10000:raise ValueError('Children')
                item['children']=[q.read('i') for _ in range(n)]
                ne=q.read('I')
                if ne>10000:raise ValueError('Effects')
                item['effects']=[q.read('i') for _ in range(ne)];q.done();nodes.append(item);continue
            item.update(bound=q.read('4f'),skin=q.read('i'),shader=q.read('i'),alpha=q.read('i'))
            desc=q.read('Q');nt=q.read('H');nv=q.read('H');data_size=q.read('I')
            # 本文件是非蒙皮的完整精度位置、半精度UV、打包法线/切线；其他描述符明确拒绝。
            if desc!=0x1b00000650407 or nv>2048 or nt>2048 or data_size!=nv*28+nt*6:
                raise ValueError('Unsupported vertex layout')
            item.update(vertex_desc=hex(desc),triangles_count=nt,vertices_count=nv,positions=[],uv=[],normals=[],tangents=[])
            for _ in range(nv):
                item['positions'].append(q.read('3f'));q.read('f')
                item['uv'].append(q.read('2e'))
                item['normals'].append([(v/127.5-1) for v in q.read('4B')[:3]])
                item['tangents'].append([(v/127.5-1) for v in q.read('4B')[:3]])
            item['triangles']=[q.read('3H') for _ in range(nt)]
            if any(v>=nv for tri in item['triangles'] for v in tri):raise ValueError('Mesh index')
            if q.read('I')!=0:raise ValueError('Unexpected particle copy')
            q.done()
            item['local_min']=[min(p[k] for p in item['positions']) for k in range(3)]
            item['local_max']=[max(p[k] for p in item['positions']) for k in range(3)]
            meshes.append(item)
        elif t=='NiTransformInterpolator':
            item={'index':index,'type':t,'translation':q.read('3f'),'rotation':q.read('4f'),
                  'scale':q.read('f'),'data':q.read('i')}
            q.done();transforms.append(item)
        elif t=='NiTransformData':
            # 实际引用文件只有比例键；不把未知旋转编码猜作Quaternion或生成伪关键帧。
            if q.read('I')!=0:raise ValueError('Rotation keys require another parser')
            item={'index':index,'type':t,'translation':group(q,3),'scale':group(q,1)}
            q.done();transforms.append(item)
    sequences=[b for b in by.values() if b['type']=='NiControllerSequence']
    bindings=[{'sequence':s['name'],**c} for s in sequences for c in s['controlled_blocks']]
    curves=[]
    for mesh in sorted(meshes,key=lambda m:(m['name']=='screen1',m['name'])):
        controllers=[b for b in by.values() if b['type']=='BSLightingShaderPropertyFloatController'
                     and b['target']==mesh['shader'] and b['variable']==0]
        if len(controllers)!=1:raise ValueError('Expected one RefractionStrength per shape')
        c=controllers[0];interp=by[c['interpolator']];keys=by[interp['data']]
        if interp['type']!='NiFloatInterpolator' or keys['type']!='NiFloatData':raise ValueError('Unexpected strength interpolation')
        values=keys['keys']
        if len(values)<2 or values[0]['time']!=0 or any(not math.isfinite(v) for k in values for v in k.values()):raise ValueError('Invalid strength keys')
        curves.append({'name':mesh['name'],'mesh':mesh['index'],'shader':mesh['shader'],'controller':c['index'],
                       'frequency':c['frequency'],'phase':c['phase'],'start':c['start'],'stop':c['stop'],
                       'interpolation':keys['interpolation'],'peak':max(k['value'] for k in values),'keys':values})
    if [c['name'] for c in curves]!=['slash'+str(i) for i in range(1,9)]+['screen1']:raise ValueError('Source optical names changed')
    return {'source':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'schema':SCHEMA,
            'meshes':meshes,'nodes':nodes,'transforms':transforms,'bindings':bindings,'curves':curves,
            'unimplemented':'Skyrim LightingShader lighting/normal-map response and engine timing are not reproduced exactly',
            'source_read_only':True}

def curve_text(result):
    # 独立九条曲线保留名称、频率、峰值、键与归一化切线；空间/像素单位仅在Kenshi适配层定义。
    rows=['JCEOPTICS 1 9']
    for c in result['curves']:
        if c['phase']!=0 or c['start']!=0:raise ValueError('Unsupported controller clock')
        rows.append('CURVE %s %d %.9g %.9g %d'%(c['name'],c['interpolation'],c['frequency'],c['peak'],len(c['keys'])))
        for k in c['keys']:rows.append('KEY %.9g %.9g %.9g %.9g'%(k['time'],k['value'],k.get('backward',0),k.get('forward',0)))
    return '\n'.join(rows)+'\n'

if __name__=='__main__':
    # 取证输出只允许新建。发布CSV由已备份的任务流程写入，不在只读工具里覆盖任何资源。
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=inspect();payload=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        with args.output.open('xb') as f:f.write(payload.replace('\n','\r\n').encode('utf8'))
    else:print(payload)
