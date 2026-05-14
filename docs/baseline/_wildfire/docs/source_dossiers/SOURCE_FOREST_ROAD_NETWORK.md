# Source Dossier — SOURCE_FOREST_ROAD_NETWORK

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FOREST_ROAD_NETWORK` |
| selected_access_option_id | `ACCESS_FOREST_ROAD_NETWORK_PRIMARY` |
| availability_status | REAL |
| verification_status | data_acquired |
| sample_path | `data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/regional_clip/jeonnam_sido/` |
| pipeline_path | `pipelines/SOURCE_FOREST_ROAD_NETWORK/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_FOREST_ROAD_NETWORK_PRIMARY` | SELECTED | forest road line | static / irregular update | Manual application selected. Official pages confirm SHP distribution path, UTM-K(EPSG:5179), and forest road line semantics. |

Decision note:

```text
Use Forest Geospatial Information Service manual download application. 전라남도 임도망도(국유림) ZIP was acquired; 광주광역시 search returned no data for this layer.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | manual_download |
| endpoint_or_layer | `https://www.forest.go.kr/kfsweb/kfi/kfs/trail/fRMap.do?pblicDataId=PBD0000062&tabs=1&mn=NKFS_06_08_02&subTitle=%EC%9E%84%EB%8F%84%EB%A7%9D%EB%8F%84` / layer `임도망도` |
| request_or_download_path | `pipelines/SOURCE_FOREST_ROAD_NETWORK/manual_download.md` |
| expected_format | SHP ZIP |
| actual_format | SHP ZIP acquired for 전라남도 시도 단위 |
| snapshot_path | `data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/regional_clip/jeonnam_sido/` |
| captured_at | 2026-04-30 |

Raw files acquired:

```text
- archives/임도망도.zip
- layers/46.shp, 46.dbf, 46.shx, 46.prj, 46.shp.xml, 46.sbn, 46.sbx
```

Raw fields observed from downloaded DBF:

```text
- HSTR_MNNMB
- ETC_PCMTT
- FRRD_NM
- FRRD_FCLTD
- FRRD_ESTBL
- FRRD_FCLTW
- FRRD_DV_I
- FRRD_DV_B
- FRRD_INSTT
- FRRD_MGC
- FRRD_RGSNO
- RBP_X
- RBP_Y
- REP_X
- REP_Y
- MAP_LABEL
- FR_TH_DV
- FR_TH_YR
- FRRD_THM
- Shape_Leng
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
Raw 단계에서는 시간 grid alignment를 수행하지 않는다. 임도망도는 static geospatial base layer로 취급한다.
```

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `geometry` |
| geometry_field | source-native SHP geometry |
| spatial_semantics | line |
| native_spatial_grain | forest road line |
| native_crs | Korea 2000 / Unified CS, EPSG:5179, confirmed from `46.prj` |
| region_filter_method | FGIS map download application location selection |
| validation_example | downloaded `46.shp` shape type 3 PolyLine; layer `46`; bbox in native CRS covers 전라남도 extract |
| space_validation_result | pass |

Notes:

```text
Raw 단계에서는 좌표계 통일, 읍면동 fan-out, Segment join을 수행하지 않는다. 전라남도 시도 단위 원본 SHP만 보존했다.
```

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 265 |
| spatial_intersection_result | partial: 전라남도 extract acquired; 광주광역시 search returned no `임도망도(국유림)` data; feature-level line intersection not performed |
| temporal_coverage_result | not_applicable_static |
| poc_coverage_result | partial |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | no |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- 전라남도 임도망도 원본은 확보했으나 광주광역시 영역은 FGIS에서 데이터 없음으로 확인됐다.
- 광주·전남 세부 지역에 대한 feature-level line intersection은 수행하지 않았다.
- 전국 full source는 확보하지 않았다.
```
