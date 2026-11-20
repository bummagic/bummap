import json,os,subprocess
# usage: python3 gen.py  → index.html(새 지도, ml.tpl.html), old.html(이전 D3 지도, index.tpl.html), ml.html(index.html로 넘기기), bld.html
#  (run in work dir containing index.tpl.html, muninames_kr.json, data/rail.json, data/hwy.json, kr-rail-map/)
def R(s):
  s=s.replace('__MUNI__',open('muninames_kr.json').read().strip())
  rail=json.load(open('data/rail.json'))
  hw=json.load(open('data/hwy.json')) if os.path.exists('data/hwy.json') else []
  try: rd=subprocess.check_output(['git','-C','kr-rail-map','log','-1','--format=%cd','--date=format:%Y.%m.%d']).decode().strip()
  except Exception: rd=os.environ.get('RAILDATE','')
  s=s.replace('__NRAIL__',str(len(rail))).replace('__NHWY__',str(len([h for h in hw if h['s']=='open']) or '—')).replace('__ROADDATE__',(lambda r:f'{r[:4]}년 {int(r[5:7])}월 {int(r[8:10])}일 배포판' if r else '')(json.load(open('data/roads_big.json'))['ref'] if os.path.exists('data/roads_big.json') else '')).replace('__HWYDATE__',os.environ.get('HWYDATE','2026년 11월 17일 조회')).replace('__RAILDATE__',rd).replace('__EDUDATE__',json.load(open('data/edu.json'))['ref'] if os.path.exists('data/edu.json') else '')
  s=s.replace('__HAGDATE__',json.load(open('data/hagwon_grid.json'))['ref'] if os.path.exists('data/hagwon_grid.json') else '')
  s=s.replace('__SHOPDATE__',json.load(open('data/shop.json'))['ref'] if os.path.exists('data/shop.json') else '')
  s=s.replace('__SEOULYM__',json.load(open('data/flow.json'))['seoul'] if os.path.exists('data/flow.json') else '')
  bi0=json.load(open('bld/index.json')) if os.path.exists('bld/index.json') else {}
  s=s.replace('__BLDDATE__',bi0.get('ref',''))
  _a=json.load(open('data/apt.json')) if os.path.exists('data/apt.json') else {'from':'','to':''}
  s=s.replace('__APTFROM__',(_a['from'][:4]+'.'+_a['from'][4:]) if _a['from'] else '').replace('__APTTO__',(_a['to'][:4]+'.'+_a['to'][4:]) if _a['to'] else '')
  s=s.replace('__BUSDATE__',json.load(open('data/bus/index.json'))['ref'] if os.path.exists('data/bus/index.json') else '')
  return s
s=R(open('index.tpl.html').read())
open('old.html','w').write(s)
if os.path.exists('ml.tpl.html'): s=R(open('ml.tpl.html').read())
open('index.html','w').write(s)
open('ml.html','w').write('<!DOCTYPE html><meta charset="utf-8"><title>사이버 임장지도</title><script>location.replace("index.html"+location.search+location.hash)</script><a href="index.html">사이버 임장지도로 이동</a>')
print('index.html(새 지도)',len(s),'old.html(이전 지도)')

if os.path.exists('bld.tpl.html'):
    b=open('bld.tpl.html').read()
    bi=json.load(open('bld/index.json')) if os.path.exists('bld/index.json') else {}
    rr=json.load(open('data/roads_big.json'))['ref'] if os.path.exists('data/roads_big.json') else ''
    open('bld.html','w').write(b.replace('__BLDDATE__',bi.get('ref','')).replace('__ROADDATE__',f'{rr[:4]}년 {int(rr[5:7])}월 {int(rr[8:10])}일 배포판' if rr else ''))

