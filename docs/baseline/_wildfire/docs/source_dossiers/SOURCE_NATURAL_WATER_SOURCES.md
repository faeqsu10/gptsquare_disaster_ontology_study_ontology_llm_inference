# Source Dossier - SOURCE_NATURAL_WATER_SOURCES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_NATURAL_WATER_SOURCES` |
| selected_access_option_id | `ACCESS_NATURAL_WATER_SOURCES_VWORLD_RIVER_NETWORK` |
| availability_status | EXCLUDE |
| verification_status | api_tested |
| sample_path | `data/raw/SOURCE_NATURAL_WATER_SOURCES/snapshots/api_probe_20260430/` |
| pipeline_path | `pipelines/SOURCE_NATURAL_WATER_SOURCES/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_NATURAL_WATER_SOURCES_VWORLD_RIVER_NETWORK` | REJECTED proposed | river network polygon feature | 2023-06 source time range/static | Excluded after API test |
| `ACCESS_NATURAL_WATER_SOURCES_PRIMARY` | REJECTED proposed | line/polygon | metadata update date/static | Rejected due to 2015 production year |

Decision note:

```text
VWorld `LT_C_WKMSTRM` river network API returned real PoC bbox features using `VWORLD_API_KEY`, but natural water source is excluded from the current PoC decision path by user decision. NGII basic spatial information is also rejected because the observed production year is 2015.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | openapi |
| endpoint_or_layer | https://api.vworld.kr/req/data; `data=LT_C_WKMSTRM` |
| request_or_download_path | `pipelines/SOURCE_NATURAL_WATER_SOURCES/fetch_vworld_river_network.py` |
| expected_format | JSON, XML |
| actual_format | JSON |
| snapshot_path | `data/raw/SOURCE_NATURAL_WATER_SOURCES/snapshots/api_probe_20260430/` |
| captured_at | 2026-04-30 |

Raw fields observed:

```text
- riv_nm
- cat_nam
- geometry
- response.record
- response.page
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `metadata.modified`; dataset time range |
| temporal_semantics | registry_updated_at, static |
| native_temporal_grain | data.go.kr metadata update; VWorld source time range |
| native_time_format | YYYY-MM-DD; YYYY년 M월 |
| parse_example | 2025-07-01; 2023년 6월 |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | geometry, riv_nm, cat_nam |
| geometry_field | response.result.featureCollection.features[].geometry |
| spatial_semantics | polygon |
| native_spatial_grain | river network polygon feature |
| native_crs | EPSG:4326 requested from VWorld API |
| region_filter_method | geomFilter BOX(minx,miny,maxx,maxy) |
| validation_example | 4 features: 광주천, 광주천, 증심사천, 석곡천 |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 4 features in PoC bbox probe |
| spatial_intersection_result | pass_bbox_probe |
| temporal_coverage_result | not_applicable |
| poc_coverage_result | not_applicable |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | exclude |
| fallback_required | no |
| mock_required | no |
| exclude_required | yes |

Open issues:

```text
- VWorld probe evidence remains archived, but this source will not feed PoC features.
- NGII fallback is rejected because observed production year is 2015.
- No nearest water distance or Segment join was computed.
```
