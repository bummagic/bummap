# 공사·계획 철도역(호재 역) → data/future.json
# usage: FUTDATE=YYYY-MM-DD python3 build_future.py data/rail.json future_st_osm.json data/future.json kr-rail-map/data
#  future_st_osm.json: OSM Overpass로 받은 공사·계획 역 [[이름, 위도, 경도, 'c'|'p'], ...]
#   (railway=construction+construction=station, construction:railway=station, railway=proposed+proposed=station,
#    proposed:railway=station, railway=station+construction=*, public_transport=station+construction=yes)
#  + kr-rail-map 역 중 공사·계획·제안 노선에만 속한 역(이름 있음, GTX 등)
# 출력 s: [이름, 위도, 경도, 노선번호(rail.json 순번, 없으면 -1), 'c'공사|'p'계획(제안 포함), 'krm'|'osm', 새 노선 이름, 기존 운행역이면 1]
import sys, json, math, os
rail = json.load(open(sys.argv[1])); osm = json.load(open(sys.argv[2])); OUT = sys.argv[3]
def dseg(p, a, b):  # 점-선분 거리(m), 위도 37° 근사
    kx, ky = 88800 * math.cos(math.radians(p[1])) / math.cos(math.radians(37)), 111000
    px, py = p[0] * kx, p[1] * ky; ax, ay = a[0] * kx, a[1] * ky; bx, by = b[0] * kx, b[1] * ky
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)
fut = [(i, r) for i, r in enumerate(rail) if r['s'] != 'open']
out = []
KD = sys.argv[4]
KL = {f['properties']['id']: f['properties'] for f in json.load(open(KD + '/lines.geojson'))['features']}
byname = {r['n']: i for i, r in enumerate(rail)}
for f in json.load(open(KD + '/stations.geojson'))['features']:
    p = f['properties']; ls = [KL[l] for l in (p.get('lines') or [p.get('line_id')]) if l in KL]
    fl = [l for l in ls if l.get('status') != 'open']        # 새로 들어올(공사·계획·제안) 노선이 하나라도 있는 역
    if not fl: continue
    lon, lat = f['geometry']['coordinates'][:2]
    li = next((byname[l['name_ko']] for l in fl if l['name_ko'] in byname), -1)
    st = 'c' if any(l.get('status') == 'construction' for l in fl) else 'p'
    out.append([p['name_ko'], round(lat, 5), round(lon, 5), li, st, 'krm', ', '.join(dict.fromkeys(l['name_ko'] for l in fl)),
                1 if any(l.get('status') == 'open' for l in ls) else 0])
for nm, lat, lon, st in osm:
    best, bd = -1, 400
    for i, r in fut:
        for line in r['l']:
            for a, b in zip(line, line[1:]):
                d = dseg((lon, lat), a, b)
                if d < bd: best, bd = i, d
    s = ('p' if rail[best]['s'] == 'planned' else 'c') if best >= 0 else st
    if any(math.hypot((o[2] - lon) * 88800, (o[1] - lat) * 111000) < 250 for o in out): continue
    out.append([nm.removesuffix('역'), lat, lon, best, s, 'osm', rail[best]['n'] if best >= 0 else '', 0])
json.dump({'ref': os.environ.get('FUTDATE', ''), 's': out}, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print('krm', sum(1 for o in out if o[5] == 'krm'), 'osm', sum(1 for o in out if o[5] == 'osm'), 'no line', sum(1 for o in out if o[3] < 0))
