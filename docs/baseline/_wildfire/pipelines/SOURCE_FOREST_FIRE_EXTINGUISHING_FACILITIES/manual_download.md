# Manual Download - SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES

| 항목 | 내용 |
|---|---|
| source_id | `SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES` |
| selected_access_option_id | `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_PRIMARY` |
| fallback_access_option_id | `ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_OPENAPI` |
| source_url | https://www.data.go.kr/data/15144785/fileData.do |
| account_required | CSV file: none observed; OpenAPI: public API key/application |
| terms_or_license | data.go.kr metadata: 이용허락범위 제한 없음 |
| expected_format | CSV, JSON, XML |

## Steps

1. Open the data.go.kr source page.
2. Use the file-data tab for CSV download.
3. Store the original CSV under:

```text
data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/full/
```

4. If file download is unavailable, use the OpenAPI tab after public API application and store the raw JSON/XML response under:

```text
data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/sample_YYYYMMDD/
```

## Verified Metadata

- `파일데이터명`: `산림청_산불상황관제시스템_산불소화시설_20211231`
- `수정일`: `2025-08-13`
- CSV total rows: 187
- OpenAPI extension: XML, JSON
- preview columns include `경도`, `위도`, `설치위치`, `관리기관1`, `관리기관2`

## Raw Preservation

Do not compute nearest distance to a facility, reproject coordinates, or join facility points to Segment in this phase.

