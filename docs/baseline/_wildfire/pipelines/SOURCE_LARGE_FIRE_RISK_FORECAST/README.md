# SOURCE_LARGE_FIRE_RISK_FORECAST

대형산불위험예보목록정보 CSV downloader.

## Verified Access

| 항목 | 값 |
|---|---|
| provider | 산림청 국립산림과학원 |
| portal page | https://www.data.go.kr/data/15092027/fileData.do |
| direct file | `https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003631149&fileDetailSn=1&insertDataPrcus=N` |
| optional ODCloud API | `https://api.odcloud.kr/api/15092027/v1/uddi:5958ff6b-46cc-4a46-9415-bc34926647cb` |
| selected grain | 읍면동명 |
| raw encoding | CP949 CSV |

## Sample Command

```bash
python3 pipelines/SOURCE_LARGE_FIRE_RISK_FORECAST/fetch.py --mode file
```

ODCloud paginated API mode for a later phase:

```bash
DATA_GO_KR_SERVICE_KEY='...' python3 pipelines/SOURCE_LARGE_FIRE_RISK_FORECAST/fetch.py \
  --mode odcloud \
  --page 1 \
  --per-page 100
```

ODCloud 자동변환 endpoint도 활용신청 후 정상 동작을 확인했다. 직접 CSV 다운로드는 로그인/키 없이 동작하고, paginated JSON 수집은 `DATA_GO_KR_SERVICE_KEY`가 필요하다.

Raw phase에서는 원본 CSV encoding, 컬럼명, 행정구역명을 그대로 보존한다.
