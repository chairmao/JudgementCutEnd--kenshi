"""时间恢复回归：原生暂停缓存合同的离线模型和源码连接检查；不编译、不启动游戏。"""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
class World:
    # 以日志/本机原生接口为依据：暂停缓存当前正速度，暂停为0，解除时恢复缓存值。
    def __init__(self,speed):
        self.speed=speed;self.paused=False;self.cached=speed;self.writes=[];self.fail=False;self.ignore=False
    def pause(self):
        if self.speed>0:self.cached=self.speed
        self.speed=0;self.paused=True
    def resume(self):
        self.paused=False;self.speed=self.cached
    def set(self,speed):
        if self.fail:raise RuntimeError('simulated native setter failure')
        if not self.ignore:self.speed=speed
        self.writes.append(speed)
class TimeOwner:
    # 模拟接口与所有权合同；这不是C++运行或真实游戏验收。
    def __init__(self,w):
        self.w=w;self.owner=None;self.owned=False;self.pending=False;self.base=1;self.slow=.001
    def begin(self):
        if self.owned:raise RuntimeError('pending')
        if not math.isfinite(self.w.speed) or self.w.speed<=0:raise RuntimeError('paused')
        self.base=self.w.speed;self.owner=self.w;self.owned=True;self.pending=False
        self.w.set(self.slow)
    def restore(self,valid=True):
        if not self.owned:return
        if not valid or self.w is not self.owner:
            self.owned=self.pending=False;self.owner=None;return
        speed=self.w.speed
        if self.w.paused or not math.isfinite(speed) or speed<=0:
            self.pending=True;return
        if abs(speed-self.slow)>=.00005 or abs(speed-self.base)<.00005:
            self.owned=self.pending=False;self.owner=None;return
        try:
            self.w.set(self.base)
            if math.isfinite(self.w.speed) and abs(self.w.speed-self.base)<.00005:
                self.owned=self.pending=False;self.owner=None
            else:self.pending=True
        except RuntimeError:self.pending=True
    def finish(self):
        if self.owned:self.pending=True
        self.restore()
    def tick(self):
        if self.pending:self.restore()
def main():
    cpp=(ROOT/'JudgementCutEnd.cpp').read_text('utf-8-sig')
    restore=cpp.split('    void RestoreTime(',1)[1].split('    void Begin(',1)[0]
    finish=cpp.split('    void Finish(',1)[1].split('    unsigned RefreshSkin',1)[0]
    begin=cpp.split('    void Begin(',1)[1].split('    void ReleaseGraphics',1)[0]
    tick=cpp.split('    void Tick(',1)[1].split('Runtime* runtime=0;',1)[0]
    check('restore before renderer/resolve/bone/weapon operations',finish.index('RestoreTime(reason,validWorld)')<min(finish.index('SameRenderer()'),finish.index('Resolve()'),finish.index('setPosition('),finish.index('RestoreWeapon(c)')))
    check('restore independent of active flag','wasActive' not in restore and 'if(!speedOwned)return;' in restore)
    check('ownership published before slow setter',begin.index('speedOwned=true')<begin.index('setFrameSpeedMultiplier(settings.slow)'))
    check('pending blocks replacement of baseline',begin.index('if(speedOwned)throw')<begin.index('previousSpeed='))
    check('idle resume recovery before new input snapshot',tick.index('RestoreTime("resume_retry")')<tick.index('bool combo='))
    check('no pause override or field writes',all(s not in restore for s in ('togglePause(', 'userPause(', 'setGameSpeed(', 'frameSpeedMult=')) and '->paused=' not in restore)
    check('old world guarded before calls',restore.index('speedWorld!=world||speedWorld!=ou')<restore.index('getFrameSpeedMultiplier()'))
    check('restore verified by native getter before release',restore.index('float after=world->getFrameSpeedMultiplier();')<restore.index('if(verified){'))
    check('bounded failure logging','speedRestoreErrors<3' in restore and 'speedRestoreErrors++' not in restore and 'if(!speedWaitNoted)' in restore)
    check('distinct pause/focus/escape diagnostics',all(s in tick for s in ('cancelled_pause','cancelled_focus','cancelled_escape','cancelled_input')))
    for base in (1,2,3):
        for reason in ('completed','escape','focus','loading','pose_error','frame_stall','begin_after_slow_failed','restart'):
            w=World(base);s=TimeOwner(w);s.begin();s.finish()
            check('restore '+reason+' base='+str(base),w.speed==base and not s.owned and not s.pending)
        w=World(base);s=TimeOwner(w);s.begin();w.pause();s.finish()
        for _ in range(10):s.tick()
        check('pause remains paused base='+str(base),w.paused and w.speed==0 and s.pending and s.base==base and w.writes==[.001])
        blocked=False
        try:s.begin()
        except RuntimeError:blocked=True
        check('pending cannot overwrite baseline base='+str(base),blocked and s.base==base)
        w.resume();s.tick()
        check('unpause restores original base='+str(base),w.speed==base and not s.pending and not s.owned)
        s.begin();check('next cast snapshots normal speed base='+str(base),s.base==base)
        s.finish()
        for external in (1,2,3,.5):
            w=World(base);s=TimeOwner(w);s.begin();w.speed=external;s.finish()
            check('preserve manual/external speed '+str(base)+' -> '+str(external),w.speed==external and not s.owned and w.writes==[.001])
    w=World(1);s=TimeOwner(w);s.begin();w.pause();s.finish();w.speed=3;w.paused=False;s.tick()
    check('manual resume speed preserved',w.speed==3 and not s.pending)
    w=World(1);s=TimeOwner(w);s.begin();w.pause();s.finish();new=World(2);s.w=new;s.tick()
    check('old world never written on replacement',w.speed==0 and new.speed==2 and not s.owned and new.writes==[])
    w=World(1);s=TimeOwner(w);s.begin();s.restore(False)
    check('invalid world releases without dereference/write',w.writes==[.001] and not s.owned)
    w=World(2);s=TimeOwner(w);s.begin();w.fail=True;s.finish()
    check('setter exception retains baseline',s.pending and s.base==2 and w.speed==.001)
    w.fail=False;s.tick();check('setter exception retry restores',w.speed==2 and not s.pending)
    w=World(3);s=TimeOwner(w);s.begin();w.ignore=True;s.finish()
    check('unverified setter retains ownership',s.pending and s.owned and s.base==3)
    w.ignore=False;s.tick();check('unverified setter retry restores',w.speed==3 and not s.pending)
    for invalid in (0,float('nan'),float('inf')):
        w=World(1);s=TimeOwner(w);s.begin();w.speed=invalid;s.finish()
        check('invalid speed deferred '+str(invalid),s.pending and s.base==1 and w.writes==[.001])
    # 重现旧缺陷：暂停取消时旧guard跳过，下一次施放把slow重新当作基线。
    w=World(1);w.set(.001);w.pause()
    if abs(w.speed-.001)<.00005:w.set(1)
    w.resume();old_snapshot=w.speed;w.set(.001);w.set(old_snapshot)
    check('old bug reproduced: poisoned baseline persists',w.speed==.001 and old_snapshot==.001)
    w=World(1);s=TimeOwner(w)
    for n in range(100):
        s.begin()
        if n%3==0:w.pause();s.finish();w.resume();s.tick()
        else:s.finish()
    check('100 repeated casts and pause cancellations do not drift',w.speed==1 and s.base==1 and not s.pending)
    return {'static_passed':True,'checks':checks,'check_count':len(checks),'compiled':False,'game_tested':False,'model_limit':'接口合同模型及源码绑定检查，不能代替实际C++和游戏验证'}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
