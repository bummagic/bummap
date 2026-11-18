# 학원가 레이어: raw/hagwon_kr.txt (상가(상권)정보에서 학원 업종만 추린 것: 이름\t분류\t위도e5\t경도e5\t건물명)
# 분류: a 입시·교과, f 외국어, p 예체능(음악·미술·태권도·무용 등), c 컴퓨터·자격
# 출력: data/hagwon_grid.json (250m 격자 밀도 + 학원가 이름표), data/hagwon_pts.json (개별 학원, 확대 시에만 불러옴)
import json, os, sys, re
from collections import defaultdict

REF = os.environ.get('HAGDATE', '2026-09')
LAT0, LON0, DLAT, DLON = 33.0, 124.5, 0.00225, 0.0028  # 약 250m 격자

rows = []
for ln in open('raw/hagwon_kr.txt', encoding='utf-8'):
    p = ln.rstrip('\n').split('\t')
    if len(p) < 4: continue
    rows.append([p[0], p[1], int(p[2]), int(p[3]), p[4] if len(p) > 4 else '', p[5] if len(p) > 5 else ''])

cell = defaultdict(lambda: [0, 0, 0, 0])  # a f p c
K = {'a': 0, 'f': 1, 'p': 2, 'c': 3}
for n, k, la, lo, b, dn in rows:
    iy = int((la / 1e5 - LAT0) / DLAT); ix = int((lo / 1e5 - LON0) / DLON)
    cell[(ix, iy)][K[k]] += 1

# 학원가 묶음: 입시·교과+외국어 15곳 이상 칸을 이웃끼리 묶고, 합계 60곳 이상이면 이름표
core = {c for c, v in cell.items() if v[0] + v[1] >= 10}
seen, clusters = set(), []
for c in core:
    if c in seen: continue
    st, comp = [c], []
    seen.add(c)
    while st:
        x = st.pop(); comp.append(x)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                y = (x[0] + dx, x[1] + dy)
                if y in core and y not in seen: seen.add(y); st.append(y)
    tot = sum(cell[x][0] + cell[x][1] for x in comp)
    if tot >= 40: clusters.append((tot, comp))

# 이름표: 묶음 안 입시·교과·외국어 학원의 행정동명(상가정보, 현행) 중 가장 많은 것
from collections import Counter
cdong = defaultdict(Counter)
for n, k, la, lo, b, dn in rows:
    if k in 'af':
        cdong[(int((lo / 1e5 - LON0) / DLON), int((la / 1e5 - LAT0) / DLAT))][dn] += 1
labels = []
for tot, comp in sorted(clusters, reverse=True):
    cnt = Counter()
    for x in comp: cnt.update(cdong[x])
    nm = cnt.most_common(1)[0][0] if cnt else ''
    nm = re.sub(r'(제?[0-9·.,]*(동|가))$', '', nm) or nm
    nm = (re.sub(r'(읍|면)$', '', nm) or nm).replace('.', '·')
    if len(nm) > 2 and nm.endswith('본'): nm = nm[:-1]
    if len(nm) == 1: nm += '동'
    best = max(comp, key=lambda x: cell[x][0] + cell[x][1])
    lon = LON0 + (best[0] + .5) * DLON; lat = LAT0 + (best[1] + .5) * DLAT
    dup = next((l for l in labels if l[0] == nm + ' 학원가' and abs(l[2] - lat) + abs(l[3] - lon) < 0.03), None)
    if dup: dup[1] += tot; dup[4] += len(comp); continue
    labels.append([nm + ' 학원가', tot, round(lat, 5), round(lon, 5), len(comp)])
labels.sort(key=lambda l: -l[1])

grid = [[ix, iy] + v for (ix, iy), v in cell.items()]
json.dump({'o': [LAT0, LON0, DLAT, DLON], 'g': grid, 'L': labels, 'ref': REF, 'n': len(rows)},
          open('data/hagwon_grid.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump([[n, k, la, lo, b] for n, k, la, lo, b, dn in rows], open('data/hagwon_pts.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('rows', len(rows), 'cells', len(grid), 'clusters', len(labels))
for l in labels[:25]: print(l)
