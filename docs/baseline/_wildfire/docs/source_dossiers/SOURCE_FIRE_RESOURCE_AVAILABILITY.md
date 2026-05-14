# Source Dossier — SOURCE_FIRE_RESOURCE_AVAILABILITY

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FIRE_RESOURCE_AVAILABILITY` |
| selected_access_option_id | `ACCESS_FIRE_RESOURCE_AVAILABILITY_BASELINE_SCENARIO` |
| availability_status | MOCK |
| verification_status | coverage_verified |
| sample_path | `data/mock/SOURCE_FIRE_RESOURCE_AVAILABILITY/scenario_baseline/` |
| pipeline_path | `pipelines/SOURCE_FIRE_RESOURCE_AVAILABILITY/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_FIRE_RESOURCE_AVAILABILITY_BASELINE_SCENARIO` | SELECTED | station_id row | 8-hour shift period | generated mock baseline |

Decision note:

```text
실시간 인력·차량 가용성은 공개 source로 확보하기 어렵다. 현재 mock 사용 규칙은 [../02_source-layer.md](../02_source-layer.md)의 Mock Contract와 [../07_runtime-operations.md](../07_runtime-operations.md)의 Runtime Overlay 규칙을 따른다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | generated_mock |
| endpoint_or_layer | scenario baseline |
| request_or_download_path | `pipelines/SOURCE_FIRE_RESOURCE_AVAILABILITY/generate.py` |
| expected_format | CSV |
| actual_format | CSV |
| snapshot_path | `data/mock/SOURCE_FIRE_RESOURCE_AVAILABILITY/scenario_baseline/fire_resource_availability_mock.csv` |
| captured_at | `mock_generated_at=2026-04-30T00:00:00+09:00` |
| row_count | 950 |

Raw fields observed:

```text
- valid_from
- valid_to
- station_id
- available_staff
- available_engines
- available_water_tankers
- available_portable_pumps
- resource_status
- mock_seed
- mock_generated_at
- mock_reason
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `valid_from`, `valid_to` |
| temporal_semantics | effective_period, scenario_time |
| native_temporal_grain | 8-hour shift period |
| native_time_format | ISO-8601 with +09:00 |
| parse_example | `2026-05-01T02:00:00+09:00` to `2026-05-01T08:00:00+09:00` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `station_id` |
| geometry_field | 없음 |
| spatial_semantics | address / no_geometry |
| native_spatial_grain | station_id |
| native_crs | not_applicable |
| region_filter_method | generated directly for PoC region |
| validation_example | `119C-300`, `119C-301`, `119C-302` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 950 |
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
- mock 값을 Feature score로 변환하지 않는다.
```
