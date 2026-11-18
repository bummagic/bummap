# 전국 규제지역·철도·고속도로 지도 — 정기 업데이트 런북

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
- 바뀐 것이 있으면 index.tpl.html을 고친다:
  - 지역 코드 배열(2013 통계청 시군구 코드 5자리 / 읍면동 7자리): `A12`(경기 3중규제 12곳), `B5`·`DT`(2026.7.1 신규: 화성 동탄구·용인 기흥구·구리시), `W5`·`BJ`(지정 거론), `FX`(외국인 토허 제외), `OLD4`(10·15 이전부터 지정된 강남·서초·송파·용산). 서울(11xxx)은 전체가 A로 처리됨(`cat` 함수).
  - 패널 문구: `const DESC`의 A/B/W 설명, 범례 `<small>` 문구, 상단 "2026년 11월 17일 기준" 날짜와 요약 수치, 하단 출처 링크.
  - 시군구 코드는 muninames_kr.json에서 이름으로 찾는다.
- 바뀐 것이 없으면 상단 "기준" 날짜만 이번 확인 날짜로 갱신.

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

## G. 인구밀도·유동인구 (반기, PC 필요)
- 인구밀도: 공공데이터포털 'SGIS 격자 통계 및 경계'(data.go.kr/data/15141768, 반기 갱신, ZIP 약 100MB, 로그인 필요 → 사용자가 크롬으로 받아 다운로드 폴더에 저장). device_bash로 ZIP 안 `1. 통계/1. ... (인구)`·`2. ... (가구)`의 `*_1K.csv`(cp949; 기준연도,격자코드,통계항목,통계값)를 읽어 격자별 to_in_001(총인구), in_age_002~004 합(5~19세), to_ga_001(가구), ga_sd_005(1인가구)를 `코드\t총인구\t5~19세\t가구\t1인가구`로 `grid1k.txt`에 쓴다. 격자코드 '다사0038' = EPSG:5179 x=700000+100000×('가나다라마바사아' 첫 글자 순번)+앞 2자리 km, y=1300000+100000×(둘째 글자 순번)+뒤 2자리 km.
- 유동인구(서울): 서울 열린데이터광장 OA-14991 '행정동 단위 서울 생활인구(내국인)' 최신 월 ZIP(로그인 불필요, 사용자가 받아 둠) → 행정동코드(8자리)별 총생활인구수 평균, 9~18시 평균, 19~6시 평균을 `seoul_lp.txt`로.
- 경기도 '유동인구 행정동별 시간대별 집계'는 동 값이 시군구 값 복제라 쓰지 않는다. 행정동 경계는 GitHub vuski/admdongkor 최신 ver 폴더 geojson(컨테이너에서 git sparse checkout) → `raw/HangJeongDong.geojson`.
- `POPDATE="2024년" SEOULYM="YYYY년 M월" python3 build_pop.py data/sub.json` → data/pop.json, data/flow.json.

## H. 건물 2D·3D (분기 또는 요청 시, PC 필요)
- 원본: 브이월드 '공간정보 다운로드' > GIS건물통합정보(dsId=18) 시도별 '전체데이터' SHP(매월 9일 기준). 사용자가 내장 브라우저에서 브이월드 로그인 → 다운로드 페이지에서 `listFnc.download('20171128DS00010', fileNo, sizeKB)` 실행(파일번호는 목록의 onclick에서 확인). 경기도(약 380MB)는 서버가 중간에 끊어 사용자 브라우저/라온K로 받아야 할 수 있음.
- 다운로드 폴더의 `AL_D010_{시도}_{기준일}.zip` 8개(11,28,30,36,41,43,44,52)를 device_stage_files로 가져와 `BLDDATE=YYYY-MM-DD python3 build_bld.py bld <zip들>` → bld/{z11묶음}.txt(타일별 gzip 조각을 이은 바이너리, 확장자는 게시 허용 때문에 .txt) + bld/index.json. 한 ZIP 안에 SHP가 여러 개일 수 있음(충남).
- 메인 지도(index.html)도 같은 bld/ 묶음 파일을 써서 일반지도·위성 배경에서 건물 2D·3D를 보여준다(MapLibre를 D3 아래에 깔고 D3 확대·이동에 카메라를 맞춤. 2D는 D3 확대 한도를 3200배로 올려 건물 축척(z14+)까지 내려감). 별도 페이지 bld.html(bld.tpl.html → gen.py)과 lib/maplibre-gl-csp*.js·css(npm maplibre-gl 4.7.1 dist)를 함께 게시. 게시 1회 64MB 한도라 bld 파일은 두 번 이상 나눠 올린다.

## I. 도로 (반기: 1월·7월, PC 필요)
- 원본: 국토교통부 ITS 국가교통정보센터 '표준노드링크' 전국 SHP(https://www.its.go.kr/nodelink/nodelinkRef, 로그인 없이 받음). 내장 브라우저로 받으면 다운로드 폴더에 GUID .tmp로 저장될 수 있어 `ls -t`로 최신 파일 확인 → device_stage_files → `/tmp/nl`에 MOCT_LINK.* 압축 해제.
- `ROADDATE=YYYY-MM-DD python3 build_road.py /tmp/nl/MOCT_LINK data/sub.json` → data/roads_big.json(고속국도·도시고속 + 한 방향 4차로↑ = 왕복 8차선↑), data/roads_main.json(국도·시도·지방도 한 방향 2차로↑). 좌표계는 EPSG:5186(GRS80 TM 중부원점, FN 600000), 수도권·충청·전북만 남김.
- LANES는 링크(한 방향) 차로 수라 왕복 차선 = 2×LANES로 추정(일방통행·분리 구간은 오차 가능).

## J. 상권 (분기, F 학원 작업과 같은 ZIP 사용, PC 필요)
- 점포 밀집도: 다운로드 폴더의 `소상공인시장진흥공단_상가(상권)정보_YYYYMMDD.zip`을 device_bash에서 `python3 shop_extract.py <zip> shop_cells.txt`로 8개 시도 점포를 250m 칸(학원과 같은 격자)·업종 대분류(I2 음식, G2 소매, S2 개인서비스, Q1 보건의료, P1 교육, R1 예술·스포츠, I1 숙박, L1 부동산, M1 과학·기술, N1 시설관리·임대)별로 센다 → device_stage_files → `raw/shop_cells.txt` → `SHOPDATE="YYYY년 M월" python3 build_shop.py` → data/shop.json(칸 + 상권 이름표: 생활업종 40곳 이상 칸을 이어 붙이고 너무 큰 덩어리는 기준을 1.6배씩 올려 나눔, 합계 400곳 이상만).
- 상권 경계: ① 서울 열린데이터광장 OA-15560 '서울시 상권분석서비스(영역-상권)' ZIP(로그인 불필요, 페이지의 `downloadFile('5')`) → `raw/seoul.*`(EPSG:5181, UTF-8) ② 공공데이터포털 15090955 '소상공인시장진흥공단_주요상권현황'(로그인 불필요, 2024-01-01 기준 1회성, cp949, 좌표는 '경도,위도|…' 문자열) → `raw/major_zones.csv`. 내장 브라우저로 받으면 GUID .tmp로 저장됨. `SEOULZONE="2023년 10월 파일" python3 build_shop_zone.py` → data/shop_zone.json. 두 원본 모두 갱신이 드물어 새 파일이 올라왔을 때만 다시 만든다.

## D. 빌드·검증·게시
1. `HWYDATE="(hwy 갱신 시 오늘, 아니면 기존 값: 2026년 11월 17일 조회)" python3 gen.py` → index.html
2. 검증: `python3 -c` 로 data/*.json 파싱, rail 노선 수 80개 이상, stations 1000개 이상, index.html에 `__` 자리표시자가 남지 않았는지.
3. 게시: `mcp__claude-artifacts__get_artifact`로 현재 version 확인 → `publish_files(slug, base_version, files=[index.html, data/rail.json, data/stations.json (+ data/hwy.json, data/edu.json, data/hagwon_grid.json, data/hagwon_pts.json, data/pop.json, data/flow.json, data/roads_big.json, data/roads_main.json, data/shop.json, data/shop_zone.json, bld.html)], label="정기 업데이트 YYYY-MM-DD")`. mode는 기본 patch.
4. 템플릿을 고쳤으면 Projects 도구로 `kr-map/index.tpl.html`(및 고친 스크립트)을 덮어쓴다.
5. `kr-map/CHANGELOG.md`에 날짜·바뀐 내용 한 줄 추가.
6. 사용자에게 바뀐 점을 짧게 보고(SendUserMessage). 바뀐 게 없으면 "변경 없음"과 확인한 출처만.

## 손대지 않는 것
- 지형(terrain.json), 강·호수·저수지(water.json), 행정경계(sub.json): 거의 변하지 않으므로 자동 갱신 대상 아님. 사용자가 요청할 때 수동 갱신.
