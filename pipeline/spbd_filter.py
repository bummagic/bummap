# 도로명주소 건물 도형(LT_C_SPBD) 중, GIS건물통합정보에 이미 제대로 그려진 건물과 겹치는 것을 빼고 남긴다.
# usage: python3 spbd_filter.py spbd_raw.json spbd_ok.json AL_D010_*.zip
#  spbd_raw.json: {id: [[[lon,lat],...], 건물명, 지상층수]}  (브이월드 data API로 받은 것)
#  겹침 판정: GIS 건물(면적 5㎡ 이상) 중심이 도형 안에 있거나, 도형 중심이 GIS 건물 안에 있으면 제외
import sys, os, re, json, zipfile, shapefile
from pyproj import Transformer
from collections import defaultdict
raw = json.load(open(sys.argv[1])); OUT = sys.argv[2]
items = [v for v in raw.values() if len(v[0]) >= 4]
def area(r):
    a = 0.0
    for i in range(len(r)): a += r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1]
    return abs(a) / 2
def inpoly(x, y, r):
    c = False
    for i in range(len(r)):
        (x1, y1), (x2, y2) = r[i - 1], r[i]
        if (y2 > y) != (y1 > y) and x < (x1 - x2) * (y - y2) / (y1 - y2) + x2: c = not c
    return c
bad = set(); prepared = {}
for zp in sys.argv[3:]:
    z = zipfile.ZipFile(zp)
    for base in [n[:-4] for n in z.namelist() if n.endswith('.shp')]:
        prj = z.read(base + '.prj').decode('utf-8', 'ignore')
        epsg = int((re.findall(r'AUTHORITY\["EPSG","(\d+)"\]\]$', prj.strip()) or ['5186'])[0])
        if epsg not in prepared:   # SPBD를 이 좌표계로 바꾸고 100m 칸 색인
            T = Transformer.from_crs(4326, epsg, always_xy=True)
            P = []; G = defaultdict(list)
            for i, it in enumerate(items):
                xs, ys = T.transform([c[0] for c in it[0]], [c[1] for c in it[0]])
                rg = list(zip(xs, ys)); b = (min(xs), min(ys), max(xs), max(ys))
                cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
                P.append((rg, b, cx, cy))
                for gy in range(int(b[1] // 100), int(b[3] // 100) + 1):
                    for gx in range(int(b[0] // 100), int(b[2] // 100) + 1): G[(gy, gx)].append(i)
            C = defaultdict(list)
            for i, p in enumerate(P): C[(int(p[3] // 100), int(p[2] // 100))].append(i)
            prepared[epsg] = (P, G, C)
        P, G, C = prepared[epsg]
        os.makedirs('/tmp/sfx', exist_ok=True)
        for e in ('.shp', '.shx', '.dbf'): z.extract(base + e, '/tmp/sfx')
        r = shapefile.Reader('/tmp/sfx/' + base)
        for sh in r.iterShapes():
            p = sh.points
            if not p: continue
            parts = list(sh.parts) + [len(p)]
            ring = max((p[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)), key=area)
            if area(ring) < 5: continue
            gx = sum(q[0] for q in ring) / len(ring); gy = sum(q[1] for q in ring) / len(ring)
            for i in G.get((int(gy // 100), int(gx // 100)), []):     # GIS 건물 중심이 SPBD 안
                if i in bad: continue
                b = P[i][1]
                if b[0] <= gx <= b[2] and b[1] <= gy <= b[3] and inpoly(gx, gy, P[i][0]): bad.add(i)
            xs = [q[0] for q in ring]; ys = [q[1] for q in ring]
            for cy in range(int(min(ys) // 100), int(max(ys) // 100) + 1):    # SPBD 중심이 GIS 건물 안
                for cx in range(int(min(xs) // 100), int(max(xs) // 100) + 1):
                    for i in C.get((cy, cx), []):
                        if i not in bad and inpoly(P[i][2], P[i][3], ring): bad.add(i)
        for e in ('.shp', '.shx', '.dbf'): os.remove('/tmp/sfx/' + base + e)
        print(zp, 'bad', len(bad), flush=True)
ok = [items[i] for i in range(len(items)) if i not in bad]
json.dump(ok, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print('spbd', len(items), 'overlap', len(bad), 'kept', len(ok))
