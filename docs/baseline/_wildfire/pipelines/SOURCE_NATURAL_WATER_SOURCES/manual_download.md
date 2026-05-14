# Manual Download - SOURCE_NATURAL_WATER_SOURCES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_NATURAL_WATER_SOURCES` |
| access_option_id | `ACCESS_NATURAL_WATER_SOURCES_PRIMARY` |
| source_url | https://www.data.go.kr/data/15059910/fileData.do |
| institution_url | http://map.ngii.go.kr/ms/map/NlipMap.do?tabGb=total |
| account_required | login required on National Land Information Platform download flow |
| terms_or_license | data.go.kr metadata: 이용허락범위 제한 없음 |
| expected_format | SHP or NGI |

## Steps

1. Open the data.go.kr source page.
2. Follow the National Land Information Platform URL.
3. Search the PoC region or desired area.
4. Select 기본공간정보 and target feature class `수계`.
5. Download the original SHP/NGI package and store it under:

```text
data/raw/SOURCE_NATURAL_WATER_SOURCES/snapshots/full/
```

## Verified Metadata

- `파일데이터명`: `국토교통부 국토지리정보원_기본공간정보_20240924`
- `수정일`: `2025-06-23`
- `확장자`: SHP
- target feature classes include `수계(하천경계면, 하천링크, 해안선, 하천노드 등)`
- download requires the National Land Information Platform flow and large-file transfer software

## Raw Preservation

Do not compute nearest distance to water, reproject geometry, or join water features to Segment in this phase.

