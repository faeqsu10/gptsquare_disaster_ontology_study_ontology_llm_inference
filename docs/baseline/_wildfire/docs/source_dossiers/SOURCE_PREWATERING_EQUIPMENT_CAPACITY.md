# Source Dossier — SOURCE_PREWATERING_EQUIPMENT_CAPACITY

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_PREWATERING_EQUIPMENT_CAPACITY` |
| selected_access_option_id | `ACCESS_PREWATERING_EQUIPMENT_CAPACITY_BASELINE_SCENARIO` |
| availability_status | MOCK |
| verification_status | coverage_verified |
| sample_path | `data/mock/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/scenario_baseline/` |
| pipeline_path | `pipelines/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_PREWATERING_EQUIPMENT_CAPACITY_BASELINE_SCENARIO` | SELECTED | station/equipment id, no geometry | scenario effective period | generated mock baseline |

Decision note:

```text
장비별 주수량·설치시간·유효폭은 내부 운영경험 자료 성격이므로 PoC baseline mock으로 생성했다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | generated_mock |
| endpoint_or_layer | scenario baseline |
| request_or_download_path | `pipelines/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/generate.py` |
| expected_format | CSV |
| actual_format | CSV |
| snapshot_path | `data/mock/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/scenario_baseline/prewatering_equipment_capacity_mock.csv` |
| captured_at | `mock_generated_at=2026-04-30T00:00:00+09:00` |
| row_count | 312 |

Raw fields observed:

```text
- scenario_time
- valid_from
- valid_to
- station_id
- equipment_id
- equipment_type
- watering_rate_lpm
- setup_time_min
- effective_width_m
- mobility_class
- mock_seed
- mock_generated_at
- mock_reason
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `scenario_time`, `valid_from`, `valid_to` |
| temporal_semantics | scenario_time, effective_period |
| native_temporal_grain | scenario effective period |
| native_time_format | ISO-8601 with +09:00 |
| parse_example | `2026-05-01T02:00:00+09:00` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `station_id`, `equipment_id` |
| geometry_field | 없음 |
| spatial_semantics | no_geometry |
| native_spatial_grain | equipment row |
| native_crs | not_applicable |
| region_filter_method | generated directly for PoC region |
| validation_example | `119C-300-EQ-01` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 312 |
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
- watering_rate_lpm 등 raw parameter를 Feature score처럼 표현하지 않는다.
```
