# 버스정류장: 공공데이터포털 15067528 '국토교통부_전국 버스정류장 위치정보'(TAGO 연계 지자체 BIS, 연 1회 수집) 중 서울·경기·인천·대전·세종·충북·충남·전북
# 원본 CSV(약 22MB, 로그인 불필요)를 내장 브라우저에서 8개 시도만 골라 '정류장명\t위도\t경도\t모바일단축번호\t도시명\t정류장번호' TSV(gzip)로 저장해 온다.
# usage: BUSDATE=2026-11-09 python3 build_bus.py krmap_busstop_8.tsv.gz → data/bus/{위도칸}_{경도칸}.json(0.1° 칸) + data/bus/index.json
import sys, os, json, gzip, collections
src = sys.argv[1]
op = gzip.open if src.endswith('.gz') else open
cells = collections.defaultdict(list); seen = set(); n = 0
for line in op(src, 'rt', encoding='utf-8'):
    f = line.rstrip('\n').split('\t')
    if len(f) < 5: continue
    try: lat, lon = float(f[1]), float(f[2])
    except ValueError: continue
    if not (33 < lat < 39 and 124 < lon < 132): continue
    key = (f[0], round(lat, 5), round(lon, 5))
    if key in seen: continue
    seen.add(key); n += 1
    cells[f'{int(lat * 10)}_{int(lon * 10)}'].append([f[0], round(lat * 1e5), round(lon * 1e5), f[3], f[4]])
os.makedirs('data/bus', exist_ok=True)
for k, v in cells.items():
    json.dump(v, open(f'data/bus/{k}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({'ref': os.environ.get('BUSDATE', ''), 'n': n, 'c': {k: len(v) for k, v in cells.items()}}, open('data/bus/index.json', 'w'), separators=(',', ':'))
print('stops', n, 'cells', len(cells), 'max per cell', max(map(len, cells.values())))
