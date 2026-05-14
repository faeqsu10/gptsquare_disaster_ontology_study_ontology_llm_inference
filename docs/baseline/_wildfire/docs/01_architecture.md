# Project Architecture

## 목적

이 프로젝트는 광주·전남 전역에서 산불 위험이 높아질 때 예비주수 대상 구간을 선별하기 위한 Decision Operating Layer를 정의한다. 현재 tree는 source acquisition, mock baseline, runtime overlay, logic definition이 함께 존재하지만, 실제 Feature/Signal 계산 엔진을 완성한 상태는 아니다.

## 판단 흐름

```text
Source
  -> AccessOption
  -> Raw Snapshot / Raw Field
  -> Derived Dataset
  -> Feature
  -> Signal
  -> State
  -> Decision
  -> Action
  -> Feedback
```

핵심 규칙:

- `Source`만 `REAL`, `MOCK`, `EXCLUDE` 판정을 받는다.
- `AccessOption`은 Source를 어떤 endpoint, file, mock generator, manual procedure로 얻는지 나타낸다.
- `Derived Dataset`은 availability status가 아니다. Source 또는 다른 Derived Dataset에서 계산되는 중간 산출물이다.
- `Feature`는 판단에 필요한 정규화 입력이다.
- `Signal`은 Feature 조합이고, `State`는 Signal과 rule의 결과다.
- `Decision`과 `Action`은 구조와 gating만 정의한다. 자동 운영 실행은 아직 하지 않는다.

## 현재 Phase Boundary

| 항목 | 현재 tree에서 완료 | 다음 phase에서 수행 |
|---|---|---|
| Source 판정 | 29개 Source의 `REAL`/`MOCK`/`EXCLUDE` catalog | 신규 source 추가 또는 교체 |
| AccessOption | 48개 option 등록, selected/fallback/rejected 구분 | 실패 option 재검증, endpoint 교체 |
| Raw 보존 | `data/raw/`, `data/mock/`, `data/reference/`에 evidence 보존 | Clean Zone table 생성 |
| Key 검증 | time key, space key, native grain 기록 | CRS 통일, temporal grid 정렬 |
| Logic | Feature/Signal/State/Decision/Action 정의 | 실제 score 계산, calibration |
| Runtime | response 계열 runtime overlay 생성 및 검증 | live Feature bundle 생성 |

Raw phase에서는 다음을 수행하지 않는다.

- 좌표계 통일
- 3시간 grid alignment
- 읍면동 fan-out
- Segment spatial join
- Feature/Signal 계산
- Decision/Action 자동 실행

## 현재 Catalog

| category | count |
|---|---:|
| Source | 29 |
| AccessOption | 48 |
| REAL Source | 18 |
| MOCK Source | 6 |
| EXCLUDE Source | 5 |
| Active Source | 24 |

## 데이터 위계

| 위치 | 의미 |
|---|---|
| `data/raw/<SOURCE_ID>/snapshots/` | 실제 source 원본 또는 수집 snapshot. native field와 native grain 보존 |
| `data/mock/<SOURCE_ID>/scenario_baseline/` | source-level mock baseline |
| `data/mock/<SOURCE_ID>/runs/<run_context_id>/` | 실행 시각 기준 runtime mock overlay |
| `data/reference/` | machine-readable catalog, access option, source dossier, runtime anchor |
| `pipelines/<SOURCE_ID>/` | 수집, manual download, mock generation 재현 절차 |
| `work/runtime_runs/<run_context_id>/` | 특정 실행 1회의 context, manifest, validation evidence |

## 판단 단위

| 단위 | 현재 의미 |
|---|---|
| 프로젝트 지역 | 광주광역시, 전라남도 |
| administrative review unit | 읍면동 |
| action unit | `PreWateringSegment` |
| 현재 source native grain | source별 원본 grain 그대로 보존 |
| regional freeze reference | 광주·전남 전역 coverage 판단 |

readiness 평가는 광주·전남 전역을 실제 수집 또는 mock 보완으로 닫을 수 있는지를 기준으로 한다.

## 현재 결론

- Source layer는 catalog와 evidence 측면에서 닫혀 있다.
- 일부 source는 `PARTIAL_*` 또는 `READY_WITH_GAP` 상태이며, 해당 gap은 logic confidence와 manual review gate로 전파한다.
- Watering actionability와 response resource 계열은 mock dominant이므로 hard gate 자동 실행에 사용하지 않는다.
- 현재 문서의 목표는 실제 운영 truth를 주장하는 것이 아니라, 어떤 입력이 실제이고 어떤 입력이 synthetic인지 분리해 다음 구현 phase의 경계를 명확히 하는 것이다.
