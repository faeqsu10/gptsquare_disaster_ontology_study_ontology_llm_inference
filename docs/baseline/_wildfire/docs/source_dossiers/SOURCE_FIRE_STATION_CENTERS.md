# Source Dossier — SOURCE_FIRE_STATION_CENTERS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FIRE_STATION_CENTERS` |
| selected_access_option_id | `ACCESS_FIRE_STATION_CENTERS_PRIMARY` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_FIRE_STATION_CENTERS/snapshots/full/` |
| pipeline_path | `pipelines/SOURCE_FIRE_STATION_CENTERS/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_FIRE_STATION_CENTERS_PRIMARY` | SELECTED | 119안전센터 address row | annual registry metadata | CSV file download works without login |
| `ACCESS_FIRE_STATION_CENTERS_AUTO_OPENAPI` | FALLBACK | 119안전센터 address row | annual registry metadata | JSON/XML auto API exists but requires application/API key |

Decision note:

```text
공공데이터포털 상세 페이지에서 파일데이터와 자동 변환 OpenAPI option을 모두 확인했다.
이번 transaction에서는 로그인 없이 재현 가능한 CSV file download를 SELECTED로 제안한다.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | file_download |
| endpoint_or_layer | https://www.data.go.kr/data/15065056/fileData.do |
| request_or_download_path | `pipelines/SOURCE_FIRE_STATION_CENTERS/sample_request.json` |
| expected_format | CSV |
| actual_format | CSV, CP949 |
| snapshot_path | `data/raw/SOURCE_FIRE_STATION_CENTERS/snapshots/full/source_fire_station_centers_20250701.csv` |
| captured_at | see `data/raw/SOURCE_FIRE_STATION_CENTERS/snapshots/full/metadata.json` |
| row_count | 1144 |

Raw fields observed:

```text
- 순번
- 시도본부
- 소방서명
- 119안전센터명
- 주소
- 전화번호
- 팩스번호
```

주소/좌표/기관명/관할 확인:

```text
주소: 주소
좌표: 원본 컬럼 없음
기관명: 시도본부, 소방서명, 119안전센터명
관할: 소방서명은 소속 소방서이나 읍면동별 관할구역 컬럼은 없음
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `registry_updated_at` |
| temporal_semantics | registry_updated_at |
| native_temporal_grain | annual |
| native_time_format | YYYY-MM-DD metadata date |
| parse_example | 수정일 `2025-08-20`, 등록일 `2025-07-18`, 차기 등록 예정일 `2026-08-28` |
| time_parse_result | pass |

Notes:

```text
row-level 시간 컬럼은 없다. registry metadata 날짜를 dossier time key로 기록한다.
```

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `순번`, `주소` |
| geometry_field | 없음 |
| spatial_semantics | address |
| native_spatial_grain | 119안전센터 address row |
| native_crs | not_applicable; source provides address only |
| region_filter_method | full CSV 수집 후 `시도본부`, `주소`, `소방서명`으로 evidence 확인 |
| space_validation_result | pass |

Notes:

```text
좌표가 없으므로 임의 geocoding하지 않는다. raw 단계에서는 주소 native field를 보존한다.
```

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 광주광역시 27 rows |
| spatial_intersection_result | partial |
| temporal_coverage_result | not_applicable |
| poc_coverage_result | partial |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | OpenAPI fallback documented, not selected |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- 좌표 컬럼 없음.
- 읍면동별 119안전센터 관할구역 컬럼 없음.
- OpenAPI option은 활용신청/API key가 필요하다.
```
