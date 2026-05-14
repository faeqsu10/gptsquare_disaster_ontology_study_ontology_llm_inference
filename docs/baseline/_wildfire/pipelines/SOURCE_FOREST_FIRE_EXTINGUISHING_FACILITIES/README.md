# Pipeline - SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES

Access options verified:

- `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_PRIMARY`: CSV file download, selected
- `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_OPENAPI`: JSON/XML OpenAPI auto-conversion, fallback
- `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_COVERAGE_SUPPLEMENT`: generated mock supplement for 광주·전남 full baseline coverage

The official page exposes a CSV file and an automatically converted OpenAPI surface. The preview rows include longitude, latitude, installation location, management agencies, protected-object class, protected object, and installation year.

Output captured for this transaction:

```text
data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/full/
  forest_fire_extinguishing_facilities_20211231_original.csv
  manifest.json

data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/regional_clip/
  gwangju_jeonnam_rows.csv

data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/sample_20260430/
  access_option_verification.json
  dcat.xml
  sample_preview.csv
  source_page.md

data/mock/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/scenario_baseline/
  forest_fire_extinguishing_facilities_coverage_supplement.csv
  forest_fire_extinguishing_facilities_coverage_supplement.geojson
  manifest.json
```

Full CSV coverage:

```text
total rows: 187
전남 rows: 13
광주 rows: 0
encoding: CP949
```

Coverage supplement:

```bash
python3 pipelines/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/generate_coverage_supplement.py
```

```text
supplement rows: 623
coverage units: SOURCE_REGION_CODE_TABLE 광주·전남 current legal 읍면동 rows
광주 units: 202
전남 units: 421
record_origin: mock_supplement
```

Raw-phase constraints:

- no nearest facility distance
- no segment join
- no CRS conversion
