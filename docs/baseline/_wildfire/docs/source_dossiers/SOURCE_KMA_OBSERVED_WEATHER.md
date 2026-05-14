# Source Dossier — SOURCE_KMA_OBSERVED_WEATHER

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_KMA_OBSERVED_WEATHER` |
| selected_access_option_id | `ACCESS_KMA_OBSERVED_WEATHER_STATION` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/sample_20260430/` |
| pipeline_path | `pipelines/SOURCE_KMA_OBSERVED_WEATHER/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_KMA_OBSERVED_WEATHER_STATION` | SELECTED | ASOS station point | hourly observation period rows | Accept with API-key gap |

Decision note:

```text
KMA APIHub ASOS 시간자료는 station id를 native space key로 제공한다. 관측소 값을 행정동 단위로 보간하지 않는다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | openapi |
| endpoint_or_layer | `https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php` |
| request_or_download_path | `sample_request.json` |
| expected_format | TEXT/CSV-like table |
| actual_format | TEXT table captured |
| snapshot_path | `data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/sample_20260430/` |
| captured_at | 2026-04-30 |

Raw fields observed from official response schema:

```text
TM, STN, WD, WS, GST_WD, GST_WS, GST_TM, TA, HM, RN, RN_DAY, RN_INT
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
| time_key_field | `TM` |
| temporal_semantics | `observed_at` |
| native_temporal_grain | hourly observation rows for selected period |
| native_time_format | `YYYYMMDDHHMM` KST |
| parse_example | `TM=202604150000` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `STN` |
| geometry_field | station lon/lat from station metadata, not observation row |
| spatial_semantics | point |
| native_spatial_grain | station point |
| native_crs | KMA station lon/lat metadata, preserve station id in raw |
| region_filter_method | use 광주 ASOS `stn=156` as station-point source |
| validation_example | `STN=156` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 168 hourly rows |
| spatial_intersection_result | pass: Gwangju station-point source selected |
| temporal_coverage_result | pass: 2026-04-15 00:00 through 2026-04-21 23:00 hourly rows captured |
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
- Station point grain is preserved; no interpolation to administrative-dong grain is performed.
```
