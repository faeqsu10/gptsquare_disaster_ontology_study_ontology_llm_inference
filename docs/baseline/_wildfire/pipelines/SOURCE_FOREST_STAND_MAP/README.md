# Pipeline — SOURCE_FOREST_STAND_MAP

## Acquisition Decision

This source is FGIS manual-download at acquisition time. The official Forest Geospatial Information Service documents the forest stand map as SHP data and provides it through the map-service "free download application" workflow, not a stable unauthenticated file URL.

The preserved manual downloads can now be registered as a reproducible 광주·전남 full raw snapshot with:

```bash
python3 pipelines/SOURCE_FOREST_STAND_MAP/build_full_gwangju_jeonnam.py
```

## Files

- `manual_download.md`: verified manual procedure and raw-preservation rules.
- `build_full_gwangju_jeonnam.py`: verifies preserved 광주/전남 FGIS SHP ZIP evidence and writes a full regional snapshot manifest without copying multi-GB archives.

## Raw Snapshot Target

```text
data/raw/SOURCE_FOREST_STAND_MAP/snapshots/full_gwangju_jeonnam_20260430/
```

The full snapshot manifest links back to preserved source archives under:

```text
data/raw/SOURCE_FOREST_STAND_MAP/snapshots/regional_clip/gwangju_sido/
data/raw/SOURCE_FOREST_STAND_MAP/snapshots/regional_clip/jeonnam_sido/
```

## Post-Download Verification

After a SHP ZIP is obtained, keep all sidecar files unchanged and inspect only metadata:

```bash
ogrinfo -so path/to/downloaded.shp
ogrinfo -al -so path/to/downloaded.shp
```

Record the source layer name, native CRS, geometry type, feature count, and raw field names. Do not dissolve polygons, reproject, or clip unless creating a separate regional evidence copy that preserves source CRS and original fields.
