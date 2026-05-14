# Pipeline — SOURCE_FOREST_ROAD_NETWORK

## Acquisition Decision

This source is FGIS manual-download at acquisition time. The Forest Service public-data page documents the forest road map and points users to the Forest Geospatial Information Service application flow for SHP downloads.

The preserved 전라남도 download and 광주광역시 no-data evidence can now be registered as a reproducible 광주·전남 full raw snapshot with:

```bash
python3 pipelines/SOURCE_FOREST_ROAD_NETWORK/build_full_gwangju_jeonnam.py
```

## Files

- `manual_download.md`: verified manual procedure and raw-preservation rules.
- `build_full_gwangju_jeonnam.py`: verifies preserved 전라남도 FGIS SHP ZIP evidence and records 광주광역시 no-data evidence without building a road graph.

## Raw Snapshot Target

```text
data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/full_gwangju_jeonnam_20260430/
```

The full snapshot manifest links back to preserved source archives under:

```text
data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/regional_clip/jeonnam_sido/
```

광주광역시 is recorded as no-data for this FGIS layer based on the prior acquisition flow; no synthetic forest-road line is generated.

## Post-Download Verification

After a SHP ZIP is obtained:

```bash
ogrinfo -so path/to/downloaded.shp
ogrinfo -al -so path/to/downloaded.shp
```

Record layer name, native CRS, geometry type, feature count, and raw road fields. Do not reproject, simplify, network-build, or spatial-join during the raw phase.
