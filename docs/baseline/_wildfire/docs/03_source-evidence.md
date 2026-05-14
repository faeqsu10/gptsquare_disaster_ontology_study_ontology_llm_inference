# Source Evidence

## 역할

Source evidence는 "이 Source를 실제로 봤는가"와 "downstream에서 어떤 key로 연결할 수 있는가"를 증명한다. Source layer의 상태 판정은 [02_source-layer.md](02_source-layer.md)에 있고, 상세 증거는 Source Dossier에 있다.

## Dossier 단위

각 Source Dossier는 다음을 기록한다.

| section | 목적 |
|---|---|
| Access Option Decision | selected, fallback, rejected option과 선택 이유 |
| Raw Snapshot Evidence | endpoint, download path, format, sample path, observed raw fields |
| Time Key Verification | raw 시간 field, semantics, grain, parse 예시 |
| Space Key Verification | raw 공간 field, geometry, CRS, native grain, region filter |
| PoC Coverage | 광주·전남 region 기준 sample 확인 |
| Final Decision | selected/fallback/mock/exclude 결론과 open issue |

## Evidence Index

전체 index는 [source_dossiers/README.md](source_dossiers/README.md)를 기준으로 본다.

중요한 예외:

- `SOURCE_CRITICAL_INFRASTRUCTURE_DETAIL`은 보안 민감 source라 raw evidence가 없다. catalog-only exclusion dossier로 관리한다.
- `SOURCE_SETTLEMENT_BOUNDARIES`는 기존 PoC-only mock이 regional coverage가 아니므로 excluded dossier로 관리한다.
- 일부 source는 JSON dossier가 없는 markdown-only exclusion memo일 수 있다. machine catalog의 authoritative state는 `data/reference/source_inventory.json`이다.

## Evidence 신뢰도 해석

| evidence 상태 | 해석 |
|---|---|
| `coverage_verified` | raw 또는 mock snapshot이 있고 time/space key 및 regional coverage 판단이 문서화됨 |
| `data_acquired` | 실제 파일은 확보했으나 downstream coverage/field 검증 gap이 남음 |
| `key_validated` | key와 sample은 확인했지만 필요한 time window 또는 regional snapshot이 부족함 |
| `api_tested` | endpoint와 response는 확인했지만 운영 snapshot으로 보기에는 부족함 |
| `source_confirmed` | source 존재 또는 절차는 확인했지만 active use에서 제외했거나 raw acquisition이 없음 |
| `unverified` | catalog에만 남기며 active dependency로 쓰지 않음 |

## Evidence와 Pipeline의 경계

- `docs/source_dossiers/`: 사람이 읽는 판단과 evidence.
- `data/reference/source_dossiers/`: 같은 evidence의 machine-readable record.
- `pipelines/<SOURCE_ID>/`: evidence를 다시 만들 수 있는 절차.
- `data/raw/`와 `data/mock/`: evidence가 가리키는 실제 artifact.

문서가 서로 충돌할 때 우선순위는 다음과 같다.

```text
data/reference/source_inventory.json
  -> data/reference/source_access_options.json
  -> docs/source_dossiers/SOURCE_*.md
  -> pipelines/SOURCE_*/README.md
  -> exploratory notes under _archive/
```
