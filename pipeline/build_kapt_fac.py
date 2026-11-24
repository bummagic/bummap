# K-apt 부대복리시설(커뮤니티)·전기차 충전기 → data/kapt_fac.json
# GitHub Actions(.github/workflows/kapt-fac.yml)에서 매일 돌린다. 키: 저장소 Secret DATA_GO_KR_KEY
#  - 공공데이터포털 활용신청 2개 필요: 단지목록 15057332(AptListService3), 기본·상세 15058453(AptBasisInfoServiceV4)
#  - 하루 호출 한도(개발계정 API별 1만 건)에 걸리면 멈추고 저장 → 다음 날 이어서(캐시에 있는 단지는 다시 안 부름)
# 매칭: apt.json 의 "시군구코드|동 지번" 키(data/kapt.json 과 같은 키)에 K-apt 기본정보 지번주소(kaptAddr)를 잇는다.
#       같은 동·본번에 하나뿐이면 본번만으로, 그래도 안 되면 같은 동 안에서 단지 이름이 가장 비슷한 것.
# 출력: {ref, src, t:[시설 이름], k:{키:[시설 비트, 전기차충전기 수]}}
import gzip, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date

KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'pipeline', 'kapt_fac_cache.json.gz')
OUT = os.path.join(ROOT, 'data', 'kapt_fac.json')
BASE = 'https://apis.data.go.kr/1613000'
MAXCALL = int(os.environ.get('KAPT_MAXCALL', '19000'))
TODAY = date.today().isoformat()

# 시설 이름표(앞 9개는 '커뮤니티'로 센다)
T = [('피트니스', r'헬스|피트니스|휘트니스|체력단련|운동시설|GX|짐'), ('골프연습장', r'골프'), ('수영장', r'수영'),
     ('사우나', r'사우나|목욕|찜질'), ('독서실', r'독서실|스터디'), ('작은도서관', r'도서관|문고'), ('카페', r'카페|라운지'),
     ('게스트하우스', r'게스트|손님'), ('실내놀이터', r'키즈|실내놀이|놀이방'),
     ('어린이집', r'보육|어린이집'), ('경로당', r'노인정|경로'), ('놀이터', r'놀이터'), ('주민공동시설', r'주민공동|커뮤니티|다목적')]

calls = 0
class Quota(Exception): pass

def get(op_path, **p):
    global calls
    if calls >= MAXCALL: raise Quota('하루 호출 상한')
    q = urllib.parse.urlencode({**p, '_type': 'json'})
    url = f'{BASE}/{op_path}?serviceKey={KEY}&{q}'  # 키는 포털이 준 인코딩 키 그대로
    for t in range(3):
        calls += 1
        try:
            with urllib.request.urlopen(url, timeout=20) as r: txt = r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 429: raise Quota('HTTP 429')
            if t == 2: return None
            time.sleep(2); continue
        except Exception:
            if t == 2: return None
            time.sleep(2); continue
        if 'LIMITED_NUMBER_OF_SERVICE_REQUESTS' in txt or '<returnReasonCode>22' in txt: raise Quota('한도 초과')
        if 'SERVICE_KEY_IS_NOT_REGISTERED' in txt or 'SERVICE_ACCESS_DENIED' in txt:
            sys.exit('키가 등록되지 않았거나 이 API 활용신청이 안 됨: ' + txt[:200])
        try: j = json.loads(txt)
        except ValueError:
            if t == 2: return None
            time.sleep(2); continue
        return j.get('response', {}).get('body')
    return None

def items(body):
    if not body: return []
    it = body.get('items')
    if isinstance(it, dict): it = it.get('item')
    if isinstance(it, dict): it = [it]
    return it or []

def norm(s): return re.sub(r'[^가-힣0-9A-Za-z]', '', s or '').replace('아파트', '')

def lcs(a, b):
    if not a or not b: return 0
    prev = [0] * (len(b) + 1); best = 0
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b):
            if x == y: cur[j + 1] = prev[j] + 1; best = max(best, cur[j + 1])
        prev = cur
    return best

def main():
    if not KEY: print('DATA_GO_KR_KEY 없음 — 건너뜀'); return
    apt = json.load(open(os.path.join(ROOT, 'data', 'apt.json'), encoding='utf-8'))['a']
    C = {'L': {}, 'B': {}, 'D': {}}
    if os.path.exists(CACHE): C = json.load(gzip.open(CACHE, 'rt', encoding='utf-8'))
    # apt.json 단지: 시군구 → 동 → [(키, 지번, 이름)]
    A = {}
    for x in apt:
        sgg, ad = x[4], x[5] or ''
        tk = ad.split(' ')
        if len(tk) < 2: continue
        A.setdefault(sgg, {}).setdefault(tk[0], []).append((f'{sgg}|{ad}', tk[1], x[0]))
    # 전주·춘천 등 특별자치도 새 코드(52·51)는 K-apt가 옛 코드(45·42)일 수 있어 둘 다 시도
    alt = lambda s: [s] + ([('45' + s[2:])] if s[:2] == '52' else [('42' + s[2:])] if s[:2] == '51' else [])
    # 전북부터(만든 사람 지역), 나머지는 단지 많은 순
    order = sorted(A, key=lambda s: (s[:2] not in ('52', '45'), -sum(len(v) for v in A[s].values())))
    stop = None
    try:
        for sgg in order:
            L = C['L'].get(sgg)
            if not L or L[0] < (date.today().toordinal() - 30):
                got = []
                for code in alt(sgg):
                    pg = 1
                    while True:
                        b = get('AptListService3/getSigunguAptList3', sigunguCode=code, numOfRows=1000, pageNo=pg)
                        its = items(b); got += [[i.get('kaptCode'), i.get('kaptName'), i.get('as3') or ''] for i in its if i.get('kaptCode')]
                        if not b or pg * 1000 >= int(b.get('totalCount') or 0): break
                        pg += 1
                    if got: break
                C['L'][sgg] = L = [date.today().toordinal(), got]
            for code, nm, dong in L[1]:
                if code not in C['B']:
                    b = get('AptBasisInfoServiceV4/getAphusBassInfoV4', kaptCode=code)
                    it = (b or {}).get('item') or {}
                    if isinstance(it, list): it = it[0] if it else {}
                    C['B'][code] = [it.get('kaptAddr') or '', it.get('kaptName') or nm]
    except Quota as e: stop = str(e)
    # 매칭
    M = {}
    for sgg in order:
        L = C['L'].get(sgg)
        if not L: continue
        D = A[sgg]
        for code, nm, dong in L[1]:
            ad = (C['B'].get(code) or ['', nm])[0]; tk = ad.split()
            hit = None
            for i, t in enumerate(tk[:-1]):
                if t in D:
                    jb = re.match(r'(\d+(?:-\d+)?)', tk[i + 1]);
                    if not jb: continue
                    jb = jb.group(1); cand = D[t]
                    ex = [c for c in cand if c[1] == jb]
                    bon = [c for c in cand if c[1].split('-')[0] == jb.split('-')[0]]
                    pool = ex or bon
                    if len(pool) == 1: hit = pool[0]
                    elif pool: hit = max(pool, key=lambda c: lcs(norm(c[2]), norm(nm)))
                    if hit: break
            if not hit and dong in D:
                c = max(D[dong], key=lambda c: lcs(norm(c[2]), norm(nm)))
                if lcs(norm(c[2]), norm(nm)) >= max(2, min(len(norm(nm)), len(norm(c[2]))) - 1): hit = c
            if hit: M.setdefault(hit[0], code)
    # 맞춰진 단지만 상세(부대복리시설) 조회
    try:
        if not stop:
            for k, code in M.items():
                if code in C['D']: continue
                b = get('AptBasisInfoServiceV4/getAphusDtlInfoV4', kaptCode=code)
                it = (b or {}).get('item') or {}
                if isinstance(it, list): it = it[0] if it else {}
                ev = sum(int(re.sub(r'\D', '', str(it.get(f) or '0')) or 0) for f in ('groundElChargerCnt', 'undergroundElChargerCnt'))
                C['D'][code] = [it.get('welfareFacility') or '', ev]
    except Quota as e: stop = str(e)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with gzip.open(CACHE, 'wt', encoding='utf-8') as f: json.dump(C, f, ensure_ascii=False, separators=(',', ':'))
    out = {}
    for k, code in M.items():
        d = C['D'].get(code)
        if not d: continue
        bits = 0
        for i, (_, rx) in enumerate(T):
            if re.search(rx, d[0]): bits |= 1 << i
        out[k] = [bits, d[1]]
    json.dump({'ref': TODAY, 'src': 'K-apt 공동주택 상세정보(국토교통부 AptBasisInfoServiceV4, 부대복리시설)', 't': [t[0] for t in T], 'k': out},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'호출 {calls}회 · 시군구 {len(C["L"])}/{len(A)} · 기본정보 {len(C["B"])} · 매칭 {len(M)} · 시설 자료 {len(out)}' + (f' · 멈춤: {stop}(내일 이어서)' if stop else ' · 완료'))

if __name__ == '__main__': main()
