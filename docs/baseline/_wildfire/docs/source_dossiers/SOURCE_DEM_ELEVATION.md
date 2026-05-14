# Source Dossier — SOURCE_DEM_ELEVATION

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_DEM_ELEVATION` |
| selected_access_option_id | `ACCESS_DEM_ELEVATION_PRIMARY` |
| availability_status | EXCLUDE |
| verification_status | source_confirmed |
| sample_path | not_applicable_excluded |
| pipeline_path | `pipelines/SOURCE_DEM_ELEVATION/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_DEM_ELEVATION_PRIMARY` | EXCLUDED | raster tile | static / irregular update | Access procedure remains documented, but DEM is excluded by user instruction on 2026-04-30. |

Decision note:

```text
DEM acquisition is out of scope for TX04 by user instruction. Do not download IMG tiles, calculate slope/aspect, or reproject in this transaction.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | excluded |
| endpoint_or_layer | `https://www.data.go.kr/data/15059920/fileData.do` / layer `공개DEM` |
| request_or_download_path | `pipelines/SOURCE_DEM_ELEVATION/manual_download.md` retained as reference only |
| expected_format | IMG raster |
| actual_format | excluded_by_user_no_download |
| snapshot_path | not_applicable_excluded |
| captured_at | 2026-04-30 |

Raw fields observed from official metadata:

```text
- elevation raster band
- NoData value
- geotransform
- raster CRS metadata
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `registry_updated_at` |
| temporal_semantics | static, registry_updated_at |
| native_temporal_grain | irregular / 수시 자동 갱신 |
| native_time_format | data.go.kr listing dates use `YYYY-MM-DD`; raster cells have no per-cell time |
| parse_example | not_applicable_excluded |
| time_parse_result | not_applicable |

Notes:

```text
Raw 단계에서는 시간 grid alignment를 수행하지 않는다. DEM은 static geospatial base raster로 취급한다.
```

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `raster_tile` |
| geometry_field | raster geotransform and band grid |
| spatial_semantics | raster |
| native_spatial_grain | raster tile |
| native_crs | not_inspected_excluded |
| region_filter_method | not_applicable_excluded |
| validation_example | not_applicable_excluded |
| space_validation_result | not_applicable_excluded |

Notes:

```text
DEM은 제외되었으므로 raster CRS inspection, resampling, slope/aspect 계산, Segment join을 수행하지 않는다.
```

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | not_acquired |
| spatial_intersection_result | not_applicable_excluded |
| temporal_coverage_result | not_applicable_excluded |
| poc_coverage_result | not_applicable |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | exclude |
| fallback_required | no |
| mock_required | no |
| exclude_required | yes |

Open issues:

```text
- DEM은 사용자 지시에 따라 TX04 원본 확보 대상에서 제외한다.
- DEM 원본 다운로드, IMG CRS 확인, pixel size/NoData/band metadata 확인은 수행하지 않는다.
- DEM에서 경사도/사면방향 계산도 수행하지 않는다.
```
