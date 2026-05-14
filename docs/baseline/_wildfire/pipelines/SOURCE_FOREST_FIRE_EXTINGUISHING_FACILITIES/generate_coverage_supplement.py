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

SOURCE_ID = "SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES"
ACCESS_OPTION_ID = "ACCESS_FOREST_FIRE_EXTINGUISHING_FACILITIES_COVERAGE_SUPPLEMENT"
DEFAULT_OUTPUT_DIR = Path("data/mock") / SOURCE_ID / "scenario_baseline"
DEFAULT_SEED = 20260501
VALID_FROM = "2026-05-01T02:00:00+09:00"
VALID_TO = "2026-05-04T02:00:00+09:00"
MOCK_GENERATED_AT = "2026-05-01T02:00:00+09:00"
MOCK_REASON = (
    "공식 산불소화시설 CSV의 광주·전남 coverage gap을 메우기 위한 current legal 읍면동 coverage supplement mock"
)

FACILITY_TYPES = (
    "forest_fire_extinguishing_box",
    "mountain_fire_hydrant",
    "forest_edge_water_tank",
)
REMOTE_CONTROL_OPTIONS = ("N", "N", "Y")
PROTECTION_TARGET_TYPES = ("산림연접지", "마을-산림 경계", "등산로/임도 인접")


def jitter(value: float, rng: random.Random) -> float:
    return round(value + rng.uniform(-0.00012, 0.00012), 7)


def build_rows(seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    units = load_coverage_units()

    for idx, unit in enumerate(units, start=1):
        facility_type = FACILITY_TYPES[(idx - 1) % len(FACILITY_TYPES)]
        remote_control = REMOTE_CONTROL_OPTIONS[(idx - 1) % len(REMOTE_CONTROL_OPTIONS)]
        target_type = PROTECTION_TARGET_TYPES[(idx - 1) % len(PROTECTION_TARGET_TYPES)]
        longitude = jitter(unit["longitude"], rng)
        latitude = jitter(unit["latitude"], rng)
        facility_id = f"FFE-MOCK-{unit['coverage_unit_id']}-{idx:04d}"
        rows.append(
            {
                "mock_id": f"{SOURCE_ID}-{idx:03d}",
                "facility_id": facility_id,
                "facility_type": facility_type,
                "coverage_unit_id": unit["coverage_unit_id"],
                "coverage_unit_name": unit["coverage_unit_name"],
                "sido_name": unit["sido_name"],
                "sigungu_code": unit["sigungu_code"],
                "sigungu_name": unit["sigungu_name"],
                "eupmyeondong_name": unit["eupmyeondong_name"],
                "longitude": longitude,
                "latitude": latitude,
                "geometry": f"POINT({longitude} {latitude})",
                "remote_control": remote_control,
                "management_agency_1": unit["sido_name"],
                "management_agency_2": unit["sigungu_name"],
                "installation_location": f"{unit['coverage_unit_name']} 대표점 mock",
                "protection_target_type": target_type,
                "protection_target_name": f"{unit['eupmyeondong_name']} 산림연접 mock target",
                "installation_year": "2026",
                "record_origin": "mock_supplement",
                "official_gap_reason": "Official full CSV preserved separately; 광주 rows=0 and 전남 rows=13 in acquired source.",
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
        properties = {key: value for key, value in row.items() if key not in {"longitude", "latitude", "geometry"}}
        features.append(
            {
                "type": "Feature",
                "id": row["facility_id"],
                "properties": properties,
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]],
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
                "region_scope": "광주광역시·전라남도",
                "mock_seed": seed,
                "row_count": len(rows),
                "native_crs": "EPSG:4326",
                "time_key_fields": ["valid_from", "valid_to", "mock_generated_at", "installation_year"],
                "space_key_fields": [
                    "facility_id",
                    "coverage_unit_id",
                    "longitude",
                    "latitude",
                    "geometry",
                ],
                "coverage_summary": summary,
                "coverage_result": "pass",
                "official_source_preserved_at": "data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/full/",
                "official_source_coverage_gap": {
                    "full_row_count": 187,
                    "gwangju_row_count": 0,
                    "jeonnam_row_count": 13,
                },
                "raw_phase_constraints": [
                    "no nearest-distance calculation",
                    "no road or Segment join",
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
    write_csv(rows, args.output_dir / "forest_fire_extinguishing_facilities_coverage_supplement.csv")
    write_geojson(rows, args.output_dir / "forest_fire_extinguishing_facilities_coverage_supplement.geojson")
    write_manifest(rows, args.output_dir / "manifest.json", args.seed)
    print(f"Wrote {len(rows)} rows to {args.output_dir}")


if __name__ == "__main__":
    main()
