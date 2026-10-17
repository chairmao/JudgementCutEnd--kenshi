// 蓝雾仅作用于本插件两种自有材质；不修改游戏全屏雾、曝光、共享shader或深度资源。
// VP沿用本机basic.hlsl的POSITION/COLOR/TEXCOORD0与worldviewproj_matrix合同，另传施放局部位置。
// 半径/时钟由各四边形的四分量UV输送；不依赖按帧改材质或游戏全局时间。
struct JCE_FOG_FRAGMENT {
    float4 pos : SV_Position;
    float4 colour : COLOR;
    float4 texCoord : TEXCOORD0;
    float3 localPosition : TEXCOORD1;
};
JCE_FOG_FRAGMENT jce_fog_vp(float4 pos : POSITION,float4 colour : COLOR,float4 texCoord : TEXCOORD0,
                           uniform float4x4 worldViewProjMatrix) {
    JCE_FOG_FRAGMENT o;
    o.pos=mul(worldViewProjMatrix,pos);
    o.colour=colour;o.texCoord=texCoord;o.localPosition=pos.xyz;
    return o;
}
Texture2D fogNoise : register(t0);
SamplerState noiseSampler : register(s0);
Texture2D fogPalette : register(t1);
SamplerState paletteSampler : register(s1);
Texture2D smokeAtlas : register(t2);
SamplerState atlasSampler : register(s2);
float jce_fog_edge(float2 uv) {
    // 四边形内用平方椭圆柔边，四边完全透明；保留低密度细节，不做稠密轮廓提取。
    float2 p=uv*2-1;
    float edge=saturate(1-dot(p,p));
    return edge*edge;
}
float jce_fog_boundary(float3 q) {
    // 底部只需不穿地，侧/顶部在半径的末18%柔和淡出；半径来自同一AreaRadius生产端。
    return (1-smoothstep(.82,1,length(q)))*smoothstep(0,.025,q.y);
}
float3 jce_fog_colour(float density) {
    // 2.7：连续烟体使用明确深蓝→青蓝的密度色带，避免灰/紫色原色表稀释主体色相。
    // 暗部仍有蓝色，密集卷边更亮；亮度有界，不能靠等RGB巨大增益形成灰白云块。
    return lerp(float3(.018,.09,.25),float3(.14,.52,.82),smoothstep(.12,.88,density));
}
// 同一施放局部场供体积切片和卷边烟带使用。原贴图的细密颗粒不再作为主体密度。
// 新纹理是自制低频周期场，远处可用mipmap；两个反向场卷动而非逐帧重抽随机噪声。
float4 jce_cloud_field(float3 q,float clock) {
    // 2.7.2参照BG3分开控制烟色/运动的结构：高度相位与低频剪切让不同区域卷动不同步。
    // 这是本地重建的连续输运场，不是缺失的BG3底层材质；仍只采样两次同一可平铺纹理。
    // clock沿用剪辑秒，世界时停不冻结；无随机闪点，也不新增整片半球或游戏全屏处理。
    float sn,cs;sincos(clock*.38+q.y*.65,sn,cs);
    float2 rolled=float2(q.x*cs-q.z*sn,q.x*sn+q.z*cs);
    float shear=sin(q.y*2.1+q.x*1.4-clock*.70)*.055;
    float2 field=rolled*float2(.66,1.02)+q.y*float2(.28,-.31)+float2(shear,-shear*.65);
    float4 first=fogNoise.Sample(noiseSampler,field+clock*float2(.12,-.09));
    float4 second=fogNoise.Sample(noiseSampler,field.yx*float2(.88,.62)
                           +(first.gb-.5)*.36+clock*float2(-.105,.13));
    return float4(.56*first.r+.44*second.g,first.g,second.r,.5*(first.b+second.b));
}
float3 jce_source_smoke_colour(float density,float young) {
    // 2.8参考BG3主烟颜色/透明度独立寿命：新生亮青蓝，尾段渐为蓝色，Alpha仍由CPU包络淡出。
    // 不用等RGB增益变白，也不把两个暗色再次相乘；颜色始终B>G>R且不超过1。
    // 这些是Kenshi适配的自制色带，BG3底层材质缺失，不能把源RGBA当最终画面照抄。
    float mix=smoothstep(.12,.88,density);
    float3 fresh=lerp(float3(.18,.48,.76),float3(.34,.74,.98),mix);
    float3 old=lerp(float3(.10,.28,.52),float3(.20,.46,.76),mix);
    return lerp(old,fresh,smoothstep(.10,.85,saturate(young)));
}
float4 jce_mist_fp(JCE_FOG_FRAGMENT input) : SV_Target {
    // 2.7.1纠正：32片密度叠加在实录中形成蓝色幕布，不能把该近似冒称为已实现体积雾。
    // 先彻底停用整体覆盖，沿刀路烟带/烟丝保持；保留材质段和VP合同，避免改变DLL几何布局。
    // 返回零RGB/Alpha，不进行纹理采样；不改世界天气、曝光、深度或演出/时间恢复。
    return float4(0,0,0,0);
}
float4 jce_smoke_frame(float frame,float2 uv) {
    // 每格64px/原图512px；半纹素内缩后再采样，插值也不能跨格或串到其它帧。
    float tile=fmod(floor(frame),64);
    float2 cell=float2(fmod(tile,8),floor(tile/8));
    float2 atlasUV=cell*.125+.5/512+saturate(uv)*(.125-1.0/512);
    return smokeAtlas.Sample(atlasSampler,atlasUV);
}
float4 jce_smoke_fp(JCE_FOG_FRAGMENT input) : SV_Target {
    // 未出生/结束的固定占位片仍提交几何，但零Alpha立即返回，不进行雾纹理采样。
    if(input.colour.a<=0)return float4(0,0,0,0);
    float radius=max(input.texCoord.w,.001);
    float3 q=(input.localPosition-float3(0,.8,0))/radius;
    float frame=max(0,input.texCoord.z);
    // frame是CPU提供的连续烟图帧（16帧/剪辑秒，含槽位相位），不是全局游戏时间。
    // 同一噪声采样同时提供卷动和密度：原图两帧插值之前扭曲局部UV，烟丝才会拉伸而不是静态贴片。
    float4 flow=fogNoise.Sample(noiseSampler,q.xz*1.65+q.y*.32+frame*float2(.013,-.009));
    float2 uv=input.texCoord.xy;
    // 边缘的位移归零，原四边形柔边及半径裁切仍作用于未扭曲坐标；每格采样继续半纹素内缩防串帧。
    float interior=16*uv.x*(1-uv.x)*uv.y*(1-uv.y);
    float2 warpedUV=uv+(flow.rg-.5)*.24*interior;
    float4 first=jce_smoke_frame(frame,warpedUV);
    float4 second=jce_smoke_frame(frame+1,warpedUV);
    float4 source=lerp(first,second,frac(frame));
    // 原Alpha为零时仍严格透明；密度变化随输运产生，不加随机亮点或放大颗粒。
    float wisps=.56*source.a+.44*sqrt(saturate(source.a));
    float alpha=wisps*input.colour.a*jce_fog_edge(uv)*jce_fog_boundary(q)*(.52+.48*flow.r);
    float density=saturate(.38+.42*source.a+.20*flow.r);
    return float4(jce_fog_colour(density)*input.colour.rgb*1.12,saturate(alpha));
}

// 4×4图集仍按固定索引读取，2.8恢复有限轮廓调制；旧64格尘烟算法保留且CPU低权重。
// shape索引固定在CPU槽位，clock随演出更新，不把源SubTexModifier关闭的图集当连续帧。
float4 jce_source_smoke_shape(JCE_FOG_FRAGMENT input,bool ribbon) {
    if(input.colour.a<=0)return float4(0,0,0,0);
    float3 q=(input.localPosition-float3(0,.8,0))/max(input.texCoord.w,.001);
    float boundary=jce_fog_boundary(q);
    if(boundary<=0)return float4(0,0,0,0);
    float shape=clamp(floor(input.texCoord.z/16),0,15);
    float clock=input.texCoord.z-shape*16;
    float2 uv=input.texCoord.xy;
    float4 field=jce_cloud_field(q,clock);
    // 2.8：扩大的连续烟带显露同一空间场的柔软卷边，不把每格原烟图当独立发射的烟团。
    // 原形状Alpha只作32%轮廓调制，不开根号放大图集灰底或颗粒；输入四分量UV不变。
    float interior=16*uv.x*(1-uv.x)*uv.y*(1-uv.y);
    float2 warped=saturate(uv+(field.yz-.5)*(.22*interior));
    float2 tile=float2(fmod(shape,4),floor(shape/4));
    float2 atlasUV=tile*.25+.5/512+warped*(.25-1.0/512);
    float sourceAlpha=smokeAtlas.Sample(atlasSampler,atlasUV).a;
    // 密度过渡放宽，低频场保留空隙；透明度仍受CPU独立寿命与上限约束，防止实体云块。
    float density=smoothstep(.18,.82,field.x);
    float ends=smoothstep(0,.12,uv.x)*(1-smoothstep(.88,1,uv.x));
    // 烟带卷边沿全条UV连续弯曲；不同shape有固定相位，不逐帧随机跳动。
    // 位移在原四边归零，末端和跨条段保持同一坐标规则，仍然全边透明。
    float crossBase=1-smoothstep(.30,1,abs(uv.y*2-1));
    float curl=sin(uv.x*5.2-clock*1.4+shape*.7)*.06+(field.y-.5)*.12;
    float crossCoord=uv.y+curl*ends*crossBase;
    float cross=1-smoothstep(.26,1,abs(crossCoord*2-1));
    // 烟带横向柔边＋两端柔出；烟丝仍低权重填卷边，全四边零透明，防止硬卡片接缝。
    float edge=ribbon?ends*cross:interior*interior;
    // 原烟Alpha恢复到32%轮廓调制，让大尺度烟体卷边有层次；不提高图集灰底，也不新增颗粒。
    // 主密度仍来自同一连续空间场；CPU尺寸/输运可见，透明度独立于RGB年龄渐变。
    float alpha=density*(.68+.32*sourceAlpha)*edge*input.colour.a*boundary;
    // 绿色通道只用来解码原生产者的寿命亮度，不更改UV布局/Alpha含义。
    // 密度与年龄颜色独立；新生青蓝、尾烟较暗蓝，烟丝略淡；无纯白HDR强化。
    float young=saturate((input.colour.g-.68)/.27);
    float3 colour=jce_source_smoke_colour(saturate(density*.85+.15*field.w),young);
    return float4(colour*(ribbon?1:.96),saturate(alpha));
}
float4 jce_source_ribbon_fp(JCE_FOG_FRAGMENT input) : SV_Target {
    return jce_source_smoke_shape(input,true);
}
float4 jce_source_wisp_fp(JCE_FOG_FRAGMENT input) : SV_Target {
    return jce_source_smoke_shape(input,false);
}
