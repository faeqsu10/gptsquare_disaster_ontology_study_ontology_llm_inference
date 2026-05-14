# Source Dossier — SOURCE_BUILDING_FOOTPRINTS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_BUILDING_FOOTPRINTS` |
| selected_access_option_id | `ACCESS_BUILDING_FOOTPRINTS_BBOX_WFS` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_BUILDING_FOOTPRINTS/snapshots/sample_20260430/` |
| full_snapshot_path | `data/raw/SOURCE_BUILDING_FOOTPRINTS/snapshots/full_gwangju_jeonnam_20260430/` |
| pipeline_path | `pipelines/SOURCE_BUILDING_FOOTPRINTS/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_BUILDING_FOOTPRINTS_BBOX_WFS` | SELECTED | building polygon | registry update | VWorld WFS endpoint, layer `dt_d010`, geometry, and keys confirmed with `VWORLD_API_KEY`. |

Decision note:

```text
Official current source should be VWorld/국토교통부 GIS건물통합WFS조회, not the older generic standard URL. The service exposes building geometry, building IDs, PNU, and `last_updt_dt`. The current primary sample is `sample_response.json` with 20 GeoJSON MultiPolygon features from the PoC bbox.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | wms_wfs |
| endpoint_or_layer | `https://api.vworld.kr/ned/wfs/getBldgisSpceWFS`, `typename=dt_d010` |
| request_or_download_path | `sample_request.json` |
| expected_format | WFS JSON/GML |
| actual_format | GeoJSON FeatureCollection |
| snapshot_path | `sample_response.json` |
| captured_at | 2026-04-30 |

Raw fields observed/documented:

```text
- ag_geom
- src_objectid
- gis_idntfc_no
- pnu
- ld_cpsg_code
- buld_prpos_code
- buld_idntfc_no
- last_updt_dt
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `last_updt_dt` |
| temporal_semantics | registry_updated_at |
| native_temporal_grain | irregular registry update |
| native_time_format | `YYYY-MM-DDTHH:mm:ss` documented |
| parse_example | `2015-11-18T13:19:59` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `ag_geom` or `gis_idntfc_no` or `pnu` |
| geometry_field | `ag_geom` |
| spatial_semantics | polygon |
| native_spatial_grain | building polygon |
| native_crs | WFS supports `srsName`; PoC request uses `EPSG:4326` |
| region_filter_method | PoC bbox WFS GetFeature |
| validation_example | 20 features returned; first geometry type `MultiPolygon` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 20 returned; `numberMatched=62083` in bbox |
| spatial_intersection_result | pass for bbox |
| temporal_coverage_result | not_applicable for static registry |
| poc_coverage_result | partial |

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept |
| fallback_required | no |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- None for TX05 acquisition. Full 광주·전남 WFS snapshot saved: 1,835,886 unique features, 622 EMD units, 0 failed/overflow tiles.
```
