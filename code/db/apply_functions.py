"""TypeDB 3.x fun 정식 적용 스크립트.

functions.tql을 wildfire DB schema에 적용. idempotent — 이미 정의된 fun이 있으면
undefine 후 재정의.

실행: ./code/run.sh code/db/apply_functions.py
"""

from __future__ import annotations

from pathlib import Path

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"
FUNCTIONS_TQL = Path(__file__).parent / "functions.tql"

# functions.tql에 정의된 fun 이름 목록 — undefine 시 사용
FUN_NAMES = [
    "sources_by_status_v2",
    "grade_to_score",
    "alert_to_score",
    "s_priority_to_state_v2",
    "resolve_state_v2",
]


def driver_ctx():
    return TypeDB.driver(
        "localhost:1729",
        Credentials("admin", "password"),
        DriverOptions(False, None),
    )


def undefine_existing_funs() -> int:
    """이미 정의된 fun 제거 (idempotent 보장).

    각 fun별 별도 트랜잭션 — undefine 실패는 트랜잭션을 abort 시키므로 격리 필요.
    """
    removed = 0
    with driver_ctx() as d:
        for name in FUN_NAMES:
            try:
                with d.transaction(DB_NAME, TransactionType.SCHEMA) as tx:
                    tx.query(f"undefine fun {name};").resolve()
                    tx.commit()
                removed += 1
            except Exception:
                # 정의된 적 없으면 스킵 (FUN1 에러)
                pass
    return removed


def apply_functions() -> None:
    tql = FUNCTIONS_TQL.read_text(encoding="utf-8")
    with driver_ctx() as d, d.transaction(DB_NAME, TransactionType.SCHEMA) as tx:
        tx.query(tql).resolve()
        tx.commit()


def verify_calls() -> None:
    """5개 fun이 정상 동작하는지 빠른 호출 검증."""
    checks = [
        (
            'match let $s in sources_by_status_v2("MOCK"); $s has source-id $id; reduce $c = count;',
            "MOCK source 카운트",
        ),
        ('match let $sc in grade_to_score("매우높음"); select $sc;', "grade_to_score(매우높음) → 1.0 기대"),
        ('match let $ac in alert_to_score("경보"); select $ac;', "alert_to_score(경보) → 1.0 기대"),
        (
            'match let $st in s_priority_to_state_v2(0.30, "v1"); select $st;',
            "s_priority_to_state_v2(0.30, v1) → EnhancedMonitoring 기대",
        ),
        (
            'match let $st in s_priority_to_state_v2(0.30, "v2"); select $st;',
            "s_priority_to_state_v2(0.30, v2) → ReviewPreWatering 기대 (격상)",
        ),
        (
            'match let $st in resolve_state_v2("ReviewPreWatering", "정상", "경보"); select $st;',
            "resolve_state_v2(ReviewPreWatering, 정상, 경보) → PriorityPreWatering 기대 (alert 격상)",
        ),
        (
            'match let $st in resolve_state_v2("ReviewPreWatering", "작업 불가", "없음"); select $st;',
            "resolve_state_v2(ReviewPreWatering, 작업 불가, 없음) → NotActionable 기대 (hazard)",
        ),
    ]
    print("\n[검증]")
    with driver_ctx() as d, d.transaction(DB_NAME, TransactionType.READ) as tx:
        for query, desc in checks:
            try:
                ans = tx.query(query).resolve()
                rows = list(ans.as_concept_rows())
                if rows:
                    var = list(rows[0].column_names())[0]
                    concept = rows[0].get(var)
                    val = concept.try_get_string() or concept.try_get_double() or concept.try_get_integer()
                    print(f"  ✅ {desc}")
                    print(f"     → {val}")
                else:
                    print(f"  ⚠️  {desc} — 결과 0건")
            except Exception as e:
                print(f"  ❌ {desc} — {str(e)[:120]}")


def main() -> None:
    print("[1] 기존 fun undefine (idempotent)")
    n = undefine_existing_funs()
    print(f"  제거: {n}개")

    print("\n[2] functions.tql 적용")
    apply_functions()
    print(f"  적용: {len(FUN_NAMES)}개 fun")

    verify_calls()


if __name__ == "__main__":
    main()
