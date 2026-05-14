# Source Dossier — SOURCE_WORKSITE_HAZARD_CONDITIONS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_WORKSITE_HAZARD_CONDITIONS` |
| selected_access_option_id | `ACCESS_WORKSITE_HAZARD_CONDITIONS_BASELINE_SCENARIO` |
| availability_status | MOCK |
| verification_status | coverage_verified |
| sample_path | `data/mock/SOURCE_WORKSITE_HAZARD_CONDITIONS/scenario_baseline/` |
| pipeline_path | `pipelines/SOURCE_WORKSITE_HAZARD_CONDITIONS/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_WORKSITE_HAZARD_CONDITIONS_BASELINE_SCENARIO` | SELECTED | generated segment point | scenario effective period | generated mock baseline |

Decision note:

```text
낙석·연기 노출 가능성은 현장성 데이터라 공개 coverage가 부족하므로 PoC baseline mock으로 생성했다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | generated_mock |
| endpoint_or_layer | scenario baseline |
| request_or_download_path | `pipelines/SOURCE_WORKSITE_HAZARD_CONDITIONS/generate.py` |
| expected_format | CSV, GeoJSON |
| actual_format | CSV, GeoJSON |
| snapshot_path | `data/mock/SOURCE_WORKSITE_HAZARD_CONDITIONS/scenario_baseline/` |
| captured_at | `mock_generated_at=2026-04-30T00:00:00+09:00` |
| row_count | 623 |

Raw fields observed:

```text
- valid_from
- valid_to
- segment_id
- rockfall_risk_flag
- smoke_exposure_possible
- hazard_severity
- geometry_wkt
- mock_seed
- mock_generated_at
- mock_reason
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `valid_from`, `valid_to` |
| temporal_semantics | effective_period, scenario_time |
| native_temporal_grain | scenario-defined |
| native_time_format | ISO-8601 with +09:00 |
| parse_example | `2026-05-01T02:00:00+09:00` to `2026-05-04T02:00:00+09:00` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `segment_id`, `geometry_wkt` |
| geometry_field | `geometry_wkt`, GeoJSON geometry |
| spatial_semantics | segment, point |
| native_spatial_grain | generated hazard point |
| native_crs | EPSG:4326; generated mock geometry |
| region_filter_method | generated directly for PoC region |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 623 |
| spatial_intersection_result | pass |
| temporal_coverage_result | pass |
| poc_coverage_result | pass |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | no |
| mock_required | already mock |
| exclude_required | no |

Open issues:

```text
- synthetic mock baseline이며 운영 데이터가 아니다.
- hazard_severity는 mock raw class이며 Feature score가 아니다.
```
