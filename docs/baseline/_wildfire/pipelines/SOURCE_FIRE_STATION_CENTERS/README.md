# SOURCE_FIRE_STATION_CENTERS Pipeline

공공데이터포털 `소방청_119안전센터 현황_20250701` 파일데이터를 다운로드해 원본 CSV와 raw field evidence를 남긴다.

## Access Options

| access_option_id | method | status | note |
|---|---|---|---|
| `ACCESS_FIRE_STATION_CENTERS_PRIMARY` | file_download | SELECTED proposal | 로그인 없이 CSV 원문 다운로드 가능 |
| `ACCESS_FIRE_STATION_CENTERS_AUTO_OPENAPI` | openapi | FALLBACK proposal | 공공데이터포털 자동 변환 JSON/XML API, 활용신청/API key 필요 |

## Raw Key Notes

- 원본 CSV 컬럼은 `순번`, `시도본부`, `소방서명`, `119안전센터명`, `주소`, `전화번호`, `팩스번호`다.
- 원본에는 좌표 컬럼이 없다. 주소를 native space key로 보존하고 임의 geocoding하지 않는다.
- `소방서명`은 소속 소방서 확인에는 사용할 수 있으나, 읍면동별 119안전센터 관할구역 필드는 아니다.

## Run

```bash
python3 pipelines/SOURCE_FIRE_STATION_CENTERS/fetch.py
```

Output:

```text
data/raw/SOURCE_FIRE_STATION_CENTERS/snapshots/full/
```
