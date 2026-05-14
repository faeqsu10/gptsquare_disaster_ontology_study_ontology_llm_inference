# Spike 결과 — TypeDB 3.x fun + 임계값 외부화 결합 검증

> 2026-05-09 (토) 진행. 1~2시간 타임박스.
> 결론: **사용자 의도(fun + 임계값 외부화 결합) 100% 동작 검증**.

---

## 1. 결과 요약

| # | 패턴 | 결과 | 비고 |
|---|---|---|---|
| S1 | 단순 fun (entity 집합) | ✅ | 길기상 패턴 그대로 |
| S2 | 매개변수 fun (직접 매칭) | ❌ | `[REP1]` 변수 충돌 |
| S2v2 | 매개변수 + 매칭 분리 | ✅ | 우회 패턴 발견 |
| S3 | scalar count `-> { integer }` | ❌ | `[FRP8]` signature 불일치 |
| S3v2 | scalar count `-> integer` | ✅ | 집합 표시 제거 |
| S4 | 분기 multiple return (lookup) | ✅ | OR 절 + `let $score = ...` |
| S5 | threshold + 매개변수 (직접 매칭) | ❌ | S2와 같은 `[REP1]` |
| S5v2 | **threshold + 매개변수 (분리)** | ✅ | **사용자 의도 완전 동작** |

## 2. 학습한 TypeDB 3.x fun 문법

### 2-1. 매개변수와 attribute 매칭 분리 (★중요)

❌ 실패:
```typeql
fun foo($status_filter: string) -> { source }:
  match
    $s isa source, has availability-status $status_filter;  ← REP1 에러
  return { $s };
```

✅ 통과:
```typeql
fun foo($status_filter: string) -> { source }:
  match
    $s isa source, has availability-status $av;
    $av == $status_filter;                                  ← 분리해서 비교
  return { $s };
```

### 2-2. 반환 타입과 호출 문법

| 반환 시그니처 | 호출 문법 | 의미 |
|---|---|---|
| `-> integer` | `let $c = fun();` | 단일 scalar |
| `-> double` | `let $d = fun();` | 단일 scalar |
| `-> string` | `let $s = fun();` | 단일 scalar |
| `-> { source }` | `let $s in fun();` | entity 집합 (스트림) |
| `-> { string }` | `let $s in fun();` | string 집합 |
| `-> { double }` | `let $d in fun();` | double 집합 |

### 2-3. 분기 multiple return — OR 절 + let 변수

```typeql
fun grade_to_score($grade_in: string) -> { double }:
  match
    {
      $grade_in == "정상";
      let $score = 0.00;
    } or {
      $grade_in == "낮음";
      let $score = 0.20;
    } or {
      $grade_in == "다소높음";
      let $score = 0.55;
    };
  return { $score };
```

### 2-4. 그래프 노드 조회 + 산술 비교 + 분기 (사용자 의도 핵심)

```typeql
fun s_priority_to_state_v2($sp_in: double, $version_in: string) -> { string }:
  match
    $t isa threshold-set,
      has config-version $cv,
      has th-low $lo, has th-mid-low $ml,
      has th-mid-high $mh, has th-high $hi;
    $cv == $version_in;                       ← 매개변수 매칭 분리
    {
      $sp_in < $lo;
      let $state = "GeneralManagement";
    } or {
      $sp_in >= $lo; $sp_in < $ml;
      let $state = "EnhancedMonitoring";
    } or { ... };
  return { $state };
```

핵심: **fun이 매개변수 받기 + 그래프 노드 조회 + 산술 비교 분기**를 모두 한 번에 처리.

## 3. 검증 결과 — 임계값 외부화 + fun 결합

| 입력 | 결과 |
|---|---|
| `s_priority_to_state_v2(0.10, "v1")` | `GeneralManagement` ✅ |
| `s_priority_to_state_v2(0.30, "v1")` | `EnhancedMonitoring` ✅ |
| `s_priority_to_state_v2(0.50, "v1")` | `ReviewPreWatering` ✅ |
| `s_priority_to_state_v2(0.70, "v1")` | `PriorityPreWatering` ✅ |
| `s_priority_to_state_v2(0.90, "v1")` | `ImmediatePreWatering` ✅ |
| `s_priority_to_state_v2(0.30, "v2")` | **ReviewPreWatering** ⭐ (v1: EnhancedMonitoring → v2에서 격상) |

→ **fun이 그래프 노드를 동적 조회하여 v1↔v2 임계값 전환 시 코드 수정 0줄로 결과 변화**.
이게 사용자가 그린 그림: "fun + 임계값 외부화 결합으로 하드코딩 회피".

## 4. As-is vs To-be 갱신

| 차원 | As-is (Python) | **새 To-be (fun + 외부화)** |
|---|---|---|
| 산식 위치 | `formulas.py` | `db/functions.tql` |
| **임계값** | ✅ threshold-set 노드 | ✅ **동일 (fun이 조회)** ★ |
| 추론 시점 | 사전 1회 | 쿼리 시 직접 |
| 그래프 자족성 | ❌ Python 필수 | ✅ **단독 가능** ★ |
| 학술적 "온톨로지 추론" | ⚠️ 약함 | ✅ **본격** ★ |
| LLM 자연어 통합 | ✅ 구현 완료 | ✅ **fun을 호출하는 TypeQL 생성하면 동일** |

→ 길기상님 To-be의 약점(임계값 하드코딩)을 **우리가 외부화로 해결**. **사용자 의도가 두 모델보다 우월한 새 기준** 확립.

## 5. 발표 시연 영향

### 시연 2(파라미터 외부화) 강화 — **듀얼 시연**

기존:
```
Python: load_thresholds("v1") → s_priority_to_state(0.30) = EnhancedMonitoring
파라미터 v2 추가
Python: load_thresholds("v2") → s_priority_to_state(0.30) = ReviewPreWatering
```

신규 추가:
```
TypeQL: match let $st in s_priority_to_state_v2(0.30, "v1"); select $st;
        → EnhancedMonitoring
TypeQL: match let $st in s_priority_to_state_v2(0.30, "v2"); select $st;
        → ReviewPreWatering
```

**같은 결과를 두 방식(Python / fun)으로 보여줌** — 청중에게 "추론을 그래프 안에 옮길 수 있고, 결과 일치를 검증한다"는 강력한 메시지.

### 새 takeaway 추가

기존 5개 takeaway에 **6번째 추가**:
> ⑥ "그래프가 직접 추론할 수 있다 (fun) — 단 임계값 외부화 유지로 정책 시뮬레이션 가능"

## 6. 다음 단계 — 정식 모듈화

- [ ] `study/wildfire-poc/db/functions.tql` 신설 (정식 schema)
- [ ] `study/wildfire-poc/db/apply_functions.py` (schema 적용)
- [ ] `study/wildfire-poc/inference/graph_inference_fun.py` (fun 호출 버전)
- [ ] `study/wildfire-poc/tests/test_python_vs_fun.py` (회귀 검증)
- [ ] 발표 자료 outline 갱신 — 시연 2 듀얼 + takeaway 6번 추가

## 7. 결정

✅ **fun + 외부화 결합 도입 권장**. 4일 안에 가능 (단, 다른 작업과 병행).
- Spike 산출물(_spike/02d_threshold_combo_v2.tql)이 이미 핵심 동작.
- 정식 모듈화 + 회귀 검증 + 발표 자료 갱신만 남음.
- As-is(Python)는 그대로 유지 — 안전망.

다만 작업량 증가:
- 본래 작업 (자료 본문 재작성, 시연 스크립트, PPT 변환) + fun 통합 = 빠듯
- 우선순위: **fun 도입 → 자료 본문 → 리허설** 순.

## 8. 발견 메모

- TypeDB Console 없이 Python driver로 schema 변경 + fun 정의 가능 ✅
- fun은 SCHEMA tx에서 정의, READ tx에서 호출
- "이미 정의된 fun 재정의" 시 `[FUN5]` 에러 — undefine 후 재정의 또는 다른 이름 사용
- temperature 0.0 + system_instruction에 fun 사용 가이드 추가하면 LLM이 fun 호출 TypeQL 생성 가능 (다음 검증 항목)
