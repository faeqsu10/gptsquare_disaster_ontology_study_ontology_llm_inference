# Source Dossier - SOURCE_NATURAL_BARRIERS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_NATURAL_BARRIERS` |
| selected_access_option_id | `ACCESS_NATURAL_BARRIERS_PRIMARY` |
| availability_status | EXCLUDE |
| verification_status | source_confirmed |
| sample_path | `data/raw/SOURCE_NATURAL_BARRIERS/snapshots/sample_20260430/` |
| pipeline_path | `pipelines/SOURCE_NATURAL_BARRIERS/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_NATURAL_BARRIERS_PRIMARY` | REJECTED proposed | line/polygon | metadata update date/static | Excluded |

Decision note:

```text
Excluded by user decision. Natural barrier contribution will be unavailable/missing in the PoC path.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | manual_download |
| endpoint_or_layer | https://www.data.go.kr/data/15059910/fileData.do |
| request_or_download_path | http://map.ngii.go.kr/ms/map/NlipMap.do?tabGb=total |
| expected_format | SHP, NGI |
| actual_format | metadata only |
| snapshot_path | `data/raw/SOURCE_NATURAL_BARRIERS/snapshots/sample_20260430/` |
| captured_at | 2026-04-30 |

Raw fields observed:

```text
- 수계
- 지형
- 교통
- metadata.modified
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `metadata.modified` |
| temporal_semantics | registry_updated_at, static |
| native_temporal_grain | 수시 자동 갱신 |
| native_time_format | YYYY-MM-DD |
| parse_example | 2025-06-23 |
| time_parse_result | not_applicable |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | geometry |
| geometry_field | SHP/NGI geometry |
| spatial_semantics | line, polygon |
| native_spatial_grain | line/polygon |
| native_crs | not inspected; preserve native SHP/NGI CRS |
| region_filter_method | platform user-selected area |
| validation_example | metadata lists barrier-relevant line/polygon classes |
| space_validation_result | not_applicable |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | not downloaded |
| spatial_intersection_result | not_applicable |
| temporal_coverage_result | not_applicable |
| poc_coverage_result | not_applicable |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | exclude |
| fallback_required | no |
| mock_required | no |
| exclude_required | yes |

Open issues:

```text
- Source excluded by user decision.
- No barrier candidate derivation or Segment join was computed.
```
