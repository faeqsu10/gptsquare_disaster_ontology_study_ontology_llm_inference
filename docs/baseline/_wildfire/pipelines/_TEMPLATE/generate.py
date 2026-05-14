#!/usr/bin/env python3
"""
Template generator for MOCK Source AccessOptions.

Source-specific copies should:
- use a fixed seed,
- generate only PoC/baseline scenario data,
- include time and space keys required by the Source Dossier contract,
- write output under data/mock/<source_id>/scenario_baseline/.
"""

from pathlib import Path

SOURCE_ID = "source_id"
ACCESS_OPTION_ID = "access_option_id"
OUTPUT_DIR = Path("data/mock") / SOURCE_ID / "scenario_baseline"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raise SystemExit(
        "Template only. Copy this file to pipelines/<source_id>/generate.py and implement the source-specific generator."
    )


if __name__ == "__main__":
    main()
