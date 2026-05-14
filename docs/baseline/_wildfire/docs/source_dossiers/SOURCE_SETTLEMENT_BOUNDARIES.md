# Source Dossier - SOURCE_SETTLEMENT_BOUNDARIES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_SETTLEMENT_BOUNDARIES` |
| selected_access_option_id | none |
| availability_status | EXCLUDE |
| verification_status | source_confirmed |
| sample_path | none in current regional freeze |
| pipeline_path | not applicable |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_SETTLEMENT_BOUNDARIES_BASELINE_SCENARIO` | REJECTED | settlement polygon | scenario-defined | 기존 settlement mock은 광주·전남 regional source로 사용할 수 없어 제외한다. |

Decision note:

```text
기존 settlement mock은 일부 행정동만 표현했으며 광주·전남 coverage를 대표하지 않는다.
주거지 노출은 별도 settlement source가 아니라 building footprint, population,
admin boundary/code 기반 Derived Dataset으로 산출한다.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | excluded |
| endpoint_or_layer | archived PoC-only mock concept |
| request_or_download_path | none in current regional freeze |
| expected_format | CSV, GeoJSON |
| actual_format | not part of current freeze |
| snapshot_path | none |
| captured_at | not_applicable |

Expected fields from archived concept:

```text
- settlement_id
- settlement_name
- admin_sido
- admin_sigungu
- admin_eupmyeondong
- scenario_time
- valid_from
- valid_to
- geometry
```

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `scenario_time`, `valid_from`, `valid_to` |
| temporal_semantics | scenario_time |
| native_temporal_grain | scenario-defined |
| native_time_format | ISO 8601 expected |
| parse_example | not_applicable in current freeze |
| time_parse_result | not_tested |

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `space_key`, `settlement_id`, `geometry` expected |
| geometry_field | `geometry` |
| spatial_semantics | polygon |
| native_spatial_grain | settlement polygon |
| native_crs | EPSG:4326 expected |
| region_filter_method | generated directly for PoC only |
| validation_example | not_applicable in current freeze |
| space_validation_result | not_tested |

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | not part of current regional freeze |
| spatial_intersection_result | archived PoC-only concept |
| temporal_coverage_result | archived PoC-only concept |
| poc_coverage_result | excluded |

---

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | EXCLUDE |
| fallback_required | no |
| mock_required | no |
| exclude_required | yes |

Open issues:

```text
- 광주·전남 전체 마을 경계의 공개 표준 source가 확정되면 새 Source로 재검토할 수 있다.
- 현재 Feature/Derived dependency에서는 사용하지 않는다.
- ResidentialExposureFeature는 building + population + admin proxy를 사용한다.
```
