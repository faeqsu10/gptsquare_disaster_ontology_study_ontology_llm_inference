# live_20260501T020000

이 디렉터리는 2026-05-01 02:22:04 KST 기준으로 생성한 live test run 1회의 증적이다.

이 run의 목적:

- 현재 시간 기준으로 response 관련 5개 source가 같은 시간축으로 생성되는지 확인
- runtime overlay 4종이 downstream raw-role input으로 쓸 수 있는지 검증

## 포함 파일

- `run_context.json`
  - 이번 실행의 기준 시간, horizon, shift, run id
- `source_cycle_status.json`
  - source별 lifecycle class와 현재 cycle hint
- `live_fire_driver_status.json`
  - 공식 산불위험예보 live fetch 결과
- `runtime_bundle_manifest.json`
  - 이번 run에서 생성한 overlay source 목록
- `validation_report.json`
  - raw-role input 검증 결과

## 핵심 결과

- live driver status: `ok`
- raw-role validation: `all_sources_raw_role_ready = true`

row 수:

- `SOURCE_FIRE_RESOURCE_AVAILABILITY`: 950
- `SOURCE_PREWATERING_EQUIPMENT_CAPACITY`: 312
- `SOURCE_SURFACE_FUEL_CONDITION`: 623
- `SOURCE_WORKSITE_HAZARD_CONDITIONS`: 623

## 삭제 정책

이 디렉터리와 아래 대응 run output은 test 증적이므로 필요 없으면 함께 삭제할 수 있다.

- `work/runtime_runs/live_20260501T020000/`
- `data/mock/SOURCE_FIRE_RESOURCE_AVAILABILITY/runs/live_20260501T020000/`
- `data/mock/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/runs/live_20260501T020000/`
- `data/mock/SOURCE_SURFACE_FUEL_CONDITION/runs/live_20260501T020000/`
- `data/mock/SOURCE_WORKSITE_HAZARD_CONDITIONS/runs/live_20260501T020000/`
- `data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/live_live_20260501T020000/`
