// Run in the built-in browser on a tab at https://maps.mail.ru/osm/tools/overpass/api/status (same-origin Overpass mirror).
// 1) paste this whole file via javascript_tool; 2) poll JSON.stringify(KRH.status()); 3) when done, read KRH.chunks[i] one by one.
window.KRH=(function(){
const K=111000,C=Math.cos(36.5*Math.PI/180);
const segd=(p,a,b)=>{const ax=a[0]*K*C,ay=a[1]*K,bx=b[0]*K*C,by=b[1]*K,px=p[0]*K*C,py=p[1]*K;const dx=bx-ax,dy=by-ay;const l=dx*dx+dy*dy;let t=l?((px-ax)*dx+(py-ay)*dy)/l:0;t=Math.max(0,Math.min(1,t));return Math.hypot(px-ax-t*dx,py-ay-t*dy)};
const dp=(pts,eps)=>{if(pts.length<3)return pts;let md=0,mi=0;for(let i=1;i<pts.length-1;i++){const d=segd(pts[i],pts[0],pts[pts.length-1]);if(d>md){md=d;mi=i}}return md>eps?dp(pts.slice(0,mi+1),eps).slice(0,-1).concat(dp(pts.slice(mi),eps)):[pts[0],pts[pts.length-1]]};
const len=l=>{let s=0;for(let i=1;i<l.length;i++)s+=Math.hypot((l[i][0]-l[i-1][0])*K*C,(l[i][1]-l[i-1][1])*K);return s};
const norm=n=>n.replace(/\s*\(.*\)\s*/g,'').replace(/(고속도로).*$/,'$1').trim();
const enc=ls=>ls.map(l=>{let px=0,py=0,s='';for(const p of l){const x=Math.round(p[0]*1e4),y=Math.round(p[1]*1e4);for(let v of [y-py,x-px]){v=v<0?~(v<<1):(v<<1);while(v>=0x20){s+=String.fromCharCode((0x20|(v&0x1f))+63);v>>=5}s+=String.fromCharCode(v+63)}px=x;py=y}return s}).join(' ');
const tiles=[];for(let la=33;la<38.7;la+=1)for(let lo=125.5;lo<130;lo+=1)tiles.push([la,lo,Math.min(la+1,38.7),lo+1]);
const ways=new Map(),log=[];let done=false;const st={chunks:[]};
async function q(t){const b=`(${t.join(',')})`;const r=await fetch('/osm/tools/overpass/api/interpreter',{method:'POST',body:'data='+encodeURIComponent(`[out:json][timeout:170];way["highway"="motorway"]${b};out tags geom;`)});if(!r.ok)throw r.status;return (await r.json()).elements}
async function run(){let i=0;async function w(){while(i<tiles.length){const t=tiles[i++];let ok=false;for(let a=0;a<6&&!ok;a++){try{const els=await q(t);for(const e of els){if(!e.geometry)continue;ways.set(e.id,[e.id,(e.tags||{}).name||'',(e.tags||{}).ref||'',0,dp(e.geometry.map(p=>[p.lon,p.lat]),25)])}log.push(t.join(',')+':'+els.length);ok=true}catch(e){await new Promise(r=>setTimeout(r,8000))}}if(!ok)log.push(t.join(',')+':FAIL')}}
await Promise.all([w(),w()]);
const G={};for(const w of ways.values()){const n=norm(w[1])||(w[2]?'고속도로 '+w[2]+'호선':'(이름 없음)');(G[n]=G[n]||{ref:w[2],ls:[]}).ls.push(w[4]);if(!G[n].ref&&w[2])G[n].ref=w[2]}
const key=p=>p[0].toFixed(4)+','+p[1].toFixed(4);const out=[];
for(const [n,g] of Object.entries(G)){let ls=g.ls.map(l=>l.slice());let ch=true;while(ch){ch=false;const ends=new Map();for(let i=0;i<ls.length;i++){if(!ls[i])continue;const s=key(ls[i][0]),e=key(ls[i][ls[i].length-1]);(ends.get(s)||ends.set(s,[]).get(s)).push([i,0]);(ends.get(e)||ends.set(e,[]).get(e)).push([i,1])}
for(const [k,arr] of ends){if(arr.length!==2)continue;const [[i,a],[j,b]]=arr;if(i===j||!ls[i]||!ls[j])continue;let A=ls[i],B=ls[j];if(a===0)A=A.slice().reverse();if(b===1)B=B.slice().reverse();ls[i]=A.concat(B.slice(1));ls[j]=null;ch=true;break}ls=ls.filter(Boolean)}
ls.sort((a,b)=>len(b)-len(a));const kept=[];for(const l of ls){const s=dp(l,60);const near=s.filter(p=>kept.some(k=>k.some((q,i)=>i<k.length-1&&segd(p,q,k[i+1])<120))).length;if(near/s.length>0.8)continue;kept.push(s)}
out.push([n,g.ref||'',enc(kept.map(l=>dp(l,90)))])}
const S=JSON.stringify(out);for(let i=0;i<S.length;i+=36000)st.chunks.push(S.slice(i,i+36000));done=true}
run();
return {status:()=>({done,tiles:tiles.length,log,ways:ways.size,chunks:st.chunks.length}),get chunks(){return st.chunks}};
})();'started'
