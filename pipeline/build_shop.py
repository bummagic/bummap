# 상권 레이어: 소상공인시장진흥공단 상가(상권)정보(분기) → 250m 격자 업종별 점포 수 + 상권 이름표
# 입력 raw/shop_cells.txt = PC에서 shop_extract.py로 만든 "ix\tiy\t코드:수,...\t최다 행정동명"
# 출력 data/shop.json = {o:[lat0,lon0,dlat,dlon], k:[업종코드 순서], g:[[ix,iy,T,...업종별]], L:[[이름,점포수,lat,lon,칸수]], ref}
import json, os, sys
from collections import Counter, defaultdict
L0, O0, DL, DO = 33.0, 124.5, 0.00225, 0.0028
K = ['I2', 'G2', 'S2', 'Q1', 'P1', 'R1', 'I1', 'L1', 'M1', 'N1']
cells = {}
for ln in open(sys.argv[1] if len(sys.argv) > 1 else 'raw/shop_cells.txt', encoding='utf-8'):
    ix, iy, cs, dn = ln.rstrip('\n').split('\t')
    c = Counter({a: int(b) for a, b in (x.split(':') for x in cs.split(','))})
    cells[(int(ix), int(iy))] = (c, dn)
# 생활상권 = 음식·소매·생활서비스·의료·예체능·숙박 (사무·부동산·시설관리는 제외)
LIFE = ['I2', 'G2', 'S2', 'Q1', 'R1', 'I1']
life = {k: sum(v[0][x] for x in LIFE) for k, v in cells.items()}
def comps(S):
    seen, out = set(), []
    for s0 in S:
        if s0 in seen: continue
        comp, st = [], [s0]; seen.add(s0)
        while st:
            p = st.pop(); comp.append(p)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (p[0] + dx, p[1] + dy)
                    if q in S and q not in seen: seen.add(q); st.append(q)
        out.append(comp)
    return out
L = []
def split(S, thr):
    # 너무 큰 덩어리(도심 전체가 이어진 경우)는 기준을 올려 다시 나눈다
    for comp in comps(S):
        tot = sum(life[p] for p in comp)
        if tot < 400: continue
        if len(comp) > 36 and thr < 400:
            sub = {p for p in comp if life[p] >= thr * 1.6}
            before = len(L); split(sub, thr * 1.6)
            if len(L) > before: continue
        nm = Counter()
        for p in comp: nm[cells[p][1]] += life[p]
        lat = sum((L0 + (p[1] + .5) * DL) * life[p] for p in comp) / tot
        lon = sum((O0 + (p[0] + .5) * DO) * life[p] for p in comp) / tot
        L.append([nm.most_common(1)[0][0], tot, round(lat, 5), round(lon, 5), len(comp)])
split({k for k, v in life.items() if v >= 40}, 40)
L.sort(key=lambda x: -x[1])
g = [[k[0], k[1], v[0]['T']] + [v[0][x] for x in K] for k, v in cells.items() if v[0]['T'] >= 3]
json.dump({'o': [L0, O0, DL, DO], 'k': K, 'g': g, 'L': L, 'ref': os.environ.get('SHOPDATE', '')},
          open('data/shop.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('cells', len(g), 'zones', len(L), 'size', os.path.getsize('data/shop.json'))
print(L[:15])
