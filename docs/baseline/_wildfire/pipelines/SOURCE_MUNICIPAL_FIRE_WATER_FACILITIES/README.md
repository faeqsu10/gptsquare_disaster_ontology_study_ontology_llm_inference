# Pipeline - SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES

Selected access option: `ACCESS_MUNICIPAL_FIRE_WATER_FACILITIES_BASELINE_SCENARIO`.

Public municipal fire-water datasets exist as fragmented fire-station or municipality CSV/API entries. This source remains mock for the practice baseline because consistent 광주·전남 point coverage is not guaranteed in one reproducible public source.

The generator now creates one baseline facility point for each SOURCE_ADMIN_BOUNDARIES 광주·전남 current legal 읍면동 row: 623 rows total, 광주 202 and 전남 421.

Generate baseline:

```bash
python3 pipelines/SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES/generate.py
```

Output:

```text
data/mock/SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES/scenario_baseline/
  municipal_fire_water_facilities.csv
  municipal_fire_water_facilities.geojson
  manifest.json
```

Raw-phase constraints:

- generated points are not joined to roads or segments
- no nearest-distance calculation
- generated native CRS is `EPSG:4326`
