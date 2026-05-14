# Manual Download — SOURCE_FOREST_ROAD_NETWORK

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FOREST_ROAD_NETWORK` |
| access_option_id | `ACCESS_FOREST_ROAD_NETWORK_PRIMARY` |
| source_url | `https://www.forest.go.kr/kfsweb/kfi/kfs/trail/fRMap.do?pblicDataId=PBD0000062&tabs=1&mn=NKFS_06_08_02&subTitle=%EC%9E%84%EB%8F%84%EB%A7%9D%EB%8F%84` |
| map_url | `https://map.forest.go.kr/forest/?systype=mapSearch&searchOption=imdo` |
| account_required | 공공/연구 또는 일반 신청 절차, 로그인 가능성 있음 |
| terms_or_license | 산림공간정보 다운로드 무료신청 절차와 이용조건 확인 필요 |
| expected_format | SHP ZIP |
| layer_name | 임도망도 |
| native_crs | UTM-K, EPSG:5179 per 산림청 자료유통현황 |
| native_spatial_grain | forest road line |

## Verified Official Evidence

- 산림청 공공데이터 개방목록은 임도망도를 "임도의 노선과 시공년도, 거리 등을 알려주는 산림지도"로 설명한다.
- 같은 페이지는 데이터 종류를 SHP로 제시하고 산림공간정보서비스에서 조회/다운로드할 수 있다고 안내한다.
- 산림청 자료유통현황은 1:5,000 임도망도를 공공연구기관 제공용으로 제시하며, 메타정보로 UTM-K(EPSG:5179), SHP 파일형식을 제시한다.

## Steps

1. 접속: 위 `source_url`에서 임도망도 공공데이터 설명을 확인한다.
2. 지도 열기: "산림공간정보서비스 이동" 또는 `map_url`로 이동한다.
3. 신청 시작: 지도 화면 왼쪽 상단의 `산림공간정보 다운로드 무료신청`을 선택한다.
4. 신청자 유형: `일반인` 또는 `공공/연구` 신청 중 사용 자격에 맞는 유형을 선택한다. 1:5,000 임도망도는 공공연구기관 제공용으로 고시되어 있어 자격 확인이 필요하다.
5. 신청대상: 산림주제도에서 `임도망도`를 선택한다.
6. 신청 영역: 광주·전남 대상 영역을 지도에서 선택한다.
7. 신청 정보: 신청 목적, 활용 용도, 신청 사유를 입력한다.
8. 다운로드: SHP ZIP을 내려받아 아래 raw snapshot 경로에 저장한다.

## Region Check

FGIS 지도 기반 위치 선택 workflow가 있으므로 광주·전남 영역 bbox 신청은 가능하다. 이 transaction에서는 로그인 후 실제 line intersection을 수행하지 않았으므로 coverage는 source-level partial로 기록한다.

## Raw Preservation

원본 파일은 변환하지 않고 아래 경로에 저장한다.

```text
data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/full/
```

광주·전남 시도 단위 추출만 받은 경우:

```text
data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/regional_clip/
```

SHP의 `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg` 등 sidecar를 모두 보존한다. 좌표계 통일, line dissolve, road network topology 생성, Segment join은 수행하지 않는다.
