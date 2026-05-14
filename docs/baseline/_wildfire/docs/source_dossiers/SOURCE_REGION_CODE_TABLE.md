# Source Dossier — SOURCE_REGION_CODE_TABLE

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_REGION_CODE_TABLE` |
| selected_access_option_id | `ACCESS_REGION_CODE_TABLE_ADMIN_CODE` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/` |
| pipeline_path | `pipelines/SOURCE_REGION_CODE_TABLE/` |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_REGION_CODE_TABLE_ADMIN_CODE` | SELECTED | 법정동/시군구/시도 code table | annual registry metadata | full CSV 저장 |
| `ACCESS_REGION_CODE_TABLE_KOSTAT_ADMIN_DONG` | FALLBACK proposal | 행정동 code table | annual registry metadata + 개정일자 | 법정동 table이 행정동명을 식별하지 못할 때 쓰는 행정동 보완 option |
| `ACCESS_REGION_CODE_TABLE_MOIS_ADMIN_LEGAL_MAPPING` | SUPPLEMENTAL proposal | 행정기관/행정동 ↔ 관할 법정동 mapping | registry effective period | 행정기관코드와 관할 법정동코드를 연결하는 raw text 보완 option |

Decision note:

```text
기존 candidate인 `국토교통부_전국 법정동_20250807`은 광주·전남 시도/시군구/법정동을 검증할 수 있다.
행정동 단위 식별이 필요할 때를 위해 `국가데이터처_행정동 정보_20250704`를 보완 AccessOption으로 조사하고 full snapshot에 함께 저장했다.
두 full 파일에서 광주·전남 region clip도 추가 생성했다.
추가로 행정안전부 `jscode20260325` 원천 텍스트 3종을 full snapshot에 저장했다. 저장 파일명에서는 `(말소코드포함)` 문자열을 제거했다.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | file_download |
| legal_table_endpoint | https://www.data.go.kr/data/15063424/fileData.do |
| admin_table_endpoint | https://www.data.go.kr/data/15136373/fileData.do |
| admin_legal_mapping_endpoint | https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=124721 |
| expected_format | CSV, fixed-width text |
| actual_format | CSV, fixed-width text |
| snapshot_path | `data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/` |
| captured_at | 2026-04-30T10:33:48.012568+00:00 |

Files:

| role | path | rows | 광주·전남 rows | source_modified_at |
|---|---|---:|---:|---|
| legal_dong_code_table | `national_legal_dong_20250807.csv` | 49,878 | 5,069 | 2025-08-07 |
| administrative_dong_code_table | `kostat_admin_dong_20250704.csv` | 582,162 | 61,194 | 2025-07-07 |
| mois_admin_legal_mapping_table | `KIKmix.20260325` | 55,461 | not clipped | 2026-03-25 effective |
| mois_administrative_dong_code_table | `KIKcd_H.20260325` | 9,106 | not clipped | 2026-03-25 effective |
| mois_legal_dong_code_table | `KIKcd_B.20260325` | 50,103 | not clipped | 2026-03-25 effective |

File relationship summary:

```text
KIKcd_H.20260325 = MOIS 행정기관/행정동 코드표
KIKcd_B.20260325 = MOIS 법정동 코드표
KIKmix.20260325  = 행정기관코드와 관할 법정동코드를 연결하는 bridge table
```

Regional clips:

```text
national_legal_dong_gwangju_jeonnam.csv
  광주광역시 248 rows
  전라남도 4,821 rows
kostat_admin_dong_gwangju_jeonnam.csv
  KOSTAT top code 24 15,142 rows
  KOSTAT top code 36 46,052 rows
```

Raw fields observed:

```text
법정동 table:
- 법정동코드
- 시도명
- 시군구명
- 읍면동명
- 리명
- 순위
- 생성일자
- 삭제일자
- 과거법정동코드

행정동 table:
- 행정동번호
- 개정일자
- 연결번호
- 행정동코드
- 행정동명
- 배경여부
- 최상위행정동코드
- 부모행정동코드
- 순번

MOIS KiK text files:
- 행정동코드
- 법정동코드
- 시도명
- 시군구명
- 읍면동명
- 동리명
- 생성일자
- 말소일자
```

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `source_metadata.dateModified`, `개정일자`, `생성일자`, `말소일자` |
| temporal_semantics | registry_updated_at |
| native_temporal_grain | annual / irregular registry update |
| native_time_format | YYYY-MM-DD; YYYYMMDD in MOIS KiK files |
| parse_example | legal source `2025-08-07`; admin latest row `2025-04-01`; MOIS effective `20260325` |
| time_parse_result | pass |

Notes:

```text
법정동 full table은 source metadata의 modified date를 registry time으로 쓴다.
행정동 full table은 row-level `개정일자`도 보유한다.
MOIS KiK files는 `생성일자`와 `말소일자`로 행정기관/법정동 관계의 유효 기간을 표현한다.
```

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `법정동코드`, `행정동코드`, `MOIS 행정기관코드` |
| geometry_field | none |
| spatial_semantics | no_geometry, admin_area |
| native_spatial_grain | 법정동 code table; 행정동 code table |
| native_crs | not applicable; no geometry |
| region_filter_method | name/code filter for 광주광역시 (sido `29`), 전라남도 (sido `46`) |
| space_validation_result | pass |

Validation examples:

| grain | code | name | result |
|---|---|---|---|
| legal sido | `2900000000` | 광주광역시 | present |

Notes:

```text
KOSTAT 행정동코드는 법정동코드와 다른 분류체계다. 광주광역시는 KOSTAT 최상위행정동코드 `24`로 나타나며, 법정동 시도코드 `29`와 직접 동일시하지 않는다.
MOIS `KIKmix.20260325`는 행정기관코드와 관할 법정동코드를 연결한다.
```

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | legal full 49,878 rows; legal 광주·전남 5,069 rows; admin full 582,162 rows; admin 광주·전남 61,194 rows; MOIS KIKmix 55,461 rows |
| spatial_intersection_result | not_applicable_no_geometry |
| temporal_coverage_result | registry/static reference |
| poc_coverage_result | pass |

PoC checks:

| check | result |
|---|---|
| 광주광역시 법정동 시도코드 | `2900000000` |

---

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | no for code lookup; yes if legal-admin harmonized mapping is required |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- 행정동명은 법정동 table에는 없고 행정동 table에만 있다.
- KOSTAT 행정동코드와 법정동코드는 분류체계가 달라 직접 join key로 사용하면 안 된다.
- MOIS `KIKmix.20260325` raw mapping은 확보했지만, 이 transaction에서는 downstream 코드체계 harmonization, 법정동-행정동 면적 배분, spatial join을 수행하지 않았다.
```
