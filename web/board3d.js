// Presentation-only WebGL renderer. No legal move logic lives here.
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.185.1/build/three.module.js';

const profiles={
 p:[[.32,0],[.34,.06],[.30,.13],[.20,.18],[.13,.34],[.18,.40],[.13,.43]],
 r:[[.34,0],[.35,.08],[.29,.15],[.22,.23],[.21,.48],[.31,.53],[.31,.66]],
 n:[[.34,0],[.35,.08],[.29,.15],[.23,.22],[.19,.30]],
 b:[[.34,0],[.35,.07],[.29,.15],[.17,.25],[.13,.48],[.24,.52],[.17,.57]],
 q:[[.35,0],[.36,.08],[.30,.16],[.18,.25],[.13,.55],[.24,.60],[.22,.66],[.32,.78]],
 k:[[.36,0],[.37,.08],[.31,.16],[.19,.26],[.14,.58],[.25,.64],[.22,.70],[.30,.79]]
};
const heights={p:.61,r:.72,n:.83,b:.88,q:.99,k:1.11};
const coord=s=>({x:s.charCodeAt(0)-97-3.5,z:8-Number(s[1])-3.5});
function mesh(geometry,material,x=0,y=0,z=0){
 const m=new THREE.Mesh(geometry,material);m.position.set(x,y,z);m.castShadow=true;m.receiveShadow=true;return m;
}
function model(type,white){
 const g=new THREE.Group();
 const mat=new THREE.MeshStandardMaterial({color:white?0xf5e4c2:0x253043,roughness:.32,metalness:.16});
 const trim=new THREE.MeshStandardMaterial({color:white?0x9d783c:0x9fb6d1,roughness:.38,metalness:.45});
 const path=profiles[type].map(([r,y])=>new THREE.Vector2(r,y));
 path.unshift(new THREE.Vector2(0,0));path.push(new THREE.Vector2(0,path.at(-1).y));
 g.add(mesh(new THREE.LatheGeometry(path,40),mat));
 const ring=mesh(new THREE.TorusGeometry(.30,.025,10,40),trim,0,.11);ring.rotation.x=Math.PI/2;g.add(ring);
 const ball=(r,y)=>g.add(mesh(new THREE.SphereGeometry(r,24,16),mat,0,y));
 if(type==='p')ball(.155,.47);
 if(type==='r'){
  for(let i=0;i<6;i++){const a=i*Math.PI/3;const m=mesh(new THREE.BoxGeometry(.16,.14,.16),mat,.23*Math.cos(a),.67,.23*Math.sin(a));m.rotation.y=-a;g.add(m)}
 }
 if(type==='b'){
  const top=mesh(new THREE.SphereGeometry(.20,24,16),mat,0,.68);top.scale.y=1.15;g.add(top);ball(.055,.86);
  const slit=mesh(new THREE.BoxGeometry(.034,.21,.022),trim,0,.70,.188);slit.rotation.z=-.5;g.add(slit);
 }
 if(type==='q'){
  for(let i=0;i<8;i++){const a=i*Math.PI/4;g.add(mesh(new THREE.ConeGeometry(.075,.17,12),mat,.25*Math.cos(a),.84,.25*Math.sin(a)))}
  ball(.095,.83);ball(.045,.97);
 }
 if(type==='k'){
  ball(.17,.79);g.add(mesh(new THREE.BoxGeometry(.075,.25,.075),trim,0,.98));
  g.add(mesh(new THREE.BoxGeometry(.23,.07,.075),trim,0,1.015));
 }
 if(type==='n'){
  const shape=new THREE.Shape();
  shape.moveTo(-.23,.27);shape.lineTo(-.19,.52);shape.lineTo(-.30,.66);shape.lineTo(-.10,.79);shape.lineTo(.04,.78);shape.lineTo(.11,.88);shape.lineTo(.18,.76);shape.quadraticCurveTo(.30,.62,.22,.43);shape.lineTo(.13,.27);shape.closePath();
  const head=mesh(new THREE.ExtrudeGeometry(shape,{depth:.18,bevelEnabled:true,bevelThickness:.025,bevelSize:.025,bevelSegments:3,steps:1}),mat,0,0,-.09);g.add(head);
  for(const side of [-1,1])g.add(mesh(new THREE.SphereGeometry(.027,12,8),trim,-.10,.68,side*.116));
 }
 return g;
}
export function createBoard3D({stage,canvas,labels,info,choose,fail}){
 const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
 renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 const scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(39,1,.1,100);
 scene.add(new THREE.HemisphereLight(0xeaf3ff,0x79706a,2.1));
 const key=new THREE.DirectionalLight(0xffffff,2.5);key.position.set(-4,10,6);key.castShadow=true;
 Object.assign(key.shadow.camera,{left:-7,right:7,top:7,bottom:-7,near:.5,far:30});key.shadow.mapSize.set(1024,1024);key.shadow.bias=-.0005;key.shadow.normalBias=.02;scene.add(key);
 const rim=new THREE.DirectionalLight(0xabc9ff,1.5);rim.position.set(5,5,-5);scene.add(rim);
 const base=mesh(new THREE.BoxGeometry(8.48,.34,8.48),new THREE.MeshStandardMaterial({color:0x30251c,roughness:.45,metalness:.1}),0,-.20);scene.add(base);
 const tiles=new Map(), pieces=new Map(), flagCache=new Map(), marks=new Map(), labelEntries=[];
 const loader=new THREE.TextureLoader();loader.setCrossOrigin('anonymous');
 let state=null,selected=null,semantic=true,mode='always',active=false,hover=null,raf=0,failed=false;
 let azimuth=0,elevation=1.03,distance=16.5;
 const ray=new THREE.Raycaster(), ndc=new THREE.Vector2(), projected=new THREE.Vector3();
 const tileGeo=new THREE.PlaneGeometry(.985,.985);
 function flag(code){
  if(!flagCache.has(code)){
   const record={texture:null,loading:true};flagCache.set(code,record);
   loader.load('https://flagcdn.com/w320/'+code+'.png',tex=>{
    tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());record.texture=tex;record.loading=false;
    if(active&&state){paintTiles();draw()}
   },undefined,()=>{record.loading=false;record.error=true;if(active&&state){paintTiles();draw()}});
  }
  return flagCache.get(code);
 }
 for(let rank=1;rank<=8;rank++)for(let file=0;file<8;file++){
  const s=String.fromCharCode(97+file)+rank,{x,z}=coord(s);
  const tile=mesh(tileGeo,new THREE.MeshStandardMaterial({color:0xd5c4a5,roughness:.9}),x,0,z);tile.rotation.x=-Math.PI/2;tile.castShadow=false;tile.userData.square=s;scene.add(tile);tiles.set(s,tile);
  const mark=new THREE.Mesh(new THREE.RingGeometry(.36,.45,40),new THREE.MeshBasicMaterial({color:0x55ffad,side:THREE.DoubleSide,depthWrite:false}));mark.rotation.x=-Math.PI/2;mark.position.set(x,.022,z);mark.visible=false;scene.add(mark);marks.set(s,mark);
 }
 function paintTiles(){
  for(const s of state.squares){
   const tile=tiles.get(s.square),record=semantic?flag(s.code):null;
   const dark=(s.square.charCodeAt(0)-97+Number(s.square[1]))%2;
   tile.material.map=record?.texture||null;tile.material.color.set(record?.texture?0xffffff:dark?0x98744e:0xe0cda9);tile.material.needsUpdate=true;
  }
 }
 function removePiece(entry){scene.remove(entry.group);entry.group.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose()}})}
 function makeLabel(text,kind,square,height){
  const el=document.createElement('span');el.className='label3d '+kind;el.textContent=text;labels.append(el);labelEntries.push({el,kind,square,height});
 }
 function update(next,selection,flags,labelMode){
  state=next;selected=selection;semantic=flags;mode=labelMode;hover=null;
  paintTiles();const seen=new Set();
  for(const s of state.squares){
   const p=s.piece,{x,z}=coord(s.square),mark=marks.get(s.square);
   const legal=selected&&state.legal.some(m=>m.startsWith(selected+s.square));mark.visible=Boolean(legal||selected===s.square);mark.material.color.set(selected===s.square?0xffd05a:0x55ffad);
   if(!p)continue;seen.add(p.id);let entry=pieces.get(p.id);
   if(entry&&entry.symbol!==p.symbol){removePiece(entry);pieces.delete(p.id);entry=null}
   if(!entry){
    const group=model(p.symbol.toLowerCase(),p.symbol===p.symbol.toUpperCase());scene.add(group);entry={group,symbol:p.symbol};pieces.set(p.id,entry);
   }
   entry.group.position.set(x,.025,z);entry.group.userData.square=s.square;
  }
  for(const [id,entry] of pieces)if(!seen.has(id)){removePiece(entry);pieces.delete(id)}
  labels.replaceChildren();labelEntries.length=0;
  for(const s of state.squares){
   if(semantic&&s.piece)makeLabel(s.piece.name+(s.piece.self_actualized?' ★':''),'character',s.square,heights[s.piece.symbol.toLowerCase()]+.17);
   if(!semantic||mode!=='none')makeLabel(semantic?s.name:s.square,'country',s.square,.06);
  }
  info.textContent='';draw();
 }
 function placeCamera(){
  const r=distance*Math.cos(elevation);
  camera.position.set(r*Math.sin(azimuth),distance*Math.sin(elevation),r*Math.cos(azimuth));camera.lookAt(0,.08,0);camera.updateMatrixWorld();
 }
 function draw(){
  if(!active||failed)return;
  placeCamera();renderer.render(scene,camera);
  const w=stage.clientWidth,h=stage.clientHeight;
  for(const l of labelEntries){
   const {x,z}=coord(l.square);
   projected.set(x,l.height,z+(l.kind==='country'?.36:0)).project(camera);
   l.el.hidden=projected.z>1||projected.z< -1||(l.kind==='country'&&semantic&&mode==='hover'&&hover!==l.square);
   l.el.style.left=((projected.x*.5+.5)*w)+'px';l.el.style.top=((-.5*projected.y+.5)*h)+'px';
  }
 }
 function resize(){
  if(!active)return;const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h)return;
  camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);draw();
 }
 const observer=new ResizeObserver(resize);observer.observe(stage);
 function hit(e){
  const r=canvas.getBoundingClientRect();ndc.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(ndc,camera);
  const targets=[...tiles.values(),...Array.from(pieces.values(),p=>p.group)];
  const hits=ray.intersectObjects(targets,true);
  for(const item of hits){let o=item.object;while(o&&!o.userData.square)o=o.parent;if(o?.userData.square)return o.userData.square}return null;
 }
 const pointers=new Map();let drag=false,down=null,pinch=0;
 canvas.addEventListener('pointerdown',e=>{if(!active)return;canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size===1){drag=false;down={x:e.clientX,y:e.clientY}}else{drag=true;const p=[...pointers.values()];pinch=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y)}});
 canvas.addEventListener('pointermove',e=>{
  const prev=pointers.get(e.pointerId);
  if(prev){pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
   if(pointers.size===2){const p=[...pointers.values()],d=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);if(pinch&&d)distance=THREE.MathUtils.clamp(distance*pinch/d,11,23);pinch=d;drag=true;draw();return}
   if(pointers.size===1&&down){if(Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)drag=true;if(drag){azimuth-=(e.clientX-prev.x)*.009;elevation=THREE.MathUtils.clamp(elevation+(e.clientY-prev.y)*.006,.56,1.565);draw();return}}
  }
  hover=hit(e);const s=state?.squares.find(s=>s.square===hover);
  info.textContent=s?(semantic?(mode==='none'?'':s.name+' · '):'')+s.square+(s.piece?' · '+s.piece.name+' ('+s.piece.capability+')':''):'';
  canvas.style.cursor=hover?'pointer':'grab';draw();
 });
 canvas.addEventListener('pointerup',e=>{if(!pointers.has(e.pointerId))return;const tap=!drag&&pointers.size===1;pointers.delete(e.pointerId);if(!pointers.size){down=null;pinch=0}if(tap){const square=hit(e);if(square)choose(square)}});
 canvas.addEventListener('pointercancel',e=>{pointers.delete(e.pointerId);drag=true;down=null;pinch=0});
 canvas.addEventListener('pointerleave',()=>{hover=null;info.textContent='';draw()});
 canvas.addEventListener('wheel',e=>{e.preventDefault();distance=THREE.MathUtils.clamp(distance*Math.exp(e.deltaY*.001),11,23);draw()},{passive:false});
 canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();failed=true;fail('WebGL context lost; reload to retry 3D. 2D remains playable.')});
 return {update,setActive(on){active=on&&!failed;if(active){resize();draw()}},flip(){azimuth+=Math.PI;draw()},overhead(){elevation=1.565;draw()},home(){azimuth=0;elevation=1.03;distance=16.5;draw()}};
}
