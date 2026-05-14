"""5주차 발표 3 — 골든 평가셋 15건 자동 실행 + 통과율 리포트.

실행 방법:
    ./_workspace/study-poc/run.sh _workspace/study-poc/llm/eval/run_eval.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from text_to_typeql import query_with_self_correction

GOLDEN_PATH = Path(__file__).parent / "golden_qna.json"


def main() -> None:
    with GOLDEN_PATH.open(encoding="utf-8") as f:
        golden = json.load(f)

    print("=" * 70)
    print(f"5주차 발표 3 — 평가셋 {len(golden)}건 자동 실행")
    print("=" * 70)

    stats = {
        "first_try": 0,
        "retry": 0,
        "fallback": 0,
        "failure": 0,
    }
    by_difficulty = {"단순": [0, 0], "중간": [0, 0], "복잡": [0, 0]}

    for case in golden:
        cat = case["category"]
        by_difficulty[cat][1] += 1

        print(f"\n# [{case['id']}] 난이도={case['difficulty']} ({cat})")
        result = query_with_self_correction(case["question"], case_id=case["id"], verbose=False)

        if result["status"] == "success":
            if result["attempt"] == 1:
                stats["first_try"] += 1
                tag = "✅ 1회 성공"
            else:
                stats["retry"] += 1
                tag = f"🔁 재시도 {result['attempt']}회 성공"
            by_difficulty[cat][0] += 1
        elif result["status"] == "fallback_success":
            stats["fallback"] += 1
            tag = "🔄 Fallback 사용"
        else:
            stats["failure"] += 1
            tag = "❌ 완전 실패"

        print(f"  {tag} — {case['question']}")

    total = len(golden)
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)
    print(f"  전체:                {total}건")
    print(f"  Gemini 1회 성공:     {stats['first_try']}건")
    print(f"  Gemini 재시도 성공:  {stats['retry']}건")
    print(f"  Fallback 사용:       {stats['fallback']}건  (Gemini 직접 실패)")
    print(f"  완전 실패:           {stats['failure']}건")
    print()
    print("  난이도별 Gemini 직접 성공률:")
    for cat in ("단순", "중간", "복잡"):
        passed, total_cat = by_difficulty[cat]
        if total_cat:
            print(f"    {cat:5s}: {passed}/{total_cat} ({100 * passed / total_cat:.0f}%)")


if __name__ == "__main__":
    main()
