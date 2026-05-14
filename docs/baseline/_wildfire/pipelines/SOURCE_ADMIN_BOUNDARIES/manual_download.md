# Manual Download — SOURCE_ADMIN_BOUNDARIES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_ADMIN_BOUNDARIES` |
| access_option_id | `ACCESS_ADMIN_BOUNDARIES_ADMIN_CODE` |
| source_url | https://www.data.go.kr/data/15123128/fileData.do |
| direct_download_url | https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000002819529&fileDetailSn=1&insertDataPrcus=N |
| account_required | none |
| terms_or_license | 이용허락범위 제한 없음 |
| expected_format | CSV, WKB geometry field |
| source_file_name | `LP_AA_EMD.csv` |
| source_size_observed | 109,743,962 bytes |

## Steps

1. Open the source URL.
2. Use the file download button or the direct download URL above.
3. For this transaction, run:

```bash
python3 pipelines/SOURCE_ADMIN_BOUNDARIES/fetch.py
```

The script writes the full source file and regional clips under:

```text
data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/
```

The 광주·전남 clip filter is `객체시군구코드` prefix in `29` or `46`.
The clip preserves selected source rows without geometry or CRS conversion.
