# 아파트 실거래가(매매·전월세) → 단지별 요약 data/apt.json
# usage: APTDATE=2026-11-20 python3 build_apt.py rt_raw.json.gz bld_addr.json sgg_codes.json geo_extra.json out.json [unmatched.json]
#  rt_raw: {"T":[[aptSeq,aptNm,sggCd,umdNm,jibun,roadNm,buildYear,ymd,price만원,area,floor]],
#           "R":[[aptSeq,aptNm,sggCd,umdNm,jibun,buildYear,ymd,deposit만원,monthly만원,area,floor]], "M":[YYYYMM...]}
#  bld_addr: build_bld_addr.py 결과("시도|시군구|동리|지번" → [lon,lat])
#  geo_extra: 브이월드 지오코더로 찾은 {"주소키":[lon,lat]} (건물자료가 없는 경기 등)
import sys, json, gzip, os, re, statistics as st, collections
raw = json.load(gzip.open(sys.argv[1], 'rt'))
A = json.load(open(sys.argv[2])); SG = json.load(open(sys.argv[3]))
GX = json.load(open(sys.argv[4])) if os.path.exists(sys.argv[4]) else {}
OUT = sys.argv[5]; UNM = sys.argv[6] if len(sys.argv) > 6 else None
OLD = {'28110': '중구', '28140': '동구', '28260': '서구', '41590': '화성시'}
SDN = {'11': '서울특별시', '28': '인천광역시', '30': '대전광역시', '36': '세종특별자치시', '41': '경기도', '43': '충청북도', '44': '충청남도', '52': '전북특별자치도'}
# 지번 사전 보조: 시도|동리|지번 (시군구 이름이 바뀐 곳용, 시도 안에서 유일할 때만)
A2 = collections.defaultdict(list)
for k, v in A.items():
    sd, sg, dn, jb = k.split('|'); A2[sd + '|' + dn + '|' + jb].append(v)
M = sorted(raw['M']); last = M[-1]
def mago(n):  # last 기준 n개월 전 YYYYMM
    y, m = int(last[:4]), int(last[4:]); m -= n
    while m <= 0: m += 12; y -= 1
    return y * 100 + m
M6, M3, M12 = mago(5), mago(2), mago(11)
def keyof(r_sgg, umd, jb, name):
    return r_sgg + '|' + umd + '|' + jb + '|' + name
C = {}
def get(seq, name, sgg, umd, jb, by):
    k = seq or keyof(sgg, umd, jb, name)
    if k not in C: C[k] = {'n': name, 's': sgg, 'u': umd, 'j': jb, 'y': by, 'T': [], 'R': []}
    c = C[k]
    if not c['j'] and jb: c['j'] = jb
    if not c['y'] and by: c['y'] = by
    return c
for r in raw['T']:
    seq, nm, sgg, umd, jb, road, by, ymd, pr, ar, fl = r
    if not pr or not ar: continue
    get(seq, nm, sgg, umd, jb, by)['T'].append((ymd, pr, ar, fl))
for r in raw['R']:
    seq, nm, sgg, umd, jb, by, ymd, dep, mon, ar, fl = r
    if not ar: continue
    get(seq, nm, sgg, umd, jb, by)['R'].append((ymd, dep, mon, ar, fl))
PY = 3.305785
def loc(c):
    sd = c['s'][:2]; sgn = re.sub(r'\s', '', SG.get(c['s']) or OLD.get(c['s'], ''))
    umd = c['u'].split()[-1] if c['u'] else ''; jb = c['j']
    if sd == '36': sgn = '-'
    for j in ([jb, jb.split('-')[0]] if jb else []):
        v = A.get(f'{sd}|{sgn}|{umd}|{j}')
        if v: return v, 'b'
        L = A2.get(f'{sd}|{umd}|{j}')
        if L and len(L) == 1: return L[0], 'b'
    v = GX.get(gkey(c))
    if v: return v, 'g'
    return None, None
def gkey(c):
    sgn = SG.get(c['s']) or OLD.get(c['s'], '')
    if c['s'][:2] == '36': sgn = ''
    return ' '.join(x for x in [SDN[c['s'][:2]], sgn, c['u'], c['j']] if x)
def med(a): return st.median(a) if a else None
out = []; unm = {}; nb = ng = 0
for k, c in C.items():
    if not c['j']: continue
    p, how = loc(c)
    if not p:
        unm[gkey(c)] = 1; continue
    nb += how == 'b'; ng += how == 'g'
    T = c['T']; R = c['R']
    T12 = [t for t in T if t[0] // 100 >= M12]; T6 = [t for t in T12 if t[0] // 100 >= M6]
    pp = lambda ts: [t[1] / (t[2] / PY) for t in ts]
    ppy = med(pp(T6)) or med(pp(T12))
    rec = med(pp([t for t in T12 if t[0] // 100 >= M3])); old = med(pp([t for t in T12 if t[0] // 100 < M6]))
    g = round((rec / old - 1) * 100, 1) if rec and old and len([1 for t in T12 if t[0] // 100 >= M3]) >= 2 else None
    J = [x for x in R if x[2] == 0 and x[0] // 100 >= M12]          # 전세(월세 0)
    W = [x for x in R if x[2] > 0 and x[0] // 100 >= M12]           # 월세
    ty = collections.defaultdict(lambda: {'t': [], 'j': [], 'w': []})
    for t in T12: ty[round(t[2])]['t'].append(t)
    for x in J: ty[round(x[3])]['j'].append(x)
    for x in W: ty[round(x[3])]['w'].append(x)
    types = []; rs = []; ws = 0
    for a in sorted(ty):
        d = ty[a]; lt = max(d['t']) if d['t'] else None
        mt = med([t[1] for t in d['t']]); mj = med([x[1] for x in d['j']])
        lw = max(d['w']) if d['w'] else None
        if mt and mj:
            w = min(len(d['t']), len(d['j'])); rs.append(mj / mt * w); ws += w
        types.append([a, lt[1] if lt else 0, lt[0] if lt else 0, lt[3] if lt else 0, round(mj) if mj else 0, len(d['j']), len(d['t']),
                      lw[1] if lw else 0, lw[2] if lw else 0])
    jr = round(sum(rs) / ws * 100) if ws else None
    lastd = max([t[0] for t in T12] + [x[0] for x in R if x[0] // 100 >= M12] or [0])
    if not lastd: continue
    out.append([c['n'], round(p[0], 5), round(p[1], 5), int(c['y'] or 0), c['s'], (c['u'] + ' ' + c['j']).strip(),
                round(ppy) if ppy else 0, len(T12), jr if jr is not None else -1, g if g is not None else -999, len(J), len(W), types])
json.dump({'ref': os.environ.get('APTDATE', ''), 'from': str(M12), 'to': last, 'a': out}, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print('complexes', len(C), 'out', len(out), 'bld', nb, 'geo', ng, 'unmatched', len(unm))
if UNM: json.dump(sorted(unm), open(UNM, 'w'), ensure_ascii=False)
