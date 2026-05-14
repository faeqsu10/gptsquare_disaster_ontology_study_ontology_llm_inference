# Source Dossier — source_id

| 항목 | 내용 |
|---|---|
| source_id | `source_id` |
| selected_access_option_id | `access_option_id` |
| availability_status | REAL / MOCK / EXCLUDE |
| verification_status | unverified |
| sample_path |  |
| pipeline_path | `pipelines/<source_id>/` |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `access_option_id` | CANDIDATE / SELECTED / FALLBACK / REJECTED |  |  |  |

Decision note:

```text
왜 이 option을 선택/보류/제외했는지 기록.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method |  |
| endpoint_or_layer |  |
| request_or_download_path |  |
| expected_format |  |
| actual_format |  |
| snapshot_path |  |
| captured_at |  |

Raw fields observed:

```text
- field_1
- field_2
```

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field |  |
| temporal_semantics |  |
| native_temporal_grain |  |
| native_time_format |  |
| parse_example |  |
| time_parse_result | not_tested |

Notes:

```text
Raw 단계에서는 시간 grid alignment를 수행하지 않는다.
```

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field |  |
| geometry_field |  |
| spatial_semantics |  |
| native_spatial_grain |  |
| native_crs |  |
| region_filter_method |  |
| validation_example |  |
| space_validation_result | not_tested |

Notes:

```text
Raw 단계에서는 좌표계 통일, 읍면동 fan-out, Segment join을 수행하지 않는다.
```

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count |  |
| spatial_intersection_result | not_tested |
| temporal_coverage_result | not_tested |
| poc_coverage_result | not_tested |

---

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | pending |
| fallback_required |  |
| mock_required |  |
| exclude_required |  |

Open issues:

```text
- issue_1
```
