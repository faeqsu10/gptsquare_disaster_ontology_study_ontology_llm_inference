# Source Dossier — SOURCE_SUN_EVENT_CALENDAR

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_SUN_EVENT_CALENDAR` |
| selected_access_option_id | `ACCESS_SUN_EVENT_CALENDAR_AREA` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_SUN_EVENT_CALENDAR/snapshots/sample_20260430/` |
| pipeline_path | `pipelines/SOURCE_SUN_EVENT_CALENDAR/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_SUN_EVENT_CALENDAR_AREA` | SELECTED | admin area name | daily | Accept |
| `ACCESS_SUN_EVENT_CALENDAR_PRIMARY` | FALLBACK | coordinate point snapped to service location | daily | Verified but not selected: coordinate-based query resolves to nearest service location, which may differ from the requested 행정동 |

Decision note:

```text
KASI 지역별 출몰시각 endpoint `location=광주` (또는 전남 시군) 단위로 호출한다. 행정구역 native grain을 보존하고, 예보 grid로 정렬하지 않는다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | openapi |
| endpoint_or_layer | `https://apis.data.go.kr/B090041/openapi/service/RiseSetInfoService/getAreaRiseSetInfo` |
| request_or_download_path | `sample_request.json` |
| expected_format | XML |
| actual_format | XML response files captured |
| snapshot_path | `data/raw/SOURCE_SUN_EVENT_CALENDAR/snapshots/sample_20260430/` |
| captured_at | 2026-04-30 |

Raw fields observed from official response schema:

```text
locdate, location, longitude, latitude, sunrise, suntransit, sunset, civilm, civile, nautm, naute, astm, aste
```

Auth/quota/schema:

```text
auth: public data.go.kr service key
quota: 개발계정 10,000 calls; 운영계정은 활용사례 등록 후 증가 가능
response item schema: response.body.items.item
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `locdate` |
| temporal_semantics | `effective_period` / daily date |
| native_temporal_grain | daily |
| native_time_format | `YYYYMMDD`, event fields as `HHMM` |
| parse_example | `locdate=20260415`, `sunrise=<HHMM>`, `sunset=<HHMM>` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `location` |
| geometry_field | service-returned `longitude`, `latitude` representative coordinate |
| spatial_semantics | admin_area |
| native_spatial_grain | admin area |
| native_crs | admin area request; service returns representative longitude/latitude |
| region_filter_method | query native KASI area `location=광주` |
| validation_example | `location=광주` returns `longitude=12651`, `latitude=3510` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 7 daily XML responses |
| spatial_intersection_result | pass: coordinate point request prepared |
| temporal_coverage_result | pass: all PoC dates captured |
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
- Coordinate endpoint was tested successfully, but coordinate-based queries resolve to the nearest service location, which may not match the requested 행정동. The area endpoint `location=광주` is therefore selected for 광주 coverage.
```
