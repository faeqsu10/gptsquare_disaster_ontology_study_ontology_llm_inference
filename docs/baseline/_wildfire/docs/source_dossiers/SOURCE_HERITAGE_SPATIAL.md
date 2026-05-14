# Source Dossier — SOURCE_HERITAGE_SPATIAL

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_HERITAGE_SPATIAL` |
| selected_access_option_id | `ACCESS_HERITAGE_SPATIAL_FEATURESERVER_BBOX` |
| availability_status | REAL |
| verification_status | coverage_verified |
| sample_path | `data/raw/SOURCE_HERITAGE_SPATIAL/snapshots/sample_20260430/` |
| full_snapshot_path | `data/raw/SOURCE_HERITAGE_SPATIAL/snapshots/full_gwangju_jeonnam_20260430/` |
| pipeline_path | `pipelines/SOURCE_HERITAGE_SPATIAL/` |

## 1. Access Option Decision

| access_option_id | status | native spatial grain | native temporal grain | decision |
|---|---|---|---|---|
| `ACCESS_HERITAGE_SPATIAL_FEATURESERVER_BBOX` | SELECTED | heritage polygon | annual/irregular registry update | Selected for reproducible bbox GeoJSON sample. |
| `ACCESS_HERITAGE_SPATIAL_OFFICIAL_WMS_WFS` | FALLBACK | WMS layer / WFS XML query | registry update | Official KHS helpAPI confirms WMS/WFS, but documented WFS is name/category query, not bbox feature extraction. |

Decision note:

```text
KHS official helpAPI remains the official WMS/WFS evidence. For PoC raw feature validation, the ArcGIS FeatureServer mirror is selected because it exposes KHS-origin heritage polygons as queryable GeoJSON without auth.
```

## 2. Raw Snapshot Evidence

| 항목 | 값 |
|---|---|
| acquisition_method | wms_wfs |
| endpoint_or_layer | `https://portal.esrikr.com/arcgis/rest/services/Hosted/KoreaHerritageSites/FeatureServer` |
| request_or_download_path | `sample_request.json` |
| expected_format | GeoJSON |
| actual_format | ArcGIS JSON native CRS; GeoJSON convenience copy |
| snapshot_path | `sample_response_arcgis_native.json`, `sample_response.geojson` |
| captured_at | 2026-04-30 |

Raw fields observed:

```text
- geometry
- fid
- 국가유산명
- 면적
- 시군구명
- 시군구코드
- 시도명
- 시도코드
- 유산코드
- 종목명
- 종목코드
- SHAPE__Length
- SHAPE__Area
- _layer_id
- _layer_name
```

## 3. Time Key Verification

| 항목 | 값 |
|---|---|
| time_key_field | `sample_response.metadata.service_metadata_updated` |
| temporal_semantics | registry_updated_at |
| native_temporal_grain | annual/irregular registry update |
| native_time_format | `YYYY.MM`; sample captured_at is ISO-8601 |
| parse_example | `2026.04` |
| time_parse_result | pass |

## 4. Space Key Verification

| 항목 | 값 |
|---|---|
| space_key_field | `geometry` |
| geometry_field | `geometry` |
| spatial_semantics | polygon |
| native_spatial_grain | point/polygon registry represented as polygon layers in selected sample |
| native_crs | service native EPSG:5179 preserved in `sample_response_arcgis_native.json`; `sample_response.geojson` is a convenience copy with `outSR=4326` |
| region_filter_method | ArcGIS REST envelope intersects filter |
| validation_example | 41 features across layers 1-6; first feature `광주 지산동 오층석탑` |
| space_validation_result | pass |

## 5. PoC Coverage

| 항목 | 값 |
|---|---|
| row_count_or_feature_count | 41 |
| spatial_intersection_result | pass for bbox |
| temporal_coverage_result | not_applicable for static registry |
| poc_coverage_result | partial |

Full 광주·전남 snapshot:

```text
data/raw/SOURCE_HERITAGE_SPATIAL/snapshots/full_gwangju_jeonnam_20260430/
total_feature_count: 1,214
layer_counts: 1=125, 2=282, 3=123, 4=557, 5=127, 6=0
native_crs: EPSG:5179 preserved in ArcGIS JSON pages
```

## 6. Final Decision

| 항목 | 값 |
|---|---|
| decision | accept_with_gap |
| fallback_required | yes |
| mock_required | no |
| exclude_required | no |

Open issues:

```text
- Integration review should decide whether the FeatureServer mirror can be primary long-term or only a PoC acquisition bridge.
```
