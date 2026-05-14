# SOURCE_HERITAGE_SPATIAL Pipeline

Purpose: verify 국가유산 spatial acquisition options and save a sample bbox feature sample.

Confirmed official API page:

```text
https://gis-heritage.go.kr/helpAPI.do
```

Practical feature endpoint:

```text
https://portal.esrikr.com/arcgis/rest/services/Hosted/KoreaHerritageSites/FeatureServer
```

Run:

```bash
python3 pipelines/SOURCE_HERITAGE_SPATIAL/fetch.py
```

The script queries layers 1-6 with a EPSG:4326 query envelope, stores `sample_response_arcgis_native.json` in the service native CRS (EPSG:5179), and also writes `sample_response.geojson` as a convenience copy for quick inspection.

Full 광주·전남 snapshot:

```bash
python3 pipelines/SOURCE_HERITAGE_SPATIAL/fetch_full_gwangju_jeonnam.py
```

The full downloader filters native ArcGIS JSON by `시도명 IN ('광주광역시','전라남도')` and preserves service-native EPSG:5179 geometry.
