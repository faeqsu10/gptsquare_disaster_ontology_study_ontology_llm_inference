# Source Dossier - SOURCE_CRITICAL_INFRASTRUCTURE_DETAIL

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_CRITICAL_INFRASTRUCTURE_DETAIL` |
| selected_access_option_id | none |
| availability_status | EXCLUDE |
| verification_status | unverified |
| sample_path | none |
| pipeline_path | not applicable |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_CRITICAL_INFRASTRUCTURE_DETAIL_DETAILED_INTERNAL` | REJECTED | facility point/line | irregular updates | 전력·통신시설 상세 위치는 보안 민감도가 높아 공개 실습 source로 쓰지 않는다. |

Decision note:

```text
이 source는 decision value가 있지만, 보안·민감성 때문에 active Source layer에서 제외한다.
문화재, 공공시설, 취약시설, 주거지 노출로 초기 판단을 대체하고,
필요 시 RequestManualReview 사유로만 보존한다.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | excluded |
| endpoint_or_layer | 전력·통신기관 내부 또는 제한 공개 자료 |
| request_or_download_path | none |
| expected_format | not_applicable |
| actual_format | not_acquired |
| snapshot_path | none |
| captured_at | not_applicable |

Raw fields expected but not acquired:

```text
- 전력시설 위치
- 통신시설 위치
- geometry
```

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `snapshot_metadata.snapshot_date` expected |
| temporal_semantics | static / registry_updated_at |
| native_temporal_grain | irregular updates |
| native_time_format | unknown |
| parse_example | not_applicable |
| time_parse_result | not_tested |

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | geometry expected |
| geometry_field | geometry expected |
| spatial_semantics | point, line |
| native_spatial_grain | facility point/line |
| native_crs | unknown |
| region_filter_method | not_applicable |
| validation_example | not_applicable |
| space_validation_result | not_tested |

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 0 acquired |
| spatial_intersection_result | not_tested |
| temporal_coverage_result | not_tested |
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
- 실제 운영에서 발전소, 변전소, 통신시설 인접성이 결정 분기점이면 RequestManualReview 사유로 처리한다.
- active Feature, Derived Dataset, Signal 입력으로 직접 사용하지 않는다.
```
