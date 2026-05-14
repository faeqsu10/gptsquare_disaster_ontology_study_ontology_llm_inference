# Manual Download - SOURCE_NATURAL_BARRIERS

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_NATURAL_BARRIERS` |
| access_option_id | `ACCESS_NATURAL_BARRIERS_PRIMARY` |
| source_url | https://www.data.go.kr/data/15059910/fileData.do |
| institution_url | http://map.ngii.go.kr/ms/map/NlipMap.do?tabGb=total |
| account_required | login required on National Land Information Platform download flow |
| terms_or_license | data.go.kr metadata: 이용허락범위 제한 없음 |
| expected_format | SHP or NGI |

## Steps

1. Open the data.go.kr source page.
2. Follow the National Land Information Platform URL.
3. Search the PoC region or desired area.
4. Select 기본공간정보 and barrier-relevant target feature classes, preserving native layers.
5. Download the original SHP/NGI package and store it under:

```text
data/raw/SOURCE_NATURAL_BARRIERS/snapshots/full/
```

## Verified Metadata

- `파일데이터명`: `국토교통부 국토지리정보원_기본공간정보_20240924`
- `수정일`: `2025-06-23`
- `확장자`: SHP
- barrier-relevant classes observed in metadata: `수계`, `지형`, `교통`
- exact open-space feature availability remains a gap until the native layer list is inspected

## Raw Preservation

Do not derive barrier candidates, reproject geometry, or join barrier features to Segment in this phase.

