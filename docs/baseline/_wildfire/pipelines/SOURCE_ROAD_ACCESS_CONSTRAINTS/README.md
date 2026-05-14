# Pipeline - SOURCE_ROAD_ACCESS_CONSTRAINTS

Selected access option: `ACCESS_ROAD_ACCESS_CONSTRAINTS_BASELINE_SCENARIO`.

Generate baseline:

```bash
python3 pipelines/SOURCE_ROAD_ACCESS_CONSTRAINTS/generate.py
```

Output:

```text
data/mock/SOURCE_ROAD_ACCESS_CONSTRAINTS/scenario_baseline/
  road_access_constraints.csv
  road_access_constraints.geojson
  manifest.json
```

The generated rows include explicit road segment keys and road names. The generator does not compute travel time, route impedance, or joins against the real road network.

The generator creates one baseline road-access segment for each SOURCE_ADMIN_BOUNDARIES 광주·전남 current legal 읍면동 row: 623 rows total, 광주 202 and 전남 421.
