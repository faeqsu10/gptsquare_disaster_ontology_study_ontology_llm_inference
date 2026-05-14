"""5주차 발표 3 회귀 — Python 추론과 fun 추론 결과 일치 검증.

전제:
- compute_and_write_back (graph_inference.py) — Python 산식 + 그래프 임계값 조회
- compute_with_fun (graph_inference_fun.py) — Python 가중평균 + fun 호출 (lookup·매핑·override)

검증:
1) 5 segment × v1 임계값 → 두 엔진 결과 (s_priority, base_state, state, reason) 일치
2) v1 → v2 임계값 변경 시에도 두 엔진 결과 일치 (fun이 동적 조회 보장)

실행: ./code/run.sh code/tests/test_python_vs_fun.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "inference"))

from graph_inference import (  # noqa: E402
    ALERT_SCORE,
    GRADE_SCORE,
    _norm,
    load_thresholds,
    load_weights,
    make_driver,
    resolve_state,
    s_priority_to_state,
)
from graph_inference_fun import DEMO_SEGMENTS, compute_with_fun  # noqa: E402


def python_compute(driver, seg: dict, config_version: str = "v1") -> dict:
    """graph_inference.compute_and_write_back과 동일 로직 + write-back 없음.

    회귀 비교용 — fun 결과와 비교할 ground truth.
    """
    weights = load_weights(driver, "S_priority", version="v1")
    thresholds = load_thresholds(driver, "S_priority_to_state", version=config_version)

    f_grade = GRADE_SCORE.get(seg["risk_grade"], 0.0)
    f_alert = ALERT_SCORE.get(seg["alert_level"], 0.0)
    s_official = 0.40 * f_grade + 0.20 * 0.5 + 0.40 * f_alert
    f_resi = 0.40 * _norm(seg["population"], 0, 30000) + 0.25 * (1.0 - _norm(seg["forest_dist"], 0, 2000))
    s_exposure = 0.40 * f_resi + 0.35 * 0.3 + 0.25 * 0.3
    s_spread = 0.40 * _norm(seg["wind"], 0, 20) + 0.25 * 0.3 + 0.35 * 0.3
    s_action = 0.5
    s_time = 0.5

    s_priority = (
        weights["official"] * s_official
        + weights["exposure"] * s_exposure
        + weights["spread"] * s_spread
        + weights["action"] * s_action
        + weights["time"] * s_time
    )

    base_state = s_priority_to_state(s_priority, thresholds)
    final_state, reason = resolve_state(seg, base_state)

    return {
        "segment_id": seg["id"],
        "f_grade": f_grade,
        "f_alert": f_alert,
        "s_priority": s_priority,
        "base_state": base_state,
        "state": final_state,
        "reason": reason,
        "config_version": config_version,
    }


def compare_results(py: dict, fn: dict) -> tuple[bool, list[str]]:
    """두 결과의 핵심 필드 일치 여부 비교."""
    diffs = []
    for key in ("f_grade", "f_alert"):
        if abs(py[key] - fn[key]) > 1e-9:
            diffs.append(f"{key}: py={py[key]} fn={fn[key]}")
    if abs(py["s_priority"] - fn["s_priority"]) > 1e-6:
        diffs.append(f"s_priority: py={py['s_priority']:.6f} fn={fn['s_priority']:.6f}")
    for key in ("base_state", "state", "reason"):
        if py[key] != fn[key]:
            diffs.append(f"{key}: py={py[key]!r} fn={fn[key]!r}")
    return (len(diffs) == 0, diffs)


def main() -> int:
    print("=" * 70)
    print("회귀 — Python 추론 ↔ fun 추론 결과 일치 검증")
    print("=" * 70)

    total = 0
    passed = 0
    failed_cases = []

    with make_driver() as driver:
        for version in ("v1", "v2"):
            print(f"\n[{version} 임계값]")
            for seg in DEMO_SEGMENTS:
                total += 1
                py = python_compute(driver, seg, config_version=version)
                fn = compute_with_fun(driver, seg, config_version=version, write_back=False)
                ok, diffs = compare_results(py, fn)
                mark = "✅" if ok else "❌"
                print(f"  {mark} {seg['id']:25s} sp={py['s_priority']:.4f} state={py['state']:20s}")
                if ok:
                    passed += 1
                else:
                    failed_cases.append((seg["id"], version, diffs))
                    for d in diffs:
                        print(f"       diff: {d}")

    print("\n" + "=" * 70)
    print(f"결과: {passed}/{total} 통과")
    if failed_cases:
        print("\n실패 케이스:")
        for seg_id, ver, diffs in failed_cases:
            print(f"  - {seg_id} ({ver}): {len(diffs)}개 차이")
        return 1
    print("→ Python 추론과 fun 추론이 모든 케이스에서 동일 결과를 산출함.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
