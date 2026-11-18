# 상권 경계: ① 서울시 상권분석서비스(영역-상권) SHP(EPSG:5181, UTF-8) — 발달상권·골목상권·전통시장·관광특구
#            ② 소상공인시장진흥공단 주요상권현황 CSV(cp949, '경도,위도|...' 문자열) — 서울 밖 7개 시도
# 출력 data/shop_zone.json = {z:[{n:이름,t:종류,s:시군구,c:[[lon,lat]..]}], ref:{seoul,major}}
import csv, json, os, sys
import shapefile
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
csv.field_size_limit(10**8)
T = Transformer.from_crs(5181, 4326, always_xy=True)
TOL = 0.00008  # 약 8m 단순화
def ring(pts):
    p = Polygon(pts).buffer(0)
    if p.is_empty: return None
    if p.geom_type == 'MultiPolygon': p = max(p.geoms, key=lambda g: g.area)
    p = orient(p.simplify(TOL, preserve_topology=True), -1.0)  # d3-geo는 바깥 고리가 시계방향이어야 함
    return [[round(x, 5), round(y, 5)] for x, y in p.exterior.coords]
out = []
r = shapefile.Reader('raw/seoul', encoding='utf-8')
F = [f[0] for f in r.fields[1:]]
for sr in r.iterShapeRecords():
    d = dict(zip(F, sr.record))
    pts = sr.shape.points[:sr.shape.parts[1]] if len(sr.shape.parts) > 1 else sr.shape.points
    xs, ys = zip(*pts); lon, lat = T.transform(xs, ys)
    c = ring(list(zip(lon, lat)))
    if c: out.append({'n': d['TRDAR_CD_N'], 't': d['TRDAR_SE_1'], 's': d['SIGNGU_CD_'], 'c': c})
KEEP = {'인천광역시', '경기도', '대전광역시', '세종특별자치시', '충청북도', '충청남도', '전북특별자치도'}
rows = csv.reader(open('raw/major_zones.csv', encoding='cp949')); h = next(rows)
mref = ''
for row in rows:
    d = dict(zip(h, row))
    if d['시도명'] not in KEEP: continue
    pts = [tuple(float(v.strip('()[] ')) for v in p.split(',')[:2]) for p in d['상권좌표'].split('|') if ',' in p]
    c = ring(pts) if len(pts) >= 3 else None
    if c: out.append({'n': d['상권명'].strip(), 't': '주요상권', 's': d['시군구명'], 'c': c}); mref = d['데이터기준일자']
json.dump({'z': out, 'ref': {'seoul': os.environ.get('SEOULZONE', ''), 'major': mref}}, open('data/shop_zone.json', 'w'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print(len(out), Counter(o['t'] for o in out), os.path.getsize('data/shop_zone.json'))
