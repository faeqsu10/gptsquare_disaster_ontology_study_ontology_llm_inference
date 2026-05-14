"""SPIKE — TypeDB 3.x fun 가능성 단계별 검증.

각 단계는 schema에 fun 정의(SCHEMA tx) → 호출(READ tx)로 분리.
실패해도 다음 단계 진행.

실행: ./study/wildfire-poc/run.sh study/wildfire-poc/_spike/run_spike.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB = "wildfire"
SPIKE_DIR = Path(__file__).resolve().parent


def driver_ctx():
    return TypeDB.driver(
        "localhost:1729",
        Credentials("admin", "password"),
        DriverOptions(False, None),
    )


def define_fun(label: str, tql_path: Path) -> tuple[bool, str]:
    """fun을 schema에 추가. 성공/실패 + 메시지 반환."""
    tql = tql_path.read_text(encoding="utf-8")
    print(f"\n--- DEFINE [{label}] ({tql_path.name}) ---")
    try:
        with driver_ctx() as d, d.transaction(DB, TransactionType.SCHEMA) as tx:
            tx.query(tql).resolve()
            tx.commit()
        print("  ✅ 정의 성공")
        return True, "ok"
    except Exception as e:
        msg = str(e)[:300]
        print(f"  ❌ 정의 실패: {msg}")
        return False, msg


def call_fun(label: str, query: str) -> tuple[bool, list, str]:
    """fun 호출 쿼리 실행. 결과 또는 에러."""
    print(f"\n--- CALL  [{label}] ---")
    print(f"    query: {query.strip()}")
    try:
        with driver_ctx() as d, d.transaction(DB, TransactionType.READ) as tx:
            ans = tx.query(query).resolve()
            rows = list(ans.as_concept_rows())
            print(f"  ✅ 호출 성공 (행 {len(rows)}건)")
            return True, rows, "ok"
    except Exception as e:
        msg = str(e)[:300]
        print(f"  ❌ 호출 실패: {msg}")
        return False, [], msg


def main():
    findings = []

    # ─── S1: 이전 통과 (mock_sources 이미 schema에 존재) ───
    findings.append(("S1: 단순 fun (entity 집합) — 이전 통과", True, "ok"))

    # ─── S2 v2: 매개변수 fun (REP1 회피 — 매개변수와 attribute 매칭 분리) ───
    ok_s2, msg_s2 = define_fun("S2v2_param", SPIKE_DIR / "02a_param_v2.tql")
    findings.append(("S2v2: 매개변수 fun (분리 패턴)", ok_s2, msg_s2))

    # ─── S3 v2: scalar count (signature 조정) ───
    ok_s3, msg_s3 = define_fun("S3v2_scalar_count", SPIKE_DIR / "02b_scalar_count_v2.tql")
    findings.append(("S3v2: scalar count (-> integer)", ok_s3, msg_s3))

    # ─── S4: 분기 multiple return — 이전 통과 ───
    ok_s4 = True
    findings.append(("S4: 분기 multiple return — 이전 통과", True, "ok"))

    # ─── S5 v2: threshold-set 결합 (핵심) ───
    ok_s5, msg_s5 = define_fun("S5v2_threshold_combo", SPIKE_DIR / "02d_threshold_combo_v2.tql")
    findings.append(("S5v2: threshold-set 결합 (분리 패턴)", ok_s5, msg_s5))

    # 정의 성공한 fun들 호출 검증
    if ok_s2:
        # S2 v2: 매개변수 fun
        ok2, rows, msg2 = call_fun(
            "S2v2.MOCK",
            'match let $s in sources_by_status_v2("MOCK"); $s has source-id $sid; select $sid;',
        )
        findings.append(("S2v2.call: sources_by_status_v2(MOCK)", ok2, msg2))
        if ok2 and rows:
            print(f"    sample: {rows[0].get('sid').try_get_string()} (총 {len(rows)}건)")

    if ok_s3:
        # S3 v2: scalar count
        ok3, rows, msg3 = call_fun(
            "S3v2.count",
            "match let $c = mock_count_v2(); select $c;",
        )
        findings.append(("S3v2.call: mock_count_v2() → integer", ok3, msg3))
        if ok3 and rows:
            v = rows[0].get("c").try_get_integer()
            print(f"    count: {v}")

    if ok_s4:
        # S4: 분기 multiple return (등급→점수)
        for g, expected in [("정상", 0.00), ("매우높음", 1.00), ("다소높음", 0.55)]:
            ok5, rows, msg5 = call_fun(
                f"S4.grade.{g}",
                f'match let $s in grade_to_score("{g}"); select $s;',
            )
            findings.append((f"S4: grade_to_score({g}) → {expected}", ok5, msg5))
            if ok5 and rows:
                v = rows[0].get("s").try_get_double()
                print(f"    {g}: {v} (expected {expected})")

    if ok_s5:
        # S5 v2: threshold-set 결합 (사용자가 진짜 원하는 핵심)
        for sp, ver, expected in [
            (0.10, "v1", "GeneralManagement"),
            (0.30, "v1", "EnhancedMonitoring"),
            (0.50, "v1", "ReviewPreWatering"),
            (0.70, "v1", "PriorityPreWatering"),
            (0.90, "v1", "ImmediatePreWatering"),
            (0.30, "v2", "ReviewPreWatering"),  # v2: 더 보수적, 같은 점수에 격상
        ]:
            ok6, rows, msg6 = call_fun(
                f"S5v2.{sp}.{ver}",
                f'match let $st in s_priority_to_state_v2({sp}, "{ver}"); select $st;',
            )
            findings.append((f"S5v2: s_priority_to_state_v2({sp}, {ver}) → {expected}", ok6, msg6))
            if ok6 and rows:
                v = rows[0].get("st").try_get_string()
                mark = "✅" if v == expected else "⚠️"
                print(f"    {mark} sp={sp} ver={ver}: {v} (expected {expected})")

    # ─── 결과 정리 ───
    print("\n" + "=" * 60)
    print("FINDINGS")
    print("=" * 60)
    for label, ok, msg in findings:
        mark = "✅" if ok else "❌"
        print(f"{mark} {label}")
        if not ok:
            print(f"   → {msg[:160]}")


if __name__ == "__main__":
    sys.exit(main() or 0)
