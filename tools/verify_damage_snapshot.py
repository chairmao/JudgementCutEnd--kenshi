"""U键伤害快照专项检查；只解析源码/原生文件，不编译、不运行游戏。"""
from pathlib import Path
import ast, hashlib, json, struct, difflib
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'releases/JudgementCutEnd-2.9.8-vfx-accepted-20261010-203848'
GAME=Path('D:/steam/steamapps/common/Kenshi')

def region(text,begin,end):
    return text.split(begin,1)[1].split(end,1)[0]

def validate_snapshot_source(cpp):
    # 检查生产源码的数据流，避免模型“通过”却仍在结算路径读取当前装备。
    damage=region(cpp,'    void Damage(){','    unsigned vertex;')
    tick=region(cpp,'    void Tick(GameWorld* w){','Runtime* runtime=0;')
    capture=region(cpp,'    bool CaptureDamageSnapshot(Character* c){','    Damages SnapshotDamageFor(')
    snapshot=region(cpp,'    Damages SnapshotDamageFor(Character* target){','    void PrepareWeapon(')
    finish=region(cpp,'    void Finish(','    unsigned RefreshSkin')
    begin=region(cpp,'    void Begin(','    void ReleaseGraphics')
    return [
        ('U键冻结公共基准和种族加成','stats->getTotalAttackDamageFor(0)' in capture and 'castDamage.raceBonuses[i->first]=i->second' in capture),
        ('结算不读取攻击方缓存或武器',not any(x in damage for x in ('getStats(', 'getTotalAttackDamageFor(', 'SameDamageWeapon(', 'DamageWeapon(', 'castWeapon.getItem('))),
        ('跨帧卸武器不撤销','SameDamageWeapon(' not in tick and 'cast_damage_disarmed:' not in cpp),
        ('快照数值校验与有界种族表',all(x in capture for x in ('!ValidDamage(base)','!Finite(stats->bonusArmourPenetration)','stats->bonusRaces.size()>4096','!Finite(i->second)','castDamage.valid=true'))),
        ('种族分类保留原生优先级',snapshot.index('race->robot?')<snapshot.index('target->isAnimal()?')<snapshot.index('target->isHuman()?') and 'raceBonuses.find(race->data)' in snapshot),
        ('伤害仍经原生护甲/随机部位',damage.count('medical.addWound(')==1 and 'Damages d(base);' in damage and 'const unsigned strikeCount=unsigned(slashes.size())' in damage),
        ('加载/换世界逐击阻止结算',damage.count('CasterBlockedReason(')>=4 and 'world->isLoadingFromASaveGame()' in region(cpp,'    const char* CasterBlockedReason(','    Renderer* Render(') and 'world!=ou' in region(cpp,'    const char* CasterBlockedReason(','    Renderer* Render(')),
        ('结束和重放清理旧快照','castDamage.Clear()' in begin and 'castDamage.Clear()' in finish and 'Finish("restarted_by_key")' in tick),
        ('初始装备核验保留',all(x in cpp for x in ('inventory->getEquippedWeapons(equipped)','damageArmed=drawOK&&CaptureDamageSnapshot(c)','!DamageCacheMatches(c)'))),
        ('不接管已移交武器清理','inventory->hasItem(owned)&&human->_NV_getCurrentWeapon()==owned' in cpp and 'if(!drewWeapon||CasterBlockedReason(c))return;' in cpp),
        ('诊断每次一份快照并限制目标详情','equipment_change_after_begin=ignored' in cpp and 'if(hitDiagnostics++<16)' in damage),
    ]

def pe_at(data):
    nt=struct.unpack_from('<I',data,60)[0];opt=nt+24
    st=opt+struct.unpack_from('<H',data,nt+20)[0];n=struct.unpack_from('<H',data,nt+6)[0]
    def at(rva):
        for i in range(n):
            vs,va,rs,rp=struct.unpack_from('<IIII',data,st+i*40+8)
            if va<=rva<va+max(vs,rs):return rp+rva-va
        raise ValueError(hex(rva))
    return at

def run():
    checks=[]
    def check(name,ok):
        checks.append(dict(name=name,passed=bool(ok)))
        if not ok:raise AssertionError(name)
    raw=(ROOT/'JudgementCutEnd.cpp').read_bytes();cpp=raw.decode('utf-8-sig').replace('\r\n','\n')
    check('源码UTF-8 BOM/CRLF保留',raw.startswith(b'\xef\xbb\xbf') and b'\n' not in raw.replace(b'\r\n',b''))
    for name,ok in validate_snapshot_source(cpp):check(name,ok)
    # 已接受的2.9.8视觉、姿势、时速恢复、目标收集及踉跄函数必须逐字一致。
    baseline=(BASE/'source/JudgementCutEnd.cpp').read_text('utf-8-sig')
    for name,a,b in (
        ('全部特效绘制','    unsigned vertex;','    void Tick(GameWorld* w){'),
        ('骨骼刷新/姿势/范围','    unsigned RefreshSkin','    void Collect(){'),
        ('时间/输入基础逻辑','    Renderer* Render(','    void Begin('),
        ('图形释放','    void ReleaseGraphics','    void Finish('),
        ('姿势/帧钩子','Runtime* runtime=0;','__declspec(dllexport) void startPlugin()')):
        check(name+'保持2.9.8',region(cpp,a,b)==region(baseline,a,b))
    # 比对所有源码差异是否落在已授权区域，防止其它视觉区域有未注意到的变化。
    old=baseline.splitlines();new=cpp.splitlines()
    allowed=[('#include', '#include'), ('void Log(', 'void Log(')]
    zones=[]
    for a,b in [('struct Settings {','// v2在旋转后增加局部位移'),('#include <kenshi/Damages.h>', '#include <kenshi/combat/CombatClass.h>'),('struct WeaponDamageSnapshot','struct Runtime'),('    Weapon* PreferredDamageWeapon(', '    Renderer* Render('),('    bool SameDamageWeapon(', '    Renderer* Render('),('    void Begin(', '    void ReleaseGraphics'),('    void Finish(', '    unsigned RefreshSkin'),('    void Collect(){','    unsigned vertex;'),('    void Tick(', 'Runtime* runtime=0;')]:
        if a in baseline:zones.append((baseline[:baseline.index(a)].count('\n'),baseline[:baseline.index(b)].count('\n')))
    # 新结构插入点在Runtime之前；只允许新增快照状态和版本标识。
    def permitted(i,j,lines):
        if any(lo<=i and j<=hi for lo,hi in zones):return True
        text='\n'.join(lines)
        return all(x.startswith('#include') or 'JCE 2.9.' in x or 'version=2.9.' in x or 'struct Runtime' in x or 'Settings settings;GameWorld* world;' in x or 'std::vector<BoneState> bones;' in x or 'WeaponDamageSnapshot' in x or 'EquippedWeapon(' in x or '启动资格只认可' in x or 'const hand& selected=' in x or 'lektor<Item*> equipped;' in x or 'for(unsigned i=0;i<equipped.size();' in x or 'if(equipped[i]&&SameHand(selected,' in x or 'if(!c||!weapon)return false;' in x or x.strip() in ('return false;','}') or '2.9.9：' in x or 'bonusRaces的GameData' in x or 'float cut,blunt,pierce' in x or 'raceBonuses' in x or 'void Clear()' in x or x.strip() in ('};','') for x in lines)
    for tag,i,j,k,l in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
        if tag!='equal':check('授权差异行'+str(i+1),permitted(i,j,old[i:j]+new[k:l]))
    manifest=json.loads((BASE/'release-manifest.json').read_text('utf8'))
    count=0
    for item in manifest['inventory']:
        if item['path'].startswith('source/package/JudgementCutEnd/'):
            p=ROOT/item['path'][len('source/'):]
            # 本轮仅更新INI/README的条件说明；数值配置仍与定稿逐项一致，纹理/材质/动画逐字核验。
            if p.name=='README.md':continue
            if p.name=='JudgementCutEnd.ini':
                def values(text):
                    return dict(line.split('=',1) for line in text.splitlines() if '=' in line and not line.startswith(('#',';')))
                check('INI数值未变化',values(p.read_text('utf8'))==values((BASE/item['path']).read_text('utf8')))
            else:check('包资源未变化:'+p.name,hashlib.sha256(p.read_bytes()).hexdigest().upper()==item['sha256'])
            count+=1
    check('已核对资源非空',count>20)
    check('游戏DLL仍为2.9.8',hashlib.sha256((GAME/'mods/JudgementCutEnd/JudgementCutEnd.dll').read_bytes()).hexdigest().upper()==manifest['dll_sha256'])
    for p in (ROOT/'tools').glob('*.py'):ast.parse(p.read_text('utf8'))
    check('工具Python语法',True)
    game=(GAME/'kenshi_x64.exe').read_bytes();at=pe_at(game)
    check('原生证据版本匹配',hashlib.sha256(game).hexdigest()=='504b362cde850d56afb1cea6f5b7b0ee014d9dd7b47e188599d91c804502cd3e')
    def bytes_at(rva,n):return game[at(rva):at(rva)+n]
    check('原生空目标明确跳过目标分支',bytes_at(0x885B66,9)==bytes.fromhex('48 85 ED 0F 84 1E 01 00 00'))
    check('空目标仍经skillMultDamage',bytes_at(0x885C8D,5)==bytes.fromhex('F3 0F 10 56 48'))
    check('原生种族键为RaceData.data',bytes_at(0x885BEF,4)==bytes.fromhex('48 8B 48 40'))
    check('机器人类型来自RaceData.robot',bytes_at(0x885B80,4)==bytes.fromhex('80 78 7C 00'))
    check('原生护甲穿透来自bonusArmourPenetration',bytes_at(0x885BC6,6)==bytes.fromhex('8B 86 C0 01 00 00'))
    # 这里只度量拆分前后浮点运算顺序的误差，不冒充游戏伤害或护甲测试。
    def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
    error=0
    for base in (0.001,1,17.333,100,10000):
        for skill in (.2,.75,1,3.5):
            for mult in (.25,.8,1,1.5,2.25):
                before=f32(f32(f32(base)*f32(mult))*f32(skill))
                after=f32(f32(f32(base)*f32(skill))*f32(mult))
                error=max(error,abs(before-after)/max(abs(before),1e-9))
    check('常见范围浮点舍入相对差小于百万分之一',error<1e-6)
    return dict(static_passed=True,checks=checks,asset_count=count,rounding_relative_error=error,source_sha256=hashlib.sha256(raw).hexdigest().upper(),compiled=False,game_tested=False)

if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))