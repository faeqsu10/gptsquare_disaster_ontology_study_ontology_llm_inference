# Pipeline — SOURCE_ADMIN_BOUNDARIES

`fetch.py` downloads the NGII public CSV stream and stores the full source file plus regional clips.

The upstream file is about 109.7 MB. The full source CSV is stored as-is, and clips preserve original CSV bytes for selected rows, including the source WKB geometry field and source encoding.

Output:

```text
data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/
  LP_AA_EMD.csv
  LP_AA_EMD_gwangju_jeonnam.csv
  metadata.json
```

Raw-phase constraints:

- no CRS conversion
- no spatial join
- no administrative-dong fan-out
- no geometry rewriting
