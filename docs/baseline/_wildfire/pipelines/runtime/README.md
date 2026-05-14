# Runtime Bundle

광주광역시·전라남도 전역 mock source를 같은 시간 기준으로 생성하는 실행 entrypoint입니다.

핵심 구조:

```text
static anchor
  - station_master_gwangju_jeonnam.csv
  - regional_context_profile_gwangju_jeonnam.csv

live driver
  - SOURCE_OFFICIAL_FIRE_RISK_FORECAST (가능하면 현재 horizon fetch)

runtime overlay
  - SOURCE_FIRE_RESOURCE_AVAILABILITY
  - SOURCE_PREWATERING_EQUIPMENT_CAPACITY
  - SOURCE_SURFACE_FUEL_CONDITION
  - SOURCE_WORKSITE_HAZARD_CONDITIONS
```

## Why

고정 시각으로 박힌 mock CSV는 live forecast와 섞이면 시간축이 어긋납니다.

이 runtime bundle은 모든 overlay를 `run_context.reference_time`에 맞춰 다시 생성합니다.

## Modes

- `scenario`: 고정 기준시각으로 재현 가능한 baseline 생성
- `live`: 현재 시각 기준으로 live driver를 최대한 활용
- `hybrid`: live driver + runtime mock overlay를 같이 사용

## Commands

Scenario baseline 재생성:

```bash
python3 pipelines/runtime/build_runtime_bundle.py \
  --mode scenario \
  --reference-time 2026-04-15T00:00:00+09:00 \
  --layout scenario_baseline \
  --scenario-name scenario_baseline \
  --skip-live-fire-fetch
```

현재 시각 live run 생성:

```bash
python3 pipelines/runtime/build_runtime_bundle.py --mode live --layout runs
```

특정 source만 재생성:

```bash
python3 pipelines/runtime/build_runtime_bundle.py \
  --mode live \
  --reference-time 2026-05-01T00:29:42+09:00 \
  --source-id SOURCE_FIRE_RESOURCE_AVAILABILITY \
  --layout runs
```

## Outputs

- static anchor:
  - `data/reference/runtime_anchors/station_master_gwangju_jeonnam.csv`
  - `data/reference/runtime_anchors/regional_context_profile_gwangju_jeonnam.csv`
- live run metadata:
  - `work/runtime_runs/<run_context_id>/run_context.json`
  - `work/runtime_runs/<run_context_id>/source_cycle_status.json`
  - `work/runtime_runs/<run_context_id>/runtime_bundle_manifest.json`
- live fire risk snapshot:
  - `data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/live_<run_context_id>/`
- runtime mock outputs:
  - `data/mock/<SOURCE_ID>/runs/<run_context_id>/`

## Notes

- geocoding은 수행하지 않습니다.
- 119안전센터 좌표가 공식 source에 없으면 비워 둡니다.
- 법정동 exact match가 안 되는 센터도 시군구 fallback context로 runtime overlay에 포함합니다.
- live fire risk API key가 없으면 live driver status만 `missing_api_key`로 기록하고 overlay는 계속 생성합니다.
