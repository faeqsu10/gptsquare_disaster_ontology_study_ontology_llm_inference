# SOURCE_KMA_OBSERVED_WEATHER Pipeline

Fetches KMA APIHub ASOS hourly observation period data (`kma_sfctm3.php`) for a native station point.

## Request

- Sample station: KMA ASOS `156` (`광주`)
- Query window: `tm1=202604150000`, `tm2=202604212300`
- Raw time key: `TM`
- Raw space key: `STN`
- Native grain: station point. Do not interpolate to administrative-dong grain.

## Regional Gwangju/Jeonnam Expansion

`fetch_regional.py` stores the KMA station master for Gwangju/Jeonnam and
then fetches observations for active ASOS stations using the selected catalog
endpoint (`kma_sfctm3.php`).

- Station master scope: active and historical ASOS/AWS rows whose KMA metadata
  address starts with `광주광역시` or `전라남도`
- Observation snapshot scope: active ASOS only
- AWS handling: AWS stations are kept in the station master, but AWS
  observations are not fetched through the ASOS endpoint until a separate AWS
  access option is validated
- Raw rule: station point values are preserved; no interpolation, spatial join,
  CRS conversion, or feature calculation is performed

## Auth

Set one of:

```bash
export KMA_APIHUB_AUTH_KEY='...'
export APIHUB_AUTH_KEY='...'
```

Then run:

```bash
./pipelines/SOURCE_KMA_OBSERVED_WEATHER/fetch.py
```

The script writes under `data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/sample_20260430/` by default.

For the regional station master and active ASOS batch snapshot:

```bash
./pipelines/SOURCE_KMA_OBSERVED_WEATHER/fetch_regional.py \
  --tm1 202604150000 \
  --tm2 202604212300
```

Outputs:

- `data/reference/runtime_anchors/kma_station_master_gwangju_jeonnam.csv`
- `data/reference/runtime_anchors/kma_station_master_gwangju_jeonnam.manifest.json`
- `data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/full_gwangju_jeonnam_20260415_20260421/`
