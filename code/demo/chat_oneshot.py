"""시연 3 — chat.py를 1회 호출용으로 감싼 진입점.

기존 chat.py를 수정하지 않기 위해 별도 파일로 분리한다.
표준 출력은 server.py가 SSE로 그대로 흘려보낸다.

사용법:
    ./code/run.sh code/demo/chat_oneshot.py \
        --query "EMD_여수_상암동 위험도 알려줘"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "llm"))

from chat import chat


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="자연어 질의 1건을 chat.py로 처리한다.")
    parser.add_argument("--query", required=True, help="사용자 자연어 질문")
    parser.add_argument("--case-id", default=None, help="평가셋 case_id (옵션)")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    chat(args.query, case_id=args.case_id)


if __name__ == "__main__":
    main()
