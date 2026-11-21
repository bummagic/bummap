# 학원 학년 구분(이름 기준) + 학원가별 집계를 hagwon_grid.json에 덧붙인다.
# usage: python3 hagwon_lv.py data/hagwon_grid.json data/hagwon_pts.json   (build_hagwon.py 끝에서도 자동 실행)
# 원본(상가(상권)정보)과 NEIS 학원교습소정보 모두 '대상 학년' 항목이 없다. 그래서 입시·교과·외국어 학원 이름에
# 아래 낱말이 들어 있을 때만 학년을 붙이고(한 학원이 여러 학년에 들 수 있음), 나머지는 '이름에 학년 표시 없음'으로 센다.
#   초등: 초등·초중·키즈·주니어 / 중등: 중등·중학·초중·중고 / 고등: 고등·고교·중고·입시·수능·재수·대입·기숙
# 결과: g 칸 = [ix,iy,a,f,p,c, 초등,중등,고등,(a+f 중 학년 표시 없음)]
#       L 학원가 = [이름,입시·교과+외국어 합계,위도,경도,칸 수, a,f,p,c, 초등,중등,고등,표시 없음]
import json, re, sys
from collections import defaultdict
LV = [r'초등|초중|키즈|주니어', r'중등|중학|초중|중고', r'고등|고교|중고|입시|수능|재수|대입|기숙']

def lv(name):
    return [1 if re.search(r, name) else 0 for r in LV]

def augment(gpath, ppath):
    G = json.load(open(gpath)); P = json.load(open(ppath))
    LAT0, LON0, DLAT, DLON = G['o']
    ex = defaultdict(lambda: [0, 0, 0, 0])
    for n, k, la, lo, b in P:
        if k not in 'af': continue
        v = lv(n); c = (int((lo / 1e5 - LON0) / DLON), int((la / 1e5 - LAT0) / DLAT))
        e = ex[c]
        for i in range(3): e[i] += v[i]
        if not any(v): e[3] += 1
    cell = {}
    for r in G['g']:
        r[:] = r[:6] + ex.get((r[0], r[1]), [0, 0, 0, 0]); cell[(r[0], r[1])] = r
    # 학원가 묶음(build_hagwon.py와 같은 규칙): 입시·교과+외국어 10곳 이상 칸을 이웃끼리 묶고 합계 40곳 이상
    core = {c for c, r in cell.items() if r[2] + r[3] >= 10}
    seen, comps = set(), []
    for c in core:
        if c in seen: continue
        st, comp = [c], []; seen.add(c)
        while st:
            x = st.pop(); comp.append(x)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    y = (x[0] + dx, x[1] + dy)
                    if y in core and y not in seen: seen.add(y); st.append(y)
        tot = sum(cell[x][2] + cell[x][3] for x in comp)
        if tot >= 40: comps.append((tot, set(comp)))
    sums = lambda cs: [sum(cell[x][i] for x in cs) for i in (2, 3, 4, 5, 6, 7, 8, 9)]
    L = G['L']; got = [[] for _ in L]; used = set()
    for i, l in enumerate(L):  # 이름표 자리 칸이 든 묶음
        c = (int((l[3] - LON0) / DLON), int((l[2] - LAT0) / DLAT))
        for j, (t, cs) in enumerate(comps):
            if j not in used and c in cs: got[i].append(j); used.add(j); break
    for j, (t, cs) in enumerate(comps):  # 같은 이름으로 합쳐진 묶음: 남은 합계가 맞고 가까운 이름표
        if j in used: continue
        cx = sum(x[0] for x in cs) / len(cs) * DLON + LON0; cy = sum(x[1] for x in cs) / len(cs) * DLAT + LAT0
        for i, l in enumerate(L):
            if l[1] - sum(comps[k][0] for k in got[i]) >= t and abs(l[2] - cy) + abs(l[3] - cx) < 0.04:
                got[i].append(j); used.add(j); break
    bad = 0
    for i, l in enumerate(L):
        cs = set().union(*[comps[j][1] for j in got[i]]) if got[i] else set()
        s = sums(cs)
        if s[0] + s[1] != l[1]: bad += 1
        l[:] = l[:5] + s
    json.dump(G, open(gpath, 'w'), ensure_ascii=False, separators=(',', ':'))
    e = sum(r[6] for r in G['g']); m = sum(r[7] for r in G['g']); h = sum(r[8] for r in G['g']); u = sum(r[9] for r in G['g'])
    print(f'학년(이름 기준) 초등 {e} 중등 {m} 고등 {h} 표시 없음 {u} · 학원가 {len(L)}곳 중 합계 불일치 {bad}')
    for l in L[:5]: print(l)

if __name__ == '__main__':
    augment(sys.argv[1] if len(sys.argv) > 1 else 'data/hagwon_grid.json', sys.argv[2] if len(sys.argv) > 2 else 'data/hagwon_pts.json')
