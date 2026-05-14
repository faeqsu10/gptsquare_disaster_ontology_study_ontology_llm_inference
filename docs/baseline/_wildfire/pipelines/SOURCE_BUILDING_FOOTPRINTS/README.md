# SOURCE_BUILDING_FOOTPRINTS Pipeline

Purpose: verify the VWorld GIS building integration WFS option for sample bbox acquisition.

Selected endpoint:

```text
https://api.vworld.kr/ned/wfs/getBldgisSpceWFS
```

Key parameters:

```text
typename=dt_d010
bbox=35.1200,126.9000,35.1800,126.9700,EPSG:4326
srsName=EPSG:4326
output=application/json
maxFeatures=20
```

Run:

```bash
VWORLD_API_KEY=<issued-key> python3 pipelines/SOURCE_BUILDING_FOOTPRINTS/fetch.py
```

Without `VWORLD_API_KEY`, the service returns a WFS exception proving that the endpoint is live and the key is required.

Full 광주·전남 snapshot:

```bash
VWORLD_API_KEY=<issued-key> python3 pipelines/SOURCE_BUILDING_FOOTPRINTS/fetch_full_gwangju_jeonnam.py
```

The full downloader uses the existing admin EMD boundary snapshot, recursively tiles bboxes until each VWorld WFS request is below `maxFeatures`, and writes native features to `building_footprints.geojsonl`. Use `--resume` to continue from `progress_manifest.json`.
