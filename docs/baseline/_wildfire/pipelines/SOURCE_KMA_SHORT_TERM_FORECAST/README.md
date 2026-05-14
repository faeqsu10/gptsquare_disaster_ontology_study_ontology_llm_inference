# SOURCE_KMA_SHORT_TERM_FORECAST Pipeline

Fetches KMA short-term forecast (`getVilageFcst`) rows for the native KMA nx/ny grid.

## Request

- Sample representative point: WGS84 `lat=35.1324844`, `lon=126.9335438` (광주 시내)
- KMA grid selected for raw snapshot: `nx=60`, `ny=74`
- Forecast issue sample: `base_date=20260415`, `base_time=0500`
- Raw time keys: `baseDate`, `baseTime`, `fcstDate`, `fcstTime`
- Raw space keys: `nx`, `ny`

## Auth

Set one of:

```bash
export KMA_DATA_GO_KR_SERVICE_KEY='...'
export DATA_GO_KR_SERVICE_KEY='...'
```

Then run:

```bash
./pipelines/SOURCE_KMA_SHORT_TERM_FORECAST/fetch.py
```

The script writes under `data/raw/SOURCE_KMA_SHORT_TERM_FORECAST/snapshots/sample_20260430/` by default.

