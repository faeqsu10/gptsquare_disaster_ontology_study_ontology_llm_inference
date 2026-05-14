# Gwangju-Jeonnam Wildfire Pre-Watering Decision Layer

> **"불이 나면 끈다"가 아니라, "불이 붙을 환경을 미리 없앤다."**
>
> — 지방 소방본부 보도자료 [산불, 타기 전에 적신다… 건조특보 속 '선제 예비주수' 총력 (2026-02-26)](https://www.jnsobang.go.kr/jnsobang/data/data_report/?boardId=bbs_0000000000000019&mode=view&cntId=427)

건조특보가 뜨면 전남 도내 **22개 소방서**가 소방차를 몰고 산림 인접 주택가와 문화재 주변으로 향하는 모습을 떠올려보세요. 불을 끄러 가는 게 아니라, **불이 붙을 자리를 미리 적시러** 가는 겁니다. 가연물 밀집 구간을 천연 방화벽으로 바꾸는 '선제적 예비주수' — 화재 발생 뒤 출동이라는 오랜 공식을 깨는 공세적 예방이죠.

 여기서 중요한 질문은 하나입니다.

> **오늘, 어느 구간에 먼저 뿌릴 것인가?**

이 프로젝트는 그 답을 데이터로 만들기 위함입니다. 광주·전남 전역의 건조도·풍속·산림 경계·문화재 위치·가연물 분포·비상소화장치 좌표를 하나의 `run_context.reference_time` 위에 정렬해, **Source → Derived → Feature → Signal → State → Decision → Action** 흐름으로 그날의 예비주수 후보 구간을 산출하는 판단 레이어입니다.

작성일: 2026-05-01  
프로젝트 지역: **광주광역시, 전라남도**

## 문서 시작점

문서 체계는 [docs/README.md](docs/README.md)에서 시작합니다.

권장 읽기 순서:

1. [Project Architecture](docs/01_architecture.md)
2. [Source Layer](docs/02_source-layer.md)
3. [Source Evidence](docs/03_source-evidence.md)
4. [Data Lineage](docs/04_data-lineage.md) --------------------- 중요!
5. [Feature Contract](docs/05_feature-contract.md) ----------------- 중요!
6. [Decision Logic](docs/06_decision-logic.md) ------------------- 중요!
7. [Runtime Operations](docs/07_runtime-operations.md)
8. [Governance](docs/08_governance.md)

Source별 상세 증거는 [docs/source_dossiers/README.md](docs/source_dossiers/README.md)를 기준으로 봅니다만, 별로 중요하진 않습니다.

## 기계 판독 파일

- [SourceItem JSON Schema](schemas/source_item.schema.json)
- [SourceAccessOption JSON Schema](schemas/source_access_option.schema.json)
- [SourceDossier JSON Schema](schemas/source_dossier.schema.json)
- [Source Inventory JSON](data/reference/source_inventory.json)
- [Source Access Options JSON](data/reference/source_access_options.json)

## 데이터 디렉터리

- `data/raw/`: 외부 원천 데이터 원본 또는 수집 snapshot
- `data/mock/`: mock baseline과 runtime overlay
- `data/processed/`: 다음 phase의 Derived Dataset 또는 정규화 결과
- `data/reference/`: source catalog, access option, dossier, runtime anchor
- `pipelines/`: source별 수집, 수동 다운로드, mock 생성 재현 절차
- `work/runtime_runs/`: 특정 runtime 실행의 context, manifest, validation evidence
