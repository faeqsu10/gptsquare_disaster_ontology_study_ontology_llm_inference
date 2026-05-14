# Source Dossier - SOURCE_ROAD_NETWORK

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_ROAD_NETWORK` |
| selected_access_option_id | `ACCESS_ROAD_NETWORK_PRIMARY` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_ROAD_NETWORK/snapshots/full/` |
| pipeline_path | `pipelines/SOURCE_ROAD_NETWORK/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_ROAD_NETWORK_PRIMARY` | SELECTED proposed | MOCT_LINK polyline / MOCT_NODE point | UPDATEDATE/package date | Full package acquired |

Decision note:

```text
`/Users/presence/Downloads/[2026-01-13]NODELINKDATA.zip` was copied into the raw full snapshot. `MOCT_LINK` and `MOCT_NODE` schema were inspected without CRS conversion, routing, or joins. The full national raw package is treated as covering 광주·전남 at source scope.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | manual_download/file_download metadata verification |
| endpoint_or_layer | https://www.data.go.kr/data/15025526/fileData.do |
| request_or_download_path | https://www.its.go.kr/nodelink/nodelinkRef |
| expected_format | SHP |
| actual_format | ZIP containing SHP/DBF/SHX/PRJ |
| snapshot_path | `data/raw/SOURCE_ROAD_NETWORK/snapshots/full/` |
| captured_at | 2026-04-30 |

Raw fields observed:

```text
- MOCT_LINK.LINK_ID
- MOCT_LINK.F_NODE
- MOCT_LINK.T_NODE
- MOCT_LINK.ROAD_NAME
- MOCT_LINK.LENGTH
- MOCT_LINK.UPDATEDATE
- MOCT_NODE.NODE_ID
- MOCT_NODE.NODE_TYPE
- MOCT_NODE.UPDATEDATE
- SHP geometry
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | UPDATEDATE; package_date |
| temporal_semantics | registry_updated_at, static |
| native_temporal_grain | per-feature update date plus package date |
| native_time_format | native UPDATEDATE values; package date 2026-01-13 |
| parse_example | 2026-01-13 |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | LINK_ID, NODE_ID, SHP geometry |
| geometry_field | MOCT_LINK.shp geometry; MOCT_NODE.shp geometry |
| spatial_semantics | line, point |
| native_spatial_grain | line/node |
| native_crs | ITRF2000_Central_Belt_60 from PRJ |
| region_filter_method | full national package acquired; 광주·전남 coverage assessment recorded; no raw-phase region clipping |
| validation_example | MOCT_LINK 1,554,487 records; MOCT_NODE 1,177,983 records |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | MOCT_LINK 1,554,487; MOCT_NODE 1,177,983 |
| spatial_intersection_result | full national coverage; 광주·전남 coverage assessment recorded; PoC clip not created |
| temporal_coverage_result | static/not_applicable |
| poc_coverage_result | pass |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept |
| fallback_required | no |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- Full national package acquired and assessed as covering 광주·전남; no 광주·전남 raw clip was created in Source phase.
- No movement time, route, nearest road, or Segment join was computed.
```
