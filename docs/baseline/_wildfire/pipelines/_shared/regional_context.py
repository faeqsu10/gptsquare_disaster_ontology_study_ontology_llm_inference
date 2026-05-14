from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from pipelines._shared.gwangju_jeonnam_units import coverage_summary, load_coverage_units
from pipelines._shared.runtime_context import KST

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data/reference/runtime_anchors"
OUTPUT_PATH = OUTPUT_DIR / "regional_context_profile_gwangju_jeonnam.csv"
MANIFEST_PATH = OUTPUT_DIR / "regional_context_profile_gwangju_jeonnam.manifest.json"


def admin_unit_type(emd_name: str) -> str:
    if emd_name.endswith(("동", "가")):
        return "urban_dong"
    if emd_name.endswith("읍"):
        return "town_eup"
    if emd_name.endswith("면"):
        return "rural_myeon"
    return "other"


def is_coastal(longitude: float, latitude: float, sigungu_name: str) -> bool:
    return longitude < 126.45 or latitude < 34.55 or sigungu_name in {"목포시", "여수시", "완도군", "진도군", "신안군"}


def is_east_inland(longitude: float, sigungu_name: str) -> bool:
    return longitude > 126.95 or sigungu_name in {"곡성군", "구례군", "순천시", "광양시", "화순군", "장성군", "담양군"}


def derive_context(unit: dict[str, Any]) -> dict[str, Any]:
    unit_type = admin_unit_type(unit["eupmyeondong_name"])
    coastal = is_coastal(unit["longitude"], unit["latitude"], unit["sigungu_name"])
    east_inland = is_east_inland(unit["longitude"], unit["sigungu_name"])

    if unit_type == "urban_dong":
        settlement_interface_class = "high"
        forest_type_class = "urban_interface"
        road_access_class = "dense_road"
        slope_class = (
            "medium" if unit["sigungu_name"] in {"동구", "북구", "남구"} and unit["longitude"] > 126.93 else "low"
        )
        dryness_class = "seasonal" if not east_inland else "elevated"
    elif unit_type == "town_eup":
        settlement_interface_class = "medium"
        forest_type_class = "mixed_hillside" if east_inland else "mixed_rural"
        road_access_class = "standard_road"
        slope_class = "medium"
        dryness_class = "moderated" if coastal else "seasonal"
    else:
        settlement_interface_class = "low"
        if coastal:
            forest_type_class = "coastal_open_mix"
            road_access_class = "limited_road"
            slope_class = "low"
            dryness_class = "moderated"
        elif east_inland:
            forest_type_class = "forest_dominant"
            road_access_class = "mountain_access"
            slope_class = "high"
            dryness_class = "elevated"
        else:
            forest_type_class = "mixed_rural"
            road_access_class = "limited_road"
            slope_class = "medium"
            dryness_class = "seasonal"

    return {
        "region_code": unit["coverage_unit_id"],
        "region_name": unit["coverage_unit_name"],
        "sido_name": unit["sido_name"],
        "sigungu_code": unit["sigungu_code"],
        "sigungu_name": unit["sigungu_name"],
        "emd_name": unit["eupmyeondong_name"],
        "representative_longitude": unit["longitude"],
        "representative_latitude": unit["latitude"],
        "admin_unit_type": unit_type,
        "forest_type_class": forest_type_class,
        "road_access_class": road_access_class,
        "slope_class": slope_class,
        "dryness_class": dryness_class,
        "settlement_interface_class": settlement_interface_class,
        "geometry_source": unit["geometry_source"],
        "code_match_status": unit["code_match_status"],
        "profile_generated_at": datetime.now(KST).isoformat(timespec="seconds"),
        "profile_basis": "boundary representative point + legal dong admin type heuristic",
    }


def build_regional_context_rows() -> list[dict[str, Any]]:
    units = load_coverage_units()
    rows = [derive_context(unit) for unit in units]
    rows.sort(key=lambda item: item["region_code"])
    return rows


def write_regional_context(rows: list[dict[str, Any]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "artifact_id": "regional_context_profile_gwangju_jeonnam",
        "coverage_summary": coverage_summary(load_coverage_units()),
        "row_count": len(rows),
        "admin_unit_type_counts": dict(Counter(row["admin_unit_type"] for row in rows)),
        "forest_type_counts": dict(Counter(row["forest_type_class"] for row in rows)),
        "road_access_counts": dict(Counter(row["road_access_class"] for row in rows)),
        "slope_counts": dict(Counter(row["slope_class"] for row in rows)),
        "dryness_counts": dict(Counter(row["dryness_class"] for row in rows)),
        "settlement_interface_counts": dict(Counter(row["settlement_interface_class"] for row in rows)),
        "notes": [
            "This is a REAL-derived reference profile, not an operational measurement source.",
            "Classification uses admin grain and representative-point geography only.",
            "No road join, DEM join, or CRS conversion is performed in this phase.",
        ],
        "fields": list(rows[0].keys()),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_regional_context(force: bool = False) -> Path:
    if force or not OUTPUT_PATH.exists():
        rows = build_regional_context_rows()
        write_regional_context(rows)
    return OUTPUT_PATH
