# 학교 레이어 생성: raw/schools_raw.txt(전국초중등학교위치표준데이터 가공본) + raw/uni_osm.txt(OSM 대학)
# 출력: data/edu.json = {"s":[[name,type,lat1e5,lon1e5],...], "u":[[name,kind,lat1e5,lon1e5],...], "ref":날짜}
import json, re, sys, os
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

SUB = sys.argv[1] if len(sys.argv) > 1 else 'data/sub.json'
REF = os.environ.get('EDUDATE', '2026-10-01')
KEEP = ('11', '23', '25', '29', '31', '33', '34', '35')  # 서울 인천 대전 세종 경기 충북 충남 전북

# --- 대상 지역 폴리곤 (topojson -> shapely)
t = json.load(open(SUB))
sc, tr = t['transform']['scale'], t['transform']['translate']
arcs = []
for a in t['arcs']:
    x = y = 0; pts = []
    for dx, dy in a:
        x += dx; y += dy; pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
    arcs.append(pts)
def ring(ix):
    out = []
    for i in ix:
        p = arcs[i] if i >= 0 else arcs[~i][::-1]
        out.extend(p if not out else p[1:])
    return out
polys = []
for gm in t['objects']['skorea_submunicipalities_geo']['geometries']:
    if not gm['properties']['code'].startswith(KEEP): continue
    rs = gm['arcs'] if gm['type'] == 'Polygon' else [r for p in gm['arcs'] for r in p]
    if gm['type'] == 'Polygon':
        polys.append(shape({'type': 'Polygon', 'coordinates': [ring(r) for r in gm['arcs']]}).buffer(0))
    else:
        for p in gm['arcs']:
            polys.append(shape({'type': 'Polygon', 'coordinates': [ring(r) for r in p]}).buffer(0))
region = unary_union(polys).buffer(0.01)  # 해안 오차 1km 여유
inside = lambda lat, lon: region.contains(Point(lon / 1e5, lat / 1e5))

# --- 초중고
S = []
for ln in open('raw/schools_raw.txt', encoding='utf-8'):
    ln = ln.rstrip('\n')
    if not ln: continue
    n, ty, la, lo = ln.rsplit(',', 3)
    S.append([n, ty, int(la), int(lo)])

# --- 대학 (OSM, 이름 규칙으로 캠퍼스만 남김)
BAD = re.compile(r'(대학원$|대학원대학교|학습관|학습센터|지역대학|평생교육원|사회교육원|미래교육원|사업단|산학협력|정문|후문|쪽문|연수원|학술림|선수촌|부속|부설|승마장|숙소|예정|강당|실버대학|불교대학|교정$|LC|호관|본부|폐교|의과대학$|치과대학$|해양교육원|창작캠퍼스|평생대학|창의팩토리|^대학|^전자정보대학|^생명자원과학대학|^재활과학대학|공동캠퍼스|도심캠퍼스|^인천글로벌캠퍼스|^미술대학교|^공과대학|방송통|사이버|디지털서울|서울디지털대|평화복지대학원)')
OK = re.compile(r'(대학교|대학|캠퍼스)( ?[^ ]*캠퍼스)?$')
EXTRA = {'한국과학기술원', '한국예술종합학교', '경찰대학'}
U = []
for ln in open('raw/uni_osm.txt', encoding='utf-8'):
    p = ln.rstrip('\n').split('\t')
    if len(p) < 4 or not p[0]: continue
    n = re.sub(r'\s+', ' ', p[0]).strip().replace('캨퍼스', '캠퍼스').replace(' 캠퍼스', '캠퍼스')
    if not (n in EXTRA or (OK.search(n) and not BAD.search(n))): continue
    la, lo = int(p[2]), int(p[3])
    if not inside(la, lo): continue
    U.append([n, 'c' if p[1] == 'college' else 'u', la, lo])
# 같은 학교(앞 단어 동일) 2km 안 중복 → 이름이 긴 쪽(캠퍼스명 포함) 하나만
U.sort(key=lambda u: -len(u[0]))
V = []
for u in U:
    b = u[0].split(' ')[0]
    if any(v[0].split(' ')[0] == b and abs(v[2] - u[2]) + abs(v[3] - u[3]) < 2500 for v in V): continue
    V.append(u)
U = V

out = {'s': S, 'u': sorted(U), 'ref': REF}
os.makedirs('data', exist_ok=True)
json.dump(out, open('data/edu.json', 'w'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print('schools', len(S), Counter(x[1][0] for x in S), 'univ', len(U))
