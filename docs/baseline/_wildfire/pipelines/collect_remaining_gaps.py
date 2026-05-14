#!/usr/bin/env python3
"""Run only the remaining source-gap collection pipelines.

This orchestration intentionally excludes already completed API/static/mock
pipelines from the 2026-05-01 reference-time collection. It currently handles
the remaining manual-acquisition gaps by promoting preserved FGIS SHP archives
to explicit 광주·전남 full snapshot manifests.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "work/source_collection_runs/ref_20260501T020000/remaining_gap_pipeline_manifest.json"


PIPELINES = [
    {
        "source_id": "SOURCE_FOREST_STAND_MAP",
        "reason": "manual-acquired FGIS 광주·전남 forest stand archives need full snapshot registration",
        "command": [sys.executable, "pipelines/SOURCE_FOREST_STAND_MAP/build_full_gwangju_jeonnam.py"],
        "manifest": "data/raw/SOURCE_FOREST_STAND_MAP/snapshots/full_gwangju_jeonnam_20260430/manifest.json",
    },
    {
        "source_id": "SOURCE_FOREST_ROAD_NETWORK",
        "reason": "manual-acquired FGIS Jeonnam forest-road archive and Gwangju no-data evidence need full snapshot registration",
        "command": [sys.executable, "pipelines/SOURCE_FOREST_ROAD_NETWORK/build_full_gwangju_jeonnam.py"],
        "manifest": "data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/full_gwangju_jeonnam_20260430/manifest.json",
    },
]


def run_pipeline(item: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    result = {
        "source_id": item["source_id"],
        "reason": item["reason"],
        "command": item["command"],
        "manifest": item["manifest"],
    }
    if dry_run:
        result["status"] = "dry_run"
        return result
    proc = subprocess.run(
        item["command"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result.update(
        {
            "status": "completed" if proc.returncode == 0 else "failed",
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "manifest_exists": (ROOT / item["manifest"]).exists(),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results = [run_pipeline(item, dry_run=args.dry_run) for item in PIPELINES]
    summary = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "scope": "remaining gaps from ref_20260501T020000 collection",
        "excluded_completed_sources": "all sources not listed in pipeline_results",
        "pipeline_results": results,
        "overall_status": "completed"
        if all(item["status"] in {"completed", "dry_run"} for item in results)
        else "failed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["overall_status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
