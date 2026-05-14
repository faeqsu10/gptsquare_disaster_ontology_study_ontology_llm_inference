# Source Dossier — SOURCE_VULNERABLE_FACILITIES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_VULNERABLE_FACILITIES` |
| selected_access_option_id | `ACCESS_VULNERABLE_FACILITIES_GJ_SENIOR_NURSING_CSV` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_VULNERABLE_FACILITIES/snapshots/regional_clip/` |
| full_snapshot_path | `data/raw/SOURCE_VULNERABLE_FACILITIES/snapshots/full_gwangju_jeonnam_20260430/` |
| mock_fallback_path | `data/mock/SOURCE_VULNERABLE_FACILITIES/scenario_baseline/` |
| pipeline_path | `pipelines/SOURCE_VULNERABLE_FACILITIES/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_VULNERABLE_FACILITIES_GJ_SENIOR_NURSING_CSV` | SELECTED | facility admin/address | registry date | Concrete no-auth CSV source; full file and Dong-gu clip acquired. |
| `ACCESS_VULNERABLE_FACILITIES_JN_ELDERLY_WELFARE_MOCK` | FALLBACK | synthetic facility point/admin/address | scenario time | Generated fallback for the unavailable Jeonnam elderly-welfare API; covers all 22 Jeonnam sigungu. |
| `ACCESS_VULNERABLE_FACILITIES_TBD` | REJECTED | unknown | unknown | Replaced by concrete URL. |

Decision note:

```text
The source provides senior nursing facility rows with 시도, 시군구, facility name, address, capacity, status, and 데이터기준일자. It has no native coordinate fields, so address/admin text is preserved and any geocoding is deferred.
The Jeonnam elderly-welfare OpenAPI remains unavailable in this session; a generated mock fallback is kept separately under data/mock and is explicitly marked as synthetic.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | file_download |
| endpoint_or_layer | `https://www.data.go.kr/data/15043855/fileData.do` |
| request_or_download_path | direct file download URL in `sample_metadata.json` |
| expected_format | CSV |
| actual_format | CSV, utf-8-sig |
| snapshot_path | `senior_nursing_facilities_gwangju_20241231.csv` |
| captured_at | 2026-04-30 |

Mock fallback evidence:

| 항목 | 값 |
|---|---|
| acquisition_method | generated_mock |
| source_url_reference | `https://www.data.go.kr/data/15102882/openapi.do` |
| generator | `pipelines/SOURCE_VULNERABLE_FACILITIES/generate_elderly_welfare_mock.py` |
| output_path | `data/mock/SOURCE_VULNERABLE_FACILITIES/scenario_baseline/` |
| generated_at | 2026-05-01 |
| row_count | 1,774 Jeonnam mock rows |
| type_counts | 노인양로복지시설 25; 노인의료복지시설 94; 노인여가복지시설 55; 경로당 1,596; 노인보호전문기관 4 |
| Gwangju handling | skipped; existing real Gwangju senior/medical welfare rows retained |

Raw fields observed:

```text
- 연번
- 시도
- 시군구
- 시설명
- 시설종류
- 장기요양지정기관여부
- 시설입소현황(정원)
- 시설입소현황(남)
- 시설입소현황(여)
- 종사자수(남)
- 종사자수(여)
- 소재지도로명주소
- 전화번호
- 팩스번호
- 시설설치일자
- 설치주체(민간)
- 운영주체(법인(단체)명)
- 운영주체(설치주체)
- 운영주체(영리구분)
- 휴업중
- 데이터기준일자
- apiSeq
- city
- location
- posX
- posY
- space_key
- scenario_time
- valid_from
- valid_to
- mock_source
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `데이터기준일자`; mock `scenario_time`, `valid_from`, `valid_to` |
| temporal_semantics | registry_updated_at; scenario_time for mock fallback |
| native_temporal_grain | annual file reference date; scenario-defined mock |
| native_time_format | `YYYY-MM-DD`; mock ISO-8601 timezone |
| parse_example | `2024-12-31`; `2026-05-01T02:00:00+09:00` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `시도`, `시군구`, `소재지도로명주소`; mock `space_key`, `city`, `emd_code`, `location`, `posX`, `posY` |
| geometry_field | none for real files; mock `posX`, `posY` and GeoJSON Point |
| spatial_semantics | address, admin_area; synthetic point for mock fallback |
| native_spatial_grain | facility address; synthetic facility point within admin boundary |
| native_crs | no_geometry for real files; EPSG:4326 for mock fallback |
| region_filter_method | native `시군구` text filter for 광주광역시; mock generated for all Jeonnam sigungu from admin boundary/code snapshots; no geocoding |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 102 Gwangju senior rows; 102 Gwangju medical welfare rows; 79 Jeonnam nursing hospital rows; 1,774 Jeonnam mock elderly-welfare rows |
| spatial_intersection_result | partial via real admin/address; Jeonnam mock covers all 22 sigungu with synthetic points |
| temporal_coverage_result | not_applicable for static registry; mock scenario time covers PoC window |
| poc_coverage_result | partial |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | yes |
| mock_required | yes for Jeonnam elderly-welfare API gap |
| exclude_required | no |

Open issues:

```text
- No native coordinates; preserve source address and admin fields only.
- Full snapshot includes Gwangju senior nursing/medical welfare rows and Jeonnam nursing hospital rows.
- Jeonnam elderly welfare API (`전라남도_어르신 종합 복지시설 유형별 정보`) returned HTTP 404 for all five functions after the 2026-05-01 retry.
- Mock fallback covers five Jeonnam elderly-welfare classes across 22 sigungu; generated coordinates/addresses are synthetic and must not be treated as official facility locations.
```
