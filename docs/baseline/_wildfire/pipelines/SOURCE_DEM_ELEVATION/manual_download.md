# Manual Download — SOURCE_DEM_ELEVATION

Status: reference only. DEM is excluded from TX04 by user instruction on 2026-04-30. Do not execute these steps for the current transaction.

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_DEM_ELEVATION` |
| access_option_id | `ACCESS_DEM_ELEVATION_PRIMARY` |
| source_url | `https://www.data.go.kr/data/15059920/fileData.do` |
| download_portal | `http://map.ngii.go.kr/ms/map/NlipMap.do?tabGb=total` |
| account_required | 국토정보플랫폼 로그인 필요; not applicable for TX04 because source is excluded |
| terms_or_license | data.go.kr listing: 이용허락범위 제한 없음; 포털 다운로드 이용조건 확인 필요 |
| expected_format | IMG raster plus source metadata/sidecar files |
| layer_name | 공개DEM |
| native_crs | not_inspected_excluded for TX04; if later downloaded, preserve and record CRS from downloaded IMG metadata |
| native_spatial_grain | raster tile |

## Verified Official Evidence

- data.go.kr dataset `국토교통부 국토지리정보원_DEM_20240924` lists extension `IMG`, provider `국토교통부 국토지리정보원`, updated date `2025-06-17`, and source URL to 국토정보플랫폼.
- The listing states that National Land Information Platform downloads require large-file transfer software and that the software is downloaded automatically during download.
- The listing's usage note gives the acquisition path: portal access, simple map search, choose index/area/radius, select an area, select `공개DEM`, choose items, and download; login is required.
- The scraped 국토정보맵 page exposes a `공개DEM` result category under the map search UI.

## Steps

Do not perform these steps for TX04. They are retained only for future reactivation of the source.

1. 접속: data.go.kr `source_url`에서 dataset metadata를 확인한다.
2. 포털 이동: `download_portal`을 연다.
3. 로그인: 국토정보플랫폼 계정으로 로그인한다.
4. 검색 방식: `간편지도 검색`에서 `영역`, `행정구역`, 또는 `인덱스`를 선택한다.
5. 검색 영역: 광주·전남 대상 영역을 지도에서 지정한다.
6. 항목 선택: 검색 결과의 `공개DEM` 항목을 선택한다.
7. 다운로드: 필요한 tile/item을 선택하고 다운로드를 실행한다. 대용량 파일전송 S/W 설치가 요구되면 포털 안내에 따라 설치한다.
8. 저장: IMG와 모든 sidecar/metadata 파일을 아래 raw snapshot 경로에 저장한다.
9. 검증: `gdalinfo`로 driver, native CRS, geotransform, pixel size, band, NoData만 기록한다.

## Region Check

DEM이 제외 상태이므로 coverage를 확인하지 않는다. 이전 확인 결과, 국토정보맵은 영역/행정구역/인덱스 기반 검색과 `공개DEM` category를 제공한다.

## Raw Preservation

TX04에서는 원본 파일을 저장하지 않는다. DEM이 향후 재도입되면 원본 파일은 변환하지 않고 아래 경로에 저장한다.

```text
data/raw/SOURCE_DEM_ELEVATION/snapshots/full/
```

광주·전남 시도 단위 tile만 받은 경우:

```text
data/raw/SOURCE_DEM_ELEVATION/snapshots/regional_clip/
```

좌표계 통일, resampling, clipping, slope/aspect/hillshade 계산은 수행하지 않는다. 시도 단위 clip이 필요하면 다운로드 포털에서 선택한 native tile 또는 native export를 그대로 보존한다.
