# 재난 온톨로지 스터디 — 온톨로지와 LLM 연동 추론

> 에이전트5기 그룹스터디 **"재난 온톨로지와 예측 모델 결합"** 의 5주차 발표 ③ 공유본.
> 산불(광주·전남) 사례로 **TypeDB 3.x + Gemini 2.5 Flash** 를 결합해 의사결정 시스템을 구성한 학습용 PoC 입니다.

> ⓘ **공유본 관점**: 본 레포의 핵심 발표는 **5주차 발표 ③ "온톨로지와 LLM 연동 추론"** 입니다.
> 다만 LLM 연동(`code/llm/`)을 시연하려면 그 앞 단계(그래프 적재 · 추론 산식 · 파라미터 외부화)가 갖춰져 있어야 하므로,
> 4·5주차 6개 발표 흐름을 한 사람이 전부 학습용으로 구현한 PoC 전체를 함께 공유합니다.
> 4주차 발표 ①~③ 및 5주차 발표 ①·② 코드는 LLM 연동의 *전제 조건* 으로 보시면 됩니다.

---

## 폴더 구조

```
.
├── code/                              # PoC 코드 (TypeDB 스키마 · 추론 · LLM · 시연 · 테스트)
│   └── README.md                      # 코드 상세 안내
├── docs/
│   ├── wildfire-study-reference.html  # 통합 기술 reference (단일 HTML, 사이드바 + 본문)
│   ├── 1_개요.md ... 5_코드_안내.md   # 발표 공유본 5종 (한 장 요약)
│   ├── pdf/                           # 위 5종 + 통합본 PDF
│   └── baseline/_wildfire/            # 3주차 baseline 가상 데이터 + 설계 문서 (215 파일)
├── pyproject.toml                     # uv 호환 의존성 정의
├── .python-version                    # 3.13
├── .env.example                       # GEMINI_API_KEY 입력 템플릿
└── LICENSE                            # MIT
```

## 빠르게 보기

- **단일 HTML 기술 reference**: `docs/wildfire-study-reference.html` — 좌측 사이드바 + 본문 스크롤. 신규 합류자 온보딩용.
- **요약 PDF 5종**: `docs/pdf/1_개요.pdf` ~ `docs/pdf/5_코드_안내.pdf` (+ 통합본 `w05_공유용_통합본.pdf`)
- **코드 직접 실행**: `code/README.md` 참조

## 발표 정보

| 항목 | 내용 |
|---|---|
| 그룹스터디 | 에이전트5기 그룹스터디 "재난 온톨로지와 예측 모델 결합" |
| 세션 | 5주차 발표 ③ — 온톨로지와 LLM 연동 추론 |
| 발표일 | 2026-05-13 |

## 환경 셋업

```bash
# 1) 의존성 (uv 사용)
uv sync

# 2) 환경변수
cp .env.example .env
# .env 안 GEMINI_API_KEY 채우기 (https://aistudio.google.com/app/apikey)

# 3) TypeDB 컨테이너 (3.x)
docker run -d --name typedb -p 1729:1729 typedb/typedb:3.4.0

# 4) baseline 적재 (TypeDB 스키마 + source 29건 + segment 5건 + 파라미터)
./code/run.sh code/db/setup_schema.py
./code/run.sh code/db/load_sources.py
./code/run.sh code/db/apply_schema_v2.py
./code/run.sh code/db/seed_params.py
./code/run.sh code/db/load_segments.py

# 5) 추론 + 그래프 write-back
./code/run.sh code/inference/run_inference_demo.py

# 6) (선택) Gemini 채팅
./code/run.sh code/llm/chat.py

# 7) (선택) demo 웹 UI — http://127.0.0.1:8765
./code/demo/run_demo.sh
```

> `run.sh` 는 TypeDB driver에 필요한 `LD_LIBRARY_PATH` 를 주입한다.
> 다른 Python 환경을 쓴다면 `PYTHON_LIB` 환경변수를 직접 지정하거나 wrapper 없이 실행.

전체 실행 흐름과 옵션은 [code/README.md](code/README.md) 참조.

## 다루는 내용 요약

- TypeDB 3.x 스키마 구성 (source / segment / threshold-set / weight-set)
- 파라미터 외부화 (임계값·가중치를 그래프 노드로 — config-version 관리)
- 그래프 기반 점수 산정 + write-back
- Self-correcting Text-to-TypeQL (Gemini, 재시도 3회 + golden fallback)
- 평가셋 15건 자동 회귀

## Baseline 데이터

- 3주차 발표 baseline 자료는 본 레포 `docs/baseline/_wildfire/` 에 포함되어 있습니다 (가상 데이터, 215 파일).
  - `data/reference/source_inventory.json` — 29건 source 명세
  - `data/reference/source_dossiers/*.json` — source별 상세 dossier
  - `docs/01_architecture.md ~ 08_governance.md` — 설계 문서 8종
  - `schemas/*.json` — JSON Schema 3종
- 코드는 이 경로를 자동 참조하므로 별도 설정 없이 그대로 실행됩니다.

## 라이선스

[MIT](LICENSE)
