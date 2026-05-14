# Source Dossier - SOURCE_ROAD_ACCESS_CONSTRAINTS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_ROAD_ACCESS_CONSTRAINTS` |
| selected_access_option_id | `ACCESS_ROAD_ACCESS_CONSTRAINTS_BASELINE_SCENARIO` |
| availability_status | MOCK |
| verification_status | coverage_verified |
| sample_path | `data/mock/SOURCE_ROAD_ACCESS_CONSTRAINTS/scenario_baseline/` |
| pipeline_path | `pipelines/SOURCE_ROAD_ACCESS_CONSTRAINTS/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_ROAD_ACCESS_CONSTRAINTS_BASELINE_SCENARIO` | SELECTED | road segment | scenario period | Generated baseline accepted |

Decision note:

```text
Generated rows include explicit `road_segment_id`, start/end node IDs, road name, and geometry. The mock models road width, slope, turn-around possibility, and firetruck access flags without computing travel time.
Updated baseline now covers 광주·전남 using SOURCE_REGION_CODE_TABLE current legal 읍면동 rows as coverage units.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | generated_mock |
| endpoint_or_layer | scenario_baseline |
| request_or_download_path | `pipelines/SOURCE_ROAD_ACCESS_CONSTRAINTS/generate.py` |
| expected_format | CSV, GeoJSON |
| actual_format | CSV, GeoJSON, manifest JSON |
| snapshot_path | `data/mock/SOURCE_ROAD_ACCESS_CONSTRAINTS/scenario_baseline/` |
| captured_at | 2026-05-01 |

Raw fields observed:

```text
- road_segment_id
- road_name
- road_class
- start_node_id
- end_node_id
- coverage_unit_id
- coverage_unit_name
- geometry_wkt
- road_width_m
- slope_percent
- firetruck_accessible
- turnaround_available
- narrow_road_flag
- valid_from
- valid_to
- mock_generated_at
- coverage_basis
- code_match_status
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | scenario_time, valid_from, valid_to, mock_generated_at |
| temporal_semantics | scenario_time |
| native_temporal_grain | scenario period |
| native_time_format | ISO-8601 with +09:00 offset |
| parse_example | 2026-05-01T02:00:00+09:00 |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | road_segment_id, start_node_id, end_node_id, coverage_unit_id, geometry_wkt |
| geometry_field | geometry_wkt |
| spatial_semantics | segment |
| native_spatial_grain | road segment |
| native_crs | EPSG:4326 |
| region_filter_method | generated from SOURCE_REGION_CODE_TABLE 광주·전남 current legal 읍면동 coverage units with SOURCE_ADMIN_BOUNDARIES/VWorld representative coordinates |
| validation_example | 623 unique `coverage_unit_id`; 광주 202, 전남 421 |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 623 |
| spatial_intersection_result | pass_by_generation; 광주·전남 current legal 읍면동 coverage units covered |
| temporal_coverage_result | pass |
| poc_coverage_result | pass |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept |
| fallback_required | no |
| mock_required | yes |
| exclude_required | no |

Open issues:

```text
- Mock input must be propagated downstream as mock_input=true.
- No travel time or real road-network join was computed.
```
