// 2.9小规模验证：只绘制三张原NIF几何，真实空间位置/法线参与投影；不生成镜框或全屏染色。
// 新NORMAL输入与原生三裂面段同步；旧四分量UV继续承载源UV、剪辑秒和施放半径。
struct JCE_SOURCE_FACET {
    float4 pos : SV_Position;
    float4 colour : COLOR;
    float4 texCoord : TEXCOORD0;
    float3 localPosition : TEXCOORD1;
    float3 normalView : TEXCOORD2;
    float3 viewPosition : TEXCOORD3;
};
JCE_SOURCE_FACET jce_facet29_vp(float4 pos : POSITION,float3 normal : NORMAL,float4 colour : COLOR,
                              float4 texCoord : TEXCOORD0,
                              uniform float4x4 worldViewProjMatrix,uniform float4x4 worldViewMatrix) {
    JCE_SOURCE_FACET o;
    o.pos=mul(worldViewProjMatrix,pos);o.colour=colour;o.texCoord=texCoord;o.localPosition=pos.xyz;
    o.viewPosition=mul(worldViewMatrix,pos).xyz;
    // 自有节点只有平移，法线已由CPU按施放朝向变换；无非均匀缩放，3x3视图矩阵足够。
    o.normalView=mul((float3x3)worldViewMatrix,normal);
    return o;
}
Texture2D sceneCopy : register(t1);
SamplerState sceneSampler : register(s1);
uniform float4 viewport;
uniform float captureValid;
float4 jce_facet29_fp(JCE_SOURCE_FACET input) : SV_Target {
    float strength=saturate(input.colour.r)*captureValid;
    if(strength<=0||input.colour.a<=0)return float4(0,0,0,0);
    float radius=max(input.texCoord.w,.001);
    float3 sphere=(input.localPosition-float3(0,.8,0))/radius;
    float boundary=(1-smoothstep(.86,1,length(sphere)))*smoothstep(0,.01,sphere.y);
    if(boundary<=0)return float4(0,0,0,0);
    float3 n=input.normalView*rsqrt(max(dot(input.normalView,input.normalView),.000001));
    float3 v=-input.viewPosition*rsqrt(max(dot(input.viewPosition,input.viewPosition),.000001));
    // 原封闭薄网格包含背面；仅显示朝向观察者的表面，避免前后面重复叠加成灰玻璃。
    float incidence=dot(n,v);
    if(incidence<=.015)return float4(0,0,0,0);
    float3 incident=-v;
    // 1.06为Kenshi屏幕适配折射率，并非读取到的源材质参数。源法线决定偏折方向。
    // 单背景副本无法恢复遮挡后的景物；只做受控屏幕采样，不把它称为真实多层光线追踪。
    float3 bent=refract(incident,n,1.0/1.06);
    float2 slope=bent.xy/max(abs(bent.z),.20)-incident.xy/max(abs(incident.z),.20);
    float2 shift=slope*float2(1,-1)*(min(viewport.x,viewport.y)*.05)*strength;
    float budget=clamp(min(viewport.x,viewport.y)/1080.0*26,12,36);
    shift*=min(1,budget/max(length(shift),.0001));
    float2 uv=input.pos.xy*viewport.zw;
    float2 sampleUV=clamp(uv+shift*viewport.zw,viewport.zw*.5,1-viewport.zw*.5);
    float3 displaced=sceneCopy.Sample(sceneSampler,sampleUV).rgb;
    // 包络由CPU逐裂面采样BG3原Alpha曲线；没有新增蓝幕、噪声、亮线或网格边框。
    float alpha=boundary*saturate(input.colour.a)*strength*smoothstep(.015,.12,incidence);
    return float4(displaced,saturate(alpha));
}
