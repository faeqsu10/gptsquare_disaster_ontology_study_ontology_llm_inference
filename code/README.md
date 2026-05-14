# 산불 예비주수 PoC (4·5주차 스터디)

> 3주차 baseline 자료(별도 비공개 — 그룹스터디 멤버 참조)를 기반으로,
> **TypeDB 3.x + Gemini 2.5 Flash**로 의사결정 시스템을 구현한 학습용 PoC.

발표일: 2026-05-13 (5주차 발표 3)

---

## 폴더 구조

```
code/
├── db/                  # TypeDB 스키마 + 적재 스크립트
│   ├── schema.tql       # 4주차: source/access-option/feature
│   ├── schema_v2.tql    # 5주차: segment/run-context/threshold-set/weight-set
│   ├── rules.tql        # baseline 산식 rule 표현 (참고용 — 3.x에선 Python으로 처리)
│   ├── setup_schema.py  # DB 생성 + schema 적용
│   ├── apply_schema_v2.py
│   ├── load_sources.py  # 원자료 29개 source 적재
│   ├── load_segments.py # 5건 segment + RunContext 적재
│   ├── seed_params.py   # threshold-set v1 + weight-set v1
│   └── check.py         # 검증 쿼리
├── inference/           # 점수 계산 + ML
│   ├── formulas.py      # 4주차: Python 산식
│   ├── formulas_v2.py   # 4주차: ML 결합 9:1
│   ├── ml_model.py      # 4주차: LightGBM 학습
│   ├── graph_inference.py    # 5주차: 그래프 기반 추론 엔진
│   └── run_inference_demo.py
├── llm/                 # 5주차: Gemini 연동
│   ├── text_to_typeql.py    # Self-correcting Text-to-TypeQL
│   ├── chat.py              # 자연어 채팅
│   └── eval/
│       ├── golden_qna.json  # 평가셋 14건
│       └── run_eval.py      # 자동 평가
├── tests/               # 회귀 테스트
│   ├── test_golden_graph.py
│   └── test_param_externalization.py
└── run.sh               # LD_LIBRARY_PATH 자동 주입 wrapper
```

## 사전 요구사항

1. **TypeDB 3.x 컨테이너**:
   ```bash
   docker run -d --name typedb -p 1729:1729 typedb/typedb:3.4.0
   ```
2. **Python 의존성**:
   - `typedb-driver`, `google-genai`, `python-dotenv`, `lightgbm`, `scikit-learn`, `numpy`
3. **`.env`** (레포 루트, `.env.example` 참조):
   ```
   GEMINI_API_KEY=<your_key>
   ```
4. **baseline 데이터** (`code/db/load_sources.py`가 참조):
   - 원자료 `source_inventory.json` 은 그룹스터디 내부 공유 자료. 본 레포에는 미포함.
   - 동일 위치(`docs/study/w03/_wildfire_full/_wildfire/data/reference/source_inventory.json`)에 두거나 `load_sources.py` 안 `INVENTORY` 상수를 수정해 사용.

## 실행 흐름 (처음부터)

```bash
# 4주차 발표 1: TypeDB 환경 + 원자료 source 적재
./code/run.sh code/db/setup_schema.py
./code/run.sh code/db/load_sources.py
./code/run.sh code/db/check.py

# 4주차 발표 2: Python 산식 시나리오 검증
./code/run.sh code/inference/test_scenarios.py

# 4주차 발표 3: ML 학습 + 9:1 결합
./code/run.sh code/inference/ml_model.py
./code/run.sh code/inference/formulas_v2.py

# 5주차 발표 1: 스키마 확장 + 파라미터 노드 + segment 적재
./code/run.sh code/db/apply_schema_v2.py
./code/run.sh code/db/seed_params.py
./code/run.sh code/db/load_segments.py
./code/run.sh code/inference/run_inference_demo.py

# 5주차 발표 2: 골든 회귀 + 파라미터 외부화 시연
./code/run.sh code/tests/test_golden_graph.py
./code/run.sh code/tests/test_param_externalization.py

# 5주차 발표 3: Gemini 채팅 + 평가셋
./code/run.sh code/llm/chat.py
./code/run.sh code/llm/eval/run_eval.py
```

## 주요 설계 결정

| 항목 | 결정 |
|---|---|
| 데이터 저장소 | **TypeDB 단독** (SQLite·PostgreSQL 안 씀) |
| 임계값/가중치 | **`threshold-set`, `weight-set` 노드로 외부화** (config-version 관리) |
| 등급→점수 lookup | Python `GRADE_SCORE` dict (TypeDB 3.x rule 부재로 대체) |
| 산식 가중평균 | Python에서 계산 → 그래프에 attribute write-back |
| State Override | Python 분기 (1순위 hazard / 6순위 alert) |
| LLM 연동 | **Self-correcting Text-to-TypeQL** (재시도 3회 + golden fallback) |

## TypeDB 3.x 호환 메모

참조한 구현 가이드 문서는 TypeDB 2.x rule 문법을 가정합니다.
실제 TypeDB 3.4에서 발견된 차이:

- **`SessionType` 폐기** — `driver.transaction(db, TransactionType.SCHEMA)` 직접 호출
- **`tx.query.define/insert/get` 통합** — `tx.query(...).resolve()` 단일 진입
- **`get` → `select`** — match-select 절로 변경
- **rule 시스템 부재** — 2.x의 `rule X: when {} then {};` 미지원
  → Python이 그래프 파라미터 노드를 읽어 분기 + write-back으로 대체
- **`try_get_long` → `try_get_integer`** — Value 메서드 명 변경
- **datetime 리터럴** — `+00:00` 미허용 (timezone 제거 후 사용)

## 평가셋 결과 (2026-05-04 기준)

```
Gemini 1회 성공:     9건  (단순 3, 중간 4, 복잡 2)
Gemini 재시도 성공:  2건  (중간 1, 복잡 1)
Fallback 사용:       0건
완전 실패:           3건  (그 중 2건은 0건 정답 — 환각 방지 성공 사례)

난이도별 직접 성공률:
  단순: 3/3 (100%)  /  중간: 5/6 (83%)  /  복잡: 3/5 (60%)
```

## 참조

- 통합 기술 reference: `docs/wildfire-study-reference.html` (레포 루트 기준)
- 발표 공유본 5종(개요/데이터·엔티티/추론·LLM/시연/코드 안내): `docs/*.md` + `docs/pdf/*.pdf`
- 3주차 baseline 자료(원자료 데이터 포함)는 그룹스터디 내부 공유 — 본 레포 비포함
