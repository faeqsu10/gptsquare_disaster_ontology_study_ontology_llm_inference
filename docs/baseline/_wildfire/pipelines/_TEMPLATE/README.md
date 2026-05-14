# Pipeline Template

이 디렉터리는 Source별 acquisition/generation pipeline의 표준 구조를 정의한다.

대상 구조:

```text
pipelines/<source_id>/
  README.md
  fetch.py
  manual_download.md
  generate.py
  sample_request.json
  sample_response.json
```

규칙:

- `openapi`: `fetch.py`, `sample_request.json`, `sample_response.json` 작성
- `file_download`: 자동화 가능하면 `fetch.py`, 아니면 `manual_download.md` 작성
- `wms_wfs`: sample bbox request를 `sample_request.json`에 기록하고 raw response 저장
- `manual_download`: `manual_download.md`에 계정, 약관, 페이지 경로, 필터 조건 기록
- `generated_mock`: `generate.py`와 baseline scenario sample 작성

금지:

- Raw phase에서 좌표계 통일 금지
- Raw phase에서 3시간 grid alignment 금지
- Raw phase에서 읍면동 fan-out 또는 Segment spatial join 금지
