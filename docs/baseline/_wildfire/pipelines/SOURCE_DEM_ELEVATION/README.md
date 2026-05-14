# Pipeline — SOURCE_DEM_ELEVATION

## Acquisition Decision

Excluded from TX04 by user instruction on 2026-04-30. Do not download DEM IMG tiles, inspect raster metadata, reproject, clip, or derive slope/aspect for this transaction.

The previously verified public access path is kept only as reference: the data.go.kr listing redirects to the National Land Information Platform and states that login and large-file transfer software are required for DEM downloads.

## Files

- `manual_download.md`: reference-only manual procedure. Not active for TX04.

## Raw Snapshot Target

No raw snapshot target is active for TX04. No raster was downloaded.

## Post-Download Verification

If DEM is reintroduced in a later transaction, inspect metadata without deriving terrain products:

```bash
gdalinfo path/to/downloaded.img
```

Record driver, band count, native CRS, geotransform, pixel size, NoData value, and tile/file name. Do not calculate slope, aspect, hillshade, ridge/valley, or reproject during the raw phase.
