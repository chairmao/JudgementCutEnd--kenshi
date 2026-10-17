"""角色资格、伤害中断与玩家队员保护：源码/原生接口合同检查，不编译或启动游戏。"""
from pathlib import Path
import ast,hashlib,json,re
from verify_damage_snapshot import region,pe_at
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('D:/steam/steamapps/common/Kenshi')

def run():
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig');checks=[]
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)))
        if not value:raise AssertionError(name)
    blocked=region(cpp,'    const char* CasterBlockedReason(','    Renderer* Render(')
    current=region(cpp,'    bool CurrentPlayerMember(','    bool ProtectedPlayer(')
    protected=region(cpp,'    bool ProtectedPlayer(','    void CaptureProtectedPlayers(')
    roster=region(cpp,'    void CaptureProtectedPlayers(','    const char* CasterBlockedReason(')
    begin=region(cpp,'    void Begin(','    void ReleaseGraphics(')
    finish=region(cpp,'    void Finish(','    unsigned RefreshSkin')
    damage=region(cpp,'    void Damage(){','    unsigned vertex;')
    collect=region(cpp,'    void Collect(){','    const char* Stagger(')
    stagger=region(cpp,'    const char* Stagger(','    void Damage(){')
    tick=region(cpp,'    void Tick(','Runtime* runtime=0;')
    check('施放资格共享启动/每帧/每击', 'CasterBlockedReason(c)' in begin and 'CasterBlockedReason(c)' in tick and 'CasterBlockedReason(currentCaster)' in damage)
    check('资格检查加载/死亡/昏迷/失能',all(x in blocked for x in ('world!=ou','world->isLoadingFromASaveGame()','c->isDead()','c->medical.unconcious','c->_NV_isUnconcious()','c->isRagdoll()','c->isBeingCarried()')))
    check('人形允许机器人排除动物','!c->isHuman()||c->isAnimal()' in blocked and 'race->robot' not in blocked)
    check('离队检查标记与全部成员列表','!c->isPlayerCharacter()||!CurrentPlayerMember(c)' in blocked and 'getAllPlayerCharacters()' in current and 'getCurrentPlatoon' not in current)
    check('四肢仅原生或替代有效','for(int i=0;i<4;++i)' in blocked and 'state!=LIMB_ORIGINAL&&state!=LIMB_REPLACED' in blocked)
    check('义肢装配身份与部位有效性',all(x in blocked for x in ('part->me!=c','part->medical!=&c->medical','state==LIMB_REPLACED&&!part->robotLimb','c->medical.getPart(limb)')))
    check('当前医疗健康含眩晕维修且拒绝原血负值','part->flesh-part->fleshStun+part->juryRigging' in blocked and 'part->flesh<0||health<0' in blocked and 'health<=0' not in blocked)
    check('加载未初始化与非有限健康拒绝','!Finite(health)' in blocked and '!Finite(maximum)||maximum<=0' in blocked)
    check('武器仅启动要求', 'caster_requires_equipped_melee_weapon' in begin and not any(x in blocked for x in ('PreferredDamageWeapon','SameDamageWeapon','EquippedWeapon','DamageWeapon')))
    check('快照失败不开始纯演出','if(settings.damage&&!damageArmed)throw' in begin and begin.index('weapon_damage_snapshot_not_ready')<begin.index('active=true'))
    check('键位配置不变','CastKeyVK' in cpp and 'castKey(\'U\')' in cpp and 'GetAsyncKeyState(int(settings.castKey))' in tick)
    check('保护全部玩家和起始队员','c->isPlayerCharacter()||CurrentPlayerMember(c)' in protected and 'SameHand(protectedPlayers[i],h)' in protected and 'getAllPlayerCharacters()' in roster)
    check('初始名单不是选择名单','selectedCharacter' not in roster and 'getCurrentPlatoon' not in roster and 'member->getHandle()' in roster)
    check('加载失去玩家接口时默认保护','world->isLoadingFromASaveGame())return true;' in protected)
    check('目标收集优先玩家保护',collect.index('ProtectedPlayer(other)')<collect.index('c->isEnemy(other,true)'))
    check('每击玩家保护优先敌对',damage.index('ProtectedPlayer(v)')<damage.index('c->isEnemy(v,true)') and damage.count('ProtectedPlayer(v)')==3)
    check('唯一扣血入口最后闸门',cpp.count('medical.addWound(')==1 and re.search(r'if\(ProtectedPlayer\(v\)\)\{stop="player_protected";break;\}\s*GameData\* part=v->medical\.addWound',damage) is not None)
    check('踉跄不能作用于玩家成员',stagger.index('ProtectedPlayer(v)')<stagger.index('a->startStumble(reaction)') and 'CasterBlockedReason(c)' in stagger)
    check('医疗回调后资格失效立即Finish返回','CasterBlockedReason(Resolve())' in damage and damage.count('Finish(')>=4 and 'Finish(reason);return;' in damage)
    check('不回滚已提交伤害','committed_hits=' in damage and 'setHealth(' not in damage and 'flesh=' not in damage)
    check('中断后本帧不绘制','{Damage();if(!active)return;}' in tick and tick.index('{Damage();if(!active)return;}')<tick.index('Draw();'))
    check('结束清空两个快照且解除骨骼/音效','protectedPlayers.clear()' in finish and 'castDamage.Clear()' in finish and 'setManuallyControlled(false)' in finish and 'PlaySoundW(0,0,0)' in finish)
    check('时间恢复优先清理且保留债务',finish.index('RestoreTime(reason,validWorld)')<finish.index('ReleaseGraphics(') and 'speedRestorePending=true' in finish)
    check('原版加速倍率与96次结算未改','const unsigned strikeCount=unsigned(slashes.size())' in damage and 'Damages d(base)' in damage)
    # 原生字节证明字段/函数来源；不依赖头文件旧public RVA。
    game=(GAME/'kenshi_x64.exe').read_bytes();at=pe_at(game)
    check('证据游戏文件版本一致',hashlib.sha256(game).hexdigest()=='504b362cde850d56afb1cea6f5b7b0ee014d9dd7b47e188599d91c804502cd3e')
    def code(rva,n):return game[at(rva):at(rva)+n]
    check('const全玩家列表导出返回成员容器',code(0x7f18f0,8)==bytes.fromhex('48 8D 81 B0 02 00 00 C3'))
    check('原生玩家标记函数判定派系玩家接口',code(0x790b37,3)==bytes.fromhex('FF 50 58') and code(0x790b3c,7)==bytes.fromhex('48 39 88 50 02 00 00'))
    check('原生MedicalSystem查询RobotLimbs状态',code(0x6430a5,7)==bytes.fromhex('48 8B 89 C8 00 00 00'))
    check('原生义肢maxHP映射部位最大值',code(0x643b8c,6)==bytes.fromhex('8B 82 68 02 00 00') and code(0x643b92,3)==bytes.fromhex('89 41 54'))
    check('原生义肢stun与flesh映射',code(0x643ba8,6)==bytes.fromhex('8B 82 74 02 00 00') and code(0x643bc4,8)==bytes.fromhex('F3 0F 5C 82 6C 02 00 00') and code(0x643bcf,5)==bytes.fromhex('F3 0F 11 41 40'))
    check('原生实时派生健康公式',code(0x6431b0,15)==bytes.fromhex('F3 0F 10 41 40 F3 0F 5C 41 44 F3 0F 58 41 4C'))
    # 平台ABI边界：项目只含授权CPP，工具语法和编码检查不触发任何编译。
    for p in (ROOT/'tools').glob('*.py'):ast.parse(p.read_text('utf8'))
    check('验证器Python语法',True)
    raw=(ROOT/'JudgementCutEnd.cpp').read_bytes()
    check('CPP BOM/CRLF和中文安全',raw.startswith(b'\xef\xbb\xbf') and b'\n' not in raw.replace(b'\r\n',b'') and not any(x in cpp for x in ('\ufffd','锟斤拷','Ã','Â','ï»¿')))
    return dict(static_passed=True,checks=checks,check_count=len(checks),source_sha256=hashlib.sha256(raw).hexdigest().upper(),compiled=False,game_tested=False,limits='源码及本机原生接口合同检查，不能代替C++编译和实机回调测试')
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))