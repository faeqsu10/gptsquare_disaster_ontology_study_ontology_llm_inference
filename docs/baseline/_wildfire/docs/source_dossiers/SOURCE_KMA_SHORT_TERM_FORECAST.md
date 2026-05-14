# Source Dossier — SOURCE_KMA_SHORT_TERM_FORECAST

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_KMA_SHORT_TERM_FORECAST` |
| selected_access_option_id | `ACCESS_KMA_SHORT_TERM_FORECAST_NXNY_GRID` |
| availability_status | REAL |
| verification_status | api_tested |
| sample_path | `data/raw/SOURCE_KMA_SHORT_TERM_FORECAST/snapshots/sample_20260430/` |
| pipeline_path | `pipelines/SOURCE_KMA_SHORT_TERM_FORECAST/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_KMA_SHORT_TERM_FORECAST_NXNY_GRID` | SELECTED | KMA 5km `nx/ny` grid | 8 issuances/day, hourly forecast rows | Accept with API-key gap |

Decision note:

```text
KMA 단기예보의 native space key는 nx/ny이다. 행정동을 grid로 fan-out하지 않고, 시군구별 대표점으로 요청 grid만 선정한다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | openapi |
| endpoint_or_layer | `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst` |
| request_or_download_path | `sample_request.json` |
| expected_format | JSON, XML |
| actual_format | JSON error response captured: `resultCode=10`, 최근 3일 간의 자료만 제공합니다 |
| snapshot_path | `data/raw/SOURCE_KMA_SHORT_TERM_FORECAST/snapshots/sample_20260430/` |
| captured_at | 2026-04-30 |

Raw fields observed from official response schema:

```text
baseDate, baseTime, category, fcstDate, fcstTime, fcstValue, nx, ny
```

Auth/quota/schema:

```text
auth: public data.go.kr service key
quota: 개발계정 10,000 calls; 운영계정은 활용사례 등록 후 증가 가능
response item schema: response.body.items.item[]
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `baseDate/baseTime`, `fcstDate/fcstTime` |
| temporal_semantics | `forecast_issued_at`, `forecast_valid_time` |
| native_temporal_grain | 발표시각 8회/일, 예보시각 hourly |
| native_time_format | `YYYYMMDD` + `HHMM` KST |
| parse_example | `baseDate=20260415`, `baseTime=0500`, `fcstDate=20260415`, `fcstTime=0600` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `nx`, `ny` |
| geometry_field | none in API body |
| spatial_semantics | grid |
| native_spatial_grain | 5km KMA grid |
| native_crs | KMA DFS grid |
| region_filter_method | representative point -> KMA grid request, preserve returned `nx/ny` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 0 for fixed PoC request on 2026-04-30 |
| spatial_intersection_result | pass: PoC representative grid request prepared |
| temporal_coverage_result | partial: API only serves recent 3 days, so 2026-04-15~2026-04-21 forecast rows are unavailable on 2026-04-30 |
| poc_coverage_result | partial |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | no |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- API key is available through environment variables, but the fixed historical PoC forecast window is outside KMA's recent-data retention for this endpoint.
```
