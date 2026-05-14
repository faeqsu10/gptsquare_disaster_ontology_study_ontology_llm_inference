# SOURCE_VULNERABLE_FACILITIES Pipeline

Purpose: replace the TBD vulnerable-facility source with a concrete Gwangju senior nursing facility CSV source.

Selected source:

```text
광주광역시_노인요양시설 현황_20241231
https://www.data.go.kr/data/15043855/fileData.do
```

Run:

```bash
python3 pipelines/SOURCE_VULNERABLE_FACILITIES/fetch.py
```

The script downloads the original CSV and preserves native `시군구` and address text. It does not geocode or join to segments.

Full 광주·전남 snapshot:

```bash
DATA_GO_KR_SERVICE_KEY=<issued-key> python3 pipelines/SOURCE_VULNERABLE_FACILITIES/fetch_full_gwangju_jeonnam.py
```

The full downloader saves Gwangju senior/medical welfare CSVs and the Jeonnam nursing hospital CSV. It records the Jeonnam elderly welfare API responses; after the 2026-05-01 retry, those five endpoints returned HTTP 404 from both the data.go.kr proxy and the Jeonnam operation URL.

Jeonnam elderly-welfare mock fallback:

```bash
python3 pipelines/SOURCE_VULNERABLE_FACILITIES/generate_elderly_welfare_mock.py
```

The mock fallback writes API-shaped JSON responses plus CSV/GeoJSON under:

```text
data/mock/SOURCE_VULNERABLE_FACILITIES/scenario_baseline/
```

It covers all 22 Jeonnam 시군구 for the five missing elderly-welfare API classes. Gwangju rows are not mocked when the existing real Gwangju senior/medical welfare snapshot is present. Generated coordinates are synthetic points constrained to admin boundary polygons, not geocoded facility locations.
