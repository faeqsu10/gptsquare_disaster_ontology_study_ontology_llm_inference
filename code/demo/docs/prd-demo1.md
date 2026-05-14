# 시연 ① PRD — 데이터 → 추론 → write-back

> 5주차 발표(2026-05-13) 시연 4건 중 첫 번째.
> 청중이 "그래프가 코드의 임계값/가중치 자리를 대신한다 + 추론 결과가 다시 그래프로 들어간다"를
> 직접 한 단계씩 클릭하며 체득하게 한다.
>
> **버전**: v2.1 (2026-05-12)
> **변경**:
> - v2 (2026-05-12 오후): reviewer 검토 반영 — 산식 예시 숫자 재계산, 함수 분리 리팩토링 명시, 카탈로그 단일화, 실패 흐름·체크리스트 보강. (보고서: `prd-demo1-review.md`)
> - v2.1 (2026-05-12 저녁): 실측 가중치 반영 — reviewer가 가정한 가중치(0.30/0.25/0.20/0.15/0.10)와 실제 그래프 seed(0.20/0.25/0.20/0.20/0.15)가 달라 `s_priority` 예시값을 0.5744 → 0.5345로 정정. band 매핑(ReviewPreWatering)과 격상 결과(PriorityPreWatering)는 동일하게 보존됨. write-back은 delete-then-insert로 멱등성 확보(TypeDB 3.x card(0..1) 대응).

---

## 1. 목적 (왜 만드는가)

기존 한방 실행 UI는 청중이 "결과만" 본다. 본 시연은 **9단계로 분해**해서 발표자가 한 단계씩
클릭하면, 단계마다 "그래프에서 가져온 값"과 "Python이 계산한 값"이 화면에 노출된다.

청중이 인지해야 할 핵심 3가지:

1. **그래프에서 파라미터를 읽는다** — 가중치 5개와 임계값 4개가 코드 상수가 아닌 `weight-set`·`threshold-set` 노드에서 옴
2. **종합 위험도는 가중평균** — 5개 신호(공식성/노출/확산/대응/시점)에 가중치를 곱해 하나로 합침
3. **결과가 그래프로 돌아간다 (write-back)** — 방금 계산한 `s-priority`, `base-state`, `state`, `state-override-reason`이 INSERT로 들어가서 다음 시연에서 그대로 사용됨

---

## 2. 발표 스토리 (3분 시연 시나리오)

> **본방 시연 대상**: ★ EMD_여수_상암동(경보 격상) + ★ EMD_장흥_유치면(안전 게이트) **2건만**.
> 나머지 3개 동네는 질의응답용 백업으로 준비만 둔다.
>
> 발표자가 "EMD_여수_상암동" 카드를 누르면서 시작.
>
> 1. (입력 카드) "이 동네는 매우높음 등급에 경보가 떠 있고, 인구 8천 명에 숲에서 100m. 풍속 16m/s. 안전은 정상이에요."
> 2. (가중치 가져오기) "가중치를 그래프에서 가져옵니다. 이게 코드가 아니라 DB 노드입니다."
> 3. (임계값 가져오기) "임계값도 마찬가지. 0.20/0.40/0.60/0.80 — DB가 갖고 있어요."
> 4. (신호 계산) "이제 다섯 가지 신호 점수를 계산합니다. 공식성·노출·확산·대응·시점."
> 5. (합산) "각 신호에 가중치를 곱해 더하면 S_priority = **0.5345**."
> 6. (기본 단계 매핑 → 오버라이드) "이 값이 0.40~0.60 구간에 떨어졌으니 ReviewPreWatering. 그런데 경보가 떠 있죠? 격상 규칙에 걸려서 PriorityPreWatering으로 한 단계 올라갑니다." (UI 한 카드에서 위→아래로 한 번 클릭에 순차 전환)
> 7. (write-back) "이 결과를 그래프에 저장합니다. 실제 INSERT 쿼리는 이렇게 나갑니다."
> 8. (검증) "방금 저장한 게 정말 들어갔는지 다시 읽어봅니다. 들어갔네요. 다음 시연(②)은 이 저장된 값을 그대로 씁니다."

---

## 3. 입력 (사용자가 무엇을 조작하는가)

5개 동네 카드 중 **1개 선택** (라디오). 카드에는 6개 attribute가 표시된다.

| 동네 | 등급 | 특보 | 인구 | 숲거리(m) | 풍속(m/s) | 안전 | 시연 가치 |
|---|---|---|---|---|---|---|---|
| EMD_광주_북구_001 | 높음 | 주의보 | 25,000 | 300 | 14.0 | 정상 | 평이한 케이스(백업) |
| ★ EMD_여수_상암동 | 매우높음 | **경보** | 8,000 | 100 | 16.0 | 정상 | **경보 격상** — 본방 시연 1 |
| EMD_나주_봉황면 | 다소높음 | 없음 | 3,000 | 1,500 | 5.0 | 정상 | 일반 관리(백업) |
| ★ EMD_장흥_유치면 | 높음 | 주의보 | 1,200 | 50 | 11.0 | **작업 불가** | **안전 게이트** — 본방 시연 2 |
| EMD_무안_운남면 | 정상 | 없음 | 5,000 | 2,000 | 3.0 | 정상 | 가장 낮은 단계(백업) |

> 본 시연은 attribute 직접 조정을 **비범위**로 둔다. 발표 실수 가능성을 줄이고 5개 시나리오의
> 의도된 인지 포인트(경보 격상, 안전 게이트)를 깔끔하게 보여주기 위함.

---

## 4. 9단계 분해

| Step | 사용자 액션 | 백엔드 호출 | 화면 표시 | 인지 포인트 (캡션) |
|:--:|---|---|---|---|
| 0 | 동네 카드 클릭 | (카탈로그 사전 로드) | 좌측 패널 입력 attribute 6개 카드 | "이 동네 정보입니다" |
| 1 | `그래프에서 가중치 가져오기` | `POST /api/demo1/load-weights` | 5개 가중치 박스 (공식성/노출/확산/대응/시점). **단계 4 합산표와 동일 색**으로 행 매칭 | "가중치는 코드가 아닌 **graph DB**에서" |
| 2 | `그래프에서 임계값 가져오기` | `POST /api/demo1/load-thresholds` | 임계값 4개 + 5단계 매핑 막대(컬러바) | "임계값도 graph DB에서" |
| 3 | `신호 5개 계산` | `POST /api/demo1/compute-signals` | 산식 5줄 + 입력값 대입 결과 | "Python은 수치 연산만" |
| 4 | `S_priority 합산` | `POST /api/demo1/aggregate` | 가중치 × 점수 표(단계 1과 동일 색) + 합계 강조 | "가중평균 = 종합 위험도" |
| 5+6 | `기본 단계 매핑 → 오버라이드` (**UI는 한 카드 1클릭, API는 2회 순차 호출**) | `POST /api/demo1/base-state` → `POST /api/demo1/override` | 위 칸: 컬러바에 마커 + base-state. 아래 칸: 룰 2개 평가 + final state | "어느 구간에 떨어졌나 → 단순 매핑 위에 규칙 한 겹" + "(현 단계에서는 룰이 코드 분기. 차후 그래프 노드화 예정)" |
| 7 | `그래프에 저장 (write-back)` | `POST /api/demo1/write-back` | 실제 발사된 TypeQL INSERT 쿼리 + `committed_at` 타임스탬프 | "**추론 결과가 다시 데이터**" |
| 8 | `다시 읽어와서 검증` | `POST /api/demo1/verify` | 그래프 재조회 결과 6개 attribute + `committed_at` 비교 라벨 | "영속됐습니다. 다음 시연에서 그대로 씁니다" |

**비활성화 규칙**:
- 각 step 버튼은 이전 step이 끝나야 활성화 (순차 진행 강제)
- **Step 7 실패 시 Step 8 비활성화**, Step 7 "재시도" 버튼 노출
- Step 8 응답의 `committed_at`이 Step 7의 그것과 일치하면 "방금 저장된 결과" 라벨, 불일치 시 "이전 회차 결과" 경고 라벨로 발표자 보호

이전 단계 결과는 화면 우측에 카드로 쌓이고, 새 단계는 강조 색으로 등장한다.

---

## 5. 와이어프레임 (ASCII)

진행 비드는 **9칸** (Step 0 ~ Step 8, Step 5+6은 UI 한 카드지만 비드는 2칸 유지).

```
┌─ 시연 ① 데이터 → 추론 → write-back ────────────────────────────────────[홈]┐
│                                                                            │
│ ┌─ 1) 동네 선택 (현재: EMD_여수_상암동) ────────────────────────────────┐  │
│ │  [북구]  [★상암동]  [봉황면]  [★유치면]  [운남면]                   │  │
│ │                                                                       │  │
│ │  등급: 매우높음 │ 특보: 경보 │ 인구: 8,000 │ 숲: 100m │ 풍속: 16    │  │
│ │  안전상태: 정상                                                       │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│ ┌─ 진행 (9칸: Step 0─1─2─3─4─5─6─7─8) ────────────────────────────────────┐│
│ │ ●─●─●─●─○─○─○─○─○   (Step 3 완료, 현재 Step 4 대기)                  ││
│ │                                                                         ││
│ │ ┌─[Step 1] 가중치 ───────┐  ┌─[Step 2] 임계값 ───────────────────┐   ││
│ │ │ 🟠 공식성  0.30        │  │ low      0.20                       │   ││
│ │ │ 🔵 노출    0.25        │  │ mid-low  0.40                       │   ││
│ │ │ 🟢 확산    0.20        │  │ mid-high 0.60                       │   ││
│ │ │ 🟡 대응    0.15        │  │ high     0.80                       │   ││
│ │ │ 🟣 시점    0.10        │  │  [───── 컬러바 5단계 ─────]         │   ││
│ │ │  ← graph DB에서        │  │  일반│감시│검토│우선│즉시           │   ││
│ │ └────────────────────────┘  └─────────────────────────────────────┘   ││
│ │                                                                         ││
│ │ ┌─[Step 3] 신호 5개 계산 (지금 진행) ─────────────────────────────┐   ││
│ │ │ 🟠 s_official  = 0.40×1.00 + 0.20×0.5 + 0.40×1.00 = 0.900        │   ││
│ │ │ 🔵 s_exposure  = 0.40×0.344 + 0.35×0.3 + 0.25×0.3 = 0.318        │   ││
│ │ │ 🟢 s_spread    = 0.40×0.80 + 0.25×0.3 + 0.35×0.3 = 0.500         │   ││
│ │ │ 🟡 s_action    = 0.500  🟣 s_time = 0.500                        │   ││
│ │ └─────────────────────────────────────────────────────────────────┘   ││
│ │                                                                         ││
│ │  [다음 단계 → 4. S_priority 합산]                                       ││
│ └─────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────┘
```

핵심 시각 요소:

- **진행 비드** 9칸. 진행 중 단계는 펄스 애니메이션.
- **컬러바 5단계**: GeneralManagement(연한 그린) → EnhancedMonitoring(노랑) → ReviewPreWatering(주황) → PriorityPreWatering(빨강) → ImmediatePreWatering(진한 빨강). NotActionable은 회색 별도 표시.
- **S_priority 마커**: Step 5에서 컬러바 위에 ▼ 마커가 슬라이드 애니메이션으로 자기 자리를 찾는다.
- **신호↔가중치 색 매칭**: 🟠 official / 🔵 exposure / 🟢 spread / 🟡 action / 🟣 time — Step 1·3·4 모두 동일 색으로 "이 색이 거기서 여기로 흘러왔다"가 즉시 보이게.
- **오버라이드 시각화**: Step 6에서 safety/alert 체크박스 형태. 발화된 룰만 강조 색.
- **TypeQL 쿼리 박스**: Step 7에서 실제 INSERT 쿼리를 코드 블록으로 노출.

---

## 6. API 명세

모든 엔드포인트는 멱등(같은 입력 → 같은 출력)이며, **각 단계가 독립**이다.
상태(이전 단계 결과)는 **클라이언트가 관리**한다. 새로고침해도 처음부터 다시 가능.

**클라가 단계 사이 보관할 상태 키** (순차 누적):

| 키 | 출처 step | 다음에 사용 step |
|---|---|---|
| `segment_id` | 0 | 3·6·7·8 |
| `weights` | 1 | 4 |
| `thresholds` | 2 | 5 |
| `signals`, `factors` | 3 | 4 |
| `s_priority` | 4 | 5 |
| `base_state`, `band_index` | 5 | 6 |
| `final_state`, `override_reason` | 6 | 7 |
| `committed_at` | 7 | 8 (일치 검증) |

**응답 캐시 규칙**: 같은 segment 재선택 시 단계 1~8 응답을 메모리 캐시에서 즉시 재렌더링. 사용자가 명시적으로 "다시 호출" 버튼을 누를 때만 API 재호출.

**숫자 예시는 EMD_여수_상암동 기준이며 모두 `graph_inference.py` 실제 코드 산식으로 재계산된 값.**

### 6.1 GET `/api/demo1/segments`
5개 동네 카탈로그. **단일 진실 원천은 `demo/api/segments_catalog.py`** (7장 참조).

```json
{
  "segments": [
    {
      "id": "EMD_여수_상암동",
      "label": "여수 상암동",
      "highlight": "경보 격상 사례",
      "input": {
        "risk_grade": "매우높음",
        "alert_level": "경보",
        "population": 8000,
        "forest_dist": 100,
        "wind": 16.0,
        "safety_class": "정상"
      }
    }
  ]
}
```

### 6.2 POST `/api/demo1/load-weights`
바디 없음. `weight-set` 노드 조회.

```json
{
  "version": "v1",
  "formula": "S_priority",
  "weights": {
    "official": 0.20, "exposure": 0.25, "spread": 0.20, "action": 0.20, "time": 0.15
  },
  "source": "graph://weight-set[config-version=v1, formula-id=S_priority]"
}
```

### 6.3 POST `/api/demo1/load-thresholds`
바디 없음. `threshold-set` 노드 조회.

```json
{
  "version": "v1",
  "metric": "S_priority_to_state",
  "thresholds": { "low": 0.20, "mid_low": 0.40, "mid_high": 0.60, "high": 0.80 },
  "state_labels": [
    {"key": "GeneralManagement",     "label": "일반 관리",  "color": "#86C99A"},
    {"key": "EnhancedMonitoring",    "label": "감시 강화",  "color": "#F4C84A"},
    {"key": "ReviewPreWatering",     "label": "검토 예비",  "color": "#F08C3A"},
    {"key": "PriorityPreWatering",   "label": "우선 예비",  "color": "#D9442C"},
    {"key": "ImmediatePreWatering",  "label": "즉시 예비",  "color": "#8B1E1A"}
  ]
}
```

### 6.4 POST `/api/demo1/compute-signals`
바디 `{ "segment_id": "EMD_여수_상암동" }`

```json
{
  "signals": {
    "official": 0.900, "exposure": 0.318, "spread": 0.500,
    "action": 0.500, "time": 0.500
  },
  "factors": {
    "f_grade": 1.00, "f_alert": 1.00,
    "pop_norm": 0.267, "forest_inv_norm": 0.950, "f_resi": 0.344,
    "wind_norm": 0.800
  },
  "breakdown": {
    "official": { "formula": "0.40·f_grade + 0.20·0.5 + 0.40·f_alert",
                  "inputs": { "f_grade": 1.00, "f_alert": 1.00 } },
    "exposure": { "formula": "0.40·f_resi + 0.35·0.3 + 0.25·0.3",
                  "inputs": { "pop_norm": 0.267, "forest_inv_norm": 0.950, "f_resi": 0.344 } },
    "spread":   { "formula": "0.40·norm(wind,0,20) + 0.25·0.3 + 0.35·0.3",
                  "inputs": { "wind": 16.0, "wind_norm": 0.800 } },
    "action":   { "formula": "고정 0.5 (현 단계)", "inputs": {} },
    "time":     { "formula": "고정 0.5 (현 단계)", "inputs": {} }
  }
}
```

### 6.5 POST `/api/demo1/aggregate`
바디 `{ "weights": {...}, "signals": {...} }` (클라가 1·3 단계 결과 전달)

```json
{
  "s_priority": 0.5345,
  "contributions": [
    { "name": "official", "weight": 0.20, "score": 0.900, "product": 0.1800 },
    { "name": "exposure", "weight": 0.25, "score": 0.318, "product": 0.0795 },
    { "name": "spread",   "weight": 0.20, "score": 0.500, "product": 0.1000 },
    { "name": "action",   "weight": 0.20, "score": 0.500, "product": 0.1000 },
    { "name": "time",     "weight": 0.15, "score": 0.500, "product": 0.0750 }
  ]
}
```

### 6.6 POST `/api/demo1/base-state`
바디 `{ "s_priority": 0.5345, "thresholds": {...} }`

```json
{
  "base_state": "ReviewPreWatering",
  "band_index": 2,
  "position_in_band": 0.672,
  "explain": "S_priority 0.5345가 0.40~0.60 구간에 떨어졌으므로 ReviewPreWatering"
}
```

### 6.7 POST `/api/demo1/override`
바디 `{ "segment_id": "...", "base_state": "..." }`

```json
{
  "final_state": "PriorityPreWatering",
  "reason": "alert_경보_priority_6",
  "rule_source": "code (현 시점). 향후 graph://override-rule[...] 노드화 예정.",
  "rules_evaluated": [
    { "rule": "hazard_gate_priority_1",
      "condition": "safety_class == '작업 불가'",
      "matched": false,
      "effect": null },
    { "rule": "alert_경보_priority_6",
      "condition": "alert_level == '경보' AND base_state in {일반·감시·검토}",
      "matched": true,
      "effect": "→ PriorityPreWatering" }
  ]
}
```

### 6.8 POST `/api/demo1/write-back`
바디 `{ "segment_id": "...", "values": { "f_grade": ..., "f_alert": ..., "s_priority": ..., "base_state": ..., "state": ..., "reason": ... } }`

**바디 키 ↔ TypeDB attribute 매핑**:

| 바디 키 | TypeDB attribute |
|---|---|
| `f_grade` | `risk-grade-score` |
| `f_alert` | `alert-score` |
| `s_priority` | `s-priority` |
| `base_state` | `base-state` |
| `state` | `state` |
| `reason` | `state-override-reason` |

```json
{
  "ok": true,
  "typeql": "match $s isa segment, has segment-id \"EMD_여수_상암동\";\ninsert\n  $s has risk-grade-score 1.0;\n  $s has alert-score 1.0;\n  $s has s-priority 0.534500;\n  $s has base-state \"ReviewPreWatering\";\n  $s has state \"PriorityPreWatering\";\n  $s has state-override-reason \"alert_경보_priority_6\";",
  "committed_at": "2026-05-13T10:32:14"
}
```

### 6.9 POST `/api/demo1/verify`
바디 `{ "segment_id": "...", "expected_committed_at": "..." }`. 그래프에서 다시 select.

```json
{
  "segment_id": "EMD_여수_상암동",
  "stored": {
    "risk-grade-score": 1.0,
    "alert-score": 1.0,
    "s-priority": 0.5345,
    "base-state": "ReviewPreWatering",
    "state": "PriorityPreWatering",
    "state-override-reason": "alert_경보_priority_6"
  },
  "committed_at": "2026-05-13T10:32:14",
  "freshness": "current"
}
```

`freshness`: `expected_committed_at`과 그래프의 마지막 commit 시각이 일치하면 `current`, 아니면 `stale` — 클라가 "방금 저장된 결과" vs "이전 회차 결과" 라벨 선택에 사용.

### 공통 에러 응답
모든 엔드포인트는 실패 시 다음 포맷.

```json
{ "ok": false, "error_code": "TYPEDB_UNAVAILABLE",
  "message": "TypeDB 연결 실패. 'docker ps | grep typedb'로 컨테이너 상태 확인.",
  "hint_for_presenter": "단계 카드의 '재시도' 버튼을 누르거나, 다른 segment로 전환해주세요." }
```

### 응답시간 측정
FastAPI 미들웨어로 모든 응답에 `X-Process-Time` 헤더 부착. 클라는 화면 하단 작은 디버그 라인에 직전 호출의 측정값을 표시(발표 본방에서는 끔, 리허설에서만 켬).

---

## 7. 백엔드 구현 메모

### 7.1 함수 분리 리팩토링 (graph_inference.py)

**현 상태**: `compute_and_write_back(driver, seg_input)`이 load + math + write를 한 함수에서 처리.

**리팩토링 (이건 무수정 재사용이 아니라 신규 함수 분리)**:

```python
# graph_inference.py에 추가
def compute_signals(seg_input: dict) -> dict:
    """가중치 곱 전 5개 신호 점수 + 중간 factor. write 트랜잭션 없음."""
    f_grade = GRADE_SCORE.get(seg_input["risk_grade"], 0.0)
    f_alert = ALERT_SCORE.get(seg_input["alert_level"], 0.0)
    s_official = 0.40 * f_grade + 0.20 * 0.5 + 0.40 * f_alert
    pop_norm = _norm(seg_input["population"], 0, 30000)
    forest_inv_norm = 1.0 - _norm(seg_input["forest_dist"], 0, 2000)
    f_resi = 0.40 * pop_norm + 0.25 * forest_inv_norm
    s_exposure = 0.40 * f_resi + 0.35 * 0.3 + 0.25 * 0.3
    wind_norm = _norm(seg_input["wind"], 0, 20)
    s_spread = 0.40 * wind_norm + 0.25 * 0.3 + 0.35 * 0.3
    return {
        "signals": {
            "official": s_official, "exposure": s_exposure, "spread": s_spread,
            "action": 0.5, "time": 0.5,
        },
        "factors": {
            "f_grade": f_grade, "f_alert": f_alert,
            "pop_norm": pop_norm, "forest_inv_norm": forest_inv_norm, "f_resi": f_resi,
            "wind_norm": wind_norm,
        },
    }

def aggregate_signals(signals: dict, weights: dict) -> float:
    return sum(weights[k] * signals[k] for k in ("official", "exposure", "spread", "action", "time"))
```

기존 `compute_and_write_back`은 위 두 함수를 호출하도록 수정 — 골든 회귀 테스트가 보장.

### 7.2 무수정 재사용 함수

다음은 그대로 import:
- `load_weights`, `load_thresholds` (단계 1·2)
- `s_priority_to_state` (단계 5)
- `resolve_state` (단계 6)
- `GRADE_SCORE`, `ALERT_SCORE`, `_norm`, `make_driver`

### 7.3 segments 카탈로그 단일화

**문제**: `db/load_segments.py`는 `safety` 키, `inference/run_inference_demo.py`는 `safety_class` 키 — 두 곳에 같은 5건이 다른 키 이름으로.

**해결**: `demo/api/segments_catalog.py` 신설하여 단일 진실 원천화. 키 이름은 **`safety_class`로 통일**.

```python
# demo/api/segments_catalog.py
SEGMENTS = [
    { "id": "EMD_광주_북구_001", "risk_grade": "높음", "alert_level": "주의보",
      "population": 25000, "forest_dist": 300, "wind": 14.0, "safety_class": "정상" },
    { "id": "EMD_여수_상암동",   "risk_grade": "매우높음", "alert_level": "경보",
      "population": 8000, "forest_dist": 100, "wind": 16.0, "safety_class": "정상" },
    # ... 3건 더
]
```

- `run_inference_demo.py`는 import 경로 변경 (코드 무수정 가능 — SEGMENTS 변수만 같으면 됨)
- `db/load_segments.py`는 `safety` → `safety_class` 키 변경 + import 경로 통일
- TypeQL insert문(`has safety-class "{seg["safety_class"]}"`)도 동시 수정

### 7.4 라우터

새 라우터: `code/demo/api/demo1.py` (FastAPI APIRouter).
`server.py`에 `app.include_router(demo1.router, prefix="/api/demo1")` 추가.

---

## 8. 비범위 (이번 PRD에서 안 함)

- 시연 ②③④와의 연동 (각각 별도 PRD)
- segment attribute 직접 슬라이더 조정
- 모바일 반응형
- 사용자 인증
- 다국어
- 녹화 재생 모드 (단, **응답 캐시는 비범위 아님** — 6장 응답 캐시 규칙 참조)
- 9단계 자동 진행 모드 (수동 클릭만)

---

## 9. 수용 기준 (Done의 정의)

1. **본방 2건(여수, 장흥) + 백업 3건** 모두 9단계 끝까지 진행 가능
2. 각 단계 백엔드 응답 **p50 < 500ms, p95 < 1500ms** (write-back 제외 < 3000ms). FastAPI `X-Process-Time` 헤더로 측정
3. 시연 ①을 끝낸 segment는 그래프에 **6개 attribute** (`risk-grade-score`, `alert-score`, `s-priority`, `base-state`, `state`, `state-override-reason`)가 모두 채워져 있을 것. `verify` API 응답으로 검증
4. 새로고침해도 처음 단계부터 정상 진행 (서버 측 세션 없음). 응답 캐시는 메모리 only
5. **가독성**: 본문 18px / 결과 숫자 24px 이상. 5월 12일 오전 리허설에서 발표 위치(회의실 발표대)에서 발표자(또는 동료 1인)가 본문/숫자를 읽을 수 있는지 실측. 안 되면 22px/28px로 상향
6. 책임님 라이브 시연 1회 통과
7. **실패 케이스**: TypeDB down 시 사용자에게 명확한 에러 + `hint_for_presenter` 표시. Step 7 실패 시 Step 8 자동 비활성화. `committed_at` 불일치 시 "이전 회차 결과" 경고

---

## 10. 발표 직전 체크리스트

- [ ] TypeDB 컨테이너 running
- [ ] `seed_params.py`로 weight-set v1, threshold-set v1 적재 완료
- [ ] `load_segments.py`로 5개 segment 적재 완료 (단, 추론 attribute 6종은 시연 중 덮어쓰기됨)
- [ ] **`scripts/reset_demo1_writeback.py` 실행** — 5개 segment의 추론 attribute 6종을 빈 상태로 초기화. 단계 8이 이전 회차 결과를 보여주는 사고 방지
- [ ] 본방 segment 2건(여수, 장흥) 발표 직전 1회 리허설 + 백업 3건 각 1회 확인 (총 ~15분)
- [ ] 브라우저 zoom 110%, 모니터 출력 OK
- [ ] X-Process-Time 디버그 라인 OFF로 설정

---

## 부록 — 다음 PRD에 반영할 일반 교훈 (reviewer 검토에서 도출)

1. **PRD 안의 모든 숫자 예시는 실제 코드로 1회 검증 후 작성** (Python REPL 30초)
2. **"무수정 재사용" 주장 전에 함수 시그니처와 트랜잭션 경계 확인** — 한 함수가 조회·계산·쓰기를 다 하면 거의 항상 리팩토링 필요
3. **여러 모듈에 같은 데이터가 다른 키 이름으로 존재하는지 확인** — 단일 진실 원천(SSoT) 명시
4. **단계 N 실패 시 N+1 이후가 어떻게 보이는지 한 줄씩 적기** — 잘못된 캐시? 비활성화? 이전 회차 데이터?
