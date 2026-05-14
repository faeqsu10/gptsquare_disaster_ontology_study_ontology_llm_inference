# Source Dossier — SOURCE_KMA_WEATHER_WARNINGS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_KMA_WEATHER_WARNINGS` |
| selected_access_option_id | `ACCESS_KMA_WEATHER_WARNINGS_WARNING_AREA` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_KMA_WEATHER_WARNINGS/snapshots/sample_20260430/` |
| pipeline_path | `pipelines/SOURCE_KMA_WEATHER_WARNINGS/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_KMA_WEATHER_WARNINGS_WARNING_AREA` | SELECTED | warning area/admin area | event-driven warning history | Accept with API-key gap |

Decision note:

```text
KMA 특보는 REG_ID warning area code를 native key로 제공한다. 특보구역을 행정동으로 재분배하지 않는다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | openapi |
| endpoint_or_layer | `https://apihub.kma.go.kr/api/typ01/url/wrn_met_data.php` |
| request_or_download_path | `sample_request.json` |
| expected_format | TEXT |
| actual_format | TEXT table captured |
| snapshot_path | `data/raw/SOURCE_KMA_WEATHER_WARNINGS/snapshots/sample_20260430/` |
| captured_at | 2026-04-30 |

Raw fields observed from official response schema:

```text
TM_FC, TM_EF, TM_IN, STN, REG_ID, WRN, LVL, CMD, GRD, CNT, RPT
```

Auth/quota/schema:

```text
auth: KMA APIHub authKey
quota: 기관 정책에 따름
response format: typ01 URL text table; help=1 exposes field help
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `TM_FC`, `TM_EF`, `TM_IN`, `CMD` |
| temporal_semantics | `event_occurred_at`, `effective_period` |
| native_temporal_grain | event-driven |
| native_time_format | `YYYYMMDDHHMM` KST |
| parse_example | `TM_FC=202604150400`, `TM_EF=202604161158`, `CMD=1`; 해제 row는 `CMD=3` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `REG_ID` |
| geometry_field | none in selected API body |
| spatial_semantics | admin_area |
| native_spatial_grain | warning area/admin area |
| native_crs | warning-area code table; geometry not emitted |
| region_filter_method | `reg=0` all areas, then preserve `REG_ID`/`REG_NAME` for 광주광역시 rows |
| validation_example | `L1050100` = 광주광역시 from `warning_area_response.txt` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 232 all-area warning rows; 0 PoC `L1050100` rows |
| spatial_intersection_result | pass: `L1050100` 광주광역시 warning area confirmed |
| temporal_coverage_result | pass: `tmfc1/tmfc2` period query covers PoC window |
| poc_coverage_result | pass |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept |
| fallback_required | no |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- PoC-specific query for `reg=L1050100` returned 0 rows, meaning no 광주광역시 warning events in the fixed PoC window.
```
