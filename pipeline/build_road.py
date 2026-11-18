# 도로 레이어: 국토교통부 ITS 전국 표준노드링크(MOCT_LINK.shp)
# LANES는 링크(한 방향) 차로 수 → 왕복 차선 = 2×LANES (일방통행 제외). '8차선 이상' = LANES ≥ 4
# ROAD_RANK: 101 고속국도, 102 도시고속도로, 103 일반국도, 104 특별·광역시도, 105 국가지원지방도, 106 지방도, 107 시군도
# 출력: data/roads_big.json(고속·8차선↑), data/roads_main.json(그 밖의 국도·시도·지방도 왕복4차선↑) = {"r":[{"n":이름,"k":등급,"l":왕복차선(추정),"g":[[lon,lat]...] 여러 줄}], "ref":기준일}
import sys, os, json
import shapefile
from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, Point, shape
from shapely.ops import linemerge, unary_union
from shapely.prepared import prep
from collections import defaultdict

SHP = sys.argv[1]; SUB = sys.argv[2] if len(sys.argv) > 2 else 'data/sub.json'
KEEP = ('11', '23', '25', '29', '31', '33', '34', '35')
T = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m +no_defs', 4326, always_xy=True)

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
region = prep(unary_union(polys).buffer(0.02))

r = shapefile.Reader(SHP, encoding='cp949', encodingErrors='replace')
F = {f[0]: i for i, f in enumerate(r.fields[1:])}
groups = defaultdict(list)
seen = set(); n = 0
for sr in r.iterShapeRecords():
    rec = sr.record
    rank = rec[F['ROAD_RANK']]; lanes = int(rec[F['LANES']] or 0)
    big = rank in ('101', '102') or lanes >= 4
    main = rank in ('103', '104', '105', '106') and lanes >= 2
    if not (big or main): continue
    fn, tn = rec[F['F_NODE']], rec[F['T_NODE']]
    if (tn, fn) in seen: continue  # 반대 방향 링크는 한 번만
    seen.add((fn, tn))
    pts = sr.shape.points
    if len(pts) < 2: continue
    xs, ys = zip(*pts)
    lon, lat = T.transform(xs, ys)
    m = len(lon) // 2
    if not region.contains(Point(lon[m], lat[m])): continue
    name = (rec[F['ROAD_NAME']] or '').strip()
    cls = 'x' if rank in ('101', '102') else ('8' if lanes >= 4 else 'm')
    groups[(rank, name, cls, min(lanes, 6))].append(LineString(list(zip(lon, lat))))
    n += 1
print('links', n, 'groups', len(groups))
out = []
for (rank, name, cls, lanes), ls in groups.items():
    g = linemerge(ls).simplify(0.00015)
    parts = list(g.geoms) if g.geom_type == 'MultiLineString' else [g]
    coords = [[[round(x, 4), round(y, 4)] for x, y in p.coords] for p in parts if p.length > 0]
    coords = [c for c in coords if len(c) >= 2]
    if coords: out.append({'n': name, 'k': int(rank), 'c': cls, 'l': lanes * 2, 'g': coords})
ref = os.environ.get('ROADDATE', '')
# 고속도로·8차선 이상(x·8)과 그 밖의 주요도로(m)를 나눠 저장 → 필요할 때만 불러옴
for fn, cs in (('data/roads_big.json', 'x8'), ('data/roads_main.json', 'm')):
    json.dump({'r': [o for o in out if o['c'] in cs], 'ref': ref}, open(fn, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(fn, os.path.getsize(fn))
