# Source Dossier — SOURCE_PUBLIC_FACILITIES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_PUBLIC_FACILITIES` |
| selected_access_option_id | `ACCESS_PUBLIC_FACILITIES_GJ_PUBLIC_HEALTH_CSV` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_PUBLIC_FACILITIES/snapshots/regional_clip/` |
| full_snapshot_path | `data/raw/SOURCE_PUBLIC_FACILITIES/snapshots/full_gwangju_jeonnam_20260430/` |
| pipeline_path | `pipelines/SOURCE_PUBLIC_FACILITIES/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_PUBLIC_FACILITIES_GJ_PUBLIC_HEALTH_CSV` | SELECTED | facility address | registry date | No-auth concrete source and sample acquired. |
| `ACCESS_PUBLIC_FACILITIES_SCHOOL_LOCATION_API` | REJECTED | school point/address | reference date | Excluded from TX05 after reproducible `NODATA_ERROR` for 광주·전남 filters. |
| `ACCESS_PUBLIC_FACILITIES_HIRA_HOSPITAL_API` | FALLBACK | hospital point/address/admin | snapshot/static | Concrete hospital source; reads `DATA_GO_KR_SERVICE_KEY`. |
| `ACCESS_PUBLIC_FACILITIES_TBD` | REJECTED | unknown | unknown | Replaced by concrete URLs above. |

Decision note:

```text
The selected sample confirms a concrete public-facility URL and address/time keys. HIRA hospital coverage is acquired as an additional concrete access option. School coverage is excluded from TX05 by user decision after the API returned `NODATA_ERROR` for 광주·전남 filters.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | file_download |
| endpoint_or_layer | `https://www.data.go.kr/data/15056455/fileData.do` |
| request_or_download_path | direct file download URL in `candidate_sources.json` |
| expected_format | CSV |
| actual_format | CSV, cp949 |
| snapshot_path | `public_health_facilities_gwangju_20240313.csv` |
| captured_at | 2026-04-30 |

Raw fields observed:

```text
- 연번
- 구분
- 기관명
- 소재지도로명주소
- 전화번호
- 팩스번호
- 데이터기준일자
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `데이터기준일자` |
| temporal_semantics | registry_updated_at |
| native_temporal_grain | file reference date |
| native_time_format | `YYYY-MM-DD` |
| parse_example | `2024-03-13` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `소재지도로명주소` |
| geometry_field | none |
| spatial_semantics | address |
| native_spatial_grain | facility address |
| native_crs | no_geometry |
| region_filter_method | native address text filter for 광주광역시; no geocoding |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 32 full rows; 3 Dong-gu clip rows |
| spatial_intersection_result | partial via address text |
| temporal_coverage_result | not_applicable for static registry |
| poc_coverage_result | partial |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept |
| fallback_required | yes |
| mock_required | no |
| exclude_required | yes; school location option excluded from TX05 |

Open issues:

```text
- HIRA hospital API is working and all pages were saved: 광주 2,329 rows, 전남 2,627 rows.
- School location API is excluded from TX05 by user decision after reproducible resultCode=03 `NODATA_ERROR` for 광주광역시/전라남도 filters.
```
