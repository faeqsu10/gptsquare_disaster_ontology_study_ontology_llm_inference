# SOURCE_KMA_WEATHER_WARNINGS Pipeline

Fetches KMA APIHub weather warning history (`wrn_met_data.php`) while preserving native warning-area keys.

## Request

- Query window: `tmfc1=202604150000`, `tmfc2=202604212359`
- Warning area access: request `reg=0`, then preserve `REG_ID`/`REG_NAME` rows for 광주광역시 when a live key is available
- Warning types of interest: `D` 건조, `W` 강풍
- Raw time keys: `TM_FC`, `TM_EF`, `TM_ED`
- Raw space key: `REG_ID`

## Auth

Set one of:

```bash
export KMA_APIHUB_AUTH_KEY='...'
export APIHUB_AUTH_KEY='...'
```

Then run:

```bash
./pipelines/SOURCE_KMA_WEATHER_WARNINGS/fetch.py
```

The script writes under `data/raw/SOURCE_KMA_WEATHER_WARNINGS/snapshots/sample_20260430/` by default.

