# 재난 온톨로지 스터디 — 온톨로지와 LLM 연동 추론

> 에이전트5기 그룹스터디 **"재난 온톨로지와 예측 모델 결합"** 의 5주차 발표 ③ 공유본.
> 산불(광주·전남) 사례로 **TypeDB 3.x + Gemini 2.5 Flash** 를 결합해 의사결정 시스템을 구성한 학습용 PoC 입니다.

---

## 폴더 구조

```
.
├── code/                              # PoC 코드 (TypeDB 스키마 · 추론 · LLM · 시연 · 테스트)
│   └── README.md                      # 코드 상세 안내
├── docs/
│   ├── wildfire-study-reference.html  # 통합 기술 reference (단일 HTML, 사이드바 + 본문)
│   ├── 1_개요.md ... 5_코드_안내.md   # 발표 공유본 5종 (한 장 요약)
│   └── pdf/                           # 위 5종 + 통합본 PDF
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
# 1) 환경변수
cp .env.example .env
# .env 안 GEMINI_API_KEY 채우기

# 2) TypeDB 컨테이너 (3.x)
docker run -d --name typedb -p 1729:1729 typedb/typedb:3.4.0

# 3) Python 의존성 / 실행 흐름
# → code/README.md 참조
```

## 다루는 내용 요약

- TypeDB 3.x 스키마 구성 (source / segment / threshold-set / weight-set)
- 파라미터 외부화 (임계값·가중치를 그래프 노드로 — config-version 관리)
- 그래프 기반 점수 산정 + write-back
- Self-correcting Text-to-TypeQL (Gemini, 재시도 3회 + golden fallback)
- 평가셋 15건 자동 회귀

## Baseline 데이터

- 3주차 발표 baseline 자료(원자료 `source_inventory.json` 등)는 **그룹스터디 내부 공유 자료**로, 본 레포에는 포함되어 있지 않습니다.
- 직접 실행하려면 `code/db/load_sources.py` 안 `INVENTORY` 경로에 자료를 배치하거나 상수를 수정하세요.

## 라이선스

[MIT](LICENSE)
