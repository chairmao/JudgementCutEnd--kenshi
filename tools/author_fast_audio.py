"""只制作三倍演出同步音效资产；不编译，不修改游戏或参考源文件。"""
import array, hashlib, io, json, wave
from author_assets import ROOT, SOURCE, put
RATE=44100
PLAYBACK_RATE=3.0
DURATION=6.7/PLAYBACK_RATE

def render():
    # 时刻与窗口除三，原 PCM 不重采样；保留音调，避免把拔刀声变为三倍高音。
    # 演出变短，因此使用各段前部片段并淡出，不声称是整段音频的无损变速。
    cues=[("JCE010Intro.wav",0,.45,2.1),("JCE020Draw.wav",2.1,.65,.7),
          ("JCE030CutAll.wav",2.35,.65,1.1),("JCE040Sheath.wav",3.66,.5,.744),
          ("JCE040Finish.wav",5.15,.7,1.55)]
    mix=[0.0]*round(DURATION*RATE);used=[]
    for name,at,gain,limit in cues:
        path=SOURCE/"sound/fx/zjc"/name
        with wave.open(str(path),"rb") as wav:
            if (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())!=(1,2,RATE):
                raise ValueError("Unexpected source PCM format")
            pcm=array.array("h",wav.readframes(wav.getnframes()))
        start=round(at/PLAYBACK_RATE*RATE)
        count=min(len(pcm),round(limit/PLAYBACK_RATE*RATE),len(mix)-start)
        fade=min(round(.01*RATE),count//4)
        if count<=0 or fade<=0:raise ValueError("Empty audio cue")
        peak=0
        for i in range(count):
            envelope=max(0,min(1,i/fade,(count-1-i)/fade))
            value=pcm[i]/32768*gain*envelope
            mix[start+i]+=value;peak=max(peak,abs(value))
        if peak<.001:raise ValueError("Effectively silent cue: "+name)
        used.append({"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                     "clip_at":at,"real_at":start/RATE,"gain":gain,
                     "used_seconds":count/RATE,"peak_before_mix":peak})
    peak=max(abs(v) for v in mix);scale=min(1,.9/peak) if peak else 1
    pcm=array.array("h",(round(v*scale*32767) for v in mix));buf=io.BytesIO()
    with wave.open(buf,"wb") as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(RATE);wav.writeframes(pcm.tobytes())
    data=buf.getvalue()
    evidence={"sources":used,"playback_rate":PLAYBACK_RATE,"duration":DURATION,
              "format":"mono PCM16 44100 Hz","method":"retime cues, trim source windows, preserve sample rate/pitch",
              "peak":peak*scale,"frames":len(mix),"sha256":hashlib.sha256(data).hexdigest(),
              "redistribution":"用户提供的本地测试音效，不声称原创，不自动分发"}
    return data,evidence

def main():
    # 使用本项目已有资产写入器的双外部备份和逐文件报告，不重新制作旧动画/纹理/音轨。
    data,evidence=render()
    put(ROOT/"package/JudgementCutEnd/assets/jce_sequence_fast.wav",data,"2.233秒同步参考音效")
    put(ROOT/"docs/fast-audio-provenance.json",json.dumps(evidence,ensure_ascii=False,indent=2)+"\n","逐来源哈希及三倍音效时序")
if __name__=="__main__":main()
