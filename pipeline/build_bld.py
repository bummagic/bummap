# 건물 레이어(2D/3D): 브이월드 GIS건물통합정보 시도별 전체데이터 SHP(AL_D010_{시도}_{기준일}.zip)
# 출력: bld/{x}_{y}.json (z13 타일, 경도·위도 1e-5도 정수 델타 부호화) + bld/index.json
# 레코드: [용도분류, 지상층수, 높이(0.1m), 사용승인연도, 동이름표번호, 지번, 건물명, 연면적(㎡), 좌표(평면 정수 델타)]
import sys, os, json, math, zipfile, io, glob, re, gzip
import shapefile
from pyproj import Transformer
from collections import defaultdict

Z = 13
OUT = sys.argv[1] if len(sys.argv) > 1 else 'bld'
ZIPS = sys.argv[2:]
os.makedirs(OUT, exist_ok=True)

CAT = {'공동주택': 1, '단독주택': 2, '제1종근린생활시설': 3, '제2종근린생활시설': 3, '근린생활시설': 3, '판매시설': 3, '숙박시설': 3, '위락시설': 3,
       '업무시설': 4, '교육연구시설': 5, '노유자시설': 5, '수련시설': 5,
       '문화및집회시설': 6, '종교시설': 6, '의료시설': 6, '운동시설': 6, '운수시설': 6, '관광휴게시설': 6, '방송통신시설': 6, '교정및군사시설': 6,
       '공장': 7, '창고시설': 7, '위험물저장및처리시설': 7, '자동차관련시설': 7, '동.식물 관련시설': 7, '분뇨.쓰레기처리시설': 7, '자원순환관련시설': 7}

def tile(lon, lat):
    n = 2 ** Z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y

def tile_sw(x, y):
    n = 2 ** Z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon, lat

def dp(pts, eps):  # Douglas-Peucker (평면 좌표, m)
    if len(pts) < 4: return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-9
    i, dm = 0, -1
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + b[0] * a[1] - b[1] * a[0]) / L
        if d > dm: i, dm = k, d
    if dm > eps:
        return dp(pts[:i + 1], eps)[:-1] + dp(pts[i:], eps)
    return [a, b]

tiles = defaultdict(lambda: {'d': [], 'r': []})
stats = defaultdict(int)
for zp in ZIPS:
    z = zipfile.ZipFile(zp)
    for base in [n[:-4] for n in z.namelist() if n.endswith('.shp')]:
        prj = z.read(base + '.prj').decode('utf-8', 'ignore')
        epsg = re.findall(r'AUTHORITY\["EPSG","(\d+)"\]\]$', prj.strip()) or ['5186']
        T = Transformer.from_crs(int(epsg[0]), 4326, always_xy=True)
        tmpd = '/tmp/bld_x'; os.makedirs(tmpd, exist_ok=True)
        for ext in ('.shp', '.shx', '.dbf'): z.extract(base + ext, tmpd)
        r = shapefile.Reader(os.path.join(tmpd, base), encoding='cp949', encodingErrors='replace')
        for sr in r.iterShapeRecords():
            rec, shp = sr.record, sr.shape
            if not shp.points: continue
            parts = list(shp.parts) + [len(shp.points)]
            ring = shp.points[parts[0]:parts[1]]  # 외곽 링만
            if len(ring) > 4:
                if ring[0] == ring[-1]: ring = ring[:-1]
                m = len(ring) // 2
                ring = dp(ring[:m + 1], 0.6)[:-1] + dp(ring[m:] + [ring[0]], 0.6)[:-1]
            if len(ring) < 3: continue
            xs, ys = zip(*ring)
            lons, lats = T.transform(xs, ys)
            cx, cy = sum(lons) / len(lons), sum(lats) / len(lats)
            tx, ty = tile(cx, cy)
            t = tiles[(tx, ty)]
            if 'o' not in t: t['o'] = tile_sw(tx, ty)
            ox, oy = t['o']
            q = [(round((lo - ox) * 1e5), round((la - oy) * 1e5)) for lo, la in zip(lons, lats)]
            if q[0] == q[-1]: q = q[:-1]
            flat, px, py = [], 0, 0
            for a, b in q:
                flat += [a - px, b - py]; px, py = a, b
            use = (rec[9] or '').strip()
            cat = CAT.get(use, 8 if use else 0)
            fl = int(rec[26] or 0); h = float(rec[16] or 0)
            if h <= 0: h = fl * 3.3 if fl > 0 else 3.5
            yr = int(str(rec[13])[:4]) if re.match(r'^\d{4}', str(rec[13] or '')) else 0
            dong = re.sub(r'\s+', ' ', (rec[4] or '').strip())
            if dong not in t['d']: t['d'].append(dong)
            nm = ' '.join(x for x in [(rec[24] or '').strip(), (rec[25] or '').strip()] if x)
            t['r'].append([cat, fl, round(h * 10), yr, t['d'].index(dong), (rec[5] or '').strip(), nm, round(float(rec[14] or 0)), flat])
            stats[cat] += 1
        r.close()
        for ext in ('.shp', '.shx', '.dbf'): os.remove(os.path.join(tmpd, base + ext))
        print(zp, base, 'done', sum(stats.values()), flush=True)

# z11 묶음(4×4 타일): 타일별 gzip 조각을 이어 붙이고 index.json에 [묶음키, 시작, 길이, 건물수] 기록
idx = {}
total = 0
bund = defaultdict(list)
for (x, y), t in tiles.items():
    s = json.dumps({'o': [round(t['o'][0], 6), round(t['o'][1], 6)], 'd': t['d'], 'r': t['r']}, ensure_ascii=False, separators=(',', ':'))
    bund[(x >> 2, y >> 2)].append((f'{x}_{y}', gzip.compress(s.encode('utf-8'), 9), len(t['r'])))
for (bx, by), items in bund.items():
    off = 0; bk = f'{bx}_{by}'
    with open(f'{OUT}/{bk}.txt', 'wb') as f:
        for k, gz, n in items:
            f.write(gz); idx[k] = [bk, off, len(gz), n]; off += len(gz)
    total += off
json.dump({'z': Z, 't': idx, 'ref': os.environ.get('BLDDATE', '')}, open(f'{OUT}/index.json', 'w'), separators=(',', ':'))
print('tiles', len(tiles), 'bundles', len(bund), 'bytes', total, 'cats', dict(stats))
