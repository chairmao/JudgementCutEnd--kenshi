// 2.9.2立向宽面验证：真实源薄网格+独立尺寸，整片背景沿一致方向偏折；无新增噪声、裂线、染色。
struct JCE_SOURCE_FACET {
    float4 pos : SV_Position;
    float4 colour : COLOR;
    float4 texCoord : TEXCOORD0;
    float3 localPosition : TEXCOORD1;
    float3 normalView : TEXCOORD2;
    float3 viewPosition : TEXCOORD3;
    float3 pivotView : TEXCOORD4;
    float3 axisView : TEXCOORD5;
};
JCE_SOURCE_FACET jce_facet292_vp(float4 pos : POSITION,float3 normal : NORMAL,float4 colour : COLOR,
                               float4 texCoord : TEXCOORD0,float3 pivot : TEXCOORD1,float3 axis : TEXCOORD2,
                               uniform float4x4 worldViewProjMatrix,uniform float4x4 worldViewMatrix) {
    JCE_SOURCE_FACET o;
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
float4 jce_facet292_fp(JCE_SOURCE_FACET input) : SV_Target {
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
    shift*=min(1,budget/max(length(shift),.0001));
    // 原光斑Alpha/UV仍作边缘遮罩；将低透明区压到边缘，避免整片背景双影把错位冲淡。
    // 这是Kenshi适配传递函数，不声称复制Skyrim的LightingShader响应；无新增图案或色彩。
    float sourceAlpha=wide?sourceMask.Sample(maskSampler,input.texCoord.xy).a:1;
    float mask=wide?smoothstep(.025,.22,sourceAlpha):1;
    float2 uv=input.pos.xy*viewport.zw;
    float2 sampleUV=clamp(uv+shift*viewport.zw,viewport.zw*.5,1-viewport.zw*.5);
    float3 displaced=sceneCopy.Sample(sceneSampler,sampleUV).rgb;
    // 强度只驱动宽面位移，不再第二次乘混合Alpha而压低背景差异；源遮罩/生命周期保留柔入柔退。
    // 宽面停留阶段保持内部接近完整背景替换，只在出生/退场及源纹理边缘柔化。
    // 两个薄面仍保持原混合合同；正反面门控防止封闭薄网格两面重复叠加，深度仍生效。
    float envelope=wide?smoothstep(.02,.70,input.colour.a):saturate(input.colour.a);
    float alpha=boundary*envelope*mask*smoothstep(.015,.12,incidence)*(wide?1:strength);
    return float4(displaced,saturate(alpha));
}
