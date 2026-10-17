// 连续空间切裂2.8.4：八道实际切面划分背景，片区内部保持稳定错位，不生成实体镜子。
// 唯一采样源是首个自有段之前的独立HDR副本；像素裁剪和世界深度测试共同限定施放半球。
struct JCE_OPTICAL_FRAGMENT {
    float4 pos : SV_Position;
    float4 colour : COLOR;
    float4 texCoord : TEXCOORD0;
    float3 localPosition : TEXCOORD1;
    float2 pivot : TEXCOORD2;
};
JCE_OPTICAL_FRAGMENT jce_refraction_vp(float4 pos : POSITION,float4 colour : COLOR,float4 texCoord : TEXCOORD0,
                                      uniform float4x4 worldViewProjMatrix) {
    JCE_OPTICAL_FRAGMENT o;
    o.pos=mul(worldViewProjMatrix,pos);o.colour=colour;o.texCoord=texCoord;o.localPosition=pos.xyz;
    // 局部平面中心经同一矩阵投影；绕该中心的微小采样旋转不依赖相机控制或全屏后处理。
    float4 centre=mul(worldViewProjMatrix,float4(0,.8+texCoord.w*.28,0,1));
    o.pivot=centre.xy/max(centre.w,.0001)*float2(.5,-.5)+.5;
    return o;
}
Texture2D sceneCopy : register(t1);
SamplerState sceneSampler : register(s1);
uniform float4 viewport;
uniform float captureValid;
uniform float4 screenState;
// xyz=单位切面法向，w=按施放半径归一化的平面常数；每道面对应真实刀光出生时间。
// state.x=独立原强度曲线归一化值，yz=投影切面法向，w=原网格宽/长比。
uniform float4 cutPlane0,cutPlane1,cutPlane2,cutPlane3,cutPlane4,cutPlane5,cutPlane6,cutPlane7;
uniform float4 cutState0,cutState1,cutState2,cutState3,cutState4,cutState5,cutState6,cutState7;
// life.x初斩脉冲，y收刀分离脉冲，z出生/退场包络，w单调退场相位；与2.8CPU/默认float4一致。
uniform float4 cutLife0,cutLife1,cutLife2,cutLife3,cutLife4,cutLife5,cutLife6,cutLife7;
// 片区种子仅依赖切面正负侧与层级，不依赖帧号；同一大片的颜色/方向不会逐帧乱跳。
float jce_region_seed(uint id) {
    uint h=id*1664525u+1013904223u;h=(h^(h>>13))*1274126177u;
    return float(h&65535u)/65535.0;
}
float2 jce_region_vector(uint id) {
    // 原向量的长度随机，导致部分大片几乎不移动；单位方向让各片的错位尺度可控。
    // 只依赖稳定片区编号，极小长度用下界保护，默认全零参数仍由像素入口拒绝。
    float2 direction=float2(jce_region_seed(id),jce_region_seed(id^23749u))*2-1;
    return direction*rsqrt(max(dot(direction,direction),.0001));
}
// 在局部覆盖面的半径坐标中限定不对称五边形，再与真实刀路分区相交。
// 这是有限光学片面的边界函数，不创建实体镜子；形状只由稳定大片种子决定。
float jce_facet_distance(float2 local,float2 axis,float seed) {
    float2 across=float2(-axis.y,axis.x);
    float2 offset=axis*(.16+.14*seed)+across*(seed-.5)*.10;
    float2 p=float2(dot(local-offset,axis),dot(local-offset,across));
    p.x+=p.y*(seed-.5)*.22;
    float2 extent=float2(.50+.18*seed,.46+.18*(1-seed));
    float box=max(max(p.x-extent.x,-p.x-extent.x*.82),max(p.y-extent.y,-p.y-extent.y*.90));
    return max(box,.58*p.x+.82*p.y-extent.y*.96);
}
float4 jce_refraction_fp(JCE_OPTICAL_FRAGMENT input) : SV_Target {
    float strength=saturate(screenState.x)*captureValid;
    if(strength<=0||input.colour.a<=0)return float4(0,0,0,0);
    float radius=max(input.texCoord.w,.001);
    float3 position=input.localPosition/radius;
    float3 sphere=(input.localPosition-float3(0,.8,0))/radius;
    // 半球只限定安全覆盖；仍保留深度测试与外沿柔退，不给整个空间染蓝或压暗。
    float boundary=(1-smoothstep(.86,1,length(sphere)))*smoothstep(0,.01,sphere.y);
    if(boundary<=0)return float4(0,0,0,0);
    float4 planes[8]={cutPlane0,cutPlane1,cutPlane2,cutPlane3,cutPlane4,cutPlane5,cutPlane6,cutPlane7};
    float4 states[8]={cutState0,cutState1,cutState2,cutState3,cutState4,cutState5,cutState6,cutState7};
    float4 lives[8]={cutLife0,cutLife1,cutLife2,cutLife3,cutLife4,cutLife5,cutLife6,cutLife7};
    float distances[8],powers[8],opened[8],inactive[8];
    float2 shift=float2(0,0);
    float edge=0,bevel=0,band=0,weight=0,releaseEnergy=0,releasePhase=0;
    float coarseRidge=0,coarseLight=0,coarseShade=0;
    float coarseMargin=2,coarseAA=.00005;
    float hold=saturate(screenState.w);
    [unroll] for(uint i=0;i<8;++i){
        float distance=dot(planes[i].xyz,position)+planes[i].w;
        float power=saturate(states[i].x)*saturate(lives[i].z);
        distances[i]=distance;powers[i]=power;
        // z包含出生与退场：用单调退场w补足已切开标记，避免收刀时重新合并为父区域。
        // 零强度的退化切面不能参与分裂；未出生的切面仍为0，默认参数全零时也无覆盖。
        inactive[i]=step(.0001,lives[i].x+lives[i].z+lives[i].w)*(1-step(.0001,states[i].x));
        opened[i]=saturate(saturate(lives[i].z)/.35+saturate(lives[i].w)*4)*step(.0001,states[i].x);
        float separation=saturate(lives[i].y);
        shift+=states[i].yz*(distance>=0?1:-1)*power*(2.2+float(i%3)*.45)*(1+separation*.8);
        releaseEnergy=max(releaseEnergy,separation*power);
        releasePhase+=saturate(lives[i].w)*power;
        float aa=max(fwidth(distance),.00005);
        float narrow=1-smoothstep(.35*aa,1.65*aa,abs(distance));
        // 极薄裂口外再留有限的倒角高光，在沙地等低对比背景也能读出大片边界。
        float rim=max(0,1-smoothstep(1.5*aa,4*aa,abs(distance))-narrow);
        float width=max(states[i].w*.85,.016);
        float wide=exp2(-3*distance*distance/(width*width));
        edge=max(edge,narrow*power*(.18+.35*saturate(lives[i].x)+.22*separation));
        bevel=max(bevel,rim*power*(.045+.075*saturate(lives[i].x)+.035*separation));
        band=max(band,wide*power);weight+=power;
        // 三道主面形成大片轮廓，其余面仍保持细裂痕。宽度来自屏幕导数，避免拉远变成粗蓝条。
        // 参考薄倒角折射面的明暗分层：仅裂口附近有亮唇/暗唇，绝不给整片加灰色底。
        if(i==0u||i==2u||i==4u){
            // 未出生/退化切面不限制当前片面；主边界按既有出生包络逐渐收紧。
            coarseMargin=min(coarseMargin,abs(distance)+(1-opened[i])*2);
            coarseAA=max(coarseAA,aa*opened[i]);
            float ridge=1-smoothstep(.8*aa,3.8*aa,abs(distance));
            float lip=max(0,1-smoothstep(1.4*aa,5.5*aa,abs(distance))-narrow);
            float side=distance>=0?1:0;
            coarseRidge=max(coarseRidge,ridge*power);
            coarseLight=max(coarseLight,(ridge*(.14+.08*hold)+lip*(.10+.12*side))
                           *power*(1+.65*saturate(lives[i].x)+.60*separation));
            coarseShade=max(coarseShade,lip*(1-side)*power*.14);
        }
    }
    if(weight<=.001)return float4(0,0,0,0);
    // 三道主切面先形成最多八块大片；其余五道只逐渐细分大片内部的采样错位。
    // 层级固定但每级按实际出生包络连续混合：未出生的边界没有片面跳变或提前显露。
    uint order[8]={0u,2u,4u,1u,3u,5u,6u,7u};uint region=1u,facetRegion=1u;
    float face=0,rotation=0,shear=0,coarseSeed=.5;
    float2 regionShift=float2(0,0),fineShift=float2(0,0);
    // 已出生但退化的面作为中性切面：不凭空划出区域，也不永久阻断后续正常细分。
    float coarseReady=min(max(opened[0],inactive[0]),min(max(opened[2],inactive[2]),max(opened[4],inactive[4])));
    [unroll] for(uint level=0;level<8;++level){
        uint index=order[level];uint parent=region;
        region=region*2u+(distances[index]>=0&&inactive[index]<.5?1u:0u);
        float seed=jce_region_seed(region);
        if(level==2u)facetRegion=region;
        if(level<3){
            float birth=opened[index];
            // 有些完整片区严格透明，保留未破裂的间隙；遮罩与刀口宽度分离，大片内部不再被清零。
            face=lerp(face,smoothstep(.18,.38,seed)*(1-smoothstep(.82,.90,seed)),birth);
            regionShift=lerp(regionShift,jce_region_vector(region),birth);
            // 大片以稳定刚性倾角和小幅错切表现折面；只按出生包络插值，不逐帧换噪声。
            rotation=lerp(rotation,(seed-.5)*.055,birth);
            shear=lerp(shear,(jce_region_seed(region^881u)-.5)*.030,birth);
            coarseSeed=lerp(coarseSeed,seed,birth);
        }else{
            // 后续刀路只有在主大片成立后才改变子区；偏移来自父子差值并平滑出生，不全帧换随机方向。
            float split=opened[index]*coarseReady;
            fineShift+=(jce_region_vector(region)-jce_region_vector(parent))*split*powers[index]*2.0;
            rotation+=(seed-jce_region_seed(parent))*.002*split*powers[index];
        }
    }
    // OpticalVertex把演出剪辑秒写入UV.z。它持续推进且独立于减速的世界时钟；没有新增uniform。
    float clipSeconds=max(input.texCoord.z,0);
    float piecePhase=coarseSeed*6.2831853;
    float midAmount=coarseReady*hold*(1-saturate(screenState.z));
    float fold=sin(clipSeconds*1.6+piecePhase);
    float sway=cos(clipSeconds*1.1+piecePhase);
    // 轮廓种子不变，只缓慢改变折面偏移/倾角；每片不同相位，禁止逐帧随机重排。
    float2 movingDirection=regionShift+float2(-regionShift.y,regionShift.x)*fold*.16*midAmount;
    movingDirection*=rsqrt(max(dot(movingDirection,movingDirection),.0001));
    rotation+=fold*.010*midAmount;shear+=sway*.006*midAmount;
    float2 uv=input.pos.xy*viewport.zw;
    float2 relative=(uv-input.pivot)*viewport.xy;
    // 初斩就有大片错层，中期保持；收刀再沿相同区域方向拉开，保留原有36像素硬上限。
    // 中期大片平移由8.5提高到22个参考像素，方向稳定；最终位移仍受12~36像素上限约束。
    // 中期保留22像素主错层并小幅呼吸；收刀的单调相位另增加外拉，仍经过原36像素硬裁剪。
    float coarsePixels=(12+10*hold+9*releaseEnergy+6*saturate(screenState.z))
                       *(1+fold*.06*midAmount)*min(weight,1);
    float2 detail=shift*.35+fineShift;
    detail+=float2(-relative.y,relative.x)*rotation*(.75+.25*hold+.6*releaseEnergy)*min(weight,1);
    // 错切仅改变背景采样，单位为屏幕像素；次级倾斜/细裂面合计最多占主偏移的30%。
    // 防止低视角下八面累积方向抵消主大片，既保留折面变化，也避免中期增强反而变弱。
    detail+=float2(relative.y,relative.x*.35)*shear*(.75+.25*hold+.40*releaseEnergy)*min(weight,1);
    float detailBudget=max(coarsePixels*.30,.001);
    detail*=min(1,detailBudget/max(length(detail),.0001));
    shift=movingDirection*coarsePixels+detail;
    float pixels=clamp(min(viewport.x,viewport.y)/1080.0*26,12,36);
    shift*=strength;
    float magnitude=length(shift);
    if(magnitude>pixels)shift*=pixels/max(magnitude,.0001);
    float2 sampleUV=clamp(uv+shift*viewport.zw,viewport.zw*.5,1-viewport.zw*.5);
    float3 displaced=sceneCopy.Sample(sceneSampler,sampleUV).rgb;
    float cutPatch=smoothstep(.12,.46,band);
    float phase=releasePhase/max(weight,.001);
    // 大片的消散种子不跟着子区增加而换号：前中期已存在的大片在结尾分离消失。
    float localRelease=saturate((phase-coarseSeed*.16)/max(1-coarseSeed*.16,.001));
    float dissolve=1-smoothstep(.25,1,localRelease);
    // UV.xy覆盖[-1.1,1.1]半径坐标，来自同一四顶点局部面；与相机转动后的生产几何一致。
    float2 local=(input.texCoord.xy-.5)*2.2;
    // 裁边固定使用三级主切面的目标片区，不归一化出生插值方向。
    // 插值方向可能接近零并快速转向；出生只通过coarseReady淡入已固定的轮廓。
    float2 stableAxis=jce_region_vector(facetRegion);
    float facetSeed=jce_region_seed(facetRegion);
    float facetDistance=jce_facet_distance(local,stableAxis,facetSeed);
    // 仅对连续的输入坐标求屏幕导数，避免片区种子不同使边界fwidth变大、形成粗发光条。
    float facetAA=max(max(fwidth(local.x),fwidth(local.y)),.00005);
    float finiteMask=1-smoothstep(-1.3*facetAA,.9*facetAA,facetDistance);
    float seamMask=smoothstep(.8*coarseAA,1.8*coarseAA,coarseMargin);
    float pieceMask=lerp(1,finiteMask*seamMask,coarseReady);
    float polygonLip=1-smoothstep(.6*facetAA,3*facetAA,abs(facetDistance));
    float seamLip=1-smoothstep(1.8*coarseAA,4.8*coarseAA,coarseMargin);
    float facetEdge=max(polygonLip*seamMask,seamLip*finiteMask)*coarseReady*face;
    // 高光沿有限裂边往复掠过，跟随每片自己的演出相位；片面内部保持场景RGB而不铺蓝底。
    float along=dot(local,float2(-stableAxis.y,stableAxis.x));
    float sweepCentre=sin(clipSeconds*1.25+piecePhase)*.8;
    float sweep=exp2(-7*(along-sweepCentre)*(along-sweepCentre));
    float facetGlint=facetEdge*(.12+.18*sweep+.15*releaseEnergy+.18*saturate(screenState.y));
    // 保留背景原RGB；蓝色只落在裂口与倒角，片面不叠灰蓝底色或全局曝光滤镜。
    float glint=edge*(1+.40*saturate(screenState.y))+bevel
               +cutPatch*.025*releaseEnergy*(.65+.35*coarseSeed);
    float3 colour=displaced*(1-coarseShade*pieceMask*face*strength)
                 +float3(.20,.58,1)*glint*strength
                 +float3(.30,.74,1)*(coarseLight*pieceMask*face+facetGlint)*strength;
    // 有限片内提高覆盖以减少原背景重影，片外保留间隙；独立刀光层仍负责96道斩击。
    // 降低旧宽切带的覆盖，避免它把新多边形轮廓重新连成整块透明幕布。
    float coverage=max(face*(.88+.08*hold)*pieceMask,max(facetEdge*.88,cutPatch*.28));
    float alpha=boundary*strength*saturate(weight)*coverage*dissolve*input.colour.a;
    return float4(colour,saturate(alpha));
}
