# Source Dossier — SOURCE_POPULATION_STATISTICS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_POPULATION_STATISTICS` |
| selected_access_option_id | `ACCESS_POPULATION_STATISTICS_DATAGOKR_AGE_GENDER` (primary), `ACCESS_POPULATION_STATISTICS_DATAGOKR_HOUSEHOLD_SIZE` (companion) |
| availability_status | REAL |
| verification_status | coverage_verified |
| pipeline_path | `pipelines/SOURCE_POPULATION_STATISTICS/` |

---

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_POPULATION_STATISTICS_DATAGOKR_AGE_GENDER` | SELECTED | 행정동 (`행정기관코드` 10자리) | 월별 (`기준연월`) | 채택. 광주·전남 행정동 row 검증 통과. |
| `ACCESS_POPULATION_STATISTICS_DATAGOKR_HOUSEHOLD_SIZE` | SELECTED | 행정동 | 월별 | 채택. `ResidentialExposureFeature`의 "세대 수" 입력 직접 충족. |
| `ACCESS_POPULATION_STATISTICS_PRIMARY` | REJECTED | 행정동 | 월별 | jumin.mois.go.kr web UI는 JS 동적 export로 보호되어 있어 자동화 reproducibility 낮음. data.go.kr file 자료가 동일 데이터를 직접 download URL로 제공하므로 대체. |

Decision note:

```text
data.go.kr file 자료 두 개가 한 쌍을 이루어 ResidentialExposureFeature의
"세대 수, 인구" 입력을 모두 충족한다. 둘 다 행정안전부 발행, 같은 기준연월,
같은 행정기관코드를 join key로 갖는다. jumin.mois.go.kr는 같은 데이터의
human-facing UI이지만 자동화에 부적합하므로 SELECTED에서 제외한다.
```

---

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | manual_download (one-time fixed snapshot, no fetch pipeline) |
| endpoint_or_layer | `https://www.data.go.kr/data/15097972/fileData.do`, `https://www.data.go.kr/data/15097974/fileData.do` |
| request_or_download_evidence | `pipelines/SOURCE_POPULATION_STATISTICS/acquisition_evidence.json` |
| expected_format | CSV (EUC-KR) |
| actual_format | CSV (EUC-KR), 콤마 구분, CRLF |
| snapshot_path | `data/raw/SOURCE_POPULATION_STATISTICS/snapshots/full_20260331/`, `.../full_gwangju_jeonnam_20260331/` |
| captured_at | 2026-04-30 KST |
| update_strategy | 정적 snapshot 1회 보존. 다음 정기 발표 후 manual으로 새 디렉토리에 추가 (READMEs §4 절차) |

Raw fields observed (인구 자료 `15097972`):

```text
- 행정기관코드        # 10-digit MOIS administrative-dong code
- 기준연월            # YYYY-MM-DD (2026-03-31)
- 시도명, 시군구명, 읍면동명
- 계, 남자, 여자
- 0세남자 ... 100세이상남자  # 101 columns
- 0세여자 ... 100세이상여자  # 101 columns
```

Raw fields observed (세대수 자료 `15097974`):

```text
- 행정기관코드, 기준연월, 시도명, 시군구명, 읍면동명
- 전체세대수
- 1인세대, 2인세대, 3인세대, 4인세대, 5인세대, 6인세대, 7인세대, 8인세대, 9인세대, 10인이상세대
```

Row counts:

| snapshot | 인구 | 세대수 |
|---|---|---|
| full (전국) | 3,619 | 3,619 |
| full_gwangju_jeonnam (광주 96 + 전남 323) | 419 | 419 |

---

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `기준연월` (column 2) + source_metadata 발행일 |
| temporal_semantics | `registry_updated_at` |
| native_temporal_grain | 월별 (월말 기준) |
| native_time_format | `YYYY-MM-DD` (실제 row 값: `2026-03-31`) |
| parse_example | `2026-03-31` → ISO date |
| time_parse_result | pass |

Notes:

```text
이 source는 forecast가 아니라 administrative_registry이므로 매 시각 row를
요구하지 않는다. 가장 가까운 정기 발표(2026-03-31 기준)를 사용하며, 산불
의사결정에서 인구·세대 구조는 분 단위로 변하지 않으므로 시즌 단위 사용에
충분하다. 다음 정기 발표(2026-04-30 기준)가 발행되면 동일 endpoint에서
갱신 가능.
```

---

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `행정기관코드` (10-digit) |
| geometry_field | (없음) |
| spatial_semantics | `admin_area`, `no_geometry` |
| native_spatial_grain | 행정동 (읍면동) |
| native_crs | not applicable; no geometry |
| region_filter_method | full file 보존 + byte-level line 필터(`행정기관코드` prefix 29/46) → `full_gwangju_jeonnam_20260331/` |
| space_validation_result | pass |

Notes:

```text
SOURCE_REGION_CODE_TABLE에서 확보한 MOIS KIKmix `행정기관코드`와 1:1 일치한다.
geometry는 없으므로 행정동 polygon이 필요하면 SOURCE_ADMIN_BOUNDARIES의
법정동 합집합을 derived dataset으로 만들거나, 시군구 polygon을 fallback
grain으로 사용해야 한다. raw 단계에서는 이 derivation을 수행하지 않는다.
```

---

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| spatial_intersection_result | pass — 행정기관코드 1:1 매칭 |
| temporal_coverage_result | pass — 가장 가까운 정기 발표 `2026-03-31` row 확보 |
| poc_coverage_result | pass |

광주·전남 coverage:

| 항목 | 값 |
|---|---|
| 광주광역시(29) 행정동 row | 95 |
| 전라남도(46) 행정동 row | 324 |
| 합계 | 419 |

---

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept |
| fallback_required | false |
| mock_required | false |
| exclude_required | false |

Open issues:

```text
- '고령자 수' field는 별도 column이 아니라 65세이상 남녀 합계로 derive 필요 (raw 단계 외).
- 행정동 polygon은 본 source에 없음. 필요 시 SOURCE_ADMIN_BOUNDARIES의 법정동
  합집합으로 derived dataset 단계에서 생성 필요.
- 다음 발표(2026-04-30 기준 또는 이후)가 나오면 fetch.py를 재실행하여 갱신.
```

---

## 7. Logic Layer 영향

| Feature | 입력 충족 여부 | 비고 |
|---|---|---|
| `ResidentialExposureFeature` | 충족 | "주택 위치"(BUILDING) + 행정구역 key + "세대 수, 인구"(본 source) + "산림-주택 거리"(derived) 입력 확보. 별도 마을경계 source 없이 건물 footprint와 행정구역/인구통계를 결합한다. |

이 source 추가로 [../04_data-lineage.md](../04_data-lineage.md)와 [../05_feature-contract.md](../05_feature-contract.md)에서 `ResidentialExposureFeature`가 요구하는 population/household 입력이 raw 단계에서 확보되어, **`ExposureSignal` 산식 정의가 가능**해진다.
