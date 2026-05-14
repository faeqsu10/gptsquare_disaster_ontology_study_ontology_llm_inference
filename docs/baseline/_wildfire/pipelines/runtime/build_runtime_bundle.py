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

from pipelines._shared.mock_builders import (
    build_fire_resource_availability,
    build_prewatering_equipment_capacity,
    build_surface_fuel_condition,
    build_worksite_hazard_conditions,
    load_anchor_tables,
    write_csv,
    write_geojson,
    write_manifest,
)
from pipelines._shared.official_fire_risk_live import fetch_live_fire_risk
from pipelines._shared.runtime_context import (
    add_run_context_arguments,
    build_source_cycle_status,
    run_context_from_args,
    write_json,
)

OUTPUT_SPECS = {
    "SOURCE_FIRE_RESOURCE_AVAILABILITY": {
        "csv": "fire_resource_availability_mock.csv",
        "manifest": "manifest.json",
        "legacy_manifest": "scenario_manifest.json",
    },
    "SOURCE_PREWATERING_EQUIPMENT_CAPACITY": {
        "csv": "prewatering_equipment_capacity_mock.csv",
        "manifest": "manifest.json",
        "legacy_manifest": "scenario_manifest.json",
    },
    "SOURCE_SURFACE_FUEL_CONDITION": {
        "csv": "surface_fuel_condition_mock.csv",
        "geojson": "surface_fuel_condition_mock.geojson",
        "manifest": "manifest.json",
        "legacy_manifest": "scenario_manifest.json",
    },
    "SOURCE_WORKSITE_HAZARD_CONDITIONS": {
        "csv": "worksite_hazard_conditions_mock.csv",
        "geojson": "worksite_hazard_conditions_mock.geojson",
        "manifest": "manifest.json",
        "legacy_manifest": "scenario_manifest.json",
    },
}


def _source_output_dir(source_id: str, run_id: str, layout: str) -> Path:
    if layout == "scenario_baseline":
        return ROOT / "data/mock" / source_id / "scenario_baseline"
    return ROOT / "data/mock" / source_id / "runs" / run_id


def _write_outputs(
    *,
    source_id: str,
    output_dir: Path,
    rows: list[dict[str, Any]],
    features: list[Any] | None,
    ctx: Any,
    manifest_meta: dict[str, Any],
    live_fire_status: str | None,
) -> None:
    spec = OUTPUT_SPECS[source_id]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, output_dir / spec["csv"])
    files = [spec["csv"]]
    if features:
        geojson_name = spec["geojson"]
        write_geojson(features, output_dir / geojson_name, source_id)
        files.append(geojson_name)
    manifest_name = spec["manifest"]
    manifest_path = output_dir / manifest_name
    write_manifest(
        source_id=source_id,
        output_path=manifest_path,
        ctx=ctx,
        row_count=len(rows),
        time_key_fields=manifest_meta["time_key_fields"],
        space_key_fields=manifest_meta["space_key_fields"],
        files=files,
        live_fire_status=live_fire_status,
    )
    if "legacy_manifest" in spec:
        legacy_path = output_dir / spec["legacy_manifest"]
        if legacy_path != manifest_path:
            legacy_path.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")


def _load_live_fire_rows(csv_path: Path | None) -> list[dict[str, Any]] | None:
    if not csv_path or not csv_path.exists():
        return None
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    typed_rows: list[dict[str, Any]] = []
    for row in rows:
        typed_rows.append(
            {
                **row,
                "mean_risk_index": int(row["mean_risk_index"]),
                "max_risk_index": int(row["max_risk_index"]),
            }
        )
    return typed_rows


def build_single_source(
    *,
    source_id: str,
    ctx: Any,
    output_dir: Path,
    station_rows: list[dict[str, str]] | None = None,
    context_rows: list[dict[str, str]] | None = None,
    live_fire_rows: list[dict[str, Any]] | None = None,
) -> None:
    station_rows = station_rows or []
    context_rows = context_rows or []
    if source_id == "SOURCE_FIRE_RESOURCE_AVAILABILITY":
        rows, features, manifest_meta = build_fire_resource_availability(
            ctx, station_rows, context_rows, live_fire_rows
        )
    elif source_id == "SOURCE_PREWATERING_EQUIPMENT_CAPACITY":
        rows, features, manifest_meta = build_prewatering_equipment_capacity(ctx, station_rows, context_rows)
    elif source_id == "SOURCE_SURFACE_FUEL_CONDITION":
        rows, features, manifest_meta = build_surface_fuel_condition(ctx, context_rows, live_fire_rows)
    elif source_id == "SOURCE_WORKSITE_HAZARD_CONDITIONS":
        rows, features, manifest_meta = build_worksite_hazard_conditions(ctx, context_rows, live_fire_rows)
    else:
        raise ValueError(f"Unsupported source_id: {source_id}")
    live_status = "present" if live_fire_rows else "absent"
    _write_outputs(
        source_id=source_id,
        output_dir=output_dir,
        rows=rows,
        features=features,
        ctx=ctx,
        manifest_meta=manifest_meta,
        live_fire_status=live_status,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a time-aligned Gwangju/Jeonnam runtime mock bundle.")
    add_run_context_arguments(parser, default_mode="live", default_scenario_name="gwangju_jeonnam_runtime")
    parser.add_argument("--layout", choices=["runs", "scenario_baseline"], default="runs")
    parser.add_argument("--source-id", choices=list(OUTPUT_SPECS.keys()), default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--live-fire-risk-csv", type=Path, default=None)
    parser.add_argument("--skip-live-fire-fetch", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ctx = run_context_from_args(args)
    station_rows, context_rows = load_anchor_tables()

    run_dir = ROOT / "work/runtime_runs" / ctx.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "run_context.json", ctx.to_dict())
    write_json(run_dir / "source_cycle_status.json", build_source_cycle_status(ctx.reference_time))

    live_fire_rows = _load_live_fire_rows(args.live_fire_risk_csv)
    live_fire_status = "not_requested"
    if args.mode in {"live", "hybrid"} and not args.skip_live_fire_fetch and live_fire_rows is None:
        live_snapshot_dir = ROOT / "data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots" / f"live_{ctx.run_id}"
        live_result = fetch_live_fire_risk(live_snapshot_dir, ctx.reference_time)
        live_fire_status = live_result["status"]
        live_fire_rows = live_result.get("rows")
        write_json(run_dir / "live_fire_driver_status.json", live_result)
    elif live_fire_rows is not None:
        live_fire_status = "loaded_from_csv"
        write_json(
            run_dir / "live_fire_driver_status.json",
            {
                "status": live_fire_status,
                "row_count": len(live_fire_rows),
                "live_fire_risk_csv": str(args.live_fire_risk_csv),
            },
        )

    source_ids = [args.source_id] if args.source_id else list(OUTPUT_SPECS.keys())
    generated = []
    for source_id in source_ids:
        output_dir = (
            args.output_dir.resolve() if args.output_dir else _source_output_dir(source_id, ctx.run_id, args.layout)
        )
        build_single_source(
            source_id=source_id,
            ctx=ctx,
            output_dir=output_dir,
            station_rows=station_rows,
            context_rows=context_rows,
            live_fire_rows=live_fire_rows,
        )
        generated.append({"source_id": source_id, "output_dir": str(output_dir.relative_to(ROOT))})

    write_json(
        run_dir / "runtime_bundle_manifest.json",
        {
            "run_context": ctx.to_dict(),
            "generated_sources": generated,
            "live_fire_driver_status": live_fire_status,
        },
    )
    print(f"Built {len(generated)} source bundle(s) for {ctx.run_id}")


if __name__ == "__main__":
    main()
