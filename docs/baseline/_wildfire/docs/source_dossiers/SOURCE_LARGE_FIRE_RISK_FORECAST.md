# Source Dossier — SOURCE_LARGE_FIRE_RISK_FORECAST

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_LARGE_FIRE_RISK_FORECAST` |
| selected_access_option_id | `ACCESS_LARGE_FIRE_RISK_FORECAST_EUPMYEONDONG` |
| availability_status | REAL |
| verification_status | key_validated |
| sample_path | `data/raw/SOURCE_LARGE_FIRE_RISK_FORECAST/snapshots/sample_20260430/` |
| pipeline_path | `pipelines/SOURCE_LARGE_FIRE_RISK_FORECAST/` |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_LARGE_FIRE_RISK_FORECAST_EUPMYEONDONG` | SELECTED | 읍면동명 admin area | event/forecast row time; monthly published file | Sample file includes 읍면동명, 실효습도, 풍속, 등급. |

Decision note:

```text
The official file page and downloaded CSV expose 시도명, 시군구명, 읍면동명.
This satisfies the 읍면동 key requirement for the alert list source, although
the file does not carry administrative codes or geometry.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | file_download |
| endpoint_or_layer | `https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003631149&fileDetailSn=1&insertDataPrcus=N` |
| request_or_download_path | `pipelines/SOURCE_LARGE_FIRE_RISK_FORECAST/sample_request.json` |
| expected_format | CSV |
| actual_format | CSV, CP949; ODCloud JSON sample also captured |
| snapshot_path | `data/raw/SOURCE_LARGE_FIRE_RISK_FORECAST/snapshots/sample_20260430/large_fire_risk_forecast_20260331.csv` |
| captured_at | 2026-04-30 |

Additional API evidence:

```text
- ODCloud JSON sample: data/raw/SOURCE_LARGE_FIRE_RISK_FORECAST/snapshots/sample_20260430_odcloud/odcloud_response.json
- ODCloud status: HTTP 200, totalCount=48192
```

Raw fields observed:

```text
- 예보일시
- 시도명
- 시군구명
- 읍면동명
- 실효습도
- 풍속
- 등급
```

Field semantics (산림청 대형산불 발령 공식 기준):

| field | type | values / unit | 의미 |
|---|---|---|---|
| `등급` | enum (Korean) | `없음`, `주의보`, `경보` | 대형산불 발령 등급 |
| `실효습도` | numeric (%) | `[0, 100]` | 발령 판정 입력 |
| `풍속` | numeric (m/s) | `≥ 0` | 발령 판정 입력 |

발령 기준 (위험지수 ≥ 51 + 다음 조건 + 2일 이상 지속):

```text
대형산불주의보 : 30 ≤ 실효습도 ≤ 45  ∧  7 ≤ 풍속 < 11
대형산불경보   : 실효습도 < 30        ∧  풍속 ≥ 11
```

`등급` 필드는 산림청에서 위 기준을 적용한 결과만 row로 발행한다. 따라서 `없음`은 row 부재로 표현되며, 'row가 없는 것'과 'coverage가 없는 것'을 구분해야 한다 (§6 Open issues 참조).

`등급`이 비어 있을 때 fallback 산식은 [06_decision-logic.md](../06_decision-logic.md) §OfficialRiskSignal `derived_alert(...)`을 따르며, `SOURCE_OFFICIAL_FIRE_RISK_FORECAST.maxi` + `SOURCE_KMA_OBSERVED_WEATHER.{REH, WS}` + 2일 rolling window를 입력으로 사용한다.

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `예보일시` |
| temporal_semantics | forecast_valid_time / alert row time |
| native_temporal_grain | hourly/event row; monthly file publication |
| native_time_format | `YYYY-MM-DD HH:MM` |
| parse_example | `2017-01-17 15:00` |
| time_parse_result | pass |

Notes:

```text
Raw 단계에서는 시간 grid alignment를 수행하지 않는다.
```

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `시도명`, `시군구명`, `읍면동명` |
| geometry_field | none |
| spatial_semantics | admin_area |
| native_spatial_grain | 읍면동명 |
| native_crs | none; no geometry |
| region_filter_method | file download then raw row filter by native admin names |
| space_validation_result | pass |

Notes:

```text
Administrative names vary historically (`광주광역시` and `광주` both appear).
Do not normalize names or join codes in Raw phase.
```

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 0 exact rows |
| spatial_intersection_result | partial: 광주·전남 historical rows exist for past windows, but the requested 2026-04-15~2026-04-21 window is not covered |
| temporal_coverage_result | fail for requested window; latest published file is `_20260331` and downloaded rows end in 2026-03 |
| poc_coverage_result | partial |

---

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | no |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- Exact PoC window 2026-04-15~2026-04-21 cannot be verified until an April 2026 file is published.
- File has admin names only, not admin codes or geometry.
- Rows are alert-list rows; no row may mean no alert rather than no spatial coverage.
```
