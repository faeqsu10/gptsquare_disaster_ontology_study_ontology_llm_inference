# Source Dossier — SOURCE_OFFICIAL_FIRE_RISK_FORECAST

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_OFFICIAL_FIRE_RISK_FORECAST` |
| selected_access_option_id | `ACCESS_OFFICIAL_FIRE_RISK_FORECAST_SIGUNGU` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/sample_20260430/` |
| pipeline_path | `pipelines/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/` |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_OFFICIAL_FIRE_RISK_FORECAST_EUPMYEONDONG` | REJECTED | not exposed | not exposed | Current official Swagger has no eupmyeondong endpoint or parameter. |
| `ACCESS_OFFICIAL_FIRE_RISK_FORECAST_SIGUNGU` | SELECTED | 시군구 admin area | current analysis/forecast issue cadence; provider states 3-hour forecast production | Best available numeric/admin-key option. |
| `ACCESS_OFFICIAL_FIRE_RISK_FORECAST_IMAGE_OR_GRID` | REJECTED | PNG/image presentation | monthly image bundle | Numeric raw fields and admin keys are not directly extractable from image files. |

Decision note:

```text
Official data.go.kr description and embedded Swagger state/provide 시군구 unit data.
Verified operations are forestPointListGeongugSearchV2, forestPointListSidoSearchV2,
and forestPointListSigunguSearchV2. No 읍면동 operation or query parameter was found.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | openapi |
| endpoint_or_layer | `https://apis.data.go.kr/1400377/forestPointV2/forestPointListSigunguSearchV2` |
| request_or_download_path | `pipelines/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/sample_request.json` |
| expected_format | JSON, XML |
| actual_format | JSON |
| snapshot_path | `data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/sample_20260430/` |
| captured_at | 2026-04-30 |

Raw fields observed from actual response and official Swagger:

```text
- resultCode
- resultMsg
- numOfRows
- pageNo
- totalCount
- analdate
- area
- d1
- d2
- d3
- d4
- doname
- maxi
- meanavg
- mini
- regioncode
- sigucode
- sigun
- std
- upplocalcd
```

Field semantics (산림청 DFFRI 공식 기준):

| field | type | values / range | 의미 |
|---|---|---|---|
| `std` | enum (Korean) | `정상`, `낮음`, `다소높음`, `높음`, `매우높음` | 산불위험예보지수 5단계 등급 |
| `maxi` | numeric | `[0, 100]` | 위험지수 최댓값. 임계 50 / 65 / 85에서 등급 경계 |
| `meanavg` | numeric | `[0, 100]` | 위험지수 평균값 |
| `mini` | numeric | `[0, 100]` | 위험지수 최솟값 |
| `d1`..`d4` | numeric or enum | 등급 또는 지수 | 1~4일 forecast horizon |

등급 임계 (산림청):

```text
정상       : 산불 위험이 거의 없음
낮음       : 위험지수 ≤ 50
다소높음   : 51 ≤ 위험지수 ≤ 65
높음       : 66 ≤ 위험지수 ≤ 85
매우높음   : 위험지수 ≥ 86
```

이 enum은 [06_decision-logic.md](../06_decision-logic.md) §Canonical Mock Enum Catalog에서 Feature lookup MAP key로 그대로 사용한다.

Additional captured snapshots:

```text
- 광주광역시 전체 시군구: data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/sample_20260430_gwangju_sigungu/
- 전라남도 전체 시군구: data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/sample_20260430_jeonnam_sigungu/
```

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `analdate` |
| temporal_semantics | forecast_valid_time-like forecast target time; separate issue time not exposed |
| native_temporal_grain | 3-hour interval forecast rows; endpoint exposes current forecast horizon only |
| native_time_format | `YYYY-MM-DD HH` |
| parse_example | `2026-04-30 18` |
| time_parse_result | pass |

Notes:

```text
Raw 단계에서는 시간 grid alignment를 수행하지 않는다.
No separate forecast issue time field is exposed in the verified response.
```

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `upplocalcd`, `sigucode`, `regioncode`, `doname`, `sigun` |
| geometry_field | none |
| spatial_semantics | admin_area |
| native_spatial_grain | 시군구 |
| native_crs | none; no geometry |
| region_filter_method | `upplocalcd=29` (광주광역시), `upplocalcd=46` (전라남도) |
| space_validation_result | pass |

Notes:

```text
읍면동 단위 key is not available from this OpenAPI. 시군구 값을 읍면동으로
fan-out하지 않는다.
```

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 광주 전체 170 rows; 전남 전체 748 rows |
| spatial_intersection_result | sigungu filter supported; eupmyeondong unsupported |
| temporal_coverage_result | current 2026-04-30~2026-05-04 forecast horizon captured; requested historical window not queryable |
| poc_coverage_result | partial |

---

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | fallback_required |
| fallback_required | yes: use 시군구 selected option because 읍면동 option is unavailable |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- The endpoint does not expose a 2026-04-15~2026-04-21 historical query parameter.
- The endpoint does not expose 읍면동 key or separate forecast issue time.
```
