from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipelines._shared.gwangju_jeonnam_units import coverage_summary, load_coverage_units
from pipelines._shared.regional_context import ensure_regional_context
from pipelines._shared.runtime_context import RunContext, write_json
from pipelines._shared.station_master import ensure_station_master

SOURCE_REASONS = {
    "SOURCE_FIRE_RESOURCE_AVAILABILITY": "실시간 소방 인력·차량 가용성은 공개 운영데이터로 확보하기 어려워 runtime overlay로 생성",
    "SOURCE_PREWATERING_EQUIPMENT_CAPACITY": "장비별 실제 작업 능력은 내부 운영성 자료 성격이 강해 runtime overlay로 생성",
    "SOURCE_SURFACE_FUEL_CONDITION": "현장성 지표연료 상태는 광역 공개 관측 source가 부족하여 runtime overlay로 생성",
    "SOURCE_WORKSITE_HAZARD_CONDITIONS": "낙석·연기·접근 위험은 단일 공개 source 부재로 runtime overlay로 생성",
}
REGIONAL_COVERAGE_SOURCE_IDS = {"SOURCE_SURFACE_FUEL_CONDITION", "SOURCE_WORKSITE_HAZARD_CONDITIONS"}


@dataclass(frozen=True)
class FeatureRecord:
    feature_id: str
    geometry_type: str
    coordinates: Any
    properties: dict[str, Any]


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_anchor_tables() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    station_path = ensure_station_master()
    regional_path = ensure_regional_context()
    return _load_csv_rows(station_path), _load_csv_rows(regional_path)


def _context_map(context_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["region_code"]: row for row in context_rows}


def _sigungu_context_map(context_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    priority = {"high": 0, "medium": 1, "low": 2}
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in context_rows:
        grouped.setdefault(row["sigungu_code"], []).append(row)
    selected: dict[str, dict[str, str]] = {}
    for sigungu_code, rows in grouped.items():
        rows.sort(key=lambda item: (priority.get(item["settlement_interface_class"], 9), item["region_code"]))
        selected[sigungu_code] = rows[0]
    return selected


def _sigungu_risk_map(live_fire_rows: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    if not live_fire_rows:
        return {}
    return {str(row["sigungu_code"]): row for row in live_fire_rows}


def _rng(seed: int, *parts: str) -> random.Random:
    return random.Random("|".join([str(seed), *parts]))


def _point_box(longitude: float, latitude: float, size: float) -> list[list[float]]:
    return [
        [round(longitude - size, 7), round(latitude - size, 7)],
        [round(longitude + size, 7), round(latitude - size, 7)],
        [round(longitude + size, 7), round(latitude + size, 7)],
        [round(longitude - size, 7), round(latitude + size, 7)],
        [round(longitude - size, 7), round(latitude - size, 7)],
    ]


def _polygon_wkt(coords: list[list[float]]) -> str:
    return "POLYGON((" + ", ".join(f"{lon} {lat}" for lon, lat in coords) + "))"


def _line_wkt(coords: list[list[float]]) -> str:
    return "LINESTRING(" + ", ".join(f"{lon} {lat}" for lon, lat in coords) + ")"


def _point_wkt(longitude: float, latitude: float) -> str:
    return f"POINT({longitude} {latitude})"


def _size_for_admin(admin_unit_type: str) -> float:
    if admin_unit_type == "urban_dong":
        return 0.0012
    if admin_unit_type == "town_eup":
        return 0.0018
    return 0.0024


def _household_estimate(context: dict[str, str], seed: int) -> int:
    rng = _rng(seed, context["region_code"], "households")
    if context["settlement_interface_class"] == "high":
        return rng.randint(180, 420)
    if context["settlement_interface_class"] == "medium":
        return rng.randint(80, 240)
    return rng.randint(15, 120)


def _station_holdings(context: dict[str, str], station_id: str) -> dict[str, int]:
    rng = _rng(0, station_id, "holdings")
    settlement = context["settlement_interface_class"]
    road = context["road_access_class"]
    if settlement == "high":
        engines = 2 if rng.random() > 0.55 else 1
        tanker = 1 if rng.random() > 0.45 else 0
    elif settlement == "medium":
        engines = 1
        tanker = 1 if rng.random() > 0.2 else 0
    else:
        engines = 1
        tanker = 1
    small_vehicle = 1 if road in {"limited_road", "mountain_access"} else (1 if rng.random() > 0.7 else 0)
    pumps = 3 if road == "mountain_access" else 2
    return {
        "engine": engines,
        "water_tanker": tanker,
        "small_vehicle": small_vehicle,
        "portable_pump": pumps,
    }


def _station_context(
    station: dict[str, str],
    context_map: dict[str, dict[str, str]],
    sigungu_context_map: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    if station["region_code"] and station["region_code"] in context_map:
        return context_map[station["region_code"]]
    if station["sigungu_code"] and station["sigungu_code"] in sigungu_context_map:
        return sigungu_context_map[station["sigungu_code"]]
    return None


def _risk_reduction(pressure: str) -> tuple[int, int]:
    if pressure == "severe":
        return 3, 1
    if pressure == "high":
        return 2, 1
    if pressure == "moderate":
        return 1, 0
    return 0, 0


def build_fire_resource_availability(
    ctx: RunContext,
    station_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
    live_fire_rows: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], None, dict[str, Any]]:
    context_map = _context_map(context_rows)
    sigungu_context_map = _sigungu_context_map(context_rows)
    risk_map = _sigungu_risk_map(live_fire_rows)
    rows: list[dict[str, Any]] = []
    for station in station_rows:
        context = _station_context(station, context_map, sigungu_context_map)
        if not context:
            continue
        holdings = _station_holdings(context, station["station_id"])
        risk_row = risk_map.get(station["sigungu_code"])
        pressure = risk_row["risk_pressure_class"] if risk_row else "low"
        staff_reduction, engine_reduction = _risk_reduction(pressure)
        base_staff = (
            9
            if context["settlement_interface_class"] == "high"
            else 7
            if context["settlement_interface_class"] == "medium"
            else 6
        )
        for window_index, (valid_from, valid_to) in enumerate(ctx.shift_windows(), start=1):
            shift_hour = valid_from.hour
            shift_penalty = 1 if shift_hour in {8, 16} else 0
            night_penalty = 1 if shift_hour in {0, 1, 2, 3, 4, 5} else 0
            rng = _rng(ctx.seed, station["station_id"], valid_from.isoformat(), "availability")
            available_staff = max(0, base_staff + rng.randint(-1, 1) - shift_penalty - night_penalty - staff_reduction)
            available_engines = max(
                0, holdings["engine"] - engine_reduction - (1 if pressure == "severe" and rng.random() > 0.5 else 0)
            )
            available_tankers = max(
                0, holdings["water_tanker"] - (1 if pressure == "severe" and rng.random() > 0.7 else 0)
            )
            available_pumps = max(
                0, holdings["portable_pump"] - (1 if pressure in {"high", "severe"} and rng.random() > 0.65 else 0)
            )
            if available_staff <= 2 or available_engines == 0:
                resource_status = "unavailable"
            elif available_staff <= 5 or pressure in {"high", "severe"}:
                resource_status = "limited"
            else:
                resource_status = "available"
            rows.append(
                {
                    "mock_id": f"FRA-{len(rows) + 1:05d}",
                    "region_code": station["region_code"],
                    "region_name": context["region_name"],
                    "station_id": station["station_id"],
                    "station_name": station["station_name"],
                    "fire_station_name": station["fire_station_name"],
                    "station_address": station["station_address"],
                    "valid_from": valid_from.isoformat(timespec="seconds"),
                    "valid_to": valid_to.isoformat(timespec="seconds"),
                    "scenario_time": ctx.reference_time_iso,
                    "reference_time": ctx.reference_time_iso,
                    "time_mode": ctx.time_mode,
                    "run_context_id": ctx.run_id,
                    "temporal_alignment_status": ctx.temporal_alignment_status,
                    "shift_index": window_index,
                    "risk_pressure_class": pressure,
                    "available_staff": available_staff,
                    "available_engines": available_engines,
                    "available_water_tankers": available_tankers,
                    "available_portable_pumps": available_pumps,
                    "resource_status": resource_status,
                    "mock_seed": ctx.seed,
                    "mock_generated_at": ctx.mock_generated_at_iso,
                    "mock_reason": SOURCE_REASONS["SOURCE_FIRE_RESOURCE_AVAILABILITY"],
                }
            )
    return (
        rows,
        None,
        {
            "time_key_fields": ["scenario_time", "valid_from", "valid_to"],
            "space_key_fields": ["station_id"],
        },
    )


def build_prewatering_equipment_capacity(
    ctx: RunContext,
    station_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], None, dict[str, Any]]:
    context_map = _context_map(context_rows)
    sigungu_context_map = _sigungu_context_map(context_rows)
    base_specs = {
        "engine": {"watering_rate_lpm": 650, "setup_time_min": 10, "effective_width_m": 6.0},
        "water_tanker": {"watering_rate_lpm": 900, "setup_time_min": 16, "effective_width_m": 7.0},
        "small_vehicle": {"watering_rate_lpm": 260, "setup_time_min": 7, "effective_width_m": 3.5},
        "portable_pump": {"watering_rate_lpm": 180, "setup_time_min": 18, "effective_width_m": 2.0},
    }
    rows: list[dict[str, Any]] = []
    for station in station_rows:
        context = _station_context(station, context_map, sigungu_context_map)
        if not context:
            continue
        holdings = _station_holdings(context, station["station_id"])
        for equipment_type, count in holdings.items():
            if count <= 0:
                continue
            spec = dict(base_specs[equipment_type])
            if context["road_access_class"] in {"limited_road", "mountain_access"} and equipment_type in {
                "engine",
                "water_tanker",
            }:
                spec["setup_time_min"] += 4
                spec["effective_width_m"] -= 1.0
            if context["road_access_class"] == "mountain_access" and equipment_type in {
                "small_vehicle",
                "portable_pump",
            }:
                spec["setup_time_min"] = max(2, spec["setup_time_min"] - 1)
            if context["slope_class"] == "high" and equipment_type in {"engine", "water_tanker"}:
                spec["effective_width_m"] = max(1.5, spec["effective_width_m"] - 0.5)
            rows.append(
                {
                    "mock_id": f"PEC-{len(rows) + 1:05d}",
                    "region_code": station["region_code"],
                    "region_name": context["region_name"],
                    "station_id": station["station_id"],
                    "station_name": station["station_name"],
                    "equipment_id": f"{station['station_id']}-{equipment_type}",
                    "equipment_type": equipment_type,
                    "holding_count": count,
                    "valid_from": ctx.valid_from_iso,
                    "valid_to": ctx.valid_to_iso,
                    "scenario_time": ctx.reference_time_iso,
                    "reference_time": ctx.reference_time_iso,
                    "time_mode": ctx.time_mode,
                    "run_context_id": ctx.run_id,
                    "temporal_alignment_status": ctx.temporal_alignment_status,
                    "watering_rate_lpm": spec["watering_rate_lpm"],
                    "setup_time_min": spec["setup_time_min"],
                    "effective_width_m": round(spec["effective_width_m"], 1),
                    "mock_seed": ctx.seed,
                    "mock_generated_at": ctx.mock_generated_at_iso,
                    "mock_reason": SOURCE_REASONS["SOURCE_PREWATERING_EQUIPMENT_CAPACITY"],
                }
            )
    return (
        rows,
        None,
        {
            "time_key_fields": ["scenario_time", "valid_from", "valid_to"],
            "space_key_fields": ["station_id", "equipment_id"],
        },
    )


def build_surface_fuel_condition(
    ctx: RunContext,
    context_rows: list[dict[str, str]],
    live_fire_rows: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[FeatureRecord], dict[str, Any]]:
    risk_map = _sigungu_risk_map(live_fire_rows)
    rows: list[dict[str, Any]] = []
    features: list[FeatureRecord] = []
    wetting_defaults = {
        "leaf_litter": "medium",
        "dry_grass": "high",
        "shrub": "medium",
        "conifer_understory": "low",
        "roadside_fuel": "high",
    }
    for idx, context in enumerate(context_rows, start=1):
        risk_row = risk_map.get(context["sigungu_code"])
        pressure = risk_row["risk_pressure_class"] if risk_row else "low"
        forest_type = context["forest_type_class"]
        if forest_type == "urban_interface":
            surface_fuel_type = "roadside_fuel" if idx % 2 == 0 else "leaf_litter"
        elif forest_type == "mixed_hillside":
            surface_fuel_type = "dry_grass" if context["dryness_class"] == "elevated" else "shrub"
        elif forest_type == "forest_dominant":
            surface_fuel_type = "conifer_understory" if idx % 2 == 0 else "leaf_litter"
        elif forest_type == "coastal_open_mix":
            surface_fuel_type = "dry_grass"
        else:
            surface_fuel_type = "shrub"
        score = 1
        if context["dryness_class"] == "elevated":
            score += 1
        if surface_fuel_type in {"conifer_understory", "roadside_fuel"}:
            score += 1
        if pressure in {"high", "severe"}:
            score += 1
        if score >= 4:
            load_class = "high"
        elif score == 3:
            load_class = "medium"
        else:
            load_class = "low"
        size = _size_for_admin(context["admin_unit_type"]) * 0.7
        longitude = float(context["representative_longitude"])
        latitude = float(context["representative_latitude"])
        coords = _point_box(longitude, latitude, size)
        segment_id = f"SFC-{context['region_code']}"
        row = {
            "mock_id": f"SFC-{idx:05d}",
            "region_code": context["region_code"],
            "region_name": context["region_name"],
            "segment_id": segment_id,
            "valid_from": ctx.valid_from_iso,
            "valid_to": ctx.valid_to_iso,
            "scenario_time": ctx.reference_time_iso,
            "reference_time": ctx.reference_time_iso,
            "time_mode": ctx.time_mode,
            "run_context_id": ctx.run_id,
            "temporal_alignment_status": ctx.temporal_alignment_status,
            "surface_fuel_type": surface_fuel_type,
            "surface_fuel_load_class": load_class,
            "wetting_response_class": wetting_defaults[surface_fuel_type],
            "field_verified": False,
            "risk_pressure_class": pressure,
            "geometry_wkt": _polygon_wkt(coords),
            "native_crs": "EPSG:4326",
            "mock_seed": ctx.seed,
            "mock_generated_at": ctx.mock_generated_at_iso,
            "mock_reason": SOURCE_REASONS["SOURCE_SURFACE_FUEL_CONDITION"],
        }
        rows.append(row)
        features.append(
            FeatureRecord(
                feature_id=segment_id,
                geometry_type="Polygon",
                coordinates=[coords],
                properties={key: value for key, value in row.items() if key != "geometry_wkt"},
            )
        )
    return (
        rows,
        features,
        {
            "time_key_fields": ["scenario_time", "valid_from", "valid_to"],
            "space_key_fields": ["segment_id", "region_code", "geometry_wkt"],
        },
    )


def build_worksite_hazard_conditions(
    ctx: RunContext,
    context_rows: list[dict[str, str]],
    live_fire_rows: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[FeatureRecord], dict[str, Any]]:
    risk_map = _sigungu_risk_map(live_fire_rows)
    rows: list[dict[str, Any]] = []
    features: list[FeatureRecord] = []
    night_operation_flag = ctx.reference_time.hour < 6 or ctx.reference_time.hour >= 19
    for idx, context in enumerate(context_rows, start=1):
        risk_row = risk_map.get(context["sigungu_code"])
        pressure = risk_row["risk_pressure_class"] if risk_row else "low"
        rockfall_risk_flag = context["slope_class"] == "high" or context["road_access_class"] == "mountain_access"
        smoke_exposure_possible = pressure in {"high", "severe"} or (
            pressure == "moderate" and 10 <= ctx.reference_time.hour <= 18
        )
        access_constraint_flag = context["road_access_class"] in {"limited_road", "mountain_access"}
        wind_hazard_flag = context["forest_type_class"] == "coastal_open_mix" and pressure in {
            "moderate",
            "high",
            "severe",
        }
        score = (
            int(rockfall_risk_flag)
            + int(smoke_exposure_possible)
            + int(access_constraint_flag)
            + int(wind_hazard_flag)
            + int(night_operation_flag)
        )
        if score >= 4:
            hazard_severity = "high"
        elif score >= 2:
            hazard_severity = "medium"
        else:
            hazard_severity = "low"
        longitude = float(context["representative_longitude"])
        latitude = float(context["representative_latitude"])
        segment_id = f"WHC-{context['region_code']}"
        row = {
            "mock_id": f"WHC-{idx:05d}",
            "region_code": context["region_code"],
            "region_name": context["region_name"],
            "segment_id": segment_id,
            "valid_from": ctx.valid_from_iso,
            "valid_to": ctx.valid_to_iso,
            "scenario_time": ctx.reference_time_iso,
            "reference_time": ctx.reference_time_iso,
            "time_mode": ctx.time_mode,
            "run_context_id": ctx.run_id,
            "temporal_alignment_status": ctx.temporal_alignment_status,
            "rockfall_risk_flag": rockfall_risk_flag,
            "smoke_exposure_possible": smoke_exposure_possible,
            "night_operation_flag": night_operation_flag,
            "access_constraint_flag": access_constraint_flag,
            "wind_hazard_flag": wind_hazard_flag,
            "hazard_severity": hazard_severity,
            "risk_pressure_class": pressure,
            "geometry_wkt": _point_wkt(longitude, latitude),
            "native_crs": "EPSG:4326",
            "mock_seed": ctx.seed,
            "mock_generated_at": ctx.mock_generated_at_iso,
            "mock_reason": SOURCE_REASONS["SOURCE_WORKSITE_HAZARD_CONDITIONS"],
        }
        rows.append(row)
        features.append(
            FeatureRecord(
                feature_id=segment_id,
                geometry_type="Point",
                coordinates=[longitude, latitude],
                properties={key: value for key, value in row.items() if key != "geometry_wkt"},
            )
        )
    return (
        rows,
        features,
        {
            "time_key_fields": ["scenario_time", "valid_from", "valid_to"],
            "space_key_fields": ["segment_id", "region_code", "geometry_wkt"],
        },
    )


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_geojson(features: list[FeatureRecord], path: Path, source_id: str) -> None:
    payload = {
        "type": "FeatureCollection",
        "name": source_id,
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [
            {
                "type": "Feature",
                "id": feature.feature_id,
                "properties": feature.properties,
                "geometry": {
                    "type": feature.geometry_type,
                    "coordinates": feature.coordinates,
                },
            }
            for feature in features
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(
    *,
    source_id: str,
    output_path: Path,
    ctx: RunContext,
    row_count: int,
    time_key_fields: list[str],
    space_key_fields: list[str],
    files: list[str],
    live_fire_status: str | None = None,
) -> None:
    payload = {
        "source_id": source_id,
        "run_context": ctx.to_dict(),
        "row_count": row_count,
        "time_key_fields": time_key_fields,
        "space_key_fields": space_key_fields,
        "files": files,
        "not_operational_data": True,
        "mock_reason": SOURCE_REASONS[source_id],
    }
    if source_id in REGIONAL_COVERAGE_SOURCE_IDS:
        summary = coverage_summary(load_coverage_units())
        payload["coverage_summary"] = summary
        payload["coverage_result"] = "pass" if row_count == summary["coverage_unit_count"] else "partial"
    if live_fire_status is not None:
        payload["live_fire_driver_status"] = live_fire_status
    write_json(output_path, payload)
