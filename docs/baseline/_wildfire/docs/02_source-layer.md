# Source Layer

## 역할

Source layer는 광주·전남 예비주수 판단에 필요한 원천을 catalog로 고정하고, 각 Source가 현재 어떤 방식으로 사용 가능한지 판정한다.

```text
SourceItem
  -> AccessOption
  -> raw snapshot or mock baseline
  -> source dossier evidence
```

이 문서는 상태와 판정만 다룬다. Source별 raw field와 key 증거는 [03_source-evidence.md](03_source-evidence.md)와 [source_dossiers/README.md](source_dossiers/README.md)에서 관리한다.

## Status Contract

| status | 의미 | 사용 방식 |
|---|---|---|
| `REAL` | 실제 접근 가능하고 프로젝트에 사용할 source | `data/raw/<SOURCE_ID>/snapshots/`에 보존 |
| `MOCK` | 공개 접근이 어렵거나 실습 목적상 synthetic 보완이 필요한 source | `data/mock/<SOURCE_ID>/scenario_baseline/` 또는 `runs/<run_context_id>/`에 보존 |
| `EXCLUDE` | 보안, 민감성, coverage 부재, 대체 가능성 때문에 active dependency에서 제거한 source | catalog에는 남기고 Feature/Derived 입력에서는 제거 |

AccessOption status:

| status | 의미 |
|---|---|
| `SELECTED` | 현재 기준으로 선택한 수집 또는 생성 방식 |
| `FALLBACK` | selected 실패 또는 coverage gap 보완용 |
| `CANDIDATE` | 가능성은 있으나 아직 검증 전 |
| `REJECTED` | 보안, key 부재, format 부적합, coverage 부재 등으로 제외 |

## Readiness Legend

| regional_readiness | 의미 |
|---|---|
| `READY_REAL` | 광주·전남 전역 또는 프로젝트 지역 coverage가 실제 source로 닫힘 |
| `READY_WITH_GAP` | 실제 source는 있으나 grain, time window, category coverage gap이 있음 |
| `READY_HYBRID` | 실제 source와 generated mock/fallback을 함께 써야 coverage가 닫힘 |
| `READY_MOCK` | 광주·전남 regional mock baseline이 존재함 |
| `PARTIAL_TIME_GAP` | key/sample은 검증했지만 필요한 historical/current time window가 부족함 |
| `PARTIAL_RECENT_ONLY` | 최근 window만 조회 가능해 재현 horizon에 제약이 있음 |
| `PARTIAL_SAMPLE_ONLY` | sample 검증만 있고 regional batch가 없음 |
| `EXCLUDED` | active Feature/Derived dependency에서 제거됨 |

## Source Inventory

| source_id | status | verification | selected option | readiness | 핵심 판정 |
|---|---|---|---|---|---|
| `SOURCE_ADMIN_BOUNDARIES` | `REAL` | `coverage_verified` | `ACCESS_ADMIN_BOUNDARIES_ADMIN_CODE` | READY_WITH_GAP | 법정동 polygon 기준. 행정동 polygon은 raw에 직접 없음. |
| `SOURCE_REGION_CODE_TABLE` | `REAL` | `coverage_verified` | `ACCESS_REGION_CODE_TABLE_ADMIN_CODE` | READY_REAL | 법정동, 행정동, MOIS namespace 분리 필요. |
| `SOURCE_OFFICIAL_FIRE_RISK_FORECAST` | `REAL` | `coverage_verified` | `ACCESS_OFFICIAL_FIRE_RISK_FORECAST_SIGUNGU` | READY_WITH_GAP | 시군구 current forecast 중심. 읍면동 endpoint와 historical window 없음. |
| `SOURCE_LARGE_FIRE_RISK_FORECAST` | `REAL` | `key_validated` | `ACCESS_LARGE_FIRE_RISK_FORECAST_EUPMYEONDONG` | PARTIAL_TIME_GAP | 최신 sample과 key는 검증했지만 2026-04-15~2026-04-21 file 미확보. |
| `SOURCE_KMA_SHORT_TERM_FORECAST` | `REAL` | `api_tested` | `ACCESS_KMA_SHORT_TERM_FORECAST_NXNY_GRID` | PARTIAL_RECENT_ONLY | 최근 3일 제한. regional grid snapshot은 reference run에 존재하나 운영 재현성은 제한됨. |
| `SOURCE_KMA_OBSERVED_WEATHER` | `REAL` | `coverage_verified` | `ACCESS_KMA_OBSERVED_WEATHER_STATION` | READY_WITH_GAP | 광주·전남 station master와 ASOS hourly snapshot 확보. AWS 관측값은 별도 검증 필요. |
| `SOURCE_KMA_WEATHER_WARNINGS` | `REAL` | `coverage_verified` | `ACCESS_KMA_WEATHER_WARNINGS_WARNING_AREA` | READY_REAL | event-driven. 지역 row 0은 특보 없음으로 해석 가능. |
| `SOURCE_FOREST_STAND_MAP` | `REAL` | `data_acquired` | `ACCESS_FOREST_STAND_MAP_PRIMARY` | READY_REAL | 광주·전남 FGIS 대축척 임상도 SHP 확보. |
| `SOURCE_DEM_ELEVATION` | `EXCLUDE` | `source_confirmed` | none | EXCLUDED | DEM contribution은 unavailable. |
| `SOURCE_BUILDING_FOOTPRINTS` | `REAL` | `coverage_verified` | `ACCESS_BUILDING_FOOTPRINTS_BBOX_WFS` | READY_REAL | 622 EMD bbox tiles, 1,835,886 unique building features 확보. |
| `SOURCE_SETTLEMENT_BOUNDARIES` | `EXCLUDE` | `source_confirmed` | none | EXCLUDED | PoC-only mock은 regional coverage가 아니므로 active dependency에서 제거. |
| `SOURCE_POPULATION_STATISTICS` | `REAL` | `coverage_verified` | `ACCESS_POPULATION_STATISTICS_DATAGOKR_AGE_GENDER` | READY_REAL | 2026-03-31 기준 광주 96 + 전남 323 = 419 행정동 row. |
| `SOURCE_HERITAGE_SPATIAL` | `REAL` | `coverage_verified` | `ACCESS_HERITAGE_SPATIAL_FEATURESERVER_BBOX` | READY_REAL | 광주·전남 FeatureServer layers 1-6, 1,214 features 확보. |
| `SOURCE_PUBLIC_FACILITIES` | `REAL` | `coverage_verified` | `ACCESS_PUBLIC_FACILITIES_GJ_PUBLIC_HEALTH_CSV` | READY_WITH_GAP | 병원/보건 중심. 학교 API는 제외. |
| `SOURCE_VULNERABLE_FACILITIES` | `REAL` | `coverage_verified` | `ACCESS_VULNERABLE_FACILITIES_GJ_SENIOR_NURSING_CSV` | READY_HYBRID | 광주 real, 전남 요양병원 real, 전남 elderly welfare mock 보강. |
| `SOURCE_CRITICAL_INFRASTRUCTURE_DETAIL` | `EXCLUDE` | `unverified` | none | EXCLUDED | 전력·통신시설 상세 위치는 보안 민감. manual review 사유로만 사용. |
| `SOURCE_ROAD_NETWORK` | `REAL` | `coverage_verified` | `ACCESS_ROAD_NETWORK_PRIMARY` | READY_REAL | 전국 NODELINKDATA full ZIP 확보. travel time 계산은 아직 금지. |
| `SOURCE_FOREST_ROAD_NETWORK` | `REAL` | `data_acquired` | `ACCESS_FOREST_ROAD_NETWORK_PRIMARY` | READY_WITH_GAP | 전남 임도망도 265 features. 광주는 FGIS 국유림 임도망도 없음. |
| `SOURCE_ROAD_ACCESS_CONSTRAINTS` | `MOCK` | `coverage_verified` | `ACCESS_ROAD_ACCESS_CONSTRAINTS_BASELINE_SCENARIO` | READY_MOCK | real Segment가 아니며 mock_input 전파 필요. |
| `SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES` | `MOCK` | `coverage_verified` | `ACCESS_MUNICIPAL_FIRE_WATER_FACILITIES_BASELINE_SCENARIO` | READY_MOCK | 공개 소화전 coverage 파편화로 mock baseline 사용. |
| `SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES` | `REAL` | `coverage_verified` | `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_PRIMARY` | READY_HYBRID | official 광주 0, 전남 13 rows. mock supplement로 regional gap 보강. |
| `SOURCE_NATURAL_WATER_SOURCES` | `EXCLUDE` | `api_tested` | none | EXCLUDED | 자연수원 contribution unavailable. |
| `SOURCE_NATURAL_BARRIERS` | `EXCLUDE` | `source_confirmed` | none | EXCLUDED | 하천·공터 차폐 contribution unavailable. |
| `SOURCE_SURFACE_FUEL_CONDITION` | `MOCK` | `coverage_verified` | `ACCESS_SURFACE_FUEL_CONDITION_BASELINE_SCENARIO` | READY_MOCK | 현장성 mock. 운영 truth로 사용 금지. |
| `SOURCE_WORKSITE_HAZARD_CONDITIONS` | `MOCK` | `coverage_verified` | `ACCESS_WORKSITE_HAZARD_CONDITIONS_BASELINE_SCENARIO` | READY_MOCK | 현장성 mock. hard gate 사용 금지. |
| `SOURCE_FIRE_STATION_CENTERS` | `REAL` | `coverage_verified` | `ACCESS_FIRE_STATION_CENTERS_PRIMARY` | READY_WITH_GAP | 전국 1,144 119안전센터 CSV 확보. 좌표와 읍면동 관할구역 없음. |
| `SOURCE_FIRE_RESOURCE_AVAILABILITY` | `MOCK` | `coverage_verified` | `ACCESS_FIRE_RESOURCE_AVAILABILITY_BASELINE_SCENARIO` | READY_MOCK | 센터별 실제 인력/차량 live availability가 아닌 synthetic overlay. |
| `SOURCE_PREWATERING_EQUIPMENT_CAPACITY` | `MOCK` | `coverage_verified` | `ACCESS_PREWATERING_EQUIPMENT_CAPACITY_BASELINE_SCENARIO` | READY_MOCK | 장비별 실측 성능자료가 아닌 mock capacity. |
| `SOURCE_SUN_EVENT_CALENDAR` | `REAL` | `coverage_verified` | `ACCESS_SUN_EVENT_CALENDAR_AREA` | PARTIAL_SAMPLE_ONLY | 광주 7일 sample 확보. 전남 시군/좌표별 batch 미확보. |

## Mock Contract

Mock source는 운영 truth가 아니다.

공통 규칙:

- 파일은 `data/mock/<SOURCE_ID>/scenario_baseline/` 또는 `runs/<run_context_id>/`에 둔다.
- 모든 row는 mock 생성 시각, 적용 시간, mock reason을 가져야 한다.
- Feature와 Signal에는 `mock_input=true`를 전파한다.
- hard gate 자동 실행에는 사용하지 않고 `RequestManualReview` 또는 `advisory_only`로 분기한다.

| mock source | 주 사용 Feature | 사용 제한 |
|---|---|---|
| `SOURCE_ROAD_ACCESS_CONSTRAINTS` | VehicleAccess, WorkSafety, WateringDuration | 폭, 회차, 포장, 협소도로, 경사 proxy는 mock이다. |
| `SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES` | WaterSource | 소화전/비상소화장치 coverage를 가정한 baseline이다. |
| `SOURCE_SURFACE_FUEL_CONDITION` | WettableBarrier | 지표연료 상태는 현장 관측이 아니다. |
| `SOURCE_WORKSITE_HAZARD_CONDITIONS` | WorkSafety | 낙석, 연기, 접근, 강풍 hazard는 hard gate에 직접 쓰지 않는다. |
| `SOURCE_FIRE_RESOURCE_AVAILABILITY` | WateringDuration | 실제 센터별 live 자원이 아니다. |
| `SOURCE_PREWATERING_EQUIPMENT_CAPACITY` | WateringDuration | 실제 장비 성능자료가 아니다. |

## Exclusion Impact

| excluded source | 제거된 contribution | 대체 또는 처리 |
|---|---|---|
| `SOURCE_DEM_ELEVATION` | 경사도, 사면방향, 고도, 도로 경사 | terrain contribution unavailable. 일부 접근/안전 항목은 mock `slope_percent`만 proxy로 사용 |
| `SOURCE_SETTLEMENT_BOUNDARIES` | 별도 마을 polygon | building footprint + population + admin code 기반 residential proxy로 대체 |
| `SOURCE_CRITICAL_INFRASTRUCTURE_DETAIL` | 전력·통신시설 상세 위치 | 문화재, 공공시설, 취약시설, 주거지 노출로 대체. 필요 시 manual review |
| `SOURCE_NATURAL_WATER_SOURCES` | 하천, 저수지 자연수원 | municipal/forest-fire facility만 active water source로 사용 |
| `SOURCE_NATURAL_BARRIERS` | 하천, 공터 자연차폐 | 도로, 임도, 건물, 산림 접점 proxy만 사용 |

## Source Layer Completion

| 완료 조건 | 상태 | 근거 |
|---|---|---|
| 29개 Source catalog 존재 | done | `data/reference/source_inventory.json` |
| 48개 AccessOption catalog 존재 | done | `data/reference/source_access_options.json` |
| 모든 Source의 availability 판정 | done | `REAL` 18, `MOCK` 6, `EXCLUDE` 5 |
| active source의 evidence dossier | done | 27 evidence/canonical dossier + 2 catalog-only exclusion dossier |
| mock source generator와 baseline | done | 6 MOCK source |
| active EXCLUDE dependency 제거 | done | Feature/Derived 입력에서 5개 EXCLUDE source 제거 |
| regional 운영 snapshot | partial | 단기예보, 일출일몰, 대형산불위험예보는 time/sample gap 존재 |
