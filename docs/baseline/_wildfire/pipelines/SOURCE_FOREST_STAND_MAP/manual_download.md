# Manual Download — SOURCE_FOREST_STAND_MAP

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FOREST_STAND_MAP` |
| access_option_id | `ACCESS_FOREST_STAND_MAP_PRIMARY` |
| source_url | `https://www.forest.go.kr/newkfsweb/html/HtmlPage.do?pg=/fgis/UI_KFS_5002_020100.html&mn=KFS_02_04_03_04_01&orgId=fgis` |
| map_url | `https://map.forest.go.kr/forest/?systype=mapSearch&searchOption=stock` |
| account_required | 로그인/무료신청 절차 필요 |
| terms_or_license | 산림공간정보 다운로드 무료신청 절차와 이용조건 확인 필요 |
| expected_format | SHP ZIP |
| layer_name | 대축척 임상도 또는 임상도 |
| native_crs | UTM-K, EPSG:5179 per 산림청 자료유통현황 |
| native_spatial_grain | forest stand polygon |

## Verified Official Evidence

- 산림청 임상도 설명 페이지는 임상도가 임종, 임상, 수종, 경급, 영급, 수관밀도 등 속성정보를 포함한다고 설명한다.
- 같은 페이지의 SHP 다운로드 안내는 "주제도 보기 > 산림공간정보 다운로드 무료신청 > 일반인 신청 > 대축척 임상도 선택 > 위치 선택 > 신청 목적 입력 > shp 파일 다운로드" 흐름을 제시한다.
- 산림청 자료유통현황은 일반 제공용 1:5,000 임상도와 1:25,000 임상도를 listed layer로 제시하며, 메타정보로 UTM-K(EPSG:5179), SHP 파일형식을 제시한다.

## Steps

1. 접속: 위 `source_url`에서 임상도 설명과 다운로드 안내를 확인한다.
2. 지도 열기: "주제도보기" 또는 `map_url`로 이동한다.
3. 신청 시작: 지도 화면 왼쪽 상단의 `산림공간정보 다운로드 무료신청`을 선택한다.
4. 신청자 유형: `일반인 신청`을 선택한다. 로그인 또는 본인 확인이 요구되면 계정으로 진행한다.
5. 신청대상: `대축척 임상도`를 선택한다. 대축척 레이어가 불가하면 `임상도` 1:25,000을 fallback 후보로 기록한다.
6. 신청 영역: 광주·전남 대상 영역을 지도에서 선택한다.
7. 신청 정보: 신청 목적, 활용 용도, 신청 사유를 입력한다.
8. 다운로드: SHP ZIP을 내려받아 아래 raw snapshot 경로에 저장한다.

## Region Check

FGIS 지도 기반 위치 선택 workflow가 있으므로 광주·전남 영역 bbox 신청은 가능하다. 이 transaction에서는 로그인 후 실제 feature intersection을 수행하지 않았으므로 coverage는 source-level partial로 기록한다.

## Raw Preservation

원본 파일은 변환하지 않고 아래 경로에 저장한다.

```text
data/raw/SOURCE_FOREST_STAND_MAP/snapshots/full/
```

광주·전남 시도 단위 추출만 받은 경우:

```text
data/raw/SOURCE_FOREST_STAND_MAP/snapshots/regional_clip/
```

SHP의 `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg` 등 sidecar를 모두 보존한다. 좌표계 통일, dissolve, forest boundary 생성, Segment join은 수행하지 않는다.
