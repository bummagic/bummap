# 공사·계획 철도역(호재 역) → data/future.json
# usage: FUTDATE=YYYY-MM-DD python3 build_future.py data/rail.json future_st_osm.json data/future.json kr-rail-map/data
#  future_st_osm.json: OSM Overpass로 받은 공사·계획 역 [[이름, 위도, 경도, 'c'|'p'], ...]
#   (railway=construction+construction=station, construction:railway=station, railway=proposed+proposed=station,
#    proposed:railway=station, railway=station+construction=*, public_transport=station+construction=yes)
#  + kr-rail-map 역 중 공사·계획·제안 노선에만 속한 역(이름 있음, GTX 등)
# 출력 s(뒤에 [개통 목표 연도, 노선 무게, 근거] 붙음): [이름, 위도, 경도, 노선번호(rail.json 순번, 없으면 -1), 'c'공사|'p'계획(제안 포함), 'krm'|'osm', 새 노선 이름, 기존 운행역이면 1]
import sys, json, math, os
rail = json.load(open(sys.argv[1])); osm = json.load(open(sys.argv[2])); OUT = sys.argv[3]
def dseg(p, a, b):  # 점-선분 거리(m), 위도 37° 근사
    kx, ky = 88800 * math.cos(math.radians(p[1])) / math.cos(math.radians(37)), 111000
    px, py = p[0] * kx, p[1] * ky; ax, ay = a[0] * kx, a[1] * ky; bx, by = b[0] * kx, b[1] * ky
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

# 노선별 개통 목표 연도(가장 이른 단계 기준, 0 = 미정·구상 단계)와 근거. 2026-11-22 보도 기준으로 확인.
YR = {
 'GTX-A 서울역~수서': (2027, '2027년 상반기(삼성역 무정차) — SBS 2026-11-03'),
 'GTX-A 창릉 정차': (0, '창릉역 개통 시기 미확정'),
 'GTX-A 평택 연장': (0, '설계 중, 개통 미정'),
 'GTX-B': (2031, '2031년 목표'), 'GTX-C': (2031, '2031년 목표(2026.9 본공사 착공, 국토부 2026-09-14)'),
 'GTX-C 상록수 갈래': (2031, 'GTX-C 본선과 같이 2031년 목표'),
 'GTX-D': (2035, '정부 구상, 1단계 2035년 목표'), 'GTX-E': (2035, '정부 구상, 2035년 목표'), 'GTX-F': (2035, '정부 구상, 1단계 2035년 목표'),
 'GTX-G': (0, '지자체 제안 단계'), 'GTX-H': (0, '지자체 제안 단계'),
 '동북선': (2027, '2027년 11월 목표 — 대광위·헤럴드경제(2026.9 공정률 76.4%)'),
 '신안산선': (2028, '2028년 하반기 전 구간(광명 붕괴사고 후 연기) — 세계일보 2026-04'),
 '월곶판교선': (2029, '2029년 말 목표'), '동탄인덕원선': (2029, '2029년 목표'),
 '9호선 4단계': (2028, '2028년 예정'),
 '7호선 청라 연장': (2031, '2031년 상반기로 미뤄질 전망 — 경기일보 2026-07-02'),
 '7호선 도봉산옥정선': (2027, '2027년 말'), '옥정포천선': (2030, '2030년 목표'),
 '신분당선 광교-호매실': (2029, '2029년 12월 목표'), '신분당선 용산-신사 연장': (0, '2027년 상반기 착공 목표, 개통 미정'),
 '대장홍대선': (2031, '2031년 목표'), '3호선 하남연장(송파하남선)': (2032, '2032년 개통 목표'),
 '강동하남남양주선': (0, '2027년 착공 목표, 개통 미정'), '동부선': (0, '구상 단계'),
 '광주 도시철도 2호선': (2028, '1단계 2028년 12월'), '대구산업선': (2030, '2030년 12월 목표'),
 '대전 도시철도 2호선': (2030, '2030년 하반기(대전시 2026-06-23)'),
 '부산 2호선 양산중앙 연장': (2026, '2026년 12월 예정'), '양산선': (2026, '2026년 12월 예정'),
}
def kind(n):  # 노선 무게: 광역급행(GTX) 1, 경전철 0.5, 그 밖 0.7
    return 1.0 if n.startswith('GTX') else 0.5 if n in ('동북선', '동부선') else 0.7
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
# 역마다 [8] 가장 이른 개통 목표 연도(0 미정) [9] 노선 무게(가장 큰 것) [10] 근거 문구 [11] 가장 이른 노선 이름
for o in out:
    names = [n.strip() for n in (o[6] or '').split(',') if n.strip()] or ([rail[o[3]]['n']] if o[3] >= 0 else [])
    ys = [YR[n][0] for n in names if n in YR and YR[n][0]]
    ys2 = sorted((YR[n][0], n) for n in names if n in YR and YR[n][0])
    o += [ys2[0][0] if ys2 else 0, max([kind(n) for n in names] or [0.7]), ' / '.join(f"{n}: {YR[n][1]}" for n in names if n in YR), ys2[0][1] if ys2 else (names[0] if names else '')]
json.dump({'ref': os.environ.get('FUTDATE', ''), 's': out}, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print('krm', sum(1 for o in out if o[5] == 'krm'), 'osm', sum(1 for o in out if o[5] == 'osm'), 'no line', sum(1 for o in out if o[3] < 0))
