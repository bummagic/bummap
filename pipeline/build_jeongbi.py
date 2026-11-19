# 정비사업 레이어: 서울 = 서울플랜+ 도시계획사업 경계(OA-22712, SHP), 전국 = 국토부 '전국 도시정비사업 통합 데이터'(15160169, CSV, 좌표 없음)
# usage: JBDATE="2026년 9월" JBNDATE="2026-05-18" python3 build_jeongbi.py <서울 SHP 경로(확장자 제외)> <national.csv> muninames_kr.json → data/jeongbi.json(서울 경계), data/jeongbi_n.json(전국 목록)
import sys, os, json, re, csv, io, shapefile
from pyproj import Transformer

stem, ncsv, munif = sys.argv[1], sys.argv[2], sys.argv[3]
# 서울플랜+ 코드정의표(대민용) 사업유형 소분류
TYPE = {'BZ101': '신속통합기획', 'BZ102': '재개발(도시정비형)', 'BZ103': '재개발(주택정비형)', 'BZ104': '재건축(단독)', 'BZ105': '재건축(공동)',
        'BZ107': '주거환경개선(관리형)', 'BZ108': '주거환경개선(정비형)', 'BZ201': '모아타운', 'BZ202': '가로주택정비', 'BZ203': '자율주택정비',
        'BZ204': '소규모재건축', 'BZ205': '소규모재개발', 'BZ301': '장기전세주택', 'BZ302': '역세권 활성화', 'BZ303': '청년안심주택', 'BZ304': '역세권사업', 'BZ305': '역세권사업',
        'BZ306': '미리내집', 'BZ401': '재정비촉진지구', 'BZ402': '재정비촉진구역', 'BZ403': '존치정비구역', 'BZ404': '존치관리구역', 'BZ501': '공공주택지구',
        'BZ502': '도심 공공주택 복합사업', 'BZ601': '도시개발사업', 'BZ602': '리모델링', 'BZ603': '시장정비사업', 'BZ604': '도시재생활성화지역', 'BZ606': '사전협상제'}
# 지도 색 묶음: r 재개발·재정비촉진, k 재건축, s 소규모(가로·소규모·자율·모아), q 신속통합기획, p 공공주택·역세권, m 리모델링, e 그 밖
GRP = lambda t: 'q' if t == 'BZ101' else 'r' if t in ('BZ102', 'BZ103', 'BZ401', 'BZ402', 'BZ403', 'BZ404', 'BZ107', 'BZ108') else 'k' if t in ('BZ104', 'BZ105') \
    else 's' if t[:3] == 'BZ2' else 'p' if t[:3] in ('BZ3', 'BZ5') else 'm' if t == 'BZ602' else 'e'
STAGE = {'PP0101': '대상지선정(추진중)', 'PP0102': '대상지선정', 'PP0103': '기획완료', 'PP0104': '보류', 'PP0201': '입안제안', 'PP0202': '열람공고', 'PP0203': '위원회심의',
         'PP0204': '구역지정', 'PP0205': '추진위구성', 'PP0206': '조합설립인가', 'PP0207': '건축심의', 'PP0208': '사업시행인가', 'PP0209': '관리처분계획인가', 'PP0210': '착공', 'PP0211': '준공',
         'PP0301': '대상지선정', 'PP0302': '정비계획수립', 'PP0303': '위원회심의', 'PP0304': '구역지정', 'PP0305': '사업시행인가', 'PP0306': '착공', 'PP0307': '준공(일부)', 'PP0308': '준공',
         'PP0401': '수립범위 자문', 'PP0402': '대상지선정', 'PP0403': '관리지역고시', 'PP0404': '사전자문', 'PP0405': '위원회심의', 'PP0406': '관리지역고시',
         'PP0500': '조합설립 추진중', 'PP0501': '조합설립인가', 'PP0502': '건축심의', 'PP0503': '사업시행인가', 'PP0504': '착공', 'PP0505': '준공',
         'PP0601': '주민합의체 구성', 'PP0602': '건축심의', 'PP0603': '사업시행인가', 'PP0604': '착공', 'PP0605': '준공',
         'PP0701': '조합설립추진중', 'PP0702': '조합설립인가', 'PP0703': '건축심의', 'PP0704': '사업시행계획인가', 'PP0705': '착공', 'PP0706': '준공',
         'PP0801': '대상지선정', 'PP0802': '사전검토', 'PP0803': '입안제안', 'PP0804': '열람공고', 'PP0805': '위원회심의', 'PP0806': '구역지정', 'PP0807': '건축심의', 'PP0808': '사업계획승인', 'PP0809': '착공', 'PP0810': '준공',
         'PP0901': '대상지선정', 'PP0902': '사전자문', 'PP0903': '입안제안', 'PP0904': '열람공고', 'PP0905': '위원회심의', 'PP0906': '구역지정', 'PP0907': '건축심의', 'PP0908': '사업계획승인', 'PP0909': '건축허가', 'PP0910': '착공', 'PP0911': '사용승인', 'PP0912': '입주',
         'PP1901': '입주자 모집공고 완료', 'PP1801': '대상지선정', 'PP1802': '사전자문', 'PP1803': '입안제안', 'PP1804': '열람공고', 'PP1805': '위원회심의', 'PP1806': '구역지정', 'PP1807': '건축·통합심의', 'PP1808': '사업계획승인', 'PP1809': '착공', 'PP1810': '준공',
         'PP1001': '지구지정', 'PP1002': '지구변경', 'PP1101': '대상지선정', 'PP1102': '촉진계획수립(변경)', 'PP1103': '열람공고', 'PP1104': '위원회심의', 'PP1105': '구역지정', 'PP1107': '추진위구성', 'PP1108': '조합설립인가',
         'PP1109': '건축심의', 'PP1110': '사업시행인가', 'PP1111': '관리처분계획인가', 'PP1112': '착공', 'PP1113': '준공', 'PP2101': '구역지정', 'PP2102': '구역변경',
         'PP2001': '입안제안', 'PP2002': '열람공고', 'PP2003': '위원회심의', 'PP2004': '구역지정', 'PP2005': '지구계획승인', 'PP2006': '착공', 'PP2007': '준공',
         'PP1201': '예정지구지정', 'PP1202': '후보지선정', 'PP1203': '지구지정', 'PP1204': '설계공모완료', 'PP1205': '사업계획승인', 'PP1206': '착공', 'PP1207': '준공', 'PP1208': '입주중', 'PP1209': '후보지철회',
         'PP1301': '입안제안', 'PP1302': '열람공고', 'PP1303': '위원회심의', 'PP1304': '구역지정', 'PP1305': '실시계획인가', 'PP1306': '준공',
         'PP1401': '조합설립인가', 'PP1402': '1차 안전진단', 'PP1403': '건축심의', 'PP1404': '리모델링허가', 'PP1405': '2차 안전진단', 'PP1406': '착공', 'PP1407': '준공',
         'PP1501': '추진계획수립중', 'PP1502': '추진계획승인', 'PP1503': '조합설립인가', 'PP1504': '사업시행계획인가', 'PP1505': '관리처분계획인가', 'PP1506': '착공', 'PP1507': '준공',
         'PP1601': '대상지선정', 'PP1602': '활성화계획수립', 'PP1603': '마중물사업(추진중)', 'PP1604': '사업완료',
         'PP2201': '대상지 선정', 'PP2202': '제안서접수', 'PP2203': '협상조정협의회', 'PP2204': '협상완료', 'PP2205': '입안절차 진행', 'PP2206': '도시건축공동위 심의', 'PP2207': '결정고시', 'PP2208': '인허가 절차', 'PP2209': '착공', 'PP2210': '준공'}
# 진행도(0~4): 0 초기(대상지·자문·입안·열람·심의), 1 구역지정·추진위, 2 조합설립·건축심의, 3 사업시행·관리처분·사업계획승인, 4 착공·준공·입주
def LEVEL(s):
    if re.search('착공|준공|입주|사용승인|사업완료|모집공고', s): return 4
    if re.search('사업시행|관리처분|사업계획승인|실시계획|건축허가|리모델링허가|지구계획승인|결정고시|인허가', s): return 3
    if re.search('조합설립인가|건축심의|통합심의|안전진단|추진계획승인|설계공모', s): return 2
    if re.search('구역지정|지구지정|추진위|관리지역고시|구역변경|지구변경|예정지구|주민합의체', s): return 1
    return 0

tr = Transformer.from_crs(open(stem + '.prj').read(), 'EPSG:4326', always_xy=True)
def dp(pts, tol):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2 - x1, y2 - y1; L = (dx * dx + dy * dy) ** .5 or 1; md, mi = 0, -1
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - x1) - dx * (pts[i][1] - y1)) / L
            if d > md: md, mi = d, i
        if md > tol: keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]
def ring(r):
    m = len(r) // 2
    r = dp(r[:m + 1], 1.5) + dp(r[m:], 1.5)[1:] if len(r) >= 8 else r
    return [[round(x, 6), round(y, 6)] for x, y in (tr.transform(*p) for p in r)]

sf = shapefile.Reader(stem, encoding='cp949')
Z = []
for sr in sf.iterShapeRecords():
    r = sr.record.as_dict(); t = r['SCLAS_CL'] or r['ATRB_SE']
    if t not in TYPE: continue
    s = sr.shape; parts = list(s.parts) + [len(s.points)]
    rings = [ring(s.points[parts[i]:parts[i + 1]]) for i in range(len(parts) - 1)]
    rings = [x for x in rings if len(x) >= 4]
    if not rings: continue
    st = STAGE.get(r['PROPEL_CD'], '')
    Z.append({'t': t, 'g': GRP(t), 'p': st, 'v': LEVEL(st), 'n': (r['DGM_NM'] or '').strip(), 'a': round(float(r['DGM_AR'] or 0)), 'd': str(r['CREATE_DAT'] or '').replace('-', '')[:8], 'c': rings})

# 전국 목록(좌표 없음) → 시군구 코드별로 묶어 동을 누르면 그 시군구 사업 목록 표시. 서울은 경계 자료가 있어 제외.
MUNI = json.load(open(munif))
raw = open(ncsv, 'rb').read()
try: txt = raw.decode('utf-8-sig')
except UnicodeDecodeError: txt = raw.decode('cp949')
SIDO = {'서울특별시': '11', '부산광역시': '21', '대구광역시': '22', '인천광역시': '23', '광주광역시': '24', '대전광역시': '25', '울산광역시': '26', '세종특별자치시': '29', '경기도': '31',
        '강원특별자치도': '32', '강원도': '32', '충청북도': '33', '충청남도': '34', '전북특별자치도': '35', '전라북도': '35', '전라남도': '36', '경상북도': '37', '경상남도': '38', '제주특별자치도': '39'}
norm = lambda s: re.sub(r'\s', '', s)
idx = {}
for c, n in MUNI.items():
    k = norm(n); idx.setdefault((c[:2], k), c); idx.setdefault((c[:2], re.sub(r'시(?=\S+구$)', '', k)), c)
    if c[:2] == '29': idx[('29', '세종시')] = c; idx[('29', '세종특별자치시')] = c
N, miss = {}, {}
clean = lambda s: re.sub(r'^\d+\)', '', (s or '').strip())
for row in csv.DictReader(io.StringIO(txt)):
    sd = SIDO.get(row['시도'].strip())
    if not sd or sd == '11': continue
    k = norm(row['시군구']); c = idx.get((sd, k)) or idx.get((sd, re.sub(r'(시|군)$', '', k) + '시')) or idx.get((sd, k + '시'))
    if not c and sd == '31' and k.startswith('화성'): c = '31240'
    # 2013 경계 이후 바뀐 시군구: 미추홀구 = 옛 남구, 청주 서원구 = 옛 상당구·흥덕구 일부(두 곳에 모두 표시)
    if not c and sd == '23' and k == '미추홀구': c = '23030'
    if not c and sd == '33' and k in ('청주서원구', '청주시서원구'):
        for cc in ('33011', '33012'): N.setdefault(cc, []).append([row['구역명칭'].strip() + ' (서원구)', clean(row['현 사업추진단계']), clean(row['사업유형']), clean(row['사업시행자']), int(re.sub(r'\D', '', row.get('공급 예정 세대수', '') or '') or 0)])
        continue
    if not c: miss[row['시도'] + ' ' + row['시군구']] = miss.get(row['시도'] + ' ' + row['시군구'], 0) + 1; continue
    u = re.sub(r'\D', '', row.get('공급 예정 세대수', '') or '')
    N.setdefault(c, []).append([row['구역명칭'].strip(), clean(row['현 사업추진단계']), clean(row['사업유형']), clean(row['사업시행자']), int(u) if u else 0])
for c in N: N[c].sort(key=lambda x: x[0])
os.makedirs('data', exist_ok=True)
json.dump({'ref': os.environ.get('JBDATE', ''), 'z': Z}, open('data/jeongbi.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({'ref': os.environ.get('JBNDATE', ''), 'n': N}, open('data/jeongbi_n.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('seoul zones', len(Z), 'national munis', len(N), 'rows', sum(map(len, N.values())), 'unmatched', miss, 'bytes', os.path.getsize('data/jeongbi.json'), os.path.getsize('data/jeongbi_n.json'))
