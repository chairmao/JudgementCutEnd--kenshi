// 2.9.7：沿用五片源网格/遮罩与投影映射；收窄切口/侧向混合并先分离后淡出，不新增亮线/染色。
struct JCE_SOURCE_FACET {
    float4 pos : SV_Position;
    float4 colour : COLOR;
    float4 texCoord : TEXCOORD0;
    float3 localPosition : TEXCOORD1;
    float3 normalView : TEXCOORD2;
    float3 viewPosition : TEXCOORD3;
    float3 pivotView : TEXCOORD4;
    float3 axisView : TEXCOORD5;
    // CPU每顶点刀路坐标线性插值；其余三个分量在本片内一致，旧模式用x=-1关闭新响应。
    float4 optical : TEXCOORD6;
    // 参考与当前顶点用同一投影；保持float4，经透视正确插值后再除w得到片内单应映射。
    float4 referenceClip : TEXCOORD7;
};
JCE_SOURCE_FACET jce_facet297_vp(float4 pos : POSITION,float3 normal : NORMAL,float4 colour : COLOR,
                               float4 texCoord : TEXCOORD0,float3 pivot : TEXCOORD1,float3 axis : TEXCOORD2,float4 optical : TEXCOORD3,float3 reference : TEXCOORD4,
                               uniform float4x4 worldViewProjMatrix,uniform float4x4 worldViewMatrix) {
    JCE_SOURCE_FACET o;
    o.optical=optical;
    o.referenceClip=mul(worldViewProjMatrix,float4(reference,1));
    o.pos=mul(worldViewProjMatrix,pos);o.colour=colour;o.texCoord=texCoord;o.localPosition=pos.xyz;
    o.viewPosition=mul(worldViewMatrix,pos).xyz;
    o.normalView=mul((float3x3)worldViewMatrix,normal);
    o.pivotView=mul(worldViewMatrix,float4(pivot,1)).xyz;
    o.axisView=mul((float3x3)worldViewMatrix,axis);
    return o;
}
Texture2D sourceMask : register(t0);
SamplerState maskSampler : register(s0);
Texture2D sceneCopy : register(t1);
SamplerState sceneSampler : register(s1);
uniform float4 viewport;
uniform float captureValid;
float4 jce_facet297_fp(JCE_SOURCE_FACET input) : SV_Target {
    // 切口导数在所有逐像素早退/非一致分支前计算，避免相邻像素提前返回导致导数未定义。
    // fwidth是屏幕X/Y导数绝对值之和；平面切口过渡约2.5～3.54像素，不再随面宽放大为5%。
    // 旧模式也可安全计算，但不使用结果；常量刀路的正数下界和0/1揭开端点防止零宽/提前露面。
    float cut=saturate(input.optical.w);
    float cutAA=max(fwidth(cut)*1.25,.00001);
    float strength=saturate(input.colour.r)*captureValid;
    if(strength<=0||input.colour.a<=0)return float4(0,0,0,0);
    float radius=max(input.texCoord.w,.001);
    float3 sphere=(input.localPosition-float3(0,.8,0))/radius;
    float boundary=(1-smoothstep(.86,1,length(sphere)))*smoothstep(0,.01,sphere.y);
    if(boundary<=0)return float4(0,0,0,0);
    float3 n=input.normalView*rsqrt(max(dot(input.normalView,input.normalView),.000001));
    float3 v=-input.viewPosition*rsqrt(max(dot(input.viewPosition,input.viewPosition),.000001));
    float incidence=dot(n,v);
    if(incidence<=.015)return float4(0,0,0,0);
    bool wide=input.colour.g>.5;
    bool progressive=wide&&input.optical.x>=0;
    // 宽面使用同一枢轴光线/主表面法线，让地面/墙轮廓一致移动；薄面保留原逐像素折射。
    // 法线槽在源NIF也引用光斑，不能把该纹理RGB当真正法线；几何法线仍来自源顶点。
    float3 planeN=input.axisView*rsqrt(max(dot(input.axisView,input.axisView),.000001));
    float3 pivotRay=input.pivotView*rsqrt(max(dot(input.pivotView,input.pivotView),.000001));
    float3 incident=wide?pivotRay:-v;
    float3 refN=wide?planeN:n;
    if(dot(refN,incident)>0)refN=-refN;
    float3 bent=refract(incident,refN,1.0/1.06);
    float2 slope=bent.xy/max(abs(bent.z),.20)-incident.xy/max(abs(incident.z),.20);
    float budget=clamp(min(viewport.x,viewport.y)/1080.0*26,12,36);
    float2 shift=slope*float2(1,-1)*(min(viewport.x,viewport.y)*.05)*strength;
    // 宽面验证将有向偏折归一到24px/1080p，仍受旧36px上界约束。
    // 这是Kenshi光学片区适配，不冒称源引擎折射方程；正对且无偏折方向时保持零位移。
    if(wide){float len=length(slope);shift=len>.00001?slope/len*float2(1,-1)*min(budget,min(viewport.x,viewport.y)/1080.0*24)*strength:float2(0,0);}
    // 2.9.4仅新三片模式改变位移响应：出生后随各自偏折进度逐步增加，不再固定长度。
    // 原偏折方向来自枢轴/表面法线；不加随机摆动/纹样/发光，幅度不超过已验收预算。
    if(progressive)shift*=saturate(input.optical.y);
    // 先由当前片反查出生参考位置，画面随本片三轴偏折/分离产生位置相关的转动/剪切。
    // 同一帧同一矩阵使镜头变化在两边同步；不读取历史帧，不用UV噪声伪造空间裂线。
    float2 uv=input.pos.xy*viewport.zw;
    if(progressive&&input.referenceClip.w>.0001){
        float2 referenceNdc=input.referenceClip.xy/input.referenceClip.w;
        float2 referenceUV=referenceNdc*float2(.5,-.5)+float2(.5,.5);
        shift+=(referenceUV-uv)*viewport.xy*strength;
    }
    // 偏折与投影映射合计仍受12..36像素预算，旧模式负揭开标记完全跳过新映射。
    // 参考点在相机后方时只保留原偏折；采样还会夹到半像素安全范围，不发生无界屏外读取。
    shift*=min(1,budget/max(length(shift),.0001));
    // 原光斑Alpha/UV仍作边缘遮罩；将低透明区压到边缘，避免整片背景双影把错位冲淡。
    // 这是Kenshi适配传递函数，不声称复制Skyrim的LightingShader响应；无新增图案或色彩。
    float sourceAlpha=wide?sourceMask.Sample(maskSampler,input.texCoord.xy).a:1;
    float mask=wide?smoothstep(.025,.22,sourceAlpha):1;
    float2 sampleUV=clamp(uv+shift*viewport.zw,viewport.zw*.5,1-viewport.zw*.5);
    float3 displaced=sceneCopy.Sample(sceneSampler,sampleUV).rgb;
    // 强度只驱动宽面位移，不再第二次乘混合Alpha而压低背景差异；源遮罩/生命周期保留柔入柔退。
    // 宽面停留阶段保持内部接近完整背景替换，只在出生/退场及源纹理边缘柔化。
    // 两个薄面仍保持原混合合同；正反面门控防止封闭薄网格两面重复叠加，深度仍生效。
    float envelope=wide?smoothstep(.02,.70,input.colour.a):saturate(input.colour.a);
    // 刀路掠过时逐像素揭开原遮罩；0严格未出生，1严格全开，中间只有窄软边，不画新边框。
    float cutMask=1,releaseFade=1;
    if(progressive){
        float reveal=saturate(input.optical.x);
        cutMask=reveal<=0?0:(reveal>=1?1:smoothstep(cut-cutAA,cut+cutAA,reveal));
        // 收刀先完成前50%的分离再连续淡出；不延长各片生命期，末片仍在END前严格归零。
        releaseFade=1-smoothstep(.50,1,saturate(input.optical.z));
    }
    // 独立裂面更早达到完整背景替换，减少侧角处原画面与偏折画面的双影；正背门控仍为0.015。
    // 只收窄角度过渡，不增亮/染色；旧0/1/2模式的0.015..0.12混合精确保留。
    float viewFade=progressive?smoothstep(.015,.055,incidence):smoothstep(.015,.12,incidence);
    float alpha=boundary*envelope*mask*viewFade*(wide?1:strength)*cutMask*releaseFade;
    return float4(displaced,saturate(alpha));
}
