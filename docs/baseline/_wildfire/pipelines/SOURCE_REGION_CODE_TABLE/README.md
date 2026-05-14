# Pipeline — SOURCE_REGION_CODE_TABLE

`fetch.py` stores full code-table snapshots for:

- `국토교통부_전국 법정동_20250807`
- `국가데이터처_행정동 정보_20250704`

The original catalog candidate only pointed to the legal-dong table. This transaction adds the administrative-dong table as an update proposal so that administrative-dong names (which are not present in the legal-code table) can also be resolved.
The full snapshot also contains manually downloaded MOIS `jscode20260325` text files for 행정기관-관할 법정동 mapping.

Output:

```text
data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/
  national_legal_dong_20250807.csv
  national_legal_dong_gwangju_jeonnam.csv
  kostat_admin_dong_20250704.csv
  kostat_admin_dong_gwangju_jeonnam.csv
  KIKmix.20260325
  KIKcd_H.20260325
  KIKcd_B.20260325
  metadata.json
```

Raw-phase constraints:

- no code-system harmonization
- no downstream legal/admin dong fan-out or area allocation
- no spatial join
