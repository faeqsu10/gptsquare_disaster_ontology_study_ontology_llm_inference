# 시연 ① PRD 검증 보고서

## 판정: 조건부 합격
PRD 9단계 구조·API 분해·시각화 의도는 발표 시연용으로 적절하지만, **6.4·6.5 예시 숫자가 코드 산식과 불일치**(f_resi/s_exposure/s_priority), **카탈로그 `safety_class` 키와 `load_segments.py`의 `safety` 키 불일치**, **단계 4의 "수치 계산만 따로 함수로 추출" 주장이 현재 코드 상으로는 미실현**의 세 가지 사실관계 오류가 발표 중 발견될 경우 신뢰도가 크게 흔들린다. 발표 전 반드시 수정.

---

## 평가 축별 결과

### 1. 청중 인지 명료성 — ⭕
- 잘 된 점:
  - 1장 "청중이 인지해야 할 핵심 3가지"가 외부화·가중평균·write-back을 정확히 분리해 명시했다. 시연의 본질을 그대로 전달한다.
  - 단계 1·2(가중치/임계값 가져오기)와 단계 7·8(write-back/검증)이 핵심 메시지를 양 끝에 배치해 청중 기억에 남기 좋다.
- 미흡한 점:
  - 단계 3·4(신호 계산 → 합산)에서 "Python은 수치 연산만 담당, 그래프는 파라미터만 제공한다"는 메시지가 캡션 1줄로만 노출된다. 가중치 박스(단계 1)와 합산표(단계 4)를 시각적으로 같은 색 라벨로 연결해야 "그래프에서 온 값이 여기 곱해진다"가 한눈에 보인다.
  - 단계 6(오버라이드)이 매우 중요한 인지 포인트(룰 자체도 그래프에 있다는 메시지가 깔리는 자리)인데 6.7 응답에 룰의 출처가 빠져 있다. "이 룰도 그래프에서 왔어요"를 말하려면 응답에 `source: graph://override-rule[...]` 같은 필드가 있는 편이 좋다(룰 외부화는 아직 이 시연 범위가 아니라면 적어도 "현 단계에서는 코드에 있음, 향후 그래프로 이동 예정" 표시 캡션 필요).
- 개선 지시:
  - 단계 1과 단계 4의 가중치 항목 색을 동일하게 매칭(예: official=주황, exposure=파랑 …)해 "이 색이 거기서 여기로 흘러왔다"를 시각화.
  - 단계 6 캡션에 "현 단계에서는 코드 분기, 차후 그래프 노드화 예정" 한 줄 명시.

### 2. 단계 분해 적정성 — △
- 잘 된 점:
  - 0~9 분해는 발표 흐름과 자연스럽게 일치. 한 단계 = 한 인지 포인트가 잘 지켜졌다.
  - 단계 7과 단계 8을 분리해 "쓰고 → 다시 읽어서 확인"을 보여준 건 write-back 신뢰감 확보에 매우 유용.
- 미흡한 점:
  - 단계 5(`base-state`)와 단계 6(`override`)은 발표 흐름상 한 호흡으로 묶이는 게 자연스럽다. 두 단계 사이에 멘트 갈아타는 시간이 짧아 청중이 "왜 한 번 더 누르지?"라고 느낄 수 있다. 그러나 분리해야 룰 메커니즘이 드러나므로, **API는 분리하되 UI는 같은 카드 안에서 위/아래 두 칸으로 한 클릭에 순차 전환**되도록 권장.
  - 단계 0이 사실상 카탈로그 로드인데 단계 번호를 차지한다. 9단계라는 카운트의 무게에 비해 단계 0은 진행 비드에 비어 있는 ○로 표시되든지, 단계 1을 "동네 선택+카탈로그 로드"로 합치는 게 청중 인지 부담을 줄인다(현 PRD는 비드 9칸 ●─●─●─○─○─○─○─○─○인데 5장 ASCII에는 칸 수가 모호. 9개 비드인지 8개 비드인지 명시 필요).
- 개선 지시:
  - 5장 ASCII에서 진행 비드 칸 수를 정확히 표기(0 포함 9칸인지 1~8 8칸인지). 본문 4장 표와 일치시킬 것.
  - 단계 5·6는 백엔드 API는 그대로 두되 UI에서는 "기본 단계 매핑 → 오버라이드 적용"을 같은 카드 내 2칸으로 묶고 단일 버튼으로 두 API를 순차 호출. PRD 4장에 "Step 5·6는 한 클릭으로 묶음" 한 줄 추가.

### 3. API 일관성 — △
- 잘 된 점:
  - 6.2~6.9가 각자 멱등이고 클라가 상태를 들고 다니는 설계는 라이브 시연에서 어떤 단계든 다시 누를 수 있게 해 안전.
  - 6.4 응답에 `breakdown.formula/inputs`가 있어 화면에 산식 노출 가능 — 청중 교육 의도와 부합.
- 미흡한 점:
  - **6.4·6.5의 숫자 예시가 실제 코드 산식 결과와 다르다**(아래 "코드 검증" 참고). 발표 중 누군가가 "왜 합산 0.5342인데 0.534×0.30 + … 해보니 안 맞아요?"라고 짚으면 곤란하다.
  - 6.4 `breakdown.exposure.inputs.f_resi: 0.108`는 잘못된 값이다. `0.108`은 `0.40*norm(8000/30000) = 0.40*0.2667 = 0.1067` 인데 이는 f_resi 식의 **첫 번째 항만**의 값이지 f_resi 전체가 아니다. f_resi 정의는 `0.40·norm(pop) + 0.25·(1-norm(forest))` 두 항 합 → 실제 0.3442.
  - 6.5 응답이 `weights`·`signals`를 입력으로 받지만 응답에는 `s_priority`만 있고 **클라가 다음 단계로 보낼 thresholds는 6.3에서 따로 들고 있어야 함**이 명시되지 않았다. 단계 6의 입력에 `thresholds`가 있으니 OK이지만 클라 상태 흐름 그림이 본문에 없다 — 6장 머리말에 "클라가 누적 보관할 키 목록"을 한 줄로 명시 권장.
  - 6.8 `write-back`의 바디 `values`에 `f_grade·f_alert·s_priority·base_state·state·reason`만 있다. 그런데 코드 `compute_and_write_back`은 segment에 `risk-grade-score·alert-score`도 INSERT한다. PRD 응답 typeql 예시에는 `risk-grade-score 1.00; alert-score 1.00;`이 들어있어 일관 — 다만 바디 키 이름(`f_grade`)과 attribute 이름(`risk-grade-score`)이 1:1 대응이라는 게 본문에 명시되지 않았다. 매핑 표 한 줄 추가 권장.
- 개선 지시:
  - 6.4·6.5 응답의 모든 숫자를 실제 코드(`graph_inference.py`) 산식 결과로 재계산해 갱신. 권장값: `s_official=0.900, s_exposure=0.318, s_spread=0.500, s_action=0.500, s_time=0.500 → s_priority=0.5744`. base-state 매핑은 동일하게 ReviewPreWatering, 오버라이드 후 PriorityPreWatering. **band 결과는 안 바뀌므로 스토리는 그대로 유지된다.**
  - 6.4 `breakdown.exposure.inputs`에 `f_resi`와 `pop_norm·forest_inv_norm` 모두 명시.
  - 6장 머리말에 "클라가 단계 사이 보관해야 할 상태 키 목록" 표 추가: `weights, thresholds, segment_id, signals, s_priority, base_state, final_state, override_reason`.

### 4. 비범위 타당성 — △
- 잘 된 점:
  - attribute 직접 조정·자동 진행·녹화 재생 제외는 발표 안정성 관점에서 옳다.
  - 모바일/다국어 비범위 합리.
- 미흡한 점:
  - **시연 ②와의 연결고리에 누락된 attribute는 없으나, 시연 ②가 어떤 attribute를 읽어야 하는지가 본 PRD에 적혀 있지 않다.** PRD 9장 수용 기준 3번이 "시연 ②에서 즉시 사용 가능"이라고만 적어 검증 단위가 약하다.
  - 녹화 재생을 비범위로 둔 근거가 "응답이 ms 단위"인데, TypeDB write 트랜잭션은 ms 단위라 보장이 어렵다(commit 지연이 종종 100~500ms). 4m 거리에서 ▼ 마커가 안 움직이는 그 1초가 발표에서 가장 길게 느껴진다. **녹화 재생까지는 아니더라도 마지막 성공한 응답을 메모리에 들고 있다가 동일 segment 재선택 시 즉시 표시하는 캐시**는 비범위에 있어선 안 됨.
- 개선 지시:
  - 9장 수용 기준 3번을 "시연 ② PRD의 'read 대상 attribute 목록'에 명시된 6개(s-priority, base-state, state, state-override-reason, risk-grade-score, alert-score)가 모두 채워져 있을 것"으로 구체화.
  - 8장 비범위에서 "응답 캐시"는 제외하고, 6장 공통 규칙에 "각 단계 응답은 클라 메모리에 캐시. 같은 segment 재선택 시 단계 1~8을 즉시 재렌더링하고 사용자가 다시 누를 때만 API 재호출" 한 줄 추가.

### 5. 발표 리스크 — △
- 잘 된 점:
  - 단계 분리로 한 단계 실패해도 그 자리에서 다시 누르면 됨 → 라이브 안전망 큰 편.
  - 6장 공통 에러 응답에 `hint_for_presenter` 필드가 있어 발표자 대응 동선이 명문화됨.
- 미흡한 점:
  - **TypeDB write 트랜잭션이 실패한 경우 클라이언트 상태가 단계 6까지는 살아 있으나 단계 7만 실패한 상태**가 된다. 단계 8(verify)을 누르면 "방금 저장 안 됐다"는 응답이 와서 발표 흐름이 멈춘다. → 단계 7 실패 시 단계 8 버튼이 자동 비활성화되고, 단계 7만 재시도 가능하다는 흐름이 PRD에 없다.
  - 사용자 클릭 순서 오류(예: 단계 1 누르고 바로 단계 4)는 "이전 step이 끝나야 활성화"로 막혔지만, **새로고침 후 segment 재선택 → 곧장 단계 8 누르기**가 가능하면 이미 write-back된 segment에 대해 verify만 통과해버린다(이전 발표 회차의 결과). 청중에게는 정상으로 보이지만 발표자가 "지금 저장한 게 들어갔다"고 멘트했을 때 거짓말이 된다.
  - 라이브 리허설 시간(9장 체크리스트의 "각 5분 × 5 = 25분")이 25분이라는데, 발표가 13일 한 번이고 segment마다 9단계×∼3초 동작 + 멘트면 segment당 3분 잡아도 15분. 25분이면 청중이 집중을 놓는다. **발표 본방에서는 1~2개 segment만 한다는 사실을 명시**할 필요(여수=경보 격상, 장흥=안전 게이트 두 개로 충분).
- 개선 지시:
  - 6장에 "각 단계의 비활성화 조건"표 추가. 특히 단계 7 실패 시 단계 8 비활성, 단계 7 재시도 버튼 노출.
  - 단계 8 응답에 `committed_at`를 포함시켜, 단계 7의 `committed_at`과 일치하는지 클라가 비교 후 일치 시에만 "방금 저장된 결과입니다" 라벨 표시. 불일치 시 "이전 회차 결과" 라벨로 발표자 보호.
  - 2장 발표 스토리에 "발표 본방에서는 여수+장흥 2건만 시연. 나머지 3개는 질의응답용 백업" 한 줄 추가.
  - 10장 체크리스트에 "발표 직전 5건 모두 1회 write-back 초기화(빈 상태로 되돌리기) 스크립트 실행" 추가. 단계 8이 이전 회차 결과를 보여주는 사고 방지.

### 6. 코드 재사용 가능성 — △
- 잘 된 점:
  - `load_weights`, `load_thresholds`, `s_priority_to_state`, `resolve_state`, `GRADE_SCORE`, `ALERT_SCORE`, `_norm`, `make_driver`는 그대로 import해서 무수정 재사용 가능. PRD 7장의 재사용 주장은 이 부분은 사실.
- 미흡한 점:
  - **단계 4(`compute-signals`) 백엔드 구현 메모가 사실과 다르다.** PRD 7장은 "`graph_inference.compute_and_write_back`의 수치 계산 부분만 따로 함수로 추출"이라고 했지만, 현재 `compute_and_write_back`은 1) load_weights·load_thresholds, 2) 수치 계산, 3) base_state·resolve_state, 4) write 트랜잭션을 한 함수에 묶고 있다. **수치 계산 부분이 별도 함수로 추출되어 있지 않으므로 "무수정 재사용"이 아니라 "리팩토링이 필요한 부분"이다.** PRD가 이걸 7장에서 "재사용"으로 표현한 건 정확하지 않음.
  - 또한 단계 4 API는 `compute_and_write_back` 안의 신호 계산 5줄(s_official, f_resi, s_exposure, s_spread, s_action, s_time)을 분리해야 하는데 이 분리는 가능. write 트랜잭션과 분리하기 어렵지 않다(load + math + write가 명확히 단계적이므로).
  - 카탈로그(6.1)의 입력 키가 `safety_class`인데 `db/load_segments.py`의 SEGMENTS는 `safety`다. 두 파일이 단일 진실 원천이 아니다(7장 마지막 줄 "run_inference_demo.py의 SEGMENTS를 그대로 import"라고 했지만 그 SEGMENTS는 `safety_class`이고 load_segments.py SEGMENTS는 `safety`). 카탈로그가 어디서 오는지에 따라 키 이름이 갈린다.
- 개선 지시:
  - 7장의 표현을 "graph_inference.py에 신호 계산용 순수 함수 `compute_signals(seg_input, weights) -> dict`를 추가(write 트랜잭션과 분리). 기존 `compute_and_write_back`은 새 함수를 호출하도록 리팩토링" 으로 수정. **이건 무수정 재사용이 아니라 단순 리팩토링임을 명시**.
  - `compute_signals(seg_input)` 시그니처에 `weights`를 받지 말고 신호값(가중치 곱하기 전 0~1 정규화 점수)만 반환. 가중치 곱은 별도 함수 `aggregate(signals, weights) -> s_priority`로 둘 것. 그래야 단계 3·4 API가 자연스럽게 분리된다.
  - 7장에 "load_segments.py의 SEGMENTS와 run_inference_demo.py의 SEGMENTS를 단일 모듈 `demo/api/segments_catalog.py`로 통합. 키 이름은 `safety_class`로 통일하고 load_segments.py가 이를 import" 추가. 두 곳에 같은 데이터가 두 가지 키 이름으로 존재하는 현 상태는 "단일 진실 원천"이 아니라 모순.

### 7. 수용 기준 측정 가능성 — △
- 잘 된 점:
  - 1번(5개 segment 9단계 끝까지), 4번(새로고침), 6번(라이브 1회 통과), 7번(에러+힌트)은 명확.
- 미흡한 점:
  - 2번 "백엔드 응답 < 1초"의 측정 도구가 없다. FastAPI 응답 로그를 어떻게 캡처할지(uvicorn 로그? 클라이언트 측정?) 명시 필요.
  - 3번 "그래프에 모든 attribute 저장"의 attribute 개수가 명시되지 않았다. 6개(s-priority/base-state/state/state-override-reason/risk-grade-score/alert-score)인지 명시.
  - **5번 "4m 거리 가독"은 측정 방법이 없다.** 18px/24px라는 폰트 크기는 명시했지만, "4m"의 검증 방법은? 발표 본방 모니터(아마 회의실 65인치 또는 프로젝터)에서 18px가 4m 거리에서 읽히는지 검증되지 않았다.
- 개선 지시:
  - 9장 2번을 "p50 < 500ms, p95 < 1500ms (write-back 제외 < 3000ms). FastAPI 미들웨어로 `X-Process-Time` 헤더 부착, 클라가 콘솔 로그 또는 화면 하단 작은 디버그 라인으로 표시" 로 구체화.
  - 9장 3번을 "그래프에 segment당 6개 attribute(`risk-grade-score`, `alert-score`, `s-priority`, `base-state`, `state`, `state-override-reason`)가 모두 채워져 있을 것. `check.py` 또는 `verify` API의 응답으로 검증" 로 구체화.
  - 9장 5번에 검증 방법 추가: "발표 회의실에서 슬라이드 띄우는 위치까지 거리 측정 후, 실제 본문/숫자 폰트로 5월 12일 오전 리허설 시 발표자(또는 동료 1인)이 발표자 위치에서 읽기 가능한지 확인. 안 되면 22px/28px로 상향".

---

## 코드 검증

### compute_and_write_back 분리 가능성 판단
**가능하다.** `compute_and_write_back`(graph_inference.py:133-193)은 다음 4블록으로 명확히 나뉜다.

1. L142-143: `load_weights`/`load_thresholds` 호출 → 그대로 단계 1·2에서 사용
2. L146-162: 수치 계산(`f_grade, f_alert, s_official, f_resi, s_exposure, s_spread, s_action, s_time, s_priority`) → 순수 함수로 분리 가능
3. L165-168: `s_priority_to_state`·`resolve_state` 호출 → 그대로 단계 5·6에서 사용
4. L171-185: write 트랜잭션 → 단계 7에서만 호출

권장 리팩토링:

```python
# graph_inference.py에 추가
def compute_signals(seg_input: dict) -> dict:
    """가중치 곱 전 5개 신호 점수. write 트랜잭션 없음."""
    f_grade = GRADE_SCORE.get(seg_input["risk_grade"], 0.0)
    f_alert = ALERT_SCORE.get(seg_input["alert_level"], 0.0)
    s_official = 0.40 * f_grade + 0.20 * 0.5 + 0.40 * f_alert
    f_resi = 0.40 * _norm(seg_input["population"], 0, 30000) + 0.25 * (1.0 - _norm(seg_input["forest_dist"], 0, 2000))
    s_exposure = 0.40 * f_resi + 0.35 * 0.3 + 0.25 * 0.3
    s_spread = 0.40 * _norm(seg_input["wind"], 0, 20) + 0.25 * 0.3 + 0.35 * 0.3
    return {
        "official": s_official, "exposure": s_exposure, "spread": s_spread,
        "action": 0.5, "time": 0.5,
        "_factors": {"f_grade": f_grade, "f_alert": f_alert, "f_resi": f_resi},
    }

def aggregate_signals(signals: dict, weights: dict) -> float:
    return sum(weights[k] * signals[k] for k in ("official","exposure","spread","action","time"))

# 기존 compute_and_write_back은 위 두 함수를 호출하도록 변경
```

분리 후 `compute_and_write_back`은 호출만 남아 회귀 위험 낮음.

### 무수정 재사용 시 발견된 이슈

| 항목 | 현 코드 | PRD 주장 | 실태 |
|---|---|---|---|
| `load_weights` | 무수정 가능 | ✅ | 일치 |
| `load_thresholds` | 무수정 가능 | ✅ | 일치 |
| `s_priority_to_state` | 무수정 가능 | ✅ | 일치 |
| `resolve_state` | 무수정 가능 | ✅ | 일치 |
| `GRADE_SCORE`, `ALERT_SCORE`, `_norm`, `make_driver` | 무수정 가능 | ✅ | 일치 |
| **신호 계산 부분 단독 호출** | 함수 미분리 | "추출" | ❌ 리팩토링 필요 |
| **카탈로그 키 `safety_class` vs `safety`** | 두 모듈에서 다름 | "SEGMENTS 그대로 import" | ❌ 통합 필요 |

### PRD 6.4·6.5 숫자 검증 (여수 상암동, alert=경보, grade=매우높음, pop=8000, forest=100m, wind=16)

코드 산식으로 실제 계산하면:
- `f_grade = 1.00, f_alert = 1.00`
- `s_official = 0.40·1.00 + 0.20·0.5 + 0.40·1.00 = 0.900` (PRD 일치)
- `pop_norm = 8000/30000 = 0.2667`
- `forest_inv_norm = 1 - 100/2000 = 0.95`
- `f_resi = 0.40·0.2667 + 0.25·0.95 = 0.1067 + 0.2375 = 0.3442` (**PRD 0.108 오류**)
- `s_exposure = 0.40·0.3442 + 0.35·0.3 + 0.25·0.3 = 0.1377 + 0.105 + 0.075 = 0.3177` (**PRD 0.246 오류**)
- `s_spread = 0.40·norm(16/20) + 0.25·0.3 + 0.35·0.3 = 0.40·0.80 + 0.075 + 0.105 = 0.500` (PRD 일치)
- `s_action = s_time = 0.5` (PRD 일치)
- `S_priority = 0.30·0.900 + 0.25·0.3177 + 0.20·0.500 + 0.15·0.500 + 0.10·0.500`
  `         = 0.270 + 0.07943 + 0.100 + 0.075 + 0.050 = 0.5744` (**PRD 0.5342 오류**)
- band 매핑: 0.5744는 여전히 0.40~0.60 → ReviewPreWatering (PRD 일치, 스토리 안전)
- 오버라이드: 경보 + ReviewPreWatering → PriorityPreWatering (PRD 일치)

→ **발표 스토리(매핑·오버라이드 결과)는 그대로 살지만, PRD의 중간 숫자 3개와 합계가 틀리다.** 화면에 산식과 결과를 함께 보여주는 시연이라 청중이 직접 더해보면 합산이 안 맞는다. 발표 사고로 직결.

---

## 시연 ② 연결고리 점검

### 시연 ①이 write-back하는 attribute 목록 (graph_inference.py L174-183 기준)

| attribute | 타입 | 값 예시 |
|---|---|---|
| `risk-grade-score` | double | 1.00 |
| `alert-score` | double | 1.00 |
| `s-priority` | double | 0.5744 |
| `base-state` | string | "ReviewPreWatering" |
| `state` | string | "PriorityPreWatering" |
| `state-override-reason` | string | "alert_경보_priority_6" |

→ 6개. PRD 6.8 응답 typeql에도 모두 포함됨. ✅

### 시연 ②가 필요한 attribute 목록 (추정)

본 PRD 작성 시점에는 시연 ② PRD가 아직 없으므로 추정:
- 시연 ②가 "임계값을 0.4 → 0.3으로 바꿔 등급이 어떻게 변하는지" 보여주는 시나리오라면 → s-priority, base-state, state 3개 필요
- 시연 ②가 시연 ①에서 만든 결과를 지도/리스트로 시각화하는 시나리오라면 → 6개 모두 필요
- 추가로 segment의 기본 attribute(segment-id, segment-name, admin-region, risk-grade, alert-level, residential-population, forest-distance-m, wind-speed, safety-class)는 시연 ②도 읽어야 함 → load_segments.py가 이미 채워둠

### 누락 발견 여부
**누락 없음, 단 PRD에 시연 ② attribute 목록 명시 책임을 둘 것**. 본 시연 ① PRD가 시연 ② PRD가 나오기 전이라 "시연 ②가 무엇을 요구하는지" 모르는 상태로 작성됐다는 위험이 있다. → 시연 ② PRD 초안이 나오면 본 PRD 9장 수용 기준 3번에 "시연 ②가 요구하는 attribute 목록" 표를 inline 인용.

---

## SFR 인지 전달 점검 (가볍게)

- **파라미터 외부화**: 단계 1·2(가중치/임계값 그래프 로드)와 단계 1·2 캡션 "← graph DB에서"로 전달됨. ⭕
- **그래프 활용**: 단계 7(write-back)과 단계 8(re-read) 분리로 그래프가 단일 진실 저장소임을 시각적으로 전달함. ⭕
- **자가 수정·환각 방지**: 본 시연 ①에서는 비범위 — 시연 ③ 검증 시 점검.

---

## 구체적 수정 지시

### must (발표 사고 방지)
1. **(6.4·6.5)** 응답 예시 숫자를 실제 코드 산식 결과로 교체. `s_exposure: 0.318`, `s_priority: 0.5744`. 6.4의 `breakdown.exposure.inputs`에 `pop_norm: 0.267, forest_inv_norm: 0.950, f_resi: 0.344` 모두 명시. 6.5의 `contributions` 합도 0.5744로 재계산.
2. **(7장)** "compute_and_write_back의 수치 계산 부분만 따로 함수로 추출" 표현을 정확히 수정: "graph_inference.py에 `compute_signals(seg_input)` 및 `aggregate_signals(signals, weights)` 순수 함수를 신규 추가 (write 트랜잭션과 분리). 기존 `compute_and_write_back`은 새 함수를 호출하도록 리팩토링". 이건 리팩토링이지 무수정 재사용이 아님을 명시.
3. **(7장)** `load_segments.py`의 SEGMENTS(`safety` 키)와 `run_inference_demo.py`의 SEGMENTS(`safety_class` 키)가 다르다는 사실을 인지하고, `demo/api/segments_catalog.py`로 단일화. 키 이름을 `safety_class`로 통일하고 `load_segments.py`도 이를 import하게 변경. 변경하지 않으면 카탈로그(6.1)와 입력 정합이 깨짐.
4. **(9장 체크리스트)** "발표 직전 5건 모두 write-back 초기화(빈 상태로 되돌리기) 스크립트 실행" 추가. 단계 8이 이전 회차 결과를 보여주는 사고 방지.
5. **(6장)** 단계 7 실패 시 단계 8 비활성화·단계 7 재시도 노출 흐름 추가. 단계 8 응답에 `committed_at`을 포함시켜 단계 7의 그것과 일치 검증.

### should (발표 품질 보강)
6. **(2장)** "발표 본방에서는 여수+장흥 2건만 시연. 나머지 3개는 질의응답용 백업" 한 줄 명시. 25분 리허설은 본방용 아님을 분리.
7. **(4장)** 단계 5·6를 "UI에서는 한 클릭으로 묶음(API는 분리)" 라고 표기. 발표자가 단계 5→6 사이 멘트 흐름을 끊지 않도록.
8. **(5장)** ASCII 진행 비드의 칸 수를 4장 표(단계 0~8 또는 1~8)와 정확히 일치시킬 것. 9칸인지 8칸인지 모호.
9. **(6장)** 머리말에 "클라가 단계 사이 보관해야 할 상태 키 목록" 표 추가: `weights, thresholds, segment_id, signals, s_priority, base_state, final_state, override_reason, committed_at`.
10. **(9장 2번)** 응답시간 기준을 p50/p95로 구체화 + FastAPI 미들웨어로 `X-Process-Time` 헤더 부착 명시.
11. **(8장 비범위)** "응답 캐시"는 비범위에서 제외하고, 6장에 "같은 segment 재선택 시 단계 1~8을 메모리 캐시에서 즉시 재렌더링" 추가.

### nice (전달력 향상)
12. **(단계 1·4 색 매칭)** 가중치 5개 박스(단계 1)와 합산표(단계 4)의 행 색을 1:1 매칭해 "이 색이 거기서 여기로" 시각화.
13. **(단계 6 캡션)** "오버라이드 룰은 현 단계에서는 코드 분기, 차후 그래프 노드화 예정" 한 줄 명시. 룰 외부화가 다음 단계라는 로드맵 암시.
14. **(9장 5번)** 4m 거리 가독성의 측정 방법 명시: "5월 12일 오전 리허설에서 실제 발표 위치에서 발표자가 본문/숫자 폰트를 읽을 수 있는지 확인. 안 되면 22px/28px로 상향".
15. **(9장 3번)** segment당 attribute 6개 명시: `risk-grade-score, alert-score, s-priority, base-state, state, state-override-reason`.

---

## 다음 PRD 작성 시 참고할 일반 교훈 (시연 ②③④용)

1. **PRD 안의 모든 숫자 예시는 실제 코드로 1회 검증 후 작성한다.** 시연 ①처럼 산식과 결과가 모두 화면에 노출되는 시연에서는 PRD의 숫자가 발표 직전 까지 그대로 화면에 반영되므로, PRD 작성 시점에 한 번이라도 실제 코드로 돌려본 값을 적어야 한다(파이썬 REPL로 30초면 된다).
2. **"무수정 재사용" 주장 전에 함수 시그니처와 트랜잭션 경계를 확인한다.** 한 함수가 "조회 → 계산 → 쓰기"를 모두 하면 그건 단계 분해 시 거의 반드시 리팩토링이 필요하다. PRD에서 "재사용"이라고 단정하면 검증자가 의심한다.
3. **여러 모듈에 같은 데이터가 다른 키 이름으로 존재하는지 확인한다.** 시연 ②③④도 segment·threshold·weight 같은 공통 데이터를 다룬다. 단일 진실 원천(SSoT)이 누구인지 PRD 머리말에 명시하고, 키 네이밍이 어긋난 곳을 통합 대상으로 표기.
4. **실패 시 발표자 동선이 살아남는지 단계별로 점검한다.** 단계 N이 실패했을 때 단계 N+1, N+2가 어떻게 보이는지(잘못된 캐시? 비활성화? 이전 회차 데이터?)를 모든 단계에 대해 한 줄씩 적어둬야 라이브에서 안 죽는다.

---

## 총평

본 PRD는 9단계 분해와 시각화 의도(가중치/임계값 외부화 → 가중평균 → write-back)가 5주차 발표의 핵심 메시지를 정확히 겨냥했다. 발표 스토리(2장)도 자연스럽다. 다만 **6.4·6.5 응답 예시 숫자가 코드 산식과 어긋나는 점**, **카탈로그 키와 load_segments.py 키가 불일치하는 점**, **단계 4 함수 추출이 "무수정 재사용"으로 잘못 표기된 점** 세 가지는 발표 중 청중이 산식과 결과를 직접 더해보면 즉시 발견될 수준의 오류라 반드시 발표 전 수정해야 한다. **band 매핑과 오버라이드 결과는 동일하게 ReviewPreWatering → PriorityPreWatering으로 살아 있으므로 발표 스토리 자체는 안전**하며, 본 보고서 must 1~5번을 반영하면 시연 ①은 발표용으로 충분히 신뢰할 수 있다. 시연 ② PRD가 나오면 본 PRD 9장 수용 기준 3번에 시연 ② 필요 attribute 목록을 inline 인용해 연결고리를 닫을 것.
