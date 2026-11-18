import json, math
def dec(s):
    out=[];
    for part in s.split(' '):
        if not part: continue
        i=0;x=y=0;pts=[]
        while i<len(part):
            vals=[]
            for _ in range(2):
                r=0;sh=0
                while True:
                    b=ord(part[i])-63;i+=1;r|=(b&0x1f)<<sh;sh+=5
                    if b<0x20:break
                vals.append(~(r>>1) if r&1 else r>>1)
            y+=vals[0];x+=vals[1];pts.append([x/1e4,y/1e4])
        out.append(pts)
    return out
raw={}
for f in ['hw.raw']:
    d=json.loads(json.loads('"'+open(f).read().strip()+'"'))
    for n,r,s in d:
        e=raw.setdefault(n,{'r':set(),'l':[]})
        if r: e['r'].add(r)
        e['l']+=dec(s)
K=111000;C=math.cos(math.radians(36.5))
def segd(p,a,b):
    ax,ay,bx,by,px,py=a[0]*K*C,a[1]*K,b[0]*K*C,b[1]*K,p[0]*K*C,p[1]*K
    dx,dy=bx-ax,by-ay;l=dx*dx+dy*dy
    t=((px-ax)*dx+(py-ay)*dy)/l if l else 0;t=max(0,min(1,t))
    return math.hypot(px-ax-t*dx,py-ay-t*dy)
def L(l): return sum(math.hypot((l[i][0]-l[i-1][0])*K*C,(l[i][1]-l[i-1][1])*K) for i in range(1,len(l)))
out=[]
for n,e in raw.items():
    if '호선' in n or '고속도로' not in n: continue
    ls=sorted(e['l'],key=L,reverse=True); kept=[]
    for l in ls:
        if L(l)<300: continue
        near=sum(1 for p in l if any(segd(p,k[i],k[i+1])<150 for k in kept for i in range(len(k)-1)))
        if near/len(l)>0.7: continue
        kept.append(l)
    if not kept: continue
    ref=sorted(e['r'],key=len)[0] if e['r'] else ''
    if n=='중부내륙고속도로': ref='45'
    out.append({'n':n,'r':ref.split(';')[0],'s':'open','l':kept})
json.dump(out,open('data/hwy.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(out),len(open('data/hwy.json').read()))
print(sorted((o['n'],round(sum(L(l) for l in o['l'])/1000)) for o in out))
