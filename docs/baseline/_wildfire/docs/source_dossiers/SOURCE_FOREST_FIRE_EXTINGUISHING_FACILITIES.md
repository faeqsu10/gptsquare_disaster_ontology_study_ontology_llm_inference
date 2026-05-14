# Source Dossier - SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES` |
| selected_access_option_id | `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_PRIMARY` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/full/`; `data/mock/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/scenario_baseline/` |
| pipeline_path | `pipelines/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_PRIMARY` | SELECTED proposed | point/address | annual registry update | Full CSV acquired |
| `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_OPENAPI` | FALLBACK proposed | point/address | annual registry update | JSON/XML fallback |
| `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_COVERAGE_SUPPLEMENT` | FALLBACK | point | scenario period | 광주·전남 coverage supplement mock |

Decision note:

```text
The official data.go.kr CSV content URL was downloaded and preserved. The full source has 187 rows; 광주 rows are 0 and 전남 rows are 13. A separate coverage supplement mock now covers 광주·전남 legal 읍면동 current legal 읍면동 units.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | file_download; openapi fallback; generated_mock coverage supplement |
| endpoint_or_layer | https://www.data.go.kr/data/15144785/fileData.do |
| request_or_download_path | file-data tab; OpenAPI tab fallback |
| expected_format | CSV, JSON, XML |
| actual_format | CP949 CSV; UTF-8 CSV/GeoJSON/manifest supplement |
| snapshot_path | `data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/full/`; `data/mock/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/scenario_baseline/` |
| captured_at | 2026-04-30 official CSV; 2026-05-01 supplement |

Raw fields observed:

```text
- 경도
- 위도
- 원격제어
- 관리기관1
- 관리기관2
- 설치위치
- 보호대상구분
- 보호대상물
- 설치년도
- facility_id
- coverage_unit_id
- longitude
- latitude
- geometry
- record_origin
- mock_generated_at
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `metadata.modified`; `설치년도`; supplement `valid_from`, `valid_to`, `mock_generated_at` |
| temporal_semantics | registry_updated_at, static |
| native_temporal_grain | annual |
| native_time_format | YYYY-MM-DD metadata modified date; YYYY installation year |
| parse_example | 2025-08-13 |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | 경도, 위도, 설치위치, 관리기관1, 관리기관2; supplement facility_id, coverage_unit_id, longitude, latitude, geometry |
| geometry_field | 경도, 위도 |
| spatial_semantics | point, address |
| native_spatial_grain | point/address |
| native_crs | not declared; longitude/latitude preview preserved as published |
| region_filter_method | official CSV filtered by 관리기관/주소; supplement generated from SOURCE_REGION_CODE_TABLE 광주·전남 current legal 읍면동 coverage units with SOURCE_ADMIN_BOUNDARIES/VWorld representative coordinates |
| validation_example | official preview row has lon/lat; supplement has 623 unique `coverage_unit_id`, 광주 202, 전남 421 |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | official 187 total, 전남 13, 광주 0; supplement 623 coverage rows |
| spatial_intersection_result | pass with supplement |
| temporal_coverage_result | registry/static |
| poc_coverage_result | pass |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept |
| fallback_required | OpenAPI fallback proposed; coverage supplement required for regional baseline |
| mock_required | yes, for official regional gap |
| exclude_required | no |

Open issues:

```text
- Full CSV acquired and preserved; official-only coverage remains 광주 0 rows and 전남 13 rows.
- 광주·전남 full baseline coverage uses `record_origin=mock_supplement` rows and must be propagated downstream as mock input.
- No nearest facility distance or Segment join was computed.
```
