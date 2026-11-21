# 시세 민감도(지역): 한국부동산원 전국주택가격동향조사 아파트 매매·전세가격지수(시군구, 월간)에서
# 지난 상승기(2019.1 → 2020~2022 고점)·하락기(고점 → 2025.6까지 저점)·회복(저점 → 최신)을 요약한 표를 data/sens.json으로 만든다.
# 입력 reb_sens.txt 한 줄: 코드|이름|구 이름|매매 고점(YYMM)|고점 지수×10|저점(YYMM)|저점×10|2019.1×10|최신×10|전세 같은 6개|2015~2026년 1월 매매지수×10 12개
# (README '시세 민감도' 절: R-ONE 시계열(신) xlsx '매매_아파트'·'전세_아파트' 시트를 내장 브라우저에서 읽어 만든 값)
import json, sys
src, out, ym = sys.argv[1], sys.argv[2], sys.argv[3]   # ym: 최신 지수 월, 예 2026.10
R = {}
for l in open(src, encoding='utf-8'):
    f = l.rstrip('\n').split('|')
    if len(f) != 27: continue
    n = lambda x: int(x) if x != '' else None
    R[f[0]] = [f[1] or f[2], f[2], f[3], n(f[4]), f[5], n(f[6]), n(f[7]), n(f[8]), f[9], n(f[10]), f[11], n(f[12]), n(f[13]), n(f[14])] + [n(x) for x in f[15:27]]
# 2026년 개편으로 새로 생긴 구는 지수 이력이 없어 옛 구 지수로 대신함
ALIAS = {'28125': '28140', '28155': '28110', '28275': '28260', '28290': '28260'}
json.dump({'src': '한국부동산원 전국주택가격동향조사 아파트 매매·전세가격지수(월간, 2026.6=100)', 'ym': ym, 'yrs': list(range(2015, 2027)), 'alias': ALIAS, 'r': R}, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print('regions', len(R))
