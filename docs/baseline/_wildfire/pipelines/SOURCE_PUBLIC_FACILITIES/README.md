# SOURCE_PUBLIC_FACILITIES Pipeline

Purpose: replace the TBD source with concrete public-facility source candidates and save a reproducible no-auth sample.

Selected sample source:

```text
광주광역시_공공보건의료기관 현황_20240313
https://www.data.go.kr/data/15056455/fileData.do
```

Additional concrete candidates recorded in `candidate_sources.json`:

```text
전국초중등학교위치표준데이터
https://www.data.go.kr/data/15021148/standard.do

건강보험심사평가원_병원정보서비스
https://www.data.go.kr/data/15001698/openapi.do
```

Run:

```bash
python3 pipelines/SOURCE_PUBLIC_FACILITIES/fetch.py
```

Optional authenticated API samples:

```bash
DATA_GO_KR_SERVICE_KEY=<issued-key> python3 pipelines/SOURCE_PUBLIC_FACILITIES/fetch.py
```

When `DATA_GO_KR_SERVICE_KEY` is present, the script also attempts:

```text
https://api.data.go.kr/openapi/tn_pubr_public_elesch_mskul_lc_api
https://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList
```

TX05 disposition:

```text
The school API option is rejected/excluded from TX05 after reproducible NODATA_ERROR for 광주·전남 filters.
HIRA hospital API pages were acquired and remain the concrete hospital fallback.
```

The script downloads the Gwangju public health facility CSV. It preserves native address text and does not geocode or join to segments.

Full 광주·전남 snapshot:

```bash
DATA_GO_KR_SERVICE_KEY=<issued-key> python3 pipelines/SOURCE_PUBLIC_FACILITIES/fetch_full_gwangju_jeonnam.py
```

The full downloader saves Gwangju/Jeonnam file-data CSVs and HIRA hospital API pages. It also records school API responses as rejected evidence; 광주/전남 school filters returned `NODATA_ERROR` and school coverage is excluded from TX05.
