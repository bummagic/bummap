import json, math
src=json.load(open('kr-rail-map/data/lines.geojson'))
K=111000; C=math.cos(math.radians(37.5))
def segd(p,a,b):
    ax,ay,bx,by,px,py=a[0]*K*C,a[1]*K,b[0]*K*C,b[1]*K,p[0]*K*C,p[1]*K
    dx,dy=bx-ax,by-ay; l=dx*dx+dy*dy
    t=((px-ax)*dx+(py-ay)*dy)/l if l else 0; t=max(0,min(1,t))
    return math.hypot(px-ax-t*dx,py-ay-t*dy)
def dp(pts,eps=25):
    if len(pts)<3: return pts
    md,mi=0,0
    for i in range(1,len(pts)-1):
        d=segd(pts[i],pts[0],pts[-1])
        if d>md: md,mi=d,i
    if md>eps: return dp(pts[:mi+1],eps)[:-1]+dp(pts[mi:],eps)
    return [pts[0],pts[-1]]
def lines_of(g):
    return [g['coordinates']] if g['type']=='LineString' else g['coordinates']
def inbox(ls):
    return True
OPEN_SKIP={'wolmi-sea-train','incheon-international-airport-shuttle-train','incheon-airport-maglev-line-eastbound','jichuk-depot-line','seoul-metro-line-4-chang-dong-depot-line','seoul-metro-line-4-nowon-chang-dong-line','gtx-a-changneung','dongbu-line'}
out=[];IDS=[]
def add(name,status,color,ls,info,src_note,approx=False,k='m',lid=None):
    IDS.append(lid)
    eps=25 if k=='m' else 60
    ls=[[[round(c[0],4),round(c[1],4)] for c in dp(l,eps)] for l in ls if len(l)>1]
    out.append({'n':name,'s':status,'c':color,'i':info,'src':src_note,'ap':approx,'k':k,'l':ls})
for f in src['features']:
    p=f['properties']; ls=lines_of(f['geometry'])
    if not inbox(ls): continue
    st=p['status']; cat=p['category']; pid=p['id']
    if pid in OPEN_SKIP or p['name_ko'] in ('군산항선','옥서삼각선','장항화물선','포스코 포항제철소선'): continue
    k={'metro':'m','urban':'m','ktx':'ktx','conventional':'rail'}.get(cat,'rail')
    if st=='open':
        add(p['name_ko'],'open',p.get('color') or '#888',ls,'운행 중','OSM',False,k,pid)
    else:
        approx=p.get('coord_source')=='own'
        s='construction' if st=='construction' else 'planned'
        info=(p.get('plan_stage') or '')+' · 개통: '+(p.get('opened') or '-')
        add(p['name_ko'],s,p.get('color') or '#888',ls,info,p.get('plan_url',''),approx,k,pid)
osm=json.load(open('osm_raw.json'))
META={
 '신안산선':('construction','#1E9E8F','공사 중 · 개통: 2028~2029년으로 연기(광명 붕괴사고 후 공기 연장 검토)'),
 '월곶판교선':('construction','#003DA5','공사 중 · 개통: 2029년 말 목표'),
 '동탄인덕원선':('construction','#3A7BD5','공사 중 · 개통: 2029년 목표 (2026.7 공정률 19.9%)'),
 '9호선 4단계':('construction','#BDB092','공사 중 · 개통: 2028년 예정'),
 '서울 지하철 7호선':('construction','#747F00','7호선 청라 연장 · 공사 중 · 개통: 2027년 목표'),
 '서울 지하철 7호선 도봉산옥정선':('construction','#747F00','7호선 도봉산~옥정 · 공사 중 · 개통: 2027년 말 (2026.1 전 구간 관통)'),
 '옥정포천선':('construction','#747F00','7호선 옥정~포천 · 공사 중(2025.3 착공) · 개통: 2030년 목표'),
 '신분당선 광교-호매실':('construction','#D4003B','공사 중 · 개통: 2029년 12월 목표'),
 '대장홍대선':('construction','#8C6D3F','공사 중(2026.3 공정률 6%) · 개통: 2031년 목표'),
 '3호선 하남연장':('planned','#EF7C1C','송파하남선 · 기본계획 승인(2025.7), 시공사 선정 중 · 2027년 착공·2032년 개통 목표'),
 '강동하남남양주선':('planned','#BDB092','9호선 연장 · 기본계획 승인(2025.7) · 2027년 착공 목표'),
 '신분당선 용산-신사 연장':('planned','#D4003B','신분당선 2단계 · 실시설계 중 · 2027년 상반기 착공 목표'),
}
for n,(s,c,info) in META.items():
    v=osm[n]
    nm={'서울 지하철 7호선':'7호선 청라 연장','서울 지하철 7호선 도봉산옥정선':'7호선 도봉산옥정선','3호선 하남연장':'3호선 하남연장(송파하남선)'}.get(n,n)
    add(nm,s,c,v['l'],info,'OSM')
json.dump(out,open('data/rail.json','w'),ensure_ascii=False,separators=(',',':'))
import collections
print(collections.Counter(o['s'] for o in out)); print(len(open('data/rail.json').read()))
for o in out:
    if o['s']!='open': print(o['s'],o['n'],o['ap'],o['i'][:60])

# stations
st=json.load(open('kr-rail-map/data/stations.geojson'))
idx={l:i for i,l in enumerate(IDS) if l}
S=[]
for f in st['features']:
    p=f['properties'];ii=sorted({idx[l] for l in (p.get('lines') or [p.get('line_id')]) if l in idx})
    if not ii: continue
    x,y=f['geometry']['coordinates'][:2]
    S.append([p['name_ko'],round(x,4),round(y,4),out[ii[0]]['k'],ii])
json.dump(S,open('data/stations.json','w'),ensure_ascii=False,separators=(',',':'))
print('stations',len(S))
