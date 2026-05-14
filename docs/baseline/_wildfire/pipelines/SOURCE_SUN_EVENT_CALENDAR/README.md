# SOURCE_SUN_EVENT_CALENDAR Pipeline

Fetches KASI sunrise/sunset information (`getAreaRiseSetInfo`) for the target admin area.

## Request

- KASI native admin-area request: `location=광주` (또는 전남 시군 단위)
- Query dates: `20260415` through `20260421`
- Raw time key: `locdate`
- Raw space key: `location`
- Native grain: admin area with service-returned representative coordinate. Do not align to weather forecast grid.

## Auth

Set one of:

```bash
export KASI_SERVICE_KEY='...'
export DATA_GO_KR_SERVICE_KEY='...'
```

Then run:

```bash
./pipelines/SOURCE_SUN_EVENT_CALENDAR/fetch.py
```

The script writes under `data/raw/SOURCE_SUN_EVENT_CALENDAR/snapshots/sample_20260430/` by default.
