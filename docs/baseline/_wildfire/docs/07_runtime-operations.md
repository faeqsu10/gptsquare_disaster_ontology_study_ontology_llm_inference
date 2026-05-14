# Runtime Operations

## 역할

Runtime 문서는 live source와 runtime mock overlay를 같은 시간 세계로 정렬하는 규칙을 정의한다. Source catalog는 [02_source-layer.md](02_source-layer.md), logic은 [06_decision-logic.md](06_decision-logic.md)에 있다.

## 기준 원칙

```text
모든 실행은 하나의 run_context.reference_time을 가진다.
same run_context_id -> same reference world
```

같은 run 안에서 live API, static anchor, generated overlay가 서로 다른 시각을 의미하지 않도록 `run_context_id`, `reference_time`, `time_mode`, `temporal_alignment_status`를 전파한다.

## Lifecycle Class

| class | 의미 | Source |
|---|---|---|
| Static Anchor | 오래 유지되는 기준표 | `SOURCE_FIRE_STATION_CENTERS`, admin/code regional context |
| Live Driver | 현재 시점 압력을 제공하는 source | `SOURCE_OFFICIAL_FIRE_RISK_FORECAST`, `SOURCE_KMA_SHORT_TERM_FORECAST`, `SOURCE_KMA_OBSERVED_WEATHER`, `SOURCE_KMA_WEATHER_WARNINGS`, `SOURCE_SUN_EVENT_CALENDAR` |
| Runtime Overlay | 실행 시각에 맞춰 다시 생성되는 mock source | `SOURCE_FIRE_RESOURCE_AVAILABILITY`, `SOURCE_PREWATERING_EQUIPMENT_CAPACITY`, `SOURCE_SURFACE_FUEL_CONDITION`, `SOURCE_WORKSITE_HAZARD_CONDITIONS` |

현재 live driver로 가장 안정적인 것은 `SOURCE_OFFICIAL_FIRE_RISK_FORECAST`다.

## Run Modes

| mode | 의미 |
|---|---|
| `scenario` | 기준시각을 명시적으로 고정. 재현성과 디버깅 우선 |
| `live` | 현재 시각 기준. live driver 수집 후 같은 reference time으로 overlay 생성 |
| `hybrid` | live driver 일부가 비어도 overlay를 계속 생성 |

## 현재 Runtime Anchor

| anchor | row count | 의미 |
|---|---:|---|
| `station_master_gwangju_jeonnam.csv` | 95 | 광주·전남 119안전센터 기준표 |
| `regional_context_profile_gwangju_jeonnam.csv` | 623 | 광주·전남 법정 읍면동 context row |
| `kma_station_master_gwangju_jeonnam.csv` | 444 | 광주·전남 기상 관측 지점 기준표 |

저장 위치는 `data/reference/runtime_anchors/`다.

## Runtime Overlay Grain

| source_id | grain | time key | space key |
|---|---|---|---|
| `SOURCE_FIRE_RESOURCE_AVAILABILITY` | `station_id x shift_window` | `valid_from`, `valid_to`, `reference_time` | `station_id` |
| `SOURCE_PREWATERING_EQUIPMENT_CAPACITY` | `station_id x equipment_type` | `valid_from`, `valid_to`, `reference_time` | `station_id`, `equipment_id` |
| `SOURCE_SURFACE_FUEL_CONDITION` | `region_code x segment_id` | `valid_from`, `valid_to`, `reference_time` | `region_code`, generated polygon |
| `SOURCE_WORKSITE_HAZARD_CONDITIONS` | `region_code x segment_id` | `valid_from`, `valid_to`, `reference_time` | `region_code`, generated point |

## Validation Run

현재 기준 live validation:

| 항목 | 값 |
|---|---|
| `run_context_id` | `live_20260501T020000` |
| `reference_time` | `2026-05-01T02:22:04+09:00` |
| evidence path | `work/runtime_runs/live_20260501T020000/` |
| live driver status | `ok` |
| raw-role validation | `all_sources_raw_role_ready = true` |

Row count:

| source_id | rows |
|---|---:|
| `SOURCE_FIRE_RESOURCE_AVAILABILITY` | 950 |
| `SOURCE_PREWATERING_EQUIPMENT_CAPACITY` | 312 |
| `SOURCE_SURFACE_FUEL_CONDITION` | 623 |
| `SOURCE_WORKSITE_HAZARD_CONDITIONS` | 623 |

검증 기준:

- 필수 컬럼 존재
- join key 존재
- row grain 일관성
- `valid_from < valid_to`
- single `reference_time`
- single `run_context_id`
- geometry 필드 존재 여부
- categorical domain 이상 없음

## 해석 경계

현재 runtime overlay는 Feature 계산 이전 단계의 raw-role input으로 사용할 수 있다. 그러나 다음을 의미하지 않는다.

- 센터별 실제 live 인력/차량 가용성
- 장비별 실측 주수능력
- 현장 확인된 지표연료 또는 작업장 위험
- 자동 dispatch 또는 자동 defer에 충분한 운영 truth

따라서 response 계열 mock dominant 입력은 Decision 단계에서 `RequestManualReview` 또는 `advisory_only`로 분기해야 한다.

## 삭제 가능 산출물

장기 보존:

- `docs/07_runtime-operations.md`
- `data/reference/runtime_anchors/`
- source catalog와 pipeline

테스트 후 삭제 가능:

- `work/runtime_runs/live_20260501T020000/`
- `data/mock/SOURCE_FIRE_RESOURCE_AVAILABILITY/runs/live_20260501T020000/`
- `data/mock/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/runs/live_20260501T020000/`
- `data/mock/SOURCE_SURFACE_FUEL_CONDITION/runs/live_20260501T020000/`
- `data/mock/SOURCE_WORKSITE_HAZARD_CONDITIONS/runs/live_20260501T020000/`
- `data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/live_live_20260501T020000/`
