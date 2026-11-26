# 사이버 임장지도 (구 전국 규제지역·철도·고속도로 지도) — 정기 업데이트 런북

대상 아티팩트: slug `debdbe3c-466e-42f4-b2ed-73ea93bf6edc` (https://claude.ai/artifact/UWHvcGvhKkYKYSgm6baSGB)
파이프라인 파일은 이 프로젝트의 `kr-map/` 문서에 있다: README.md, index.tpl.html, gen.py, build_rail.py, build_hwy.py, build_edu.py, build_hagwon.py, build_pop.py, build_bld.py, build_road.py, build_shop.py, build_shop_zone.py, shop_extract.py, bld.tpl.html, osm_raw.json, muninames_kr.json, overpass_hwy.js, CHANGELOG.md

## 작업 폴더 준비 (매번 새 세션)
1. `mkdir -p ~/krmap/data && cd ~/krmap`
2. Projects 도구로 `kr-map/` 문서 9개를 읽어 같은 이름의 파일로 저장 (index.tpl.html, gen.py, build_rail.py, build_hwy.py, osm_raw.json, muninames_kr.json, overpass_hwy.js, README.md, CHANGELOG.md).
   - Projects 도구를 쓸 수 없으면 같은 파일이 아티팩트의 `pipeline/` 폴더에도 있다: `read_file(slug, paths=["pipeline/index.tpl.html", "pipeline/gen.py.txt", "pipeline/build_rail.py.txt", "pipeline/build_hwy.py.txt", "pipeline/osm_raw.json", "pipeline/muninames_kr.json", "pipeline/overpass_hwy.js.txt", "pipeline/CHANGELOG.md"])` 후 `.txt`를 뗀 이름으로 저장.
   - 템플릿·스크립트·CHANGELOG를 고치면 프로젝트 문서와 아티팩트 `pipeline/`(같은 publish_files 호출에 포함) 양쪽을 갱신한다.
3. 아티팩트 현재 데이터 받기: `mcp__claude-artifacts__read_file(slug, paths=["data/hwy.json"])` → `data/hwy.json`에 저장. (sub.json·terrain.json·water.json은 다시 만들지 않으므로 받지 않아도 된다. 게시는 patch 모드라 그대로 유지된다.)
4. `git clone --depth 1 https://github.com/plazalabs/kr-rail-map.git` (GitHub는 컨테이너에서 접근 가능)

## A. 규제지역 (매월)
- WebSearch로 최근 소식 확인: "조정대상지역 지정 해제", "투기과열지구 지정", "토지거래허가구역 연장 해제", "부동산 대책" (최근 한 달). 국토교통부·정책브리핑·주요 언론으로 교차 확인.
- 특히 서울 25개구+경기 12곳 토지거래허가구역은 **2026.12.31 만료**, 12월 중 연장 여부 결정 예정 → 결정 내용을 반드시 반영.
- 바뀐 것이 있으면 **ml.tpl.html(새 지도 = index.html)과 index.tpl.html(이전 지도 = old.html) 두 템플릿을 똑같이** 고친다:
  - 지역 코드 배열(2013 통계청 시군구 코드 5자리 / 읍면동 7자리): `A12`(경기 3중규제 12곳), `B5`·`DT`(2026.7.1 신규: 화성 동탄구·용인 기흥구·구리시), `W5`·`BJ`(지정 거론), `FX`(외국인 토허 제외), `OLD4`(10·15 이전부터 지정된 강남·서초·송파·용산). 서울(11xxx)은 전체가 A로 처리됨(`cat` 함수).
  - 패널 문구: `const DESC`의 A/B/W 설명, 범례 `<small>` 문구, 상단 "2026년 11월 17일 기준" 날짜와 요약 수치, 하단 출처 링크.
  - 시군구 코드는 muninames_kr.json에서 이름으로 찾는다.
- 바뀐 것이 없으면 두 템플릿의 상단 "기준" 날짜만 이번 확인 날짜로 갱신.

## B. 철도 (매월)
- `python3 build_rail.py` → data/rail.json, data/stations.json (kr-rail-map 최신 + osm_raw.json 수도권 공사·계획 노선)
- build_rail.py의 `META`(공사·계획 노선 개통 목표 문구)는 최근 보도로 점검해 바뀐 것만 고친다(예: 개통 연기, 착공, 개통 완료 → 개통이면 META에서 빼고 kr-rail-map open 노선으로 들어오는지 확인).

## C. 고속도로 (반기: 1월·7월, 내장 브라우저 필요)
- 사용자 PC 내장 브라우저에서 `https://maps.mail.ru/osm/tools/overpass/api/status` 탭을 연다(사이트 승인 필요할 수 있음).
- overpass_hwy.js 내용을 javascript_tool로 실행 → 30~60초 간격으로 `JSON.stringify(KRH.status())` 확인(수 분~수십 분). done이면 `KRH.chunks[i]`를 순서대로 받아 그대로 이어 붙여 `hw.raw`에 저장(JSON 문자열 이스케이프 상태 그대로).
- `python3 build_hwy.py` → data/hwy.json. 노선 수가 기존(50)보다 크게 줄면 실패로 보고 기존 hwy.json 유지.
- 성공하면 D단계에서 `HWYDATE="YYYY년 M월 D일 조회"`로 gen.py를 실행하고 data/hwy.json도 함께 게시한다.
- 브라우저에 연결할 수 없으면 C는 건너뛰고 보고.

## E. 학교 (반기: 1월·7월, 내장 브라우저 + PC '다운로드' 폴더 접근 필요)
- 초·중·고: 내장 브라우저에서 `https://www.data.go.kr/data/15021148/standard.do` 열고 javascript_tool로 페이지 자체 함수 사용:
  `const m=new StdDownloadManager();const h=await m.getHeader('JSON');const p=m.preProcessDataParam(h);let all=[];for(let c=1;c<=Math.ceil(p.totalCount/p.perPage);c++){p.page=c;all=all.concat(await m.getData(p))}`
  → 주소 첫 단어가 서울특별시·경기도·인천광역시·대전광역시·세종특별자치시·충청북도·충청남도·전북특별자치도인 행만 `이름(학교급 접미사는 ~로),유형,위도×1e5,경도×1e5` 줄로 만든다. 유형 = e/m/h + (사립 s, 국립 n) + (분교 b). 데이터기준일자(REFERENCE_DATE)도 기록.
  → Blob 다운로드(a.download)로 PC 다운로드 폴더에 저장 → device_bash로 `~/mnt/Downloads`에서 최신 `.tmp`/파일 확인 → device_stage_files → `raw/schools_raw.txt`.
- 대학: maps.mail.ru Overpass 탭에서 `[out:json][timeout:180];(nwr["amenity"~"^(university|college)$"](35.25,125.8,38.4,129.0););out center tags;` → `이름\t종류\t위도×1e5\t경도×1e5` 줄로 같은 방식 저장 → `raw/uni_osm.txt`.
- `EDUDATE=YYYY-MM-DD python3 build_edu.py data/sub.json` (sub.json은 아티팩트에서 read_file) → data/edu.json. 학교 6,000개·대학 250개 이상이면 게시(data/edu.json 포함).
- 사용자 PC가 꺼져 있거나 폴더 접근이 없으면 E는 건너뛰고 보고.

## F. 학원 (분기: 상가(상권)정보는 분기마다 갱신 — 1·4·7·10월 반기 작업 때 함께, PC 필요)
- 원본: 공공데이터포털 '소상공인시장진흥공단_상가(상권)정보'(data.go.kr/data/15083033) ZIP(약 350MB, 시도별 CSV). 다운로드에 로그인이 필요하고 용량이 커서 **사용자가 자기 크롬으로 받아 다운로드 폴더에 저장**하는 방식이 가장 확실하다. 자동 실행 시에는 다운로드 폴더에 더 새 ZIP이 있을 때만 진행하고, 없으면 사용자에게 받아 달라고 보고.
- device_bash로 다운로드 폴더에서 ZIP을 열어 서울·경기·인천·대전·세종·충북·충남·전북 CSV만 읽고, 상권업종소분류명이 입시·교과학원(a)·외국어학원(f)·음악/미술/태권도·무술/기타 예술·스포츠 교육기관(p)·컴퓨터/전문자격·고시학원(c)인 행만 `상호명(+지점명)\t분류\t위도e5\t경도e5\t건물명\t행정동명` 줄로 `hagwon_kr.txt`에 쓴다 → device_stage_files → `raw/hagwon_kr.txt`.
- `HAGDATE="YYYY년 M월" python3 build_hagwon.py` → data/hagwon_grid.json(250m 격자·학원가 이름표), data/hagwon_pts.json(개별 학원, 확대 시 지연 로딩). 행 80,000 이상이면 게시.
- 학년 구분·학원가 집계(2026-11-21): build_hagwon.py 끝에서 `hagwon_lv.py`가 자동 실행돼 hagwon_grid.json의 칸(g)에 [초등, 중등, 고등·입시, 학년 표시 없음] 4개 값을, 학원가(L)에 [입시·교과, 외국어, 예체능, 컴퓨터·자격, 초등, 중등, 고등, 표시 없음]을 덧붙인다(원본 raw 없이 `python3 hagwon_lv.py data/hagwon_grid.json data/hagwon_pts.json`로도 다시 만들 수 있음, 학원가 합계 불일치 0이어야 함). **상가(상권)정보와 나이스 학원교습소정보(분야·계열·교습과정 = 보습·논술·입시 등) 모두 대상 학년 항목이 없다** → 입시·교과·외국어 학원 이름에 초등·초중·키즈·주니어 / 중등·중학·초중·중고 / 고등·고교·중고·입시·수능·재수·대입·기숙이 있을 때만 학년으로 센다(2026년 9월 자료: 초등 498·중등 224·고등 2,062, 나머지 약 5만 곳은 표시 없음). 화면에는 반드시 '이름 기준'으로 적는다.
- 지도: 학원가 이름표 = 이름 + 입시·교과·외국어 수 두 줄(맨 위 레이어로 올려 먼저 자리 잡음), 누르면 종류·학년(이름 기준)별 수. 칸·개별 학원 정보창에도 학년. 단지 카드 '주변 학원'·관심 단지 비교 '학원 1km' = 단지에서 1km 안에 중심이 든 250m 칸 합계(대략값).

## G. 인구밀도·유동인구 (반기, PC 필요)
- 인구밀도: 공공데이터포털 'SGIS 격자 통계 및 경계'(data.go.kr/data/15141768, 반기 갱신, ZIP 약 100MB, 로그인 필요 → 사용자가 크롬으로 받아 다운로드 폴더에 저장). device_bash로 ZIP 안 `1. 통계/1. ... (인구)`·`2. ... (가구)`의 `*_1K.csv`(cp949; 기준연도,격자코드,통계항목,통계값)를 읽어 격자별 to_in_001(총인구), in_age_002~004 합(5~19세), to_ga_001(가구), ga_sd_005(1인가구)를 `코드\t총인구\t5~19세\t가구\t1인가구`로 `grid1k.txt`에 쓴다. 격자코드 '다사0038' = EPSG:5179 x=700000+100000×('가나다라마바사아' 첫 글자 순번)+앞 2자리 km, y=1300000+100000×(둘째 글자 순번)+뒤 2자리 km.
- 유동인구(서울): 서울 열린데이터광장 OA-14991 '행정동 단위 서울 생활인구(내국인)' 최신 월 ZIP(로그인 불필요, 사용자가 받아 둠) → 행정동코드(8자리)별 총생활인구수 평균, 9~18시 평균, 19~6시 평균을 `seoul_lp.txt`로.
- 경기도 '유동인구 행정동별 시간대별 집계'는 동 값이 시군구 값 복제라 쓰지 않는다. 행정동 경계는 GitHub vuski/admdongkor 최신 ver 폴더 geojson(컨테이너에서 git sparse checkout) → `raw/HangJeongDong.geojson`.
- `POPDATE="2024년" SEOULYM="YYYY년 M월" python3 build_pop.py data/sub.json` → data/pop.json, data/flow.json.

## H. 건물 2D·3D (분기 또는 요청 시, PC 필요)
- 원본: 브이월드 '공간정보 다운로드' > GIS건물통합정보 (`https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?svcCde=NA&dsId=18`, 로그인 필요 — 사용자가 내장 브라우저에서 로그인). 목록은 같은 주소에 `datPageIndex`·`datPageSize=100`을 POST해 읽고, 구분 '전체데이터'·기준일(매월 9일) 시도 파일의 `listFnc.download('20171128DS00010', 파일번호, 용량KB)`를 실행(confirm은 페이지에서 true로 바꿔 둠). 다운로드 폴더에 `AL_D010_{시도}_{기준일}.zip`으로 저장됨(경기 약 377MB도 2026-11에는 한 번에 받아짐). 대상 11·28·30·36·41·43·44·52.
- **원본에는 모양 없이 면적 0~수㎡ 점으로만 들어 있는 건물이 있다**(예: 금호동 래미안하이리버 101~108동 — 건축물대장 정보만 있고 도형 미작성). 8개 시도 약 19.6만 동, 그중 용도가 있는 것 약 4.6만 동. 이런 건물은 도로명주소 건물 도형으로 채운다:
  1. `python3 bld_degen.py /tmp/degen.json AL_D010_*.zip` → 점 건물 목록. 용도가 있는 것만 0.002° 칸으로 묶어(우선순위: 공동주택·3층↑·연면적 300㎡↑) 임시 브랜치 geo-tmp에 올림.
  2. 내장 브라우저를 `https://api.vworld.kr/` 탭에 두고(탭이 뒤에 있으면 타이머가 느려지므로 앞으로) vwkey.js를 fetch해 키를 쓰고, 칸마다 `/req/data?service=data&request=GetFeature&data=LT_C_SPBD&domain=bummagic.github.io&size=1000&geomFilter=BOX(...)`로 도로명주소 건물 도형을 받아, 점 건물이 안에 있거나 30m 안인 도형만 모은다(2026-11: 2.8만 칸, 23.9만 도형, 130ms 간격 9개 동시로 약 1시간). gzip 두 개로 나눠 다운로드.
  3. `python3 spbd_filter.py spbd_raw.json spbd_ok.json AL_D010_*.zip` → 이미 그려진 GIS 건물과 겹치는 도형 제외(2026-11: 6.1만 남음).
- `SPBD=spbd_ok.json BLDDATE=YYYY-MM-DD python3 build_bld.py bld AL_D010_*.zip` → bld/{z11묶음}.txt + bld/index.json. 여러 조각 건물은 가장 큰 링을 쓰고, 단순화로 면적이 20% 넘게 줄면 원본 유지. 점 건물은 같은 자리 도로명주소 도형으로 채우고 레코드 끝에 1을 붙여 정보창에 '도로명주소 건물 도형으로 채움'을 표시, 못 채운 점 건물은 버림.
- 메인 지도(index.html)·old.html·bld.html이 같은 bld/ 파일을 쓴다. GitHub 저장소에 커밋(파일 하나 100MB 미만).

## I. 도로 (반기: 1월·7월, PC 필요)
- 원본: 국토교통부 ITS 국가교통정보센터 '표준노드링크' 전국 SHP(https://www.its.go.kr/nodelink/nodelinkRef, 로그인 없이 받음). 내장 브라우저로 받으면 다운로드 폴더에 GUID .tmp로 저장될 수 있어 `ls -t`로 최신 파일 확인 → device_stage_files → `/tmp/nl`에 MOCT_LINK.* 압축 해제.
- `ROADDATE=YYYY-MM-DD python3 build_road.py /tmp/nl/MOCT_LINK data/sub.json` → data/roads_big.json(고속국도·도시고속 + 한 방향 4차로↑ = 왕복 8차선↑), data/roads_main.json(국도·시도·지방도 한 방향 2차로↑). 좌표계는 EPSG:5186(GRS80 TM 중부원점, FN 600000), 수도권·충청·전북만 남김.
- LANES는 링크(한 방향) 차로 수라 왕복 차선 = 2×LANES로 추정(일방통행·분리 구간은 오차 가능).

## J. 상권 (분기, F 학원 작업과 같은 ZIP 사용, PC 필요)
- 점포 밀집도: 다운로드 폴더의 `소상공인시장진흥공단_상가(상권)정보_YYYYMMDD.zip`을 device_bash에서 `python3 shop_extract.py <zip> shop_cells.txt`로 8개 시도 점포를 250m 칸(학원과 같은 격자)·업종 대분류(I2 음식, G2 소매, S2 개인서비스, Q1 보건의료, P1 교육, R1 예술·스포츠, I1 숙박, L1 부동산, M1 과학·기술, N1 시설관리·임대)별로 센다 → device_stage_files → `raw/shop_cells.txt` → `SHOPDATE="YYYY년 M월" python3 build_shop.py` → data/shop.json(칸 + 상권 이름표: 생활업종 40곳 이상 칸을 이어 붙이고 너무 큰 덩어리는 기준을 1.6배씩 올려 나눔, 합계 400곳 이상만).
- 상권 경계: ① 서울 열린데이터광장 OA-15560 '서울시 상권분석서비스(영역-상권)' ZIP(로그인 불필요, 페이지의 `downloadFile('5')`) → `raw/seoul.*`(EPSG:5181, UTF-8) ② 공공데이터포털 15090955 '소상공인시장진흥공단_주요상권현황'(로그인 불필요, 2024-01-01 기준 1회성, cp949, 좌표는 '경도,위도|…' 문자열) → `raw/major_zones.csv`. 내장 브라우저로 받으면 GUID .tmp로 저장됨. `SEOULZONE="2023년 10월 파일" python3 build_shop_zone.py` → data/shop_zone.json. 두 원본 모두 갱신이 드물어 새 파일이 올라왔을 때만 다시 만든다.

## K. 지도 페이지 구성 (2026-11-19 MapLibre 전환 완료)
- `index.html` = 새 지도(MapLibre, 템플릿 `ml.tpl.html`). 모든 레이어: 규제지역·지형·강·경계·이름표, 철도·역(노선 목록)·역세권, 도로·고속도로, 학교·대학, 학원 밀집도·위치, 인구밀도·유동인구, 상권 밀집도·경계, 정비사업, 건물 2D·3D(용도·연식 색), 배경 단색·일반·위성(위성 3D = 브이월드 실사, v3d.html).
- `old.html` = 이전 D3 지도(템플릿 `index.tpl.html`, 같은 데이터로 계속 생성). `ml.html` = index.html로 넘겨 주는 페이지(예전 링크용).
- gen.py 한 번으로 index.html·old.html·ml.html·bld.html을 모두 만든다. 글자는 Hangul만 브라우저 글꼴로 그리고, 숫자·영문은 `fonts/Noto Sans Regular|Medium/{범위}.pbf`(protomaps/basemaps-assets, OFL).
- 칸·면 레이어(인구·유동·상권·학원·정비구역)와 학교·도로는 켤 때 data/*.json을 불러온다. 기존 지도의 확대 배율 k는 `zk(k)=Z0+log2(k)`(Z0=전국 맞춤 줌)로 환산해 표시 기준을 맞춘다.
- 브이월드 키: 브라우저에 저장한 키가 먼저, 없으면 저장소 루트 `vwkey.js`(GitHub에만, 프로젝트 문서에는 넣지 않음).
- 정비사업(L. 반기 또는 요청 시, PC 다운로드 폴더 필요): ① 서울 경계 = 서울열린데이터광장 OA-22712 '서울시 도시계획사업 현황(서울플랜+) 공간정보'. 내장 브라우저로 https://datafile.seoul.go.kr/ 탭을 열고 `fetch('/bigfile/iot/inf/nio_download.do?&useCache=false',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'infId=OA-22712&seqNo=&seq=5&infSeq=1'})` → Blob 다운로드(seq는 데이터셋 페이지 downloadFile(n)의 최신 번호). ② 전국 목록 = 공공데이터포털 15160169 '전국 도시정비사업 통합 데이터' CSV(로그인 불필요; 페이지에서 `/tcs/dss/selectFileDataDownload.do?recommendDataYn=Y&publicDataPk=15160169&publicDataDetailPk=<uddi>` → atchFileId → `/cmm/cmm/check-limit.json` POST → `/cmm/cmm/fileDownload.do?atchFileId=..&fileDetailSn=1`). 다운로드 폴더에 GUID .tmp로 저장됨 → device_stage_files → ZIP 안 SHP(EPSG:5174) 추출 → `JBDATE="YYYY년 M월" JBNDATE=YYYY-MM-DD python3 build_jeongbi.py <SHP 경로(확장자 제외)> <national.csv> muninames_kr.json` → data/jeongbi.json(서울 경계, 지도에서 켤 때 불러옴), data/jeongbi_n.json(서울 밖 시군구별 목록, 동 정보창에 표시). 전국 경계는 브이월드 dsId=30335(로그인 필요)라 아직 미포함.
- 기존 지도의 확대 배율 k는 `zk(k)=Z0+log2(k)`(Z0=전국 맞춤 줌)로 환산해 표시 기준을 맞춘다.

## I-2. 모든 도로 (데이터 갱신 없음, 2026-11-22)
- '교통·역세권'의 '모든 도로 (OpenStreetMap)'와 빠른 켜기 '도로' 단추. 켤 때 OpenFreeMap 벡터 타일(`https://tiles.openfreemap.org/planet`, OpenMapTiles 스키마, 키·가입 없음, 매주 갱신)을 원본으로 붙이고 화면에 보이는 타일만 받는다 → 저장소에 자료를 넣지 않음. source-layer `transportation`(class: motorway·trunk·primary·secondary·tertiary·minor·service·track·path·pedestrian)·`transportation_name`(name:ko/name).
- 레이어 osrc(테두리)·osr(면)는 국토부 도로(rdm) 아래, 이름 osrn은 역(stc) 아래. 보기: 골목길까지 전부(기본) / 간선+보조간선·집산 / 간선만 / 보행로까지. 노란 길 = motorway·trunk·primary. 누르면 이름·종류·다리/터널·일방통행(차선 수는 없음 → 국토부 도로 레이어). 출처 표시: © OpenFreeMap · OpenMapTiles · OpenStreetMap contributors.
- 컨테이너에서는 tiles.openfreemap.org에 닿지 않으므로, 시험할 때는 국토부 도로 자료로 같은 스키마의 가짜 타일을 만들어 Playwright route로 응답한다.
- MapLibre 4.7은 line-dasharray에 데이터 식(case·match)을 못 써서 레이어 추가가 조용히 실패한다 → 쓰지 않음.

## M. 버스정류장 (연 1회, 원본이 11월경 갱신, PC 다운로드 폴더 필요)
- 원본: 공공데이터포털 15067528 '국토교통부_전국 버스정류장 위치정보'(CSV 약 22MB, 로그인 불필요, TAGO 연계 지자체 BIS 수집일 기준 연 1회). 내장 브라우저로 데이터 페이지를 열고 `fn_fileDataDown` 버튼의 uddi로 `/tcs/dss/selectFileDataDownload.do` → `/cmm/cmm/check-limit.json` → `/cmm/cmm/fileDownload.do`를 fetch, 페이지 안에서 도시명이 서울·경기·인천·대전·세종·충청북도·충청남도·전라북도(전북)인 행만 `정류장명\t위도\t경도\t모바일단축번호\t도시명\t정류장번호`로 골라 gzip Blob으로 다운로드(`krmap_busstop_8.tsv.gz`, 22MB 원본을 그대로 받으면 다운로드 폴더에 남지 않는 경우가 있었음).
- `BUSDATE=YYYY-MM-DD(정보수집일) python3 build_bus.py krmap_busstop_8.tsv.gz` → data/bus/{위도×10}_{경도×10}.json(0.1° 칸, 2026-11-09 기준 447칸 11.8만 곳) + data/bus/index.json. 지도는 확대(z14↑)했을 때 화면 안 칸만 불러온다. 10만 곳 미만이면 기존 유지.

## N. 아파트 실거래가 (매월 권장, 내장 브라우저 + PC 다운로드 폴더 필요)
- 원본: 국토교통부 아파트 매매 실거래가 상세(`RTMSDataSvcAptTradeDev`)·전월세(`RTMSDataSvcAptRent`) 오픈API(공공데이터포털, 사용자 인증키). **인증키는 저장소·페이지·프로젝트 문서 어디에도 쓰지 않는다** — 수집할 때 사용자에게 받아 브라우저 안에서만 쓴다. 컨테이너·PC 셸에서는 apis.data.go.kr에 닿지 않으므로 내장 브라우저 탭을 `https://apis.data.go.kr/`에 열어 같은 출처 fetch로 받는다.
- 대상 시군구: 행정동 경계(vuski/admdongkor 최신판)의 sgg 코드 중 11·28·30·36·41·43·44·52 (2026-11 기준 134개 + 화성 옛 코드 41590). 최근 12개월 × 매매·전월세. 초당 호출 제한(429)이 있으므로 3개 동시·호출 간격 260ms 이상, 429면 3초 쉬고 재시도. 해제 거래(cdealType=O) 제외. 2026-11 수집: 매매 32.4만·전월세 73.9만 건, 약 50분.
- 페이지 안에서 `{T,M}`·`{R,M}`을 gzip Blob으로 다운로드(`krmap_rt_T.json.gz`·`krmap_rt_R.json.gz`, XML 문서 페이지라 a 요소는 `createElementNS('http://www.w3.org/1999/xhtml','a')`) → device_stage_files.
- 위치: 실거래 자료에 좌표가 없다. ① `python3 build_bld_addr.py ../bld /tmp/bld_addr.json`(건물자료의 '시도|시군구|동리|지번' → 건물 중심, 경기 제외) ② 못 찾은 주소(경기 대부분)는 브이월드 지오코더(`api.vworld.kr/req/address`, type=PARCEL, 브이월드 탭에서 vwkey.js를 fetch해 키를 씀)로 찾아 `{주소:[lon,lat]}`를 다운로드 → geo_extra.json. 주소 목록은 공개 주소뿐이라 임시 브랜치(geo-tmp)에 올려 raw.githubusercontent.com에서 브라우저로 읽는다. 브이월드는 6개 동시·무지연으로 돌리면 IP가 몇 분 막힌다 → 3개 동시·400ms 간격. 건물 매칭 검증(지오코더 대비 120곳): 중앙값 15m, 90% 70m, 최대 160m.
- `APTDATE=YYYY-MM-DD python3 build_apt.py rt_raw.json.gz bld_addr.json sgg_codes.json geo_extra.json ../data/apt.json [unmatched.json]` → data/apt.json(단지: 이름·좌표·준공연도·시군구코드·동 지번·평당가(전용 3.3㎡, 최근 6개월 매매 중앙값, 없으면 12개월)·12개월 매매 수·전세가율(같은 면적끼리 전세 중앙값÷매매 중앙값, 건수 가중)·최근 3개월 변동(평당가 중앙값, 7~12개월 전 대비, 최근 3개월 2건 이상일 때)·전세·월세 수·면적별 [전용㎡, 최근 매매가, 날짜, 층, 전세 중앙값, 전세 수, 매매 수, 최근 월세 보증금, 월세]). gen.py가 기간(__APTFROM__·__APTTO__)을 채운다.

### N-1. 실거래가 매일 자동 갱신(GitHub Actions `.github/workflows/apt.yml`, 2026-11-27~)
- 매일 05:23(KST) `pipeline/update_apt.py`가 돈다. **저장소 Secret `DATA_GO_KR_KEY`**(공공데이터포털 인코딩 키, 활용신청: 아파트 매매 실거래가 상세·아파트 전월세 실거래가)가 있어야 한다. 키는 Secret에만 두고 파일·문서에 쓰지 않는다.
- 원본 월 묶음(`T_YYYYMM.json.gz`·`R_YYYYMM.json.gz`)은 저장소가 아니라 Actions 캐시(`rtcache`)에 둔다. 최근 3개월은 매일 다시 받고(신고 30일·해제 반영), 36개월까지 빈 달은 API별 하루 9,500회 안에서 최근 달부터 채운다(처음 한두 날). 캐시가 지워지면 다시 채운다.
- 최근 12개월이 다 모이면 `build_apt.py`로 `data/apt.json`(한 줄에 한 단지 — git이 바뀐 줄만 저장)과 **`data/apt_h/<시군구코드>.json`**(전체 기간 면적별 월별 [월 번호, 매매 중앙값(만원), 건수]·전세 같은 꼴, 키 "동 지번|단지명")을 만든다. 12개월이 덜 모였으면 빌드하지 않는다(지도 자료가 줄지 않게).
- 위치: `pipeline/apt_loc.json`("시군구코드|동 지번" → [lon,lat], 기존 apt.json에서 만듦). 새 단지는 브이월드 지오코더(PARCEL, vwkey.js의 키, 시군구 이름은 `pipeline/sgg_names.json`)로 찾아 보탠다(하루 600곳까지, 실패하면 다음 날 다시).
- 관심 단지 알림(선택): Secret `WATCH_KEYS`(지도 아파트 탭 '즐겨찾는 단지 → 알림 목록 복사' 내용: 줄마다 `시군구코드|동 지번|단지명`), `TELEGRAM_TOKEN`(텔레그램 @BotFather로 만든 봇 토큰), `TELEGRAM_CHAT`(내 대화방 번호: 봇에게 아무 말을 보낸 뒤 `https://api.telegram.org/bot<토큰>/getUpdates`의 chat.id). 다시 받은 달에 새로 생긴 매매가 있으면 보낸다.
- 화면: 지도 문구의 실거래 기간은 apt.json의 from·to·ref를 읽어 표시. 단지 카드 '면적별 흐름'(최대 36개월, 면적 고르기), 즐겨찾기 비교 그림 '최대 3년 · 대표 면적'.
- 시험: `RTDIR=<원본 폴더> APT_DRY=1 python3 pipeline/update_apt.py`(받기 없이 캐시만으로 빌드).

## O. 호재 역 (철도 B와 함께 매월)
- `FUTDATE=YYYY-MM-DD python3 build_future.py data/rail.json future_st_osm.json data/future.json kr-rail-map/data` → data/future.json: kr-rail-map 역 중 공사·계획·제안 노선이 지나는 역(기존 운행역에 새 노선이 들어오는 경우 포함) + OSM 공사·계획 역(Overpass: railway=construction+construction=station, construction:railway=station, railway=proposed+proposed=station, proposed:railway=station 등, overpass-api.de를 내장 브라우저에서 fetch) 중 250m 안 중복 제외. 2026-11: 247곳. 신안산선·대장홍대선·9호선 4단계·7호선 청라·옥정포천선 역은 아직 일부만 있음.
- 지도: '공사 중'·'계획' 체크 시 주황/보라 테 동그라미, 아파트 정보창 '호재 역', 아파트 색 기준 '호재 역 거리', 보기 '호재 역 1km 안', 후보지 찾기·내 조건으로 아파트 찾기의 호재 역 조건.

## O-2. 호재 점수·개통 연도 (호재 역 O와 함께, 노선 소식이 바뀌면)
- build_future.py의 `YR`(노선 이름 → (개통 목표 연도, 근거 문구))를 최근 보도로 점검해 고친다. 0 = 미정·구상. future.json 역마다 [8] 가장 이른 개통 목표 연도 [9] 노선 무게(GTX 1·경전철 0.5·그 밖 0.7) [10] 근거 [11] 그 노선 이름이 붙는다. 철도 정보창 문구는 build_rail.py META(rail.json 'i')를 같이 고친다.
- 지도(ml.tpl.html aptLoad): 단지마다 1.5km 안 호재 역으로 호재 점수(0~100, 이 지도 자체 기준) = 역마다 거리(500m 1·1km 0.6·1.5km 0.3) × 개통 시기(2년 안 1·5년 안 0.7·10년 안 0.4·그 밖·미정 0.2) × 노선 무게 × (기존 운행역이면 0.8), 역 이름별 가장 큰 값 하나 + 다음 두 역 0.3배씩, 100에서 자름. 1km 안 가장 이른 개통 연도(a.fy)로 '2028·2031년까지 개통할 역 1km 안' 보기·추천 조건.
- 2026-11-22 확인: GTX-A 서울역~수서 2027 상반기(삼성 무정차), 동북선 2027.11, 신안산선 2028 하반기, 7호선 청라 2031 상반기 전망(당초 2027).

## P. 단지 검색·추천·거리 재기 (데이터 갱신 없음)
- 검색창에 두 글자 이상 치면 apt.json 단지 이름 후보가 붙는다(최대 15개). '내 조건으로 아파트 찾기': 목적(매매/전세/갭), 예산, 면적, 지역, 역·호재 역 거리, 준공 연수, 정렬 → 면적별 최근 매매가·전세 중앙값으로 맞는 단지 100곳까지 목록·지도 표시. '📏 거리' 버튼: 점을 차례로 눌러 직선거리 합계.
- 단지 정보창: 가까운 역·호재 역·초등학교 직선거리, 월별 평당 매매·전세 중앙값 그림(apt.json 13번째 값, `m`에 월 목록).
- 관심 단지 비교('내 장소' 탭 아래, 2026-11-21): 저장한 곳 중 apt.json 단지와 좌표가 같거나(±2e-5°) 같은 이름으로 300m 안인 곳을 2~4곳 골라 표로 비교. 행 = 면적·최근 매매·전세 중앙값·갭(최근 매매−전세 중앙값)·전세가율·3.3㎡당·3개월 변동·가까운 역·호재 역(3km 안)·준공·12개월 거래. 비교 면적은 고른 면적대(전체면 84㎡에 가장 가까운 것) 중 거래 많은 면적 하나로 매매·전세를 함께 봄. 고른 단지는 localStorage 'krmap_cmp'(좌표 키), 단지 카드에서 저장하면 4곳 미만일 때 자동으로 비교에 들어가고 '관심 단지 비교' 단추가 생김. apt.json을 쓰므로 데이터 갱신 없음, 탭을 열 때 불러옴.

## P-2. 임장 코스 자동 재생 (데이터 갱신 없음, 2026-11-22)
- 단지 카드 '▶ 임장 코스': 동네(z13) → 단지(z16.6, 기울여 천천히 돌기, 최근 매매·전세·전세가율) → 가까운 역(3km 안) → 초등학교(2km 안) → 호재 역(호재 점수 상위 2곳, 같은 자리 중복 제외) → 정리(전체 경로가 보이게, 호재 점수·거리·거래 수 + 출처 한 줄) 순서로 자막과 함께 자동 이동. 역·학교·호재 역은 먼저 단지와 이은 노란 점선이 보이게 두 점을 맞춘 뒤 내려앉음.
- 재생 중에는 검색·버튼·패널·카드·지역 말풍선을 숨기고(body.touring) 지도·단지 가격표·자막·출처 표시만 남김 → 화면 녹화로 임장 영상을 만들 수 있게. 오른쪽 위 작은 막대(일시정지·다음·끝내기), 키보드 Space·→·Esc. 단색·일반지도에서 건물이 켜져 있으면 3D로 바꿨다가 끝나면 되돌림(위성은 실사 3D 창을 띄우지 않고 기울인 2D).
- 거리는 단지 중심 직선거리. 걸어서 걸리는 시간은 `wmin(dk)` = 직선 km × 1.2(실제 걷는 길 보정) × 15분(시속 4km) → 직선 1km ≈ 18분, 2.5km 넘으면 표시 안 함. 단지 카드(가까운 역·초등학교·기차역·버스터미널), 임장 코스 자막('실제 길로 약 …'), 통근 추정의 걷기 구간, 역세권 범례가 같은 값을 씀. 1.2배는 지도 앱 도보 경로와 직선을 비교한 사례(직선 870m→도보 1,045m, 750m→900m대)에서 잡은 대략값. 자막의 값은 apt.json·future.json·edu.json에서 그대로 가져옴.

- (2026-11-22 추가) 시작 전 설정창 tourStart → tourRun(i, O). O = {pill, base(-1 그대로·0·1·2), b3, dem, sky, sp(0.7·1·1.4 = 기다림 배수), g{by,st,el,shop,life,fut}}. 장면은 st.push 때 붙는 g로 거름. b3면 bOn·mode3를 켜고 b3를 용도 색(col)으로, b3h(같은 동·지번 또는 이름 포함 공동주택)를 주황으로, 단계마다 bPre(목적지 z13 타일 3×3 미리 받기). dem면 raster-dem 'dem'(AWS terrarium) setTerrain 1.5배, sky면 setSky. 숨긴 레이어(me.hid)·배경·건물·3D 상태는 tourEnd에서 복구.

## P-3. 지하철 없는 시: 기차역·버스터미널 거리 (2026-11-22)
- 단지가 있는 시(광역·특별자치시는 시 전체, 구가 있는 시는 시 단위)에 운행 중인 전철·도시철도 역(rail.json k='m')이 하나도 없으면, 단지 카드·임장 코스·관심 단지 비교('역·터미널' 행)·내 조건 찾기 목록에서 '가까운 역' 대신 **가까운 기차역**(KTX·일반철도 운행역)과 **버스터미널**까지 직선거리를 보여 준다. 지하철 있는 시의 '가까운 역'은 전철·도시철도 역만으로 계산.
- 2026-11 기준 지하철 없는 곳: 세종, 충북 전체, 충남 대부분(천안·아산 제외), 전북 전체, 경기 일부(여주·안성·포천 대부분·이천 등).
- 버스터미널: data/terminal.json `{ref, t:[[이름, 위도, 경도]]}` 211곳. OpenStreetMap amenity=bus_station 중 이름에 '터미널'이 있는 곳(폐쇄·임시·승하차장·매표소·리무진·도심공항·시내버스터미널 제외, 같은 이름 1.5km·다른 이름 120m 안 중복 제거). 내장 브라우저에서 Overpass(maps.mail.ru 미러) `nwr["amenity"="bus_station"](35.25,125.8,38.4,129.0);out center tags;` → 걸러서 Blob 다운로드. 전국 터미널 좌표를 주는 공식 파일 자료는 2026-11 기준 찾지 못함(지자체별 파일만 있음). 반기마다 철도 B와 함께 갱신 권장.
- stations.json에 일반철도역(k='rail', 210곳)이 들어오도록 build_rail.py를 다시 돌림(1,014 → 1,229곳). 일반철도역은 지도에서 '일반철도' 체크를 따름. 역 순번이 바뀌므로 build_commute.py도 함께 다시 돌림(commute.json은 stations.json 순번 기준).

## Q. 화면 틀(디자인) 규칙 (2026-11-21 다시 씀, ml.tpl.html의 <style> 한 덩어리)
- 원칙: 지도가 주인공. 틀(단추·패널·카드)은 먹색(--ink)·종이색(--panel)만 쓰고 색은 지도 자료(가격 단계·규제·노선)에만 쓴다. 켜고 끄는 단추는 켜지면 먹색 바탕(button.on), 여럿 중 하나를 고르는 묶음(.seg)은 옅은 바탕 + 굵은 글씨. 글꼴은 지도 이름표와 같은 Noto Sans KR.
- 아이콘은 그림 글자(emoji) 대신 body 맨 위 SVG 묶음(symbol id="i-…")을 `<svg class="ic"><use href="#i-…"/></svg>`로 쓴다.
- 지도 위 배치: 왼쪽 위 = 검색(.find) + 지금 지역(.where, 누르면 지역 이동 목록), 그 아래 시세 줄(.abar: '아파트 시세' 켜기 → 매매/전세/평당가/전세가율/변동, 면적), 오른쪽 위 = 배경·건물·2D/3D(.mopt; 화면 너비 1280px 이하에서는 빠른 켜기 맨 위 '지도' 단추의 팝업), 오른쪽 = 빠른 켜기(.rail: 호재역·역세권·학교·학원·정비·버스), 오른쪽 아래 = 내 위치·거리·확대(.zoom), 왼쪽 아래 = 가격 색 범례(.mlg), 왼쪽 위에서 아래로 = 정보 카드(.card; 좁은 화면은 아래 시트). 오른쪽 패널 탭 5개(지도·아파트·후보지·내 장소·안내), 900px 이하는 아래 탭 + 올라오는 패널.
- 시세 표시 단계(aptTier): z<8.3 시도 → z<10.8 시군구 → z<13.4 동(지역 중앙값 말풍선 .rpl; 매매·전세는 고른 면적대만 모음, 전체면 84㎡ 안팎) → z<14.8 단지 점 → 그 위는 단지 가격표(.pill, 겹치면 거래 많은 단지 먼저, 고른 단지는 테두리). 가격 색 단계(APC)는 흰 글자가 읽히는 색만 쓴다. 시세를 켜면 건물은 옅은 회색(건물 색 기준 '용도별 (시세를 켜면 옅게)').
- 지도 정리: 규제지역 면은 확대할수록 옅게(zfo), 역세권 원은 z12.6부터, 지역 말풍선이 떠 있는 동안 같은 단계 지도 이름표는 숨김, 표시 기준 줌(zk)은 좁은 화면에서도 6.1을 바닥으로 계산.
- 보조지표·순위(2026-11-22, 리치고 참고): 시세 막대 끝 '지표 더보기'(#abX 팝업, 키 gap·pj·g6·g12 + y·s·f·h)와 빠른 켜기 맨 위 '순위'(#rank, _rkDraw가 moveend·지표 변경 때 aptVis에서 화면 안 단지를 줄 세움, 변동 지표는 12개월 매매 3건+). g6·g12·pj는 aptLoad에서 a[13] 월별 값(월별 3.3㎡당 중앙값을 거래 수 가중 평균, 앞뒤 3개월 묶음 매매 각 2건+)으로 계산 → 자료 파일 변경 없음. 임장 코스 재생 중에는 둘 다 숨김.
- 그 밖: 단지 카드의 '내 장소에 저장', 시세 표시 상태 기억(localStorage 'krmap_ui'), Esc로 카드·팝업 닫기, 홈 화면에 추가용 파일(저장소 루트 manifest.json·icon.svg·icon-180/192/512.png — gen.py가 만들지 않는 고정 파일).

## R. 추가 지표·통근·시세 민감도 (2026-11-22)
- 지표 더보기(#abX)에 묶음 3개를 더함. 공통 정의는 ml.tpl.html의 `XM`(값·표시·색 단계·지역 말풍선 여부·순위 기본 정렬)에 있고 aptV·LBF·MLT·fmtV·범례·순위가 모두 이걸 씀. 새 지표는 XM과 #abX 단추, #aptc option 세 곳에 넣는다.
- 저평가·거래(apt.json만 사용, aptLoad에서 계산): 동네 대비 가격(nb, 1km 안·준공 ±10년 단지 3곳 이상의 3.3㎡당 중앙값 대비 %) · 입지·연식 대비 가격(lv, 같은 시군구 8단지 이상에서 입지 점수 = 역 거리 1·초등 거리 0.5·학원 1km(log) 0.7·호재 점수 0.5·연식 0.8 가중 표준점수 → 입지 백분위 − 가격 백분위, +면 입지에 비해 쌈) · 거래량 증감(vl, 신고가 다 찬 최근 3개월(수집 월 −1·−2·−3)의 월평균 ÷ 그 앞 달들 월평균, 합계 6건+) · 전세 6개월 변동(j6, g6와 같은 방식으로 전세).
- 통근(추정): `python3 pipeline/build_commute.py data/rail.json data/stations.json data/commute.json` → 역마다 강남·여의도·광화문·판교역까지 분. 운행 중 전철·도시철도·GTX·일반철도(KTX 제외) 선형을 따라가는 그래프(노선별 표정속도, 환승 5분, 첫 대기 4분, 같은 이름 노선은 역 목록 공유). 단지 값 = 2km 안 역 중 (직선 거리×15분 + 역 시간) 최솟값. 철도(B) 갱신 때 같이 다시 돌린다. 시간표·급행 반영 안 됨 → 화면에 '추정' 표시.
- 시세 민감도(지역): 한국부동산원 R-ONE 공표보고서 '전국주택가격동향조사(월간) 시계열 통계표'(https://www.reb.or.kr/r-one/portal/bbs/rpt/selectBulletinPage.do?bbCd=RPT&seq=3267, 매월 갱신, 로그인 불필요)의 '시계열(신).xlsx'(약 43MB, 다운로드는 `/r-one/portal/bbs/rpt/downloadAttachFile.do?fileSeq=…&seq=3267`) '매매_아파트'(rId11)·'전세_아파트'(rId15) 시트. 컨테이너에서는 reb.or.kr에 닿지 않으므로 내장 브라우저 탭에서 fetch → 페이지 안에서 zip(DecompressionStream deflate-raw)·시트 XML을 읽어 지역마다 [고점(2020.1~2022.12 최대)·저점(고점~2025.6 최소)·2019.1·최신, 전세도 같게, 2015~2026년 1월 값]을 계산한 줄(코드|이름|구|…27칸)만 꺼내 `pipeline/reb_sens.txt`로 저장(합계 검산). `python3 pipeline/build_sens.py pipeline/reb_sens.txt data/sens.json 2026.10` → data/sens.json. 지표: 지난 상승기 상승폭(sup)·하락기 하락폭(sdn)·하락 민감도(sbt = 지역 하락률 ÷ 전국 하락률)·전고점 대비 지금(svp). 단지는 시군구 코드로 연결(구 없으면 시, 군은 시도 평균, 2026년 새 인천 구는 옛 구: build_sens.py ALIAS). 단지 카드 '지역 시세 민감도'에 연도별 그림.
- 단지 카드: '한눈에'(강점·살필 점, aptSum의 기준은 이 지도 기준), 통근, 동네 대비, 입지·연식 대비, 초등학교까지 직선이 왕복 8차선 이상 큰길(roads_big.json c=x·8)을 건너는지(카드를 열 때 계산).
- 좁은 화면 순위 창은 높이 36%, 제목을 누르면 접힘. 통근·역 거리 지표는 순위 기본이 낮은 순.

## S. 도로 선형·이름 켜고 끄기·큰 상권 (2026-11-22 밤)
- 국토부 표준노드링크(rdb·rdm)와 고속도로(hwy, OSM 25~120m 단순화)는 개략선이라 동네 축척에서 배경지도와 어긋나 보임 → z12.4~13.4에서 서서히 사라지고(FAD), 같은 자리에 OpenFreeMap(OSM) 벡터 타일의 실제 선형(osxc 테두리·osx)을 그림. 고속도로 켜짐 = motorway, 국토부 도로 켜짐 = 보기에 따라 trunk(고속도로만)·trunk+primary(기본)·+secondary(주요도로 전체), 터널 제외. 누르면 여전히 국토부 차선 정보(투명해진 rdb·rdm이 클릭을 받음). 고속도로 노선 이름(hwn)은 z13까지만.
- 이름 표시 묶음(#lblG): 시도·시군구·동·역·호재 역·고속도로·도로·강호수·학교대학·학원가·상권·정비구역·버스정류장·내 장소·단지 이름(가격표)·위성 지명(브이월드 Hybrid) 켜고 끄기, 모두 켜기/끄기. 꺼 둔 레이어 id는 localStorage 'krmap_lbl'에 두고 `vis()`가 늘 숨김(LOFF). 새 이름 레이어를 만들면 체크박스 data-l에 id를 넣는다.
- 큰 상권까지 거리(cb): data/shop_big.json(상권 이름표 중 생활업종 1,000곳 이상, build_shop.py가 함께 만듦)에서 가장 가까운 곳. 지하철 없는 지역의 생활권 지표로 단지 카드·지표 더보기·비교표에.
- 관심 단지 비교표에 통근·큰 상권·동네 대비·입지·연식 대비·지역 하락기·전고점 대비·거래량 행, '내 조건으로 찾기'에 통근·저평가·민감도 조건과 정렬, 임장 코스 정리 자막에 강남 통근·지역 하락기.
- 미완: 호재 역 보강(신안산선·대장홍대선·9호선 4단계·7호선 청라·옥정포천선) — 2026-11-22 밤 Overpass(overpass-api.de 406, maps.mail.ru 504)가 응답하지 않아 다음에.

## I-3. 주요도로 그리기 (2026-11-22)
- 국토부 표준노드링크는 링크마다 LANES가 달라 '8차선 이상'·'4차선 이상'으로 고르면 같은 도로가 토막 나고, 일반시의 시내 큰길은 시군도(107)라 build_road.py에서 빠진다 → 화면의 도로 선은 OpenFreeMap transportation(motorway·trunk·primary·secondary, z7부터, 터널은 osxt 옅은 점선)으로 그리고, rdb의 '8'(왕복 8차선↑ 구간)·'x'(고속국도·도시고속)만 z13.4까지 덧칠, rdm은 투명(누르면 차선 정보용). roads_big.json은 큰길 건넘 판정(bigRoad)에도 계속 씀.

## T-3. 점수·내 조건·상급종합병원·실사 3D 임장 (2026-11-22)
- 객관 점수(scoreParts, 이 지도 기준 0~100): 교통 30(지하철 시: 역 거리 0.3→2km, 강남·여의도·광화문·판교 중 가장 짧은 통근 30→90분 / 지하철 없는 시: KTX역·터미널 차 10→40분) · 교육 20(초등 0.3→1.2km, 큰길 건너면 ×0.8, 학원 1km 로그 300곳=100) · 생활 20(500m 음식·소매·서비스 로그 600=100, 병원·약국 40곳=100, 상급종합병원 차 10→40분, 가장 가까운 공원 0.2→1km) · 단지 20(10대 건설사 100/40, 세대 규모 추정, 연식) · 환경 10(둘레 300m 고도차 10→50m, 공원).
- 내 조건 점수(subjOf): 가족 형태별 가중(FAM), 차량 없음이면 교통 ×1.3·있음 ×0.85, 직장을 넣으면 직장 점수(20→70분) 30% + 나머지 70%. 직장 시간: 차 있음 = OSRM, 없음 = data/rgraph.json(build_commute.py가 함께 만드는 역×노선 축약 그래프, 2km 안 역 걷기 포함). 직장 위치는 검색 목록(역·동·대학·단지)에서 찾음.
- data/bighosp.json = 보건복지부 제5기 상급종합병원(2024.1.1~2026.12.31) 47곳 중 수록 8개 시도 29곳, 좌표는 OSM(건양대병원은 브이월드 주소 검색). 2027년 제6기 지정(2026년 12월 발표 예정) 뒤 갱신.
- 임장 코스 tourRun: ① 구름 '준비' 화면에서 bydsOf·kxRoute·bigHosp·shopNear·lifeScan·상권 도로 이름·점수·3D 건물(bPre, 장면 지점 전부)을 미리 받음 ② 장면 = 시작(z15.8)·단지·점수·브역대신평초·역/KTX·초등·상권·상급종합병원(10km 안, 없으면 1km 안 병원)·편의시설·공원·호재 역·정리 ③ 지점 사이 0.7km 넘게 떨어지면 구름으로 덮고 그 사이 카메라를 옮겨 타일·건물이 다 올라온 뒤 펼침. 실사 3D는 vw3On 창(v3d.html)에 postMessage {v3c:'view'|'fly'|'orbit'|'marks'|'tiles'}; 실패하면 지도 3D로.
- 지도에서 공동주택 건물을 누르면 _bldApt(같은 동·지번, 아니면 같은 동 안 이름)로 단지 카드를 띄움.

## T-4. 임장 코스 화면 (2026-11-23)
- 3D 건물: 지도 3D 임장에서는 국토부 건물자료(b3) 대신 브이월드 LT_C_SPBD(도로명주소 건물, JSONP·1,000개씩 최대 6쪽, 장면 지점마다 ±0.005°, 단지는 ±0.008°)를 'bs' 원본·'b3s' 레이어로 그림. 높이 = gro_flo_co × 3.1m(80층 제한), 회색, 이 단지(buld_nm이 단지 이름과 같고 600m 안, 없으면 120m 안 10층↑) 주황. 그동안 bLoad는 멈춤(_bOff).
- 걷는 길: footT = routing.openstreetmap.de/routed-foot table(CORS 허용, 키 없음). 장면·단지 카드·생활권 목록의 거리·시간을 보행 경로로(4km 넘으면 길 거리만), 못 찾으면 직선×1.2 추정 표시.
- 준비 화면: 로딩 바(cloudBar), 장면마다 + 회전 장면은 중간·끝 방향까지 jumpTo 후 idle(8초까지)로 타일을 받아 둠. 재생 중 settle은 2.5초 이내.
- 회전은 '단지'(90°)·'정리'(−90°)만. 왼쪽 위 나침반(.tcomp, 지도 bearing·실사 3D getCam().b). 주변 주요 시설 이름 레이어 tlmc·tlmn(1.6km 안 역, 1.2km 안 초중고, 대학, 3km 안 상급종합병원, 생활권 병원·마트·공원·도서관·주민센터·영화관/체육), 실사 3D에서는 marks에 함께.

## T-5. 단색 지도 상세·길 선 (2026-11-23)
- 단색 배경(baseMode 0)일 때 vbInit()이 OpenFreeMap 원본('ofm')으로 vb_lc(landcover)·vb_lu(landuse)·vb_park·vb_wa(water)·vb_ww(waterway)·vb_rdc/vb_rd(도로 테두리·면, 터널 제외)·vb_bld(건물, z13.5↑)·vb_poi(병원·학교·공원·도서관·관공서·시장 등 이름, z14.5↑ rank 단계)를 'terr' 아래에 넣음. 이때 우리 산지(terr)·물(wb·rv)은 숨기고 물 이름(lw)은 둠. 임장 중 vb_poi는 숨기고 tlm 이름표를 씀.
- 길 선: routeGeo(c,q,'foot'|'car') = routing.openstreetmap.de 보행 / OSRM 자동차 route(overview=full, geojson). rTicks로 걷기 250m(2km 넘으면 500m)·차 1km(12km 넘으면 2km) 눈금. 임장 장면은 단지·목적지·길을 cameraForBounds로 한 화면에(z 11.2~16.3), 2D는 tour 원본(tourlc 흰 테두리 + tourl 주황 걷기/파랑 차), 실사 3D는 marks line·눈금 점.
- 우리 단지 주황: 이름이 같은 SPBD 건물의 지번(bd_mgt_sn 앞 19자리) 또는 실거래 지번(gu = 동, sn[11:15] 본번, sn[15:19] 부번)이 같은 5층 이상 건물.

## T-6. 단색 지도 건물 채우기 (2026-11-23)
- 국토부 GIS건물통합정보(bld/)에 빠진 신축 단지(예: 전북혁신도시)를 채우려고 단색 배경·z14.5↑에서 spView()가 브이월드 LT_C_SPBD를 0.01° 칸마다 JSONP로 받음(칸 캐시 40개). 2D = vb_sp(면, b2 아래), 3D = vb_sp3(기둥, 국토부 건물 bbox 안에 중심이 든 것은 dup=1로 빼서 겹치지 않게). 브이월드 키가 없으면 안 그림.

## T-2. KTX역 실제 이동 시간 (데이터 갱신 없음, 2026-11-22)
- KTX역 목록 = stations.json 중 t='ktx' + 운행 중 KTX 노선(rail.json k='ktx')이 지나는 역 + `KXN`(수서·동탄·평택지제(2026.9 KTX·SRT 통합), 행신, 서대전·계룡·논산(기존선 KTX), 원주·제천·단양(중앙선 KTX-이음), 서울). 노선·정차역이 바뀌면 KXN을 고친다. 단지마다 직선 가장 가까운 KTX역 a.kx, 지하철 없는 시는 a.tr = a.kx.
- 단지 카드·임장 코스·관심 단지 비교: OSRM 공개 서버(router.project-osrm.org, table/v1/driving, 브라우저에서 바로 호출, 키 없음)로 직선 가까운 KTX역 3곳 + 가까운 버스터미널까지 자동차 시간·도로 거리를 받아 가장 빠른 KTX역을 보여 줌. 막힘·신호 대기 반영 안 됨, 서버에 닿지 않으면 직선거리. 카카오맵 '길찾기' 링크(map.kakao.com/link/to).

## T. 브역대신평초·주변 생활권 (데이터 갱신 없음, 2026-11-22)
- 단지 카드 '브역대신평초'(카드를 열 때 계산)와 '주변 생활권' 단추, 임장 코스(동네 → 단지 → 평가 → 역 → 초등학교 → 상권 → 생활권 → 병원 → 편의시설 → 공원 → 호재 역 → 정리).
- 기준(이 지도 기준, ml.tpl.html `BRD`·`bydsOf`): 브 = 국토교통부 2026년 시공능력평가(2026.7.30 공시) 1~10위 건설사 브랜드를 단지 이름에서 찾음(래미안·힐스테이트·디에이치·자이·푸르지오·써밋·e편한세상·아크로·롯데캐슬·르엘·더샵·오티에르·SK뷰·아이파크). **매년 7월 말 시평 발표 뒤 BRD 순위를 고친다.** 역 500m ✓·1km △ / 대 = bld 타일에서 같은 동·지번(또는 이름)인 공동주택 연면적 합 ÷ 100㎡로 세대 규모 추정, 1,000↑ ✓·500↑ △(건물 자료에 빠진 동이 있으면 작게 나옴) / 신 10년 이내 ✓·20년 △ / 평 = AWS Terrain Tiles(terrarium z15, 브라우저에서 바로 읽음) 단지 중심과 300m 둘레 8점의 고도차 10m 미만 ✓·25m △, 1.5km 안 역과의 고도 차 / 초 400m 안이고 roads_big 왕복 8차선 큰길을 안 건너면 ✓·800m △.
- 생활권: 상권 = shop.json 상권 덩어리(1.5km 안, 점포 수 ÷ (1+2×거리) 최대) 또는 서울 shop_zone(1.2km 안 가장 가까운 발달상권·전통시장·관광특구), 도로 이름 = 그곳으로 날아가 OpenFreeMap transportation_name을 화면에서 읽음, 업종 수 = 단지 500m 안 250m 칸 합계. 시설 이름 = OpenFreeMap poi(class hospital·doctors·dentist·pharmacy·grocery·park·library·town_hall·post·cinema·sports_centre) 1km 안. OSM에 동네 의원·편의점은 빠진 곳이 많음 → 병원·약국 수는 상가정보 칸으로 본다. 공식 병의원(건강보험심사평가원)·대규모점포·도시공원 표준데이터로 바꾸려면 PC 다운로드 폴더 접근이 필요(2026-11-22 미승인).

## D. 빌드·검증·게시
- (GitHub 게시) gen.py는 index.html(새 지도)·old.html·ml.html·bld.html을 만든다. 커밋할 때 이 파일들을 함께 넣고, 저장소 루트의 vwkey.js(브이월드 공용 키)는 건드리지 않으며 프로젝트 문서에 내용을 옮기지 않는다.
1. (ml.tpl.html도 함께 처리됨) `HWYDATE="(hwy 갱신 시 오늘, 아니면 기존 값: 2026년 11월 17일 조회)" python3 gen.py` → index.html
2. 검증: `python3 -c` 로 data/*.json 파싱, rail 노선 수 80개 이상, stations 1000개 이상, index.html에 `__` 자리표시자가 남지 않았는지.
3. 게시: `mcp__claude-artifacts__get_artifact`로 현재 version 확인 → `publish_files(slug, base_version, files=[index.html, data/rail.json, data/stations.json (+ data/hwy.json, data/edu.json, data/hagwon_grid.json, data/hagwon_pts.json, data/pop.json, data/flow.json, data/roads_big.json, data/roads_main.json, data/shop.json, data/shop_zone.json, bld.html)], label="정기 업데이트 YYYY-MM-DD")`. mode는 기본 patch.
4. 템플릿을 고쳤으면 Projects 도구로 `kr-map/index.tpl.html`(및 고친 스크립트)을 덮어쓴다.
5. `kr-map/CHANGELOG.md`에 날짜·바뀐 내용 한 줄 추가.
6. 사용자에게 바뀐 점을 짧게 보고(SendUserMessage). 바뀐 게 없으면 "변경 없음"과 확인한 출처만.

## 손대지 않는 것
- 지형(terrain.json), 강·호수·저수지(water.json), 행정경계(sub.json): 거의 변하지 않으므로 자동 갱신 대상 아님. 사용자가 요청할 때 수동 갱신.

## 전국 확대 준비 (2026-11-24)
- 대상 시도는 `pipeline/regions.py` 한곳에서 관리. 기본값은 지금의 8개 시도, `REGIONS=all`이면 17개 시도, `REGIONS=11,26`처럼 법정동 시도코드로 직접 지정. build_edu·build_pop·build_apt·build_shop_zone·shop_extract·build_bld_addr가 이 파일을 읽음(기본값 결과는 이전과 같음).
- 전국으로 넓힐 때 새로 받아야 하는 원본: 실거래가(매매·전월세) 나머지 9개 시도, GIS건물통합정보 9개 시도, 버스정류장·학원(상가정보)·초중고 위치는 원본이 이미 전국이라 다시 추출만, 한국부동산원 지수는 전국 시군구 포함 여부 확인, 통근 추정 목적지(강남·여의도·광화문·판교)는 권역별 중심지(부산 서면·센텀, 대구 동성로, 광주 상무 등) 추가 필요.
- 화면 쪽 남은 일: apt.json(8개 시도 7.5MB)을 시도별 파일로 나눠 보이는 지역만 받기(전국이면 2배 안팎), 안내 문구의 '서울·경기…' 지역 표기를 자료에서 읽어 오기, 지역 바로가기 목록에 새 시도 추가.
- 주차대수: K-apt(공동주택관리정보시스템) 단지 기본정보의 주차대수(지상·지하)·세대수를 받아 단지에 붙이면 '세대당 주차대수' 표시·점수 반영 가능(공공데이터포털 인증키 또는 K-apt 엑셀 파일 필요, 아직 없음).

## U. 세대수·주차대수 (분기 권장, 내장 브라우저 필요, 로그인 불필요)
- 원본: K-apt 자료실(https://www.k-apt.go.kr/web/board/webReference/boardList.do) '관리비공개의무단지 기본정보(날짜)' 엑셀(매주 금요일, 전국 약 2.2만 단지, 88개 항목: 세대수 14·동수 13·총주차 52·지상 53·지하 54·시공사 22·최고층 69 등). 글을 열고 `dx5.get('BOARD_FILE').getItems()[0].url`을 fetch → 페이지 안에서 xlsx(zip)를 풀어(시트는 inlineStr) 읽는다.
- 같은 페이지에서 사이트의 data/apt.json을 받아 시도코드|동리|지번(안 되면 시도|동리|단지명)으로 잇고, apt.json 순서대로 '세대,주차,지하' 줄을 만든다. 컨테이너로 옮길 때 PC 폴더 접근이 없으면 gzip한 바이트를 화면에 흑백 4px 칸으로 그려 확대 캡처(zoom) 이미지로 받아 풀 수 있다(조각마다 해시 검산, /home/claude/work/dec.py 방식).
- data/kapt.json = {ref, k:{"시군구코드|동 지번"(겹치면 |단지명): [세대수, 총주차, 지하주차]}}. 전국 확대 때는 apt.json만 넓히면 같은 방법으로 붙는다(원본이 전국).

## V. 커뮤니티 시설(부대복리시설) — GitHub Actions가 매일 자동
- `.github/workflows/kapt-fac.yml`이 매일 새벽 3:17(한국)에 `pipeline/build_kapt_fac.py`를 돌려 `data/kapt_fac.json`과 캐시(`pipeline/kapt_fac_cache.json.gz`)를 커밋한다. 하루 호출 한도에 걸리면 멈췄다가 다음 날 이어서 채운다(전국 처음 채우기 3~4일).
- 필요: 공공데이터포털 활용신청 2개(단지목록 15057332, 공동주택 기본·상세 15058453) → 인증키(인코딩)를 저장소 Secret `DATA_GO_KR_KEY`로 등록. 키가 없으면 그냥 건너뛴다.
- data/kapt_fac.json = {ref, src, t:[시설 13종], k:{"시군구코드|동 지번":[시설 비트, 전기차충전기 수]}}. 앞 9종을 '커뮤니티 N종'으로 센다.
