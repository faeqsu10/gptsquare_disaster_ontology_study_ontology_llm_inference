# Source Dossier — SOURCE_FOREST_STAND_MAP

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FOREST_STAND_MAP` |
| selected_access_option_id | `ACCESS_FOREST_STAND_MAP_PRIMARY` |
| availability_status | REAL |
| verification_status | data_acquired |
| sample_path | `data/raw/SOURCE_FOREST_STAND_MAP/snapshots/regional_clip/` |
| pipeline_path | `pipelines/SOURCE_FOREST_STAND_MAP/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_FOREST_STAND_MAP_PRIMARY` | SELECTED | forest stand polygon | static / irregular update | Manual download selected. Official pages confirm SHP distribution, UTM-K(EPSG:5179), and forest stand attributes; direct unauthenticated URL was not available. |

Decision note:

```text
Use Forest Geospatial Information Service manual download application. Preserve downloaded SHP and source CRS. Do not dissolve stand polygons or create a forest boundary in the raw phase.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | manual_download |
| endpoint_or_layer | `https://www.forest.go.kr/newkfsweb/html/HtmlPage.do?pg=/fgis/UI_KFS_5002_020100.html&mn=KFS_02_04_03_04_01&orgId=fgis` / layer `대축척 임상도` |
| request_or_download_path | `pipelines/SOURCE_FOREST_STAND_MAP/manual_download.md` |
| expected_format | SHP ZIP |
| actual_format | SHP ZIP acquired for 광주광역시 and 전라남도 시도 단위 |
| snapshot_path | `data/raw/SOURCE_FOREST_STAND_MAP/snapshots/regional_clip/gwangju_sido/`, `data/raw/SOURCE_FOREST_STAND_MAP/snapshots/regional_clip/jeonnam_sido/` |
| captured_at | 2026-04-30 |

Raw files acquired:

```text
- archives/2013.zip
- archives/2019.zip
- archives/2024.zip
- archives/2025.zip
- gwangju_sido/layers/<year>/29.shp, 29.dbf, 29.shx, 29.prj, 29.shp.xml, 29.sbn, 29.sbx
- jeonnam_sido/archives/<year>.zip with native 46.* shapefile components preserved inside ZIP
```

Raw fields observed from downloaded DBF / Esri metadata:

```text
- STORUNST
- OBJECTID
- FROR_CD
- FRTP_CD
- KOFTR_GROU
- DMCLS_CD
- AGCLS_CD
- DNST_CD
- HEIGHT
- LDMARK_STN
- MAP_LABEL
- 갱신년도
- ETC_PCMTT
- FRTP_NM
- KOFTR_NM
- DMCLS_NM
- AGCLS_NM
- DNST_NM
- HEIGHT_NM
- Shape_Leng
- Shape_Area
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `registry_updated_at` |
| temporal_semantics | static, registry_updated_at |
| native_temporal_grain | irregular source updates |
| native_time_format | static layer; no per-feature time field observed before download |
| parse_example | not_applicable |
| time_parse_result | not_applicable |

Notes:

```text
Raw 단계에서는 시간 grid alignment를 수행하지 않는다. 임상도는 static geospatial base layer로 취급한다.
```

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `geometry` |
| geometry_field | source-native SHP geometry; Esri metadata field label `Shape` where present |
| spatial_semantics | polygon |
| native_spatial_grain | forest stand polygon |
| native_crs | Korea 2000 / Unified CS, EPSG:5179, confirmed from `29.prj` and `29.shp.xml` |
| region_filter_method | FGIS map download application location selection |
| validation_example | downloaded `29.shp` and archived `46.shp` both shape type 5 Polygon; layers `29` and `46`; bbox in native CRS covers 광주광역시 and 전라남도 extracts |
| space_validation_result | pass |

Notes:

```text
Raw 단계에서는 좌표계 통일, 읍면동 fan-out, Segment join을 수행하지 않는다. 광주광역시 및 전라남도 시도 단위 원본 SHP/ZIP만 보존했다.
```

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 광주 2013: 19006, 2019: 13513, 2024: 12030, 2025: 11796; 전남 2013: 508004, 2019: 430717, 2024: 418150, 2025: 412892 |
| spatial_intersection_result | pass at administrative coverage: 광주광역시 extract and 전라남도 extract cover the project region; feature-level intersection not performed |
| temporal_coverage_result | not_applicable_static |
| poc_coverage_result | pass |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | no |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- 광주광역시/전라남도 target-region 임상도 원본은 확보했으나 전국 full source는 확보하지 않았다.
- 광주·전남 feature-level polygon intersection은 수행하지 않았다. 현재 검증은 시도 행정구역 추출본의 coverage 기준이다.
- 임도망도는 별도 source dossier에 기록한다.
```
