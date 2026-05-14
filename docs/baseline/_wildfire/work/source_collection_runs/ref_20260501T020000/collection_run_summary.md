# Reference-time collection summary

- run_id: `ref_20260501T020000`
- reference_time: `2026-05-01T02:00:00+09:00`
- scope: `광주광역시·전라남도`
- phase: Source snapshot collection only; no Clean Zone, CRS normalization, time-grid alignment, spatial join, or Feature/Signal calculation.

## Catalog / validation

- JSON parse: **PASS**
- schema validation: source_item: **PASS**
- schema validation: source_access_option: **PASS**
- schema validation: source_dossier: **PASS**
- Source <-> AccessOption cross-reference: **PASS**
- selected_access_option_id exists: **PASS**
- REAL source has selected or fallback option: **PASS**
- MOCK source has generated_mock selected option: **PASS**
- EXCLUDE source has no active dependency: **PASS**
- unknown SOURCE_* refs: **FAIL**
- snapshot path contract: **PASS**
- placeholder URL: **PASS**
- time/space key 6-item completeness: **PASS**
- PoC coverage result recorded: **PASS**

## Completeness assessment

- Full actual collection complete: **NO**
- Main hard gaps: **none after remaining-gap pipelines**
- Important fallback/partial cases: vulnerable facilities Jeonnam elderly welfare API 404 -> mock fallback; forest fire extinguishing facilities official regional rows are sparse -> generated supplement; public school location API returned NODATA for current filters.

## Source results

| source_id | status | counts | issue |
|---|---|---:|---|
| `SOURCE_ADMIN_BOUNDARIES` | collected_static_latest | `{"region_feature_count":622}` |  |
| `SOURCE_BUILDING_FOOTPRINTS` | collected_static_wfs_full_region | `{"admin_emd_count":622,"features_written":1835886,"count_requests":11458,"fetch_requests":8749,"overflow_tiles":0,"fa...` |  |
| `SOURCE_CRITICAL_INFRASTRUCTURE_DETAIL` | excluded_not_collected | `{}` |  |
| `SOURCE_DEM_ELEVATION` | excluded_not_collected | `{}` |  |
| `SOURCE_FIRE_RESOURCE_AVAILABILITY` | generated_reference_time_mock | `{"row_count":950}` |  |
| `SOURCE_FIRE_STATION_CENTERS` | collected_static_latest | `{"national_rows":1144,"gwangju_rows":27,"jeonnam_rows":68}` |  |
| `SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES` | existing_real_plus_generated_coverage_supplement | `{"official_full_row_count":187,"official_gwangju_jeonnam_row_count":13,"supplement_rows":623}` | regional full coverage depends on generated supplement, not official point coverage |
| `SOURCE_FOREST_ROAD_NETWORK` | collected_manual_archive_pipeline_with_no_data_evidence | `{"feature_count_total":265,"coverage_result":"pass_with_gwangju_no_data_evidence"}` | Gwangju has no FGIS forest-road line data in the recorded acquisition flow; no synthetic road lines were generated |
| `SOURCE_FOREST_STAND_MAP` | collected_manual_archive_pipeline_full_region | `{"latest_vintage":"2025","latest_vintage_feature_count_total":424688,"coverage_result":"pass"}` |  |
| `SOURCE_HERITAGE_SPATIAL` | collected_static_featureserver_full_region | `{"total_feature_count":1214,"layer_feature_counts":{"1":125,"2":282,"3":123,"4":557,"5":127,"6":0}}` |  |
| `SOURCE_KMA_OBSERVED_WEATHER` | collected_reference_time_api | `{"bytes":80805,"data_lines":290}` |  |
| `SOURCE_KMA_SHORT_TERM_FORECAST` | collected_reference_time_api | `{"unique_grid_count":276,"success_count":276,"failed_count":0}` |  |
| `SOURCE_KMA_WEATHER_WARNINGS` | collected_reference_time_api | `{"warning_history":1013,"warning_area_table":676}` |  |
| `SOURCE_LARGE_FIRE_RISK_FORECAST` | collected_file_latest | `{"row_count":48192}` |  |
| `SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES` | generated_reference_time_mock | `{"row_count":623}` |  |
| `SOURCE_NATURAL_BARRIERS` | excluded_not_collected | `{}` |  |
| `SOURCE_NATURAL_WATER_SOURCES` | excluded_not_collected | `{}` |  |
| `SOURCE_OFFICIAL_FIRE_RISK_FORECAST` | collected_reference_time_live | `{"row_count":27,"selected_valid_time_range":{"min":"2026-05-01T03:00:00+09:00","max":"2026-05-01T03:00:00+09:00"}}` |  |
| `SOURCE_POPULATION_STATISTICS` | existing_monthly_full_region_snapshot_validated | `{"age_gender_rows":419,"household_size_rows":419}` |  |
| `SOURCE_PREWATERING_EQUIPMENT_CAPACITY` | generated_reference_time_mock | `{"row_count":312}` |  |
| `SOURCE_PUBLIC_FACILITIES` | collected_static_file_and_api | `{"file_rows":{"gwangju_public_health_facilities":32,"jeonnam_public_health_centers":22,"jeonnam_public_health_posts":...` | school_locations_gwangju/jeonnam returned NODATA_ERROR with current address filter |
| `SOURCE_REGION_CODE_TABLE` | collected_static_latest | `{"legal_dong_gwangju_jeonnam_rows":5069,"kostat_admin_dong_gwangju_jeonnam_rows":61194}` |  |
| `SOURCE_ROAD_ACCESS_CONSTRAINTS` | generated_reference_time_mock | `{"row_count":623}` |  |
| `SOURCE_ROAD_NETWORK` | existing_manual_full_national_snapshot | `{"coverage_scope":"광주광역시·전라남도","coverage_unit_grain":"current legal 읍면동 row","coverage_unit_count":623,"coverage_coun...` | no routing, clipping, road-width inference, travel-time calculation, or spatial join performed |
| `SOURCE_SETTLEMENT_BOUNDARIES` | excluded_not_collected | `{}` |  |
| `SOURCE_SUN_EVENT_CALENDAR` | collected_reference_date_api | `{"original_location_count":29,"expanded_location_item_count":23}` | 행정명 with 시/군 suffix mostly returned no item; alias responses are preserved separately as sun_event_alias_*.xml |
| `SOURCE_SURFACE_FUEL_CONDITION` | generated_reference_time_mock | `{"row_count":623}` |  |
| `SOURCE_VULNERABLE_FACILITIES` | collected_real_with_mock_fallback | `{"real_file_rows":{"gwangju_senior_nursing_facilities":102,"gwangju_medical_welfare_facilities":102,"jeonnam_nursing_...` | Jeonnam elderly welfare OpenAPI functions returned HTTP 404; generated mock fallback created |
| `SOURCE_WORKSITE_HAZARD_CONDITIONS` | generated_reference_time_mock | `{"row_count":623}` |  |
