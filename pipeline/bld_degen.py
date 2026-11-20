# GIS건물통합정보에서 모양이 점처럼 작은(면적 5㎡ 미만) 자리표시 건물만 뽑는다 → 도로명주소 건물(LT_C_SPBD)로 모양 보충용
# usage: python3 bld_degen.py out.json AL_D010_*.zip
import sys, os, re, json, zipfile, shapefile
from pyproj import Transformer
out = sys.argv[1]; res = []
def area(r):
    a = 0.0
    for i in range(len(r)): a += r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1]
    return abs(a) / 2
for zp in sys.argv[2:]:
    z = zipfile.ZipFile(zp)
    for base in [n[:-4] for n in z.namelist() if n.endswith('.shp')]:
        prj = z.read(base + '.prj').decode('utf-8', 'ignore')
        epsg = re.findall(r'AUTHORITY\["EPSG","(\d+)"\]\]$', prj.strip()) or ['5186']
        T = Transformer.from_crs(int(epsg[0]), 4326, always_xy=True)
        os.makedirs('/tmp/bdx', exist_ok=True)
        for e in ('.shp', '.shx', '.dbf'): z.extract(base + e, '/tmp/bdx')
        r = shapefile.Reader('/tmp/bdx/' + base, encoding='cp949', encodingErrors='replace')
        for sr in r.iterShapeRecords():
            p = sr.shape.points
            if not p: continue
            parts = list(sr.shape.parts) + [len(p)]
            if max(area(p[parts[i]:parts[i + 1]]) for i in range(len(parts) - 1)) >= 5: continue
            rec = sr.record
            x = sum(q[0] for q in p) / len(p); y = sum(q[1] for q in p) / len(p)
            lon, lat = T.transform(x, y)
            res.append([round(lon, 6), round(lat, 6), (rec[9] or '').strip(), int(rec[26] or 0), round(float(rec[14] or 0)),
                        re.sub(r'\s+', ' ', (rec[4] or '').strip()), (rec[5] or '').strip(), ' '.join(v for v in [(rec[24] or '').strip(), (rec[25] or '').strip()] if v)])
        for e in ('.shp', '.shx', '.dbf'): os.remove('/tmp/bdx/' + base + e)
        print(zp, len(res), flush=True)
json.dump(res, open(out, 'w'), ensure_ascii=False)
