// 同原有Basic_Coloured_Texture_VP接口；HDR增益独立于归一化顶点颜色。
// 透明度同时乘原DDS Alpha与演出曲线，防止演出前后零Alpha仍发光。
Texture2D sourceTexture : register(t0);
SamplerState sourceSampler : register(s0);
uniform float hdrGain;
uniform float grayscale;
// 淡蓝资源修订：只改变RGB，Alpha/图集/独立粒子时钟保持；白色缺省值兼容旧材质。
uniform float3 colourTint;
// 仅SourceDust启用细雾轮廓；默认0使刀光、拖尾、闪光和光屑保持2.0原像素路径。
uniform float dustDetail;
struct JCE_SOURCE_FRAGMENT {float4 pos:SV_Position;float4 colour:COLOR;float4 texCoord:TEXCOORD0;};
float4 jce_source_texture_fp(JCE_SOURCE_FRAGMENT input):SV_Target {
    float4 source=sourceTexture.Sample(sourceSampler,input.texCoord.xy);
    float mask=dot(source.rgb,float3(.2126,.7152,.0722));
    float3 colour=lerp(source.rgb,mask.xxx,saturate(grayscale));
    float detail=1;
    if(dustDetail>.5){
        // 使用原8x8图集Alpha提取稠密细丝，压低低密度灰底；不扭曲UV、不采样邻格。
        // 局部边缘柔化避免拉长后的雾片露出矩形边界；动画和流向由各独立粒子时钟/刀路提供。
        float2 local=frac(input.texCoord.xy*8);
        float edge=min(min(local.x,1-local.x),min(local.y,1-local.y));
        float core=smoothstep(.025,.32,source.a);
        detail=(.25+.75*core)*smoothstep(0,.10,edge);
    }
    // 2.7：用同一个标量压缩HDR峰值，不能逐RGB通道截断，否则高亮又失去冷蓝比例。
    // 仍为原源纹理乘颜色；不改Alpha、逐斩计时或共享Basic程序，也没有额外纹理采样。
    float3 light=colour*input.colour.rgb*colourTint*hdrGain;
    float peak=max(light.r,max(light.g,light.b));
    light/=1+.35*peak;
    return float4(light,source.a*input.colour.a*detail);
}

// 独立主刀光2.7：Basic VP继续传UV和归一化颜色；只有本材质将Alpha解码为0..2能量。
// 材质采用ONE ONE加法混合，因为能量已经乘入输出RGB；零能量必须严格零光，不污染退场。
float4 jce_glow27_fp(JCE_SOURCE_FRAGMENT input):SV_Target {
    float energy=saturate(input.colour.a)*2;
    if(energy<=0)return float4(0,0,0,0);
    float4 source=sourceTexture.Sample(sourceSampler,input.texCoord.xy);
    float mask=dot(source.rgb,float3(.2126,.7152,.0722))*source.a;
    float3 light=mask*input.colour.rgb*colourTint*hdrGain*energy;
    float peak=max(light.r,max(light.g,light.b));
    return float4(light/(1+.45*peak),0);
}
