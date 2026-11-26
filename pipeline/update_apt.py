# 아파트 실거래가 매일 자동 갱신 — GitHub Actions(.github/workflows/apt.yml)에서 돈다.
# 키: 저장소 Secret DATA_GO_KR_KEY(공공데이터포털 인코딩 키, 활용신청: 아파트 매매 실거래가 상세 RTMSDataSvcAptTradeDev,
#      아파트 전월세 실거래가 RTMSDataSvcAptRent). 키는 어디에도 쓰지 않는다.
# 하는 일
#  1) 원본 월 묶음 캐시(RTDIR/T_YYYYMM.json.gz·R_YYYYMM.json.gz, Actions 캐시에 보관)를 채운다.
#     - 없는 달은 받고(처음엔 HIST개월치를 여러 날에 걸쳐 채움), 최근 RECENT개월은 매일 다시 받는다(신고 기한 30일·해제 반영).
#     - 하루 호출 상한(API별 1만 건)에 걸리면 받은 데까지만 저장하고 다음 날 이어서.
#  2) 관심 단지(Secret WATCH_KEYS: 지도 '즐겨찾는 단지 → 알림 목록 복사' 내용)에 새 거래가 생기면 텔레그램으로 알림
#     (Secret TELEGRAM_TOKEN, TELEGRAM_CHAT — 없으면 건너뜀).
#  3) build_apt.py로 data/apt.json(최근 12개월)과 data/apt_h/<시군구>.json(전체 기간 면적별 월별 흐름)을 다시 만든다.
#  위치: pipeline/apt_loc.json("시군구코드|동 지번" → [lon,lat]). 새 단지는 브이월드 지오코더로 찾아 보탠다(실패하면 다음 날 다시).
import gzip, json, os, re, sys, time, threading, subprocess, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
RTDIR = os.environ.get('RTDIR', P('rtcache'))
HIST = int(os.environ.get('APT_HIST', '36'))      # 모아 둘 개월 수
RECENT = int(os.environ.get('APT_RECENT', '3'))   # 매일 다시 받는 최근 개월 수
MAXCALL = int(os.environ.get('APT_MAXCALL', '9500'))  # API별 하루 상한보다 조금 작게
DRY = os.environ.get('APT_DRY')                   # 시험: 받기 없이 캐시만으로 빌드
KST = timezone(timedelta(hours=9)); TODAY = datetime.now(KST).date()
BASE = 'https://apis.data.go.kr/1613000'
OPS = {'T': 'RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev', 'R': 'RTMSDataSvcAptRent/getRTMSDataSvcAptRent'}
os.makedirs(RTDIR, exist_ok=True)

def months(n):
    y, m = TODAY.year, TODAY.month; o = []
    for _ in range(n):
        o.append(f'{y}{m:02d}'); m -= 1
        if m == 0: m = 12; y -= 1
    return o[::-1]
MS = months(HIST)
SGG = sorted({k.split('|')[0] for k in json.load(open(P('pipeline', 'apt_loc.json')))} | {'41590'})

calls = {'T': 0, 'R': 0}; lock = threading.Lock(); last = [0.0]
class Quota(Exception): pass

def call(op, sgg, ym, page):
    with lock:
        if calls[op] >= MAXCALL: raise Quota(op + ' 하루 상한')
        calls[op] += 1
        w = 0.26 - (time.time() - last[0])
        if w > 0: time.sleep(w)
        last[0] = time.time()
    url = f'{BASE}/{OPS[op]}?serviceKey={KEY}&' + urllib.parse.urlencode({'LAWD_CD': sgg, 'DEAL_YMD': ym, 'pageNo': page, 'numOfRows': 1000})
    for t in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r: txt = r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(3 + 3 * t); continue
            time.sleep(2); continue
        except Exception:
            time.sleep(2); continue
        if 'LIMITED_NUMBER_OF_SERVICE_REQUESTS' in txt or '<returnReasonCode>22<' in txt: raise Quota(op + ' 한도 초과')
        if 'SERVICE_KEY_IS_NOT_REGISTERED' in txt or 'SERVICE_ACCESS_DENIED' in txt or 'SERVICE KEY IS NOT REGISTERED' in txt:
            sys.exit(f'키가 등록되지 않았거나 {op} API 활용신청이 안 됨: ' + txt[:200])
        try: return ET.fromstring(txt)
        except ET.ParseError: time.sleep(2)
    raise RuntimeError(f'{op} {sgg} {ym} p{page} 실패')

def g(it, k):
    e = it.find(k); return (e.text or '').strip() if e is not None and e.text else ''
def num(s):
    try: return float(s.replace(',', ''))
    except Exception: return 0

def fetch(op, sgg, ym):
    rows = []; page = 1
    while True:
        x = call(op, sgg, ym, page)
        items = x.findall('.//item'); tot = int(x.findtext('.//totalCount') or 0)
        for it in items:
            ymd = int(g(it, 'dealYear') + g(it, 'dealMonth').zfill(2) + g(it, 'dealDay').zfill(2) or 0)
            jb = g(it, 'jibun'); nm = g(it, 'aptNm'); umd = g(it, 'umdNm'); by = int(num(g(it, 'buildYear')))
            ar = round(num(g(it, 'excluUseAr')), 2); fl = int(num(g(it, 'floor')))
            if op == 'T':
                if g(it, 'cdealType') == 'O': continue  # 해제 거래 제외
                rows.append([g(it, 'aptSeq'), nm, sgg, umd, jb, g(it, 'roadNm'), by, ymd, int(num(g(it, 'dealAmount'))), ar, fl])
            else:
                rows.append([g(it, 'aptSeq'), nm, sgg, umd, jb, by, ymd, int(num(g(it, 'deposit'))), int(num(g(it, 'monthlyRent'))), ar, fl])
        if page * 1000 >= tot or not items: break
        page += 1
    return rows

def path(op, ym): return os.path.join(RTDIR, f'{op}_{ym}.json.gz')
def load(op, ym):
    try: return json.load(gzip.open(path(op, ym), 'rt'))
    except Exception: return None
def save(op, ym, rows):
    tmp = path(op, ym) + '.tmp'
    with gzip.open(tmp, 'wt') as f: json.dump(rows, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, path(op, ym))

# ── 1) 받기: 최근 달 먼저(매일 다시), 그다음 비어 있는 옛 달을 최근 쪽부터
old = {}
todo = [(op, ym) for ym in MS[-RECENT:][::-1] for op in 'TR'] + [(op, ym) for ym in MS[:-RECENT][::-1] for op in 'TR' if not os.path.exists(path(op, ym))]
stop = {'T': False, 'R': False}; got = 0
if KEY and not DRY:
    for op, ym in todo:
        if stop[op]: continue
        prev = load(op, ym)
        try:
            with ThreadPoolExecutor(3) as ex: parts = list(ex.map(lambda s: fetch(op, s, ym), SGG))
        except Quota as e:
            print('멈춤:', e); stop[op] = True; continue
        except RuntimeError as e:
            print('건너뜀:', e); continue
        rows = [r for p in parts for r in p]
        if prev is not None and op == 'T': old[ym] = prev
        save(op, ym, rows); got += 1
        print(op, ym, len(rows), '건', '호출', calls)
elif not KEY:
    print('DATA_GO_KR_KEY 없음 — 받기 건너뜀(캐시만으로 빌드)')

have = [ym for ym in MS if os.path.exists(path('T', ym)) and os.path.exists(path('R', ym))]
print('캐시', len(have), '/', len(MS), '개월')
if not have: sys.exit(0)
FULL = set(MS[-12:]) <= set(have)  # 최근 12개월이 다 있어야 apt.json을 새로 만든다(처음 채우는 중에 지도 자료가 줄지 않게)

# ── 2) 관심 단지 새 거래 알림(텔레그램)
WATCH = [w.strip() for w in re.split(r'[\n,]+', os.environ.get('WATCH_KEYS', '')) if w.strip()]
TG, CH = os.environ.get('TELEGRAM_TOKEN', '').strip(), os.environ.get('TELEGRAM_CHAT', '').strip()
if WATCH and TG and CH and old:
    W = {}
    for w in WATCH:  # 시군구코드|동 지번|단지명
        p = w.split('|')
        if len(p) >= 3: W[(p[0], p[1])] = p[2]
    msgs = []
    for ym, prev in old.items():
        seen = {json.dumps(r, ensure_ascii=False) for r in prev}
        for r in load('T', ym) or []:
            k = (r[2], (r[3] + ' ' + r[4]).strip())
            if k in W and json.dumps(r, ensure_ascii=False) not in seen:
                d = str(r[7]); eok = r[8] / 10000
                msgs.append(f'• {W[k]} {r[9]:.0f}㎡ {r[10]}층 {eok:.2f}억 ({d[4:6]}.{d[6:]} 계약)')
    if msgs:
        txt = '🏠 관심 단지 새 실거래\n' + '\n'.join(msgs[:40]) + ('\n…' if len(msgs) > 40 else '') + '\nhttps://bummagic.github.io/bummap/'
        try:
            urllib.request.urlopen(urllib.request.Request(f'https://api.telegram.org/bot{TG}/sendMessage',
                data=urllib.parse.urlencode({'chat_id': CH, 'text': txt, 'disable_web_page_preview': 'true'}).encode()), timeout=20)
            print('알림 보냄', len(msgs))
        except Exception as e: print('알림 실패', e)
    else: print('관심 단지 새 거래 없음')

if not FULL:
    print('최근 12개월 중 빠진 달이 있어 이번엔 빌드하지 않음(다음 날 이어서 받음)'); sys.exit(0)
# ── 3) 빌드: 원본 묶기 → 새 단지 위치 찾기 → build_apt.py
T, R = [], []
for ym in have: T += load('T', ym); R += load('R', ym)
import tempfile
raw = os.path.join(tempfile.gettempdir(), 'rt_raw.json.gz')
with gzip.open(raw, 'wt') as f: json.dump({'T': T, 'R': R, 'M': have}, f, ensure_ascii=False, separators=(',', ':'))
LOCF = P('pipeline', 'apt_loc.json'); LOC = json.load(open(LOCF))
# 최근 12개월에 거래가 있는데 위치를 모르는 단지 → 브이월드 지오코더(PARCEL). 키는 저장소의 vwkey.js(이미 공개된 지도용 키)
recent = set(have[-12:]); need = {}
from regions import NAME as SDN
SGN = json.load(open(P('pipeline', 'sgg_names.json'))) if os.path.exists(P('pipeline', 'sgg_names.json')) else {}
for r in T:
    if str(r[7])[:6] in recent and r[4]:
        k = r[2] + '|' + (r[3] + ' ' + r[4]).strip()
        if k not in LOC: need[k] = 1
for r in R:
    if str(r[6])[:6] in recent and r[4]:
        k = r[2] + '|' + (r[3] + ' ' + r[4]).strip()
        if k not in LOC: need[k] = 1
VW = ''
try: VW = re.search(r"'([^']+)'", open(P('vwkey.js')).read()).group(1)
except Exception: pass
found = 0
if need and VW and not DRY:
    for k in list(need)[:600]:
        sg, addr = k.split('|', 1); q = ' '.join(x for x in [SDN.get(sg[:2], ''), SGN.get(sg, ''), addr] if x)
        u = 'https://api.vworld.kr/req/address?' + urllib.parse.urlencode({'service': 'address', 'request': 'getcoord', 'version': '2.0', 'crs': 'epsg:4326',
            'address': q, 'refine': 'true', 'simple': 'false', 'format': 'json', 'type': 'PARCEL', 'key': VW, 'domain': 'https://bummagic.github.io'})
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={'Referer': 'https://bummagic.github.io/bummap/'}), timeout=15) as r: j = json.loads(r.read())
            pt = j['response']['result']['point']; LOC[k] = [round(float(pt['x']), 5), round(float(pt['y']), 5)]; found += 1
        except Exception: pass
        time.sleep(0.4)
print('위치 모르는 주소', len(need), '새로 찾음', found)
with open(LOCF, 'w') as f:
    f.write('{\n' + ',\n'.join(json.dumps(k, ensure_ascii=False) + ':' + json.dumps(v) for k, v in sorted(LOC.items())) + '\n}\n')
E = os.path.join(tempfile.gettempdir(), 'empty.json'); open(E, 'w').write('{}')
env = dict(os.environ, APTLOC=LOCF, APTHIST=P('data', 'apt_h'), APTDATE=TODAY.isoformat(), PYTHONPATH=P('pipeline'))
subprocess.run([sys.executable, P('pipeline', 'build_apt.py'), raw, E, E, E, P('data', 'apt.json')], env=env, check=True)
