#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines._shared.gwangju_jeonnam_units import coverage_summary, load_coverage_units

SOURCE_ID = "SOURCE_ROAD_ACCESS_CONSTRAINTS"
ACCESS_OPTION_ID = "ACCESS_ROAD_ACCESS_CONSTRAINTS_BASELINE_SCENARIO"
DEFAULT_OUTPUT_DIR = Path("data/mock") / SOURCE_ID / "scenario_baseline"
DEFAULT_SEED = 20260430
VALID_FROM = "2026-05-01T02:00:00+09:00"
VALID_TO = "2026-05-04T02:00:00+09:00"
MOCK_GENERATED_AT = "2026-05-01T02:00:00+09:00"
REGION_SCOPE = "광주광역시·전라남도"
MOCK_REASON = "공개 도로망만으로 소방차 진입 가능성, 도로 폭, 회차 가능성을 확정하기 어려워 법정 읍면동 boundary coverage baseline mock으로 생성"


ROAD_CLASSES = ("local", "residential", "mountain_access", "arterial", "forest_track")


def adjusted_width(base_width: float, rng: random.Random) -> float:
    return round(max(2.0, min(8.0, base_width + rng.uniform(-0.2, 0.2))), 1)


def synthetic_segment(longitude: float, latitude: float, idx: int) -> list[list[float]]:
    lon_delta = 0.0008 + (idx % 5) * 0.00005
    lat_delta = 0.00045 + (idx % 7) * 0.00004
    direction = -1 if idx % 2 else 1
    return [
        [round(longitude - lon_delta / 2, 7), round(latitude - direction * lat_delta / 2, 7)],
        [round(longitude + lon_delta / 2, 7), round(latitude + direction * lat_delta / 2, 7)],
    ]


def build_rows(seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    units = load_coverage_units()
    for idx, unit in enumerate(units, start=1):
        segment_id = f"RAC-{unit['coverage_unit_id']}-{idx:04d}"
        road_name = f"{unit['eupmyeondong_name']} 접근 mock segment"
        road_class = ROAD_CLASSES[(idx - 1) % len(ROAD_CLASSES)]
        coordinates = synthetic_segment(unit["longitude"], unit["latitude"], idx)
        base_width = 2.8 + (idx % 8) * 0.55
        slope_percent = round(1.0 + (idx % 13) * 0.9, 1)
        paved_flag = road_class != "forest_track" or idx % 3 != 0
        turnaround_hint = road_class in {"local", "arterial"} or idx % 5 == 0
        width = adjusted_width(base_width, rng)
        narrow_road_flag = width < 3.5
        firetruck_accessible = bool(width >= 3.5 and slope_percent <= 10.0 and paved_flag)
        turnaround_available = bool(turnaround_hint and width >= 3.5)
        if not firetruck_accessible:
            access_class = "restricted"
        elif not turnaround_available:
            access_class = "limited_turnaround"
        else:
            access_class = "accessible"
        rows.append(
            {
                "mock_id": f"{SOURCE_ID}-{idx:03d}",
                "road_segment_id": segment_id,
                "road_name": road_name,
                "road_class": road_class,
                "start_node_id": f"{segment_id}-S",
                "end_node_id": f"{segment_id}-E",
                "coverage_unit_id": unit["coverage_unit_id"],
                "coverage_unit_name": unit["coverage_unit_name"],
                "region_code": unit["coverage_unit_id"],
                "region_name": unit["coverage_unit_name"],
                "sido_name": unit["sido_name"],
                "sigungu_code": unit["sigungu_code"],
                "sigungu_name": unit["sigungu_name"],
                "eupmyeondong_name": unit["eupmyeondong_name"],
                "geometry": "LINESTRING(" + ", ".join(f"{lon} {lat}" for lon, lat in coordinates) + ")",
                "road_width_m": width,
                "slope_percent": slope_percent,
                "paved_flag": paved_flag,
                "firetruck_accessible": firetruck_accessible,
                "turnaround_available": turnaround_available,
                "narrow_road_flag": narrow_road_flag,
                "access_constraint_class": access_class,
                "coverage_basis": unit["coverage_basis"],
                "geometry_source": unit["geometry_source"],
                "code_match_status": unit["code_match_status"],
                "valid_from": VALID_FROM,
                "valid_to": VALID_TO,
                "mock_seed": seed,
                "mock_generated_at": MOCK_GENERATED_AT,
                "mock_reason": MOCK_REASON,
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_geojson(rows: list[dict[str, Any]], output_path: Path) -> None:
    features = []
    for row in rows:
        coordinates = [
            [float(pair.split()[0]), float(pair.split()[1])]
            for pair in row["geometry"].removeprefix("LINESTRING(").removesuffix(")").split(", ")
        ]
        properties = {key: value for key, value in row.items() if key != "geometry"}
        features.append(
            {
                "type": "Feature",
                "id": row["road_segment_id"],
                "properties": properties,
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
            }
        )
    output_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": SOURCE_ID,
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": features,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_manifest(rows: list[dict[str, Any]], output_path: Path, seed: int) -> None:
    summary = coverage_summary(load_coverage_units())
    output_path.write_text(
        json.dumps(
            {
                "source_id": SOURCE_ID,
                "access_option_id": ACCESS_OPTION_ID,
                "scenario_name": "scenario_baseline",
                "region_scope": REGION_SCOPE,
                "mock_seed": seed,
                "row_count": len(rows),
                "native_crs": "EPSG:4326",
                "time_key_fields": ["valid_from", "valid_to", "mock_generated_at"],
                "space_key_fields": [
                    "road_segment_id",
                    "start_node_id",
                    "end_node_id",
                    "coverage_unit_id",
                    "geometry",
                ],
                "coverage_summary": summary,
                "coverage_result": "pass",
                "raw_phase_constraints": [
                    "no travel-time calculation",
                    "no real road-network join",
                    "no CRS conversion",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = build_rows(args.seed)
    write_csv(rows, args.output_dir / "road_access_constraints.csv")
    write_geojson(rows, args.output_dir / "road_access_constraints.geojson")
    write_manifest(rows, args.output_dir / "manifest.json", args.seed)
    print(f"Wrote {len(rows)} rows to {args.output_dir}")


if __name__ == "__main__":
    main()
