"""原创低频流场：周期Fourier密度/流动数据，固定种子；不下载或修改参考资产。"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
FREQUENCIES=[(1,1),(2,-1),(1,3),(3,2),(4,-2),(5,1)]
WEIGHTS=[1,.75,.55,.38,.22,.12]
def field(size=512):
    # 每方向最高5周期，只有大尺度结构；不用逐像素随机噪点或尖锐阈值。
    # 采样不包含重复终点，wrap跨边仍连续；RGB/A为四个独立周期场，非烟雾透明度。
    y,x=np.mgrid[0:size,0:size]/size
    rng=np.random.default_rng(270041);channels=[]
    for channel in range(4):
        values=np.zeros((size,size),dtype=np.float64)
        for (kx,ky),weight in zip(FREQUENCIES,WEIGHTS):
            values+=weight*np.sin(2*np.pi*(kx*x+ky*y)+rng.uniform(0,2*np.pi))
        channels.append(.5+.48*values/sum(WEIGHTS))
    return np.stack(channels,axis=2)
def main():
    values=field();raw=np.rint(values*255).astype(np.uint8)
    dest=ROOT/'package/JudgementCutEnd/assets/jce_cloud_field27.tga'
    # 新资源拒绝无备份覆盖；需要重新制作时走项目双备份规则后由用户明确处理旧文件。
    with dest.open('xb') as out:Image.fromarray(raw).save(out,format='TGA')
    return {'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'dimensions':[512,512,4],
        'seed':270041,'frequencies':FREQUENCIES,'weights':WEIGHTS,'min':float(values.min()),'max':float(values.max()),
        'role':'周期连续密度与输运数据，非灰颗粒烟形图集','provenance':'independently authored procedural Fourier field','compiler_used':False}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))
