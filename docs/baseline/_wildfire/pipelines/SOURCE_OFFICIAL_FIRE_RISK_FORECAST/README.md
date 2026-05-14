# SOURCE_OFFICIAL_FIRE_RISK_FORECAST

공식 산불위험예보정보 OpenAPI sample fetcher.

## Verified Access

| 항목 | 값 |
|---|---|
| provider | 산림청 국립산림과학원 |
| portal page | https://www.data.go.kr/data/15084817/openapi.do |
| service base | `https://apis.data.go.kr/1400377/forestPointV2` |
| selected endpoint | `/forestPointListSigunguSearchV2` |
| auth | `DATA_GO_KR_SERVICE_KEY` |
| selected grain | 시군구 |

현재 공식 Swagger에는 전국, 시도, 시군구 endpoint만 있고 읍면동 endpoint 또는 읍면동 query parameter가 없다. 따라서 읍면동 option은 `REJECTED`, 시군구 option은 `SELECTED`로 제안한다.

## Sample Command

```bash
DATA_GO_KR_SERVICE_KEY='...' python3 pipelines/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/fetch.py \
  --local-areas "" \
  --upplocalcd 29 \
  --exclude-forecast 0
```

Request metadata만 쓰려면:

```bash
python3 pipelines/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/fetch.py --write-request-only
```

## Full Ingestion Parameters

- `--endpoint`: `forestPointListGeongugSearchV2`, `forestPointListSidoSearchV2`, `forestPointListSigunguSearchV2`
- `--local-areas`: 시도 2자리 또는 시군구 5자리 코드
- `--upplocalcd`: 시도 2자리 코드
- `--page-no`, `--num-of-rows`
- `--exclude-forecast`: `0` include, `1` exclude

Raw phase에서는 행정구역 fan-out, 3시간 grid alignment, Feature 계산을 수행하지 않는다.
