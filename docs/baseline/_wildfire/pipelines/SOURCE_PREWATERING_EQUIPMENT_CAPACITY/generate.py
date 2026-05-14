#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines._shared.mock_builders import load_anchor_tables
from pipelines._shared.runtime_context import add_run_context_arguments, run_context_from_args
from pipelines.runtime.build_runtime_bundle import build_single_source

SOURCE_ID = "SOURCE_PREWATERING_EQUIPMENT_CAPACITY"
DEFAULT_OUTPUT_DIR = ROOT / "data/mock" / SOURCE_ID / "scenario_baseline"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate time-aligned prewatering equipment capacity mock data.")
    add_run_context_arguments(parser, default_mode="scenario", default_scenario_name="scenario_baseline")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    ctx = run_context_from_args(args)
    station_rows, context_rows = load_anchor_tables()
    build_single_source(
        source_id=SOURCE_ID,
        ctx=ctx,
        output_dir=args.output_dir,
        station_rows=station_rows,
        context_rows=context_rows,
        live_fire_rows=None,
    )
    print(f"Wrote {SOURCE_ID} to {args.output_dir}")


if __name__ == "__main__":
    main()
