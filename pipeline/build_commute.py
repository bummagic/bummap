# 역 연결망으로 주요 업무지구(강남·여의도·광화문·판교)까지 지하철 소요 시간(분)을 추정한다.
# usage: python3 build_commute.py data/rail.json data/stations.json data/commute.json
# 운행 중인 전철·도시철도·GTX·일반철도(KTX 제외) 선형 위를 따라 이동: 노선별 표정속도(GTX 75, 공항철도·경강·서해·경춘 48, 신분당 45, 1호선·경의중앙·경원 40, 그 밖 32km/h),
# 환승 5분, 처음 기다림 4분. 역은 그 노선 선형에서 300m 안 가장 가까운 꼭짓점에 붙인다. 결과는 추정값(실제 시간표·급행 반영 안 됨).
import json, sys, math, heapq, collections
rail = json.load(open(sys.argv[1])); sts = json.load(open(sys.argv[2])); OUT = sys.argv[3]
DEST = [('강남', 127.0276, 37.498), ('여의도', 126.9243, 37.5217), ('광화문', 126.9769, 37.5716), ('판교', 127.1112, 37.3947)]
def km(a, b): return math.hypot((a[0]-b[0])*88.8, (a[1]-b[1])*111.2)
def speed(n):
    if n.startswith('GTX'): return 75
    if '신분당' in n: return 45
    if '공항' in n or '경강' in n or '서해' in n or '경춘' in n: return 48
    if '1호선' in n or '경의' in n or '중앙' in n or '경원' in n or '경부' in n: return 40
    return 32
G = collections.defaultdict(list)
def edge(a, b, w): G[a].append((b, w)); G[b].append((a, w))
def proj(p, a, b):
    ax, ay = a[0]*88.8, a[1]*111.2; bx, by_ = b[0]*88.8, b[1]*111.2; px, py = p[0]*88.8, p[1]*111.2
    dx, dy = bx-ax, by_-ay; L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return t, math.hypot(ax+t*dx-px, ay+t*dy-py)
SN = {}
# 같은 이름 노선(예: 서해선 일반철도·전철 두 줄)은 역 목록을 함께 씀
SAME = collections.defaultdict(set)
for i, r in enumerate(rail): SAME[r['n']].add(i)
for st in sts:
    if len(st) > 4: st[4] = sorted(set(st[4]) | {j for i in st[4] if i < len(rail) for j in SAME[rail[i]['n']]})
for i, r in enumerate(rail):
    if r['k'] not in ('m', 'rail') or r['s'] != 'open' or 'KTX' in r['n']: continue
    sp = speed(r['n']); segs = []
    for part in r['l']:
        for a, b in zip(part, part[1:]): segs.append((a, b))
    # 이 노선이 지나는 역: 선분 위 가장 가까운 점(300m 안)
    cut = collections.defaultdict(list)
    for s_, st in enumerate(sts):
        if i not in (st[4] if len(st) > 4 else []): continue
        best = None
        for k, (a, b) in enumerate(segs):
            if min(a[0], b[0]) - .01 > st[1] or max(a[0], b[0]) + .01 < st[1]: continue
            if min(a[1], b[1]) - .01 > st[2] or max(a[1], b[1]) + .01 < st[2]: continue
            t, d = proj(st[1:3], a, b)
            if best is None or d < best[0]: best = (d, k, t)
        if best and best[0] <= .3: cut[best[1]].append((best[2], s_)); SN[(s_, i)] = 1
    ends = []
    for k, (a, b) in enumerate(segs):
        A = (i, round(a[0], 5), round(a[1], 5)); B = (i, round(b[0], 5), round(b[1], 5)); ends += [A, B]
        L = km(a, b); pts = [(0, A)] + [(t, ('s', s_, i)) for t, s_ in sorted(cut.get(k, []))] + [(1, B)]
        for (t1, n1), (t2, n2) in zip(pts, pts[1:]):
            if n1 != n2: edge(n1, n2, (t2-t1) * L / sp * 60)
    es = list(set(ends)); gg = collections.defaultdict(list)
    for e in es: gg[(int(e[1]/.001), int(e[2]/.001))].append(e)
    for e in es:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for f in gg.get((int(e[1]/.001)+dx, int(e[2]/.001)+dy), []):
                    if e < f and km(e[1:], f[1:]) < .03: edge(e, f, 0)
by = collections.defaultdict(list)
for (s, i) in SN: by[s].append(i)
for s, ls in by.items():
    for a in ls:
        for b in ls:
            if a < b: edge(('s', s, a), ('s', s, b), 5)
# 이름이 같고 500m 안인 역끼리, 또는 150m 안 역끼리 환승
keys = list(by)
for x in range(len(keys)):
    for y in range(x+1, len(keys)):
        a, b = keys[x], keys[y]; d = km(sts[a][1:3], sts[b][1:3])
        if (sts[a][0] == sts[b][0] and d < .5) or d < .15:
            for la in by[a]:
                for lb in by[b]: edge(('s', a, la), ('s', b, lb), 5 + d * 15)
def dij(srcs):
    D = {}; h = [(0, k, n) for k, n in enumerate(srcs)]; cnt = len(h)
    for c, k, n in h: D[n] = 0
    heapq.heapify(h)
    while h:
        c, _, n = heapq.heappop(h)
        if c > D.get(n, 1e9) or c > 150: continue
        for m, w in G[n]:
            nc = c + w
            if nc < D.get(m, 1e9): D[m] = nc; cnt += 1; heapq.heappush(h, (nc, cnt, m))
    return D
res = [[-1]*len(DEST) for _ in sts]
for j, (nm, lo, la) in enumerate(DEST):
    ds = min((s for s in by if sts[s][0] == nm), key=lambda s: km((lo, la), sts[s][1:3]))
    D = dij([('s', ds, i) for i in by[ds]])
    for s, ls in by.items():
        t = min(D.get(('s', s, i), 1e9) for i in ls)
        if t < 150: res[s][j] = round(t + (4 if s != ds else 0))
json.dump({'d': [d[0] for d in DEST], 'note': '운행 중 전철·도시철도·GTX 선형 기준 추정(표정속도·환승 5분·첫 대기 4분)', 't': res}, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
ok = sum(1 for r in res if r[0] >= 0); print('stations', len(sts), 'reach 강남', ok)
for n in ['잠실', '노원', '일산', '수원', '동탄', '인천', '판교', '광교중앙', '사당', '김포공항', '정자']:
    for s, st in enumerate(sts):
        if st[0] == n and 37 < st[2] < 38: print(n, res[s])
