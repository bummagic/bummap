# 인구밀도·유동인구 레이어
# 입력: raw/grid1k.txt (SGIS 2024 1km 격자: 코드\t총인구\t5~19세\t가구\t1인가구)
#       raw/seoul_lp.txt (서울 생활인구 행정동: 코드8\t하루평균\t주간09~18\t야간19~06)
#       raw/gg_fp.txt (경기 유동인구 행정동 시간대별: 기준년월\t시간대\t행정동코드10\t동명\t유동인구수)
#       raw/HangJeongDong.geojson (vuski/admdongkor 현행 행정동 경계)
# 출력: data/pop.json, data/flow.json
import json, os, sys
from pyproj import Transformer
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union

SUB = sys.argv[1] if len(sys.argv) > 1 else 'data/sub.json'
KEEP = ('11', '23', '25', '29', '31', '33', '34', '35')
T = Transformer.from_crs(5179, 4326, always_xy=True)
L = '가나다라마바사아'

# 대상 지역 폴리곤(2013 통계청 경계)
t = json.load(open(SUB)); sc, tr = t['transform']['scale'], t['transform']['translate']
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
    for p in ([gm['arcs']] if gm['type'] == 'Polygon' else gm['arcs']):
        polys.append(shape({'type': 'Polygon', 'coordinates': [ring(r) for r in p]}).buffer(0))
region = unary_union(polys).buffer(0.01)
from shapely.prepared import prep
pregion = prep(region)

G = []
for ln in open('raw/grid1k.txt', encoding='utf-8'):
    c, p, a, h, o = ln.rstrip('\n').split('\t')
    p, a, h, o = int(p), int(a), int(h), int(o)
    if p <= 0: continue
    x = 700000 + 100000 * L.index(c[0]) + int(c[2:4]) * 1000 + 500
    y = 1300000 + 100000 * L.index(c[1]) + int(c[4:6]) * 1000 + 500
    lon, lat = T.transform(x, y)
    if not pregion.contains(Point(lon, lat)): continue
    G.append([round(lat, 4), round(lon, 4), p, a, h, o])
json.dump({'g': G, 'ref': os.environ.get('POPDATE', '2024년'), 'src': 'SGIS 격자 통계(1km)'},
          open('data/pop.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('pop grids', len(G), 'pop sum', sum(g[2] for g in G))

# 유동인구
adm = json.load(open('raw/HangJeongDong.geojson'))
seoul = {}
for ln in open('raw/seoul_lp.txt'):
    c, a, d, n = ln.split()
    seoul[c] = (int(a), int(d), int(n))
gg, ggym = {}, ''
for ln in open('raw/gg_fp.txt', encoding='utf-8'):
    ym, tz, cd, nm, v = ln.rstrip('\n').split('\t')
    ggym = ym
    gg.setdefault(cd, {})[tz] = float(v)

from pyproj import Geod
geod = Geod(ellps='WGS84')
F = []
for f in adm['features']:
    pr = f['properties']; cd2 = pr['adm_cd2']
    if pr['sido'] == '11':
        v = seoul.get(cd2[:8])
        if not v: continue
        val, extra = v[0], [v[1], v[2]]
    else:  # 경기 파일은 행정동 값이 시군구 값 복제(2026.11 확인)라 동 단위 표시에서 제외

        continue
    gmt = shape(f['geometry']).buffer(0)
    area = abs(geod.geometry_area_perimeter(gmt)[0]) / 1e6
    s = gmt.simplify(0.0004, preserve_topology=True)
    def rnd(o):
        if isinstance(o, (list, tuple)) and o and isinstance(o[0], (int, float)): return [round(o[0], 4), round(o[1], 4)]
        return [rnd(x) for x in o]
    gj = mapping(s)
    F.append({'n': pr['adm_nm'].split(' ', 1)[1], 's': pr['sido'], 'v': round(val), 'a': round(area, 2), 'd': round(val / max(area, 0.05)), 'x': extra,
              't': gj['type'], 'c': rnd(gj['coordinates'])})
# 시도별 백분위 등급(밀도 기준): 4=상위10%, 3=상위25%, 2=상위50%, 1=나머지
for sd in ('11',):
    arr = sorted(x['d'] for x in F if x['s'] == sd)
    q = lambda p: arr[int(len(arr) * p)]
    q90, q75, q50 = q(.9), q(.75), q(.5)
    for x in F:
        if x['s'] == sd: x['k'] = 4 if x['d'] >= q90 else 3 if x['d'] >= q75 else 2 if x['d'] >= q50 else 1
json.dump({'f': F, 'seoul': os.environ.get('SEOULYM', '2026년 7월')},
          open('data/flow.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('flow dongs', len(F), 'gg ym', ggym)
