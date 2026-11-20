# 건물 자료(bld/)에서 '시군구+법정동+지번 → 좌표' 사전을 만든다(실거래가 단지 위치 찾기용).
# usage: python3 build_bld_addr.py bld /tmp/bld_addr.json
import sys, json, gzip, re
root, out = sys.argv[1], sys.argv[2]
idx = json.load(open(f'{root}/index.json'))
bund = {}
A = {}
SD = {'서울': '11', '인천': '28', '대전': '30', '세종': '36', '경기': '41', '충청': None, '충북': '43', '충남': '44', '전라': None, '전북': '52'}
norm = lambda s: re.sub(r'\s', '', s)
for k, v in idx['t'].items():
    bk, off, ln = v[:3]
    if bk not in bund: bund[bk] = open(f'{root}/{bk}.txt', 'rb').read()
    j = json.loads(gzip.decompress(bund[bk][off:off + ln]))
    ox, oy = j['o']
    for r in j['r']:
        d = j['d'][r[4]]; jb = str(r[5]).strip()
        if not jb: continue
        f = r[8]; x = y = 0; sx = sy = 0; n = len(f) // 2
        for i in range(0, len(f), 2): x += f[i]; y += f[i + 1]; sx += x; sy += y
        lon, lat = ox + sx / n / 1e5, oy + sy / n / 1e5
        parts = d.split()
        if len(parts) < 3: continue
        mid = [p for p in parts[1:-1] if not re.search(r'[읍면]$', p)]
        sd = {'충청북도': '43', '충청남도': '44', '전라북도': '52'}.get(parts[0]) or SD.get(parts[0][:2]) or parts[0]
        key = sd + '|' + (norm(''.join(mid)) or '-') + '|' + parts[-1] + '|' + jb   # 시군구(읍면 제외, 붙여씀)|법정동·리|지번
        w = (2 if r[0] == 1 else 1) * (r[7] or 1)                    # 공동주택·큰 건물 우선
        if key not in A or w > A[key][2]: A[key] = [round(lon, 6), round(lat, 6), w]
json.dump({k: v[:2] for k, v in A.items()}, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print('keys', len(A))
