# Governance

## 역할

이 문서는 문서와 source catalog가 어떤 기준으로 완료되었고, 앞으로 무엇을 바꿀 때 어디를 갱신해야 하는지 정의한다.

## 완료 기준

Source phase 완료 의미:

```text
Source가 REAL / MOCK / EXCLUDE로 모두 판정됨
+ AccessOption이 catalog에 등록됨
+ REAL source는 raw snapshot 또는 acquisition procedure가 있음
+ MOCK source는 generator와 baseline 또는 runtime overlay가 있음
+ EXCLUDE source는 제거 사유와 downstream 영향이 문서화됨
+ selected/fallback option은 time/space key와 evidence가 기록됨
+ Derived/Feature/Signal/State/Decision/Action은 정의만 문서화됨
```

현재 상태:

| 조건 | 상태 |
|---|---|
| Source catalog 29개 | done |
| AccessOption catalog 48개 | done |
| active Source evidence | done |
| EXCLUDE dependency 제거 | done |
| mock propagation rule | done |
| Feature/Signal/State/Decision/Action definition | done |
| 실제 Feature 계산 engine | not started |
| calibration with operational data | not started |

## 현재 Blocker

| blocker | 영향 | 처리 |
|---|---|---|
| KMA short-term forecast recent-only retention | historical PoC 재현 제한 | live/reference run으로만 사용, scenario replay에는 별도 snapshot 필요 |
| Large fire risk forecast time gap | 2026-04-15~2026-04-21 window 부족 | 최신 file 확보 전까지 alert absence 해석 주의 |
| Sun event regional batch 부족 | 전남 시군/좌표별 야간 판단 제한 | batch fetch 추가 필요 |
| 119안전센터 좌표 부재 | DispatchLeadTime geocoding 의존 | geocoding audit 또는 공식 좌표 source 필요 |
| road access/water/resource/equipment mock dominance | hard gate 자동 실행 불가 | `RequestManualReview`/`advisory_only` 유지 |
| DEM, natural water/barrier exclusion | terrain, water, barrier contribution 축소 | unavailable 또는 proxy로 표시 |

## 변경 시 갱신 규칙

| 변경 유형 | 반드시 갱신할 문서 |
|---|---|
| Source 추가/삭제/status 변경 | [02_source-layer.md](02_source-layer.md), `data/reference/source_inventory.json`, [source_dossiers/README.md](source_dossiers/README.md) |
| AccessOption 추가/평가 변경 | `data/reference/source_access_options.json`, 해당 Source Dossier |
| raw snapshot 또는 mock baseline 변경 | 해당 Source Dossier, pipeline README, 필요 시 [02_source-layer.md](02_source-layer.md) |
| Derived Dataset 추가/변경 | [04_data-lineage.md](04_data-lineage.md), [05_feature-contract.md](05_feature-contract.md) |
| Feature input field 변경 | [05_feature-contract.md](05_feature-contract.md), [06_decision-logic.md](06_decision-logic.md) |
| weight/threshold 변경 | [06_decision-logic.md](06_decision-logic.md)와 calibration 근거 |
| runtime overlay 변경 | [07_runtime-operations.md](07_runtime-operations.md), runtime pipeline README |

## 문서 우선순위

문서 간 충돌이 있을 때 우선순위:

```text
machine catalog and schema
  -> active docs under docs/
  -> source dossiers
  -> pipeline README
  -> work/runtime_runs evidence
  -> _archive exploratory notes
```

단, 실제 source field나 row count는 artifact evidence를 우선한다.

## Change Control

- weight와 threshold는 [06_decision-logic.md](06_decision-logic.md)의 git history로 추적한다.
- source availability 변경은 `data/reference/source_inventory.json`과 [02_source-layer.md](02_source-layer.md)를 함께 바꾼다.
- mock source를 REAL source로 교체하면 Feature confidence와 Decision gate를 반드시 재검토한다.
- EXCLUDE source를 재도입하면 [04_data-lineage.md](04_data-lineage.md)의 removed input table을 먼저 수정한다.

## 다음 구현 순서

1. Clean Zone schema 설계: CRS, time grid, admin namespace, segment table.
2. Foundation derived 구현: admin code harmonization, facility geocoding, station geocoding.
3. Segment candidate 생성.
4. 17 Feature 계산 prototype.
5. Signal/State score distribution simulation.
6. Decision gate와 manual review payload 구현.
7. Calibration ledger 작성.
