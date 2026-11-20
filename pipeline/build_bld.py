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

def area(r):
    a = 0.0
    for i in range(len(r)):
        a += r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1]
    return abs(a) / 2

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

# 보충 도형(도로명주소 건물 LT_C_SPBD, 이미 그려진 건물과 겹치지 않는 것만): spbd_filter.py 결과
SP = json.load(open(os.environ['SPBD'])) if os.environ.get('SPBD') else []
SPG = defaultdict(list); SPU = set()
for i, (rg, nm, fl) in enumerate(SP):
    xs = [c[0] for c in rg]; ys = [c[1] for c in rg]
    SP[i].append((min(xs), min(ys), max(xs), max(ys)))
    for gy in range(int(min(ys) / .001), int(max(ys) / .001) + 1):
        for gx in range(int(min(xs) / .001), int(max(xs) / .001) + 1): SPG[(gy, gx)].append(i)
def inpoly(x, y, r):
    c = False
    for i in range(len(r)):
        (x1, y1), (x2, y2) = r[i - 1], r[i]
        if (y2 > y) != (y1 > y) and x < (x1 - x2) * (y - y2) / (y1 - y2) + x2: c = not c
    return c
def sp_find(lon, lat):
    cand = set()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): cand.update(SPG.get((int(lat / .001) + dy, int(lon / .001) + dx), []))
    best = None; bd = 3e-4   # 약 30m 안
    for i in cand:
        if i in SPU: continue
        rg = SP[i][0]; b = SP[i][3]
        if inpoly(lon, lat, rg): best = i; break
        d = max(b[0] - lon, lon - b[2], b[1] - lat, lat - b[3], 0)
        if d < bd: best, bd = i, d
    if best is not None: SPU.add(best)
    return best

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
            # 여러 조각(멀티파트·구멍)이 있으면 면적이 가장 큰 링을 건물 외곽으로 쓴다
            # (예전엔 첫 조각만 써서, 첫 조각이 작은 건물이 점처럼 찌그러졌음)
            rings = [shp.points[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
            ring = max(rings, key=area)
            if ring and ring[0] == ring[-1]: ring = ring[:-1]
            if len(ring) > 4:
                m = len(ring) // 2
                sr2 = dp(ring[:m + 1], 0.6)[:-1] + dp(ring[m:] + [ring[0]], 0.6)[:-1]
                if area(sr2) >= 0.8 * area(ring): ring = sr2   # 단순화로 모양이 망가지면 원본 유지
            if len(ring) < 3 or area(ring) < 5:
                # 원본에 모양 없이 점(면적 5㎡ 미만)으로만 있는 건물: 용도가 있으면 같은 자리 도로명주소 건물 도형으로 채움
                if not SP or not (rec[9] or '').strip() or not ring: continue
                px = sum(q[0] for q in ring) / len(ring); py = sum(q[1] for q in ring) / len(ring)
                plon, plat = T.transform(px, py)
                hit = sp_find(plon, plat)
                if hit is None: continue
                stats['spbd'] += 1
                lons, lats = zip(*SP[hit][0]); fill = 1
            else:
                fill = 0
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
            t['r'].append([cat, fl, round(h * 10), yr, t['d'].index(dong), (rec[5] or '').strip(), nm, round(float(rec[14] or 0)), flat] + ([1] if fill else []))
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
