"""시연 ②에서 추가된 사용자 정의 threshold-set 정리.

보호 버전(v1, v2)을 제외한 모든 S_priority_to_state threshold-set 노드를 삭제한다.
발표 직전 또는 회차 사이에 실행해 그래프 오염을 막는다.

실행 방법:
    ./code/run.sh code/scripts/reset_thresholds.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inference"))

from graph_inference import DB_NAME, make_driver  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

PROTECTED_VERSIONS = frozenset({"v1", "v2"})
METRIC_NAME = "S_priority_to_state"


def list_versions(driver) -> list[str]:
    q = f"""
        match
          $t isa threshold-set,
            has metric-name "{METRIC_NAME}",
            has config-version $v;
        select $v;
        sort $v asc;
    """
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        answer = tx.query(q).resolve()
        return [row.get("v").try_get_string() for row in answer.as_concept_rows()]


def delete_version(driver, version: str) -> None:
    q = f"""
        match
          $t isa threshold-set,
            has metric-name "{METRIC_NAME}",
            has config-version "{version}";
        delete $t;
    """
    with driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
        tx.query(q).resolve()
        tx.commit()


def main() -> int:
    print("=" * 70)
    print("시연 ② threshold-set 정리 (보호 버전 외 모두 삭제)")
    print("=" * 70)

    with make_driver() as driver:
        versions = list_versions(driver)
        if not versions:
            print("그래프에 threshold-set이 없습니다. seed_params.py를 먼저 실행해주세요.")
            return 1

        print(f"현재 버전: {', '.join(versions)}")
        to_delete = [v for v in versions if v not in PROTECTED_VERSIONS]
        if not to_delete:
            print("삭제 대상 없음. 보호 버전(v1, v2)만 남아 있습니다.")
            return 0

        print(f"삭제 대상: {', '.join(to_delete)}")
        for v in to_delete:
            delete_version(driver, v)
            print(f"  ✓ {v} 삭제")

    print()
    print(f"✓ {len(to_delete)}건 정리 완료. v1·v2만 남아 있습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
