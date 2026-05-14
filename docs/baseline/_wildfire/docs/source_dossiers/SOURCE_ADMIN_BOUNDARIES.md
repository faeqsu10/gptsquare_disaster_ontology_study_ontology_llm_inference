# Source Dossier — SOURCE_ADMIN_BOUNDARIES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_ADMIN_BOUNDARIES` |
| selected_access_option_id | `ACCESS_ADMIN_BOUNDARIES_ADMIN_CODE` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/` |
| pipeline_path | `pipelines/SOURCE_ADMIN_BOUNDARIES/` |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_ADMIN_BOUNDARIES_ADMIN_CODE` | SELECTED | 법정 읍면동 polygon-like WKB in CSV | registry/static metadata | full 원본과 광주·전남 clip 저장 |

Decision note:

```text
공공데이터포털 `국토교통부 국토지리정보원_공간정보공동활용_읍면동_20230915` 원문 CSV를 확인했다.
원천은 읍면동코드, 읍면동명, 객체시군구코드, 공간정보(WKB)를 제공한다.
원본 full CSV와 광주·전남 clip을 저장했다.
행정동 단위 polygon은 이 경계 원천에 직접 존재하지 않으며, 법정동 polygon만 제공된다.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | file_download |
| endpoint_or_layer | https://www.data.go.kr/data/15123128/fileData.do |
| direct_download_url | https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000002819529&fileDetailSn=1&insertDataPrcus=N |
| expected_format | CSV |
| actual_format | CSV, CP949-compatible source bytes, WKB hex geometry field |
| source_file_name | `LP_AA_EMD.csv` |
| source_file_size | 109,743,962 bytes |
| full_snapshot_path | `data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/LP_AA_EMD.csv` |
| gwangju_jeonnam_clip_path | `data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/LP_AA_EMD_gwangju_jeonnam.csv` |
| metadata_path | `data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/metadata.json` |
| captured_at | 2026-04-30T10:34:29.851961+00:00 |

Raw fields observed:

```text
- 공간정보일렬번호
- 읍면동코드
- 읍면동명
- 객체시군구코드
- 오브젝트아이디
- 공간정보
```

Clip evidence:

```text
full_feature_count: 5028
gwangju_jeonnam_filter: 객체시군구코드 prefix in 29, 46
gwangju_jeonnam_feature_count: 622
gwangju_feature_count: 202
jeonnam_feature_count: 420
```

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `source_metadata.dateModified` |
| temporal_semantics | registry_updated_at, static |
| native_temporal_grain | 수시 (1회성 데이터), source metadata |
| native_time_format | YYYY-MM-DD |
| parse_example | `2025-11-20` |
| time_parse_result | pass |

Notes:

```text
Raw 데이터 행에는 관측/유효 시간이 없다. 행정경계 기준 레이어이므로 source registry metadata를 time key로 기록한다.
```

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `읍면동코드`, `객체시군구코드`, `공간정보` |
| geometry_field | `공간정보` |
| spatial_semantics | polygon, admin_area |
| native_spatial_grain | 법정 읍면동 WKB geometry |
| native_crs | source metadata에 명시 없음 |
| region_filter_method | 광주·전남 clip은 `객체시군구코드` prefix `29`/`46` |
| space_validation_result | pass |

Validation examples:

| code | name | sigungu_code | geometry_prefix | geometry_present |
|---|---|---|---|---|

Notes:

```text
좌표계 변환, geometry rewrite, 행정동 fan-out, spatial join은 수행하지 않았다.
```

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | full 5,028 features; 광주·전남 622 features (광주 202, 전남 420) |
| spatial_intersection_result | not_performed_raw_phase |
| temporal_coverage_result | static/reference metadata only |
| poc_coverage_result | partial |

PoC checks:

| check | result |
|---|---|
| 광주광역시 legal sido code | `29` |

---

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- SOURCE_ADMIN_BOUNDARIES full 원본과 광주·전남 clip은 확보했다.
- 이 Source는 법정 읍면동 경계만 제공하며 행정동 polygon은 직접 제공하지 않는다.
- 행정동 단위 decision unit이 필요하면 행정동 경계 Source 또는 법정동-행정동 mapping을 별도 Source로 검증해야 한다.
- source metadata에 native CRS가 명시되어 있지 않다. Raw WKB는 변환하지 않았다.
```
