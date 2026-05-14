#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines._shared.mock_builders import load_anchor_tables
from pipelines._shared.runtime_context import add_run_context_arguments, run_context_from_args
from pipelines.runtime.build_runtime_bundle import build_single_source

SOURCE_ID = "SOURCE_FIRE_RESOURCE_AVAILABILITY"
DEFAULT_OUTPUT_DIR = ROOT / "data/mock" / SOURCE_ID / "scenario_baseline"


def load_live_fire_rows(path: Path | None) -> list[dict[str, Any]] | None:
    if not path or not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate time-aligned fire resource availability mock data.")
    add_run_context_arguments(parser, default_mode="scenario", default_scenario_name="scenario_baseline")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--live-fire-risk-csv", type=Path, default=None)
    args = parser.parse_args()

    ctx = run_context_from_args(args)
    station_rows, context_rows = load_anchor_tables()
    build_single_source(
        source_id=SOURCE_ID,
        ctx=ctx,
        output_dir=args.output_dir,
        station_rows=station_rows,
        context_rows=context_rows,
        live_fire_rows=load_live_fire_rows(args.live_fire_risk_csv),
    )
    print(f"Wrote {SOURCE_ID} to {args.output_dir}")


if __name__ == "__main__":
    main()
