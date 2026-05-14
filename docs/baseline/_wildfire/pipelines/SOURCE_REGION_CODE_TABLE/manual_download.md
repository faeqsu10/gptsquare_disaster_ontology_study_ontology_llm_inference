# Manual Download — SOURCE_REGION_CODE_TABLE

## Legal-Dong Table

| 항목 | 내용 |
|---|---|
| source_url | https://www.data.go.kr/data/15063424/fileData.do |
| direct_download_url | https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003207360&fileDetailSn=1&insertDataPrcus=N |
| account_required | none |
| terms_or_license | 이용허락범위 제한 없음 |
| expected_format | CSV |
| source_file_name | `국토교통부_전국_법정동_20250807.csv` |
| source_size_observed | 3,799,696 bytes |

## Administrative-Dong Table

| 항목 | 내용 |
|---|---|
| source_url | https://www.data.go.kr/data/15136373/fileData.do |
| direct_download_url | https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003181687&fileDetailSn=1&insertDataPrcus=N |
| account_required | none |
| terms_or_license | 이용허락범위 제한 없음 |
| expected_format | CSV |
| source_file_name | `HJ_HJDONG.csv` |
| source_size_observed | 30,532,809 bytes |

## MOIS Administrative-Legal Mapping

| 항목 | 내용 |
|---|---|
| source_url | https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=124721 |
| attachment | `jscode20260325(말소코드포함).zip` |
| account_required | none |
| expected_format | fixed-width text, XLSX |
| source_effective_at | 2026-03-25 |
| copied_source_files | `KIKmix.20260325`, `KIKcd_H.20260325`, `KIKcd_B.20260325` |
| note | Stored filenames remove the source suffix `(말소코드포함)`. |

## Steps

Run:

```bash
python3 pipelines/SOURCE_REGION_CODE_TABLE/fetch.py
```

The script stores both full source files under:

```text
data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/
```

It also writes 광주·전남 clips:

```text
national_legal_dong_gwangju_jeonnam.csv
kostat_admin_dong_gwangju_jeonnam.csv
```

The MOIS KiK files are supplemental manual-download inputs. Copy the three text files into the same snapshot directory with normalized filenames:

```text
KIKmix.20260325
KIKcd_H.20260325
KIKcd_B.20260325
```
