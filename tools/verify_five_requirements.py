"""五项施放合同：静态源码连接与键位边界模型；不编译，不启动游戏。"""
from pathlib import Path
import json,re,hashlib
from verify_damage_snapshot import region
ROOT=Path(__file__).resolve().parents[1]

def source_contracts(cpp):
    blocked=region(cpp,'    const char* CasterBlockedReason(','    Renderer* Render(')
    begin=region(cpp,'    void Begin(','    void ReleaseGraphics(')
    tick=region(cpp,'    void Tick(','Runtime* runtime=0;')
    preferred=region(cpp,'    Weapon* PreferredDamageWeapon(','    bool EquippedWeapon(')
    equipped=region(cpp,'    bool EquippedWeapon(','    bool SameDamageWeapon(')
    settings=region(cpp,'struct Settings {','// v2在旋转后增加局部位移')
    return {
      '1人形包含机器人动物排除':'!c->isHuman()||c->isAnimal()' in blocked and 'race->robot' not in blocked,
      '2四肢原生或已装义肢':'for(int i=0;i<4;++i)' in blocked and 'state!=LIMB_ORIGINAL&&state!=LIMB_REPLACED' in blocked and 'state==LIMB_REPLACED&&!part->robotLimb' in blocked,
      '2实时健康与零边界':'part->flesh<0||health<0' in blocked and 'health<=0' not in blocked and '!Finite(maximum)||maximum<=0' in blocked,
      '3加载先于选中角色解析':tick.index('w->isLoadingFromASaveGame()?"loading"')<tick.index('selectedCharacter.getCharacter()'),
      '3加载上升沿消费不积压':tick.index('wasKey=combo')<tick.index('w->isLoadingFromASaveGame()?"loading"') and 'if(!active)return;' in tick,
      '3活动演出加载取消':'if(w->isLoadingFromASaveGame()){Finish("loading");return;}' in tick,
      '3世界身份更换停止旧演出':'Finish("world_replaced",false)' in tick and 'if(!SameAnimation(c))' in tick,
      '3启动初始化和骨架所有权验证':all(x in begin for x in ('animation->getIsActivated()','skin.initialised(body)','Visible body/skeleton mismatch','Another plugin owns pose bone')),
      '4使用游戏原生选择而非首个物品':'human->_NV_getThePreferredWeapon()' in preferred and 'SKILL_UNARMED' in preferred and 'inventory->getEquippedWeapons(equipped)' in equipped,
      '4武器是启动条件':'caster_requires_equipped_melee_weapon' in begin and not any(x in tick for x in ('SameDamageWeapon(', 'EquippedWeapon(')),
      '4伤害快照准备失败拒绝':'if(settings.damage&&!damageArmed)throw' in begin and begin.index('weapon_damage_snapshot_not_ready')<begin.index('active=true'),
      '5默认U输入使用配置':"castKey('U')" in settings and 'GetAsyncKeyState(int(settings.castKey))' in tick,
      '5严格整数拒绝尾部垃圾':all(x in settings for x in ('strtol(value.c_str(),&end,10)',"*end=='\\0'",'end!=value.c_str()','vk>=65&&vk<=90','vk>=VK_F1&&vk<=VK_F12')),
      '5空格BOM行末注释':all(x in settings for x in ('ConfigText(line.substr(0,e))','\\xEF\\xBB\\xBF','value.find_first_of("#;")')),
    }

def config_model(text,previous=85):
    # 明确为解析边界的离线合同模型，不能代替v100 C++的执行；源码连接独立检查上述完整消费条件。
    key=previous
    for line in text.lstrip('\ufeff').splitlines():
        line=line.strip(' \t\r')
        if not line or line.startswith(('#',';')) or '=' not in line:continue
        name,value=line.split('=',1);name=name.strip(' \t\r')
        value=re.split('[#;]',value,1)[0].strip(' \t\r')
        if name!='CastKeyVK':continue
        if re.fullmatch('[+-]?[0-9]+',value):
            vk=int(value)
            if 65<=vk<=90 or 112<=vk<=123:key=vk
    return key

def run():
    raw=(ROOT/'JudgementCutEnd.cpp').read_bytes();cpp=raw.decode('utf-8-sig');checks=[]
    def check(name,ok):
        checks.append(dict(name=name,passed=bool(ok)))
        if not ok:raise AssertionError(name)
    for name,ok in source_contracts(cpp).items():check(name,ok)
    cases=[('CastKeyVK=85',85),('  CastKeyVK = 119 # F8',119),('\ufeffCastKeyVK=74 ; J',74),('CastKeyVK=112',112),('CastKeyVK=123',123),('CastKeyVK=65',65),('CastKeyVK=90',90),('CastKeyVK=85abc',85),('CastKeyVK=119.0',85),('CastKeyVK=',85),('CastKeyVK=-119',85),('CastKeyVK=27',85),('CastKeyVK=64',85),('CastKeyVK=91',85),('CastKeyVK=111',85),('CastKeyVK=124',85),('CastKeyVK=999999999999999999999999',85),('CastKeyVK=119\nCastKeyVK=bad',119)]
    for n,(text,want) in enumerate(cases):check('配置边界离线模型'+str(n),config_model(text)==want)
    # 故意删掉生产连接验证检查能抓住回归；不修改真实源码。
    bad=cpp.replace('human->_NV_getThePreferredWeapon()','0')
    check('故障注入捕获绕开原生武器选择',not source_contracts(bad)['4使用游戏原生选择而非首个物品'])
    bad=cpp.replace('if(w->isLoadingFromASaveGame()){Finish("loading");return;}','')
    check('故障注入捕获活动演出遗漏加载取消',not source_contracts(bad)['3活动演出加载取消'])
    ini=(ROOT/'package/JudgementCutEnd/JudgementCutEnd.ini').read_text('utf8')
    check('分发默认键值与启动说明一致',config_model(ini)==85 and '武器是启动条件' in ini and '演出中卸下/更换不撤销' in ini)
    check('CPP BOM与纯CRLF',raw.startswith(b'\xef\xbb\xbf') and b'\n' not in raw.replace(b'\r\n',b''))
    return dict(checks=checks,check_count=len(checks),source_sha256=hashlib.sha256(raw).hexdigest().upper(),compiled=False,game_tested=False,limits='静态数据流连接、原生证据由其他专项工具核验；键位模型非C++执行，不保证未测试的加载回调安全')
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
