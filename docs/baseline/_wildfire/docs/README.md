# Wildfire Pre-Watering Docs

이 문서 체계는 광주·전남 산불 선제 예비주수 프로젝트를 다음 인지 흐름으로 설명한다.

```text
문제와 경계
  -> Source 확보 상태
  -> Source evidence
  -> Derived/Feature 의존성
  -> Logic 계산식
  -> Runtime 실행 방식
  -> 남은 gap과 변경 규칙
```

## 읽는 순서

| 순서 | 문서 | 읽는 이유 |
|---|---|---|
| 1 | [01_architecture.md](01_architecture.md) | 프로젝트가 무엇을 판단하고, 이번 tree가 어느 phase까지 닫혔는지 파악한다. |
| 2 | [02_source-layer.md](02_source-layer.md) | 29개 Source의 `REAL`/`MOCK`/`EXCLUDE` 판정, 수집 방식, 남은 gap을 본다. |
| 3 | [03_source-evidence.md](03_source-evidence.md) | Source Dossier가 어떤 증거 단위인지, 어디까지 믿을 수 있는지 확인한다. |
| 4 | [04_data-lineage.md](04_data-lineage.md) | Source가 Derived Dataset과 Feature로 어떻게 흐르는지 본다. |
| 5 | [05_feature-contract.md](05_feature-contract.md) | 17개 Feature의 입력 field, mock/exclude 영향, confidence를 확인한다. |
| 6 | [06_decision-logic.md](06_decision-logic.md) | Feature, Signal, State, Decision, Action 계산 규칙을 확인한다. |
| 7 | [07_runtime-operations.md](07_runtime-operations.md) | live source와 runtime mock overlay가 같은 시간축에서 실행되는 방식을 본다. |
| 8 | [08_governance.md](08_governance.md) | 완료 기준, 현재 blocker, 문서 변경 규칙을 확인한다. |

## 기준 파일

사람이 읽는 기준 문서는 이 `docs/` 하위의 markdown이다. 기계 판독 기준은 아래 파일이다.

| 파일 | 역할 |
|---|---|
| `data/reference/source_inventory.json` | 29개 Source의 canonical catalog |
| `data/reference/source_access_options.json` | 48개 AccessOption의 endpoint, grain, 평가 상태 |
| `data/reference/source_dossiers/*.json` | Source별 time/space key와 evidence record |
| `schemas/source_item.schema.json` | Source catalog schema |
| `schemas/source_access_option.schema.json` | AccessOption schema |
| `schemas/source_dossier.schema.json` | Source dossier schema |

## Evidence Appendix

Source별 상세 증거는 [source_dossiers/README.md](source_dossiers/README.md)에서 시작한다.

- `docs/source_dossiers/SOURCE_*.md`: 사람이 읽는 Source별 evidence.
- `data/reference/source_dossiers/SOURCE_*.json`: 같은 내용을 기계 검증에 쓰는 reference record.
- `pipelines/SOURCE_*/README.md`: 실제 수집, 수동 다운로드, mock 생성 절차.

## 현재 상태 요약

| 항목 | 값 |
|---|---|
| 프로젝트 지역 | 광주광역시, 전라남도 |
| Source count | 29 |
| AccessOption count | 48 |
| Active Source | 24 (`REAL` 18 + `MOCK` 6) |
| Excluded Source | 5 |
| Source phase guardrail | raw native time/space 보존, CRS 통일/3시간 grid alignment/spatial join 미수행 |
| Runtime 기준 | 모든 실행은 하나의 `run_context.reference_time`을 가진다 |

## 문서 경계

- Source 가용성, 수집 위치, mock/exclude 판정은 [02_source-layer.md](02_source-layer.md)에만 둔다.
- Source별 샘플, raw field, key 검증은 [source_dossiers/](source_dossiers/)에만 둔다.
- Derived lineage와 Feature 의존성은 [04_data-lineage.md](04_data-lineage.md)에 둔다.
- Feature input field와 confidence는 [05_feature-contract.md](05_feature-contract.md)에 둔다.
- 계산식, weight, threshold는 [06_decision-logic.md](06_decision-logic.md)에 둔다.
- live run과 overlay 생성 규칙은 [07_runtime-operations.md](07_runtime-operations.md)에 둔다.
