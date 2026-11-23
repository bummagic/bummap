import zipfile,io,csv,sys,collections
z=zipfile.ZipFile(sys.argv[1])
from regions import SHORT as KEEP  # 대상 시도 — regions.py
L0,O0,DL,DO=33.0,124.5,0.00225,0.0028
C=collections.defaultdict(collections.Counter); D=collections.defaultdict(collections.Counter)
big=collections.Counter(); n=0
for nm in z.namelist():
    if not any('_'+k+'_' in nm for k in KEEP): continue
    r=csv.reader(io.TextIOWrapper(z.open(nm),encoding='utf-8-sig')); h=next(r)
    ib,im,ilo,ila,idn=h.index('상권업종대분류코드'),h.index('상권업종중분류코드'),h.index('경도'),h.index('위도'),h.index('행정동명')
    for row in r:
        try: lo=float(row[ilo]); la=float(row[ila])
        except: continue
        k=(int((lo-O0)/DO),int((la-L0)/DL)); b=row[ib]
        C[k][b]+=1; C[k]['T']+=1; D[k][row[idn]]+=1; big[b]+=1; n+=1
        if b=='I2' and row[im] in ('I211','I212'): C[k]['cafe']+=1  # 확인용
print('stores',n,'cells',len(C),big.most_common(),file=sys.stderr)
with open(sys.argv[2],'w') as f:
    for k,c in C.items():
        f.write('%d\t%d\t%s\t%s\n'%(k[0],k[1],','.join('%s:%d'%x for x in c.items()),D[k].most_common(1)[0][0]))
