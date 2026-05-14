# Manual Download - SOURCE_ROAD_NETWORK

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_ROAD_NETWORK` |
| access_option_id | `ACCESS_ROAD_NETWORK_PRIMARY` |
| source_url | https://www.data.go.kr/data/15025526/fileData.do |
| institution_url | https://www.its.go.kr/nodelink/nodelinkRef |
| account_required | data.go.kr page: none observed; ITS download flow must be confirmed manually |
| terms_or_license | data.go.kr metadata: 이용허락범위 제한 없음 |
| expected_format | SHP |

## Steps

1. Open the data.go.kr source page.
2. Follow the institution download link to ITS standard node/link reference.
3. Download the standard node/link SHP package without changing CRS or geometry.
4. Store the original package under:

```text
data/raw/SOURCE_ROAD_NETWORK/snapshots/full/
```

## Verified Metadata

- `파일데이터명`: `국토교통부_표준노드링크_20210713`
- `수정일`: `2025-06-24`
- `제공형태`: `기관자체에서 다운로드(제공데이터URL기재)`
- `URL`: `https://www.its.go.kr/nodelink/nodelinkRef`
- native spatial grain: road node/link

## Raw Preservation

Do not calculate movement time, route impedance, nearest road distance, or road-to-segment joins in this phase.

