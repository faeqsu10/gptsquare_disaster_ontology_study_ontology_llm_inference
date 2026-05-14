from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

KST = timezone(timedelta(hours=9))
DEFAULT_SCENARIO_REFERENCE_TIME = datetime(2026, 4, 15, 0, 0, tzinfo=KST)
DEFAULT_SCENARIO_HORIZON_HOURS = 168
DEFAULT_RUNTIME_HORIZON_HOURS = 72
DEFAULT_SHIFT_HOURS = 8
DEFAULT_SEED = 20260501

FIRE_RISK_ANALYSIS_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)
FIRE_RISK_VALID_HOURS = (0, 3, 6, 9, 12, 15, 18, 21)
KMA_FORECAST_BASE_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)

SOURCE_CYCLE_POLICIES = [
    {
        "source_id": "SOURCE_FIRE_STATION_CENTERS",
        "lifecycle_class": "static_anchor",
        "refresh_cycle": "annual or registry refresh",
        "time_key_semantics": "registry_updated_at",
        "runtime_role": "station master anchor",
        "required_env_vars": [],
    },
    {
        "source_id": "SOURCE_FIRE_RESOURCE_AVAILABILITY",
        "lifecycle_class": "runtime_mock_overlay",
        "refresh_cycle": "recomputed per run_context and shift window",
        "time_key_semantics": "valid_from / valid_to",
        "runtime_role": "runtime overlay",
        "required_env_vars": [],
    },
    {
        "source_id": "SOURCE_PREWATERING_EQUIPMENT_CAPACITY",
        "lifecycle_class": "runtime_mock_overlay",
        "refresh_cycle": "recomputed per run_context",
        "time_key_semantics": "scenario_time / valid window",
        "runtime_role": "runtime overlay",
        "required_env_vars": [],
    },
    {
        "source_id": "SOURCE_SURFACE_FUEL_CONDITION",
        "lifecycle_class": "runtime_mock_overlay",
        "refresh_cycle": "recomputed per run_context with regional profile",
        "time_key_semantics": "scenario_time / valid window",
        "runtime_role": "runtime overlay",
        "required_env_vars": [],
    },
    {
        "source_id": "SOURCE_WORKSITE_HAZARD_CONDITIONS",
        "lifecycle_class": "runtime_mock_overlay",
        "refresh_cycle": "recomputed per run_context with live risk pressure",
        "time_key_semantics": "scenario_time / valid window",
        "runtime_role": "runtime overlay",
        "required_env_vars": [],
    },
    {
        "source_id": "SOURCE_OFFICIAL_FIRE_RISK_FORECAST",
        "lifecycle_class": "live_driver",
        "refresh_cycle": "3-hour forecast horizon, 72 hours",
        "time_key_semantics": "forecast_valid_time",
        "runtime_role": "live pressure driver",
        "required_env_vars": ["DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY"],
    },
    {
        "source_id": "SOURCE_KMA_SHORT_TERM_FORECAST",
        "lifecycle_class": "live_driver",
        "refresh_cycle": "8 issuances/day, hourly forecast",
        "time_key_semantics": "forecast_issued_at / forecast_valid_time",
        "runtime_role": "future weather driver",
        "required_env_vars": ["KMA_DATA_GO_KR_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY"],
    },
    {
        "source_id": "SOURCE_KMA_OBSERVED_WEATHER",
        "lifecycle_class": "live_driver",
        "refresh_cycle": "hourly",
        "time_key_semantics": "observed_at",
        "runtime_role": "observed weather driver",
        "required_env_vars": ["KMA_APIHUB_AUTH_KEY", "APIHUB_AUTH_KEY"],
    },
    {
        "source_id": "SOURCE_KMA_WEATHER_WARNINGS",
        "lifecycle_class": "live_driver",
        "refresh_cycle": "event-driven",
        "time_key_semantics": "effective_period / event_occurred_at",
        "runtime_role": "warning driver",
        "required_env_vars": ["KMA_APIHUB_AUTH_KEY", "APIHUB_AUTH_KEY"],
    },
    {
        "source_id": "SOURCE_SUN_EVENT_CALENDAR",
        "lifecycle_class": "daily_reference",
        "refresh_cycle": "daily",
        "time_key_semantics": "effective_period",
        "runtime_role": "daylight reference",
        "required_env_vars": ["KASI_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY"],
    },
]


def parse_reference_time(raw: str | None, *, mode: str) -> datetime:
    if raw:
        text = raw.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return dt.astimezone(KST)
    if mode == "scenario":
        return DEFAULT_SCENARIO_REFERENCE_TIME
    return datetime.now(KST)


def floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def align_shift_start(dt: datetime, shift_hours: int) -> datetime:
    hour = (dt.hour // shift_hours) * shift_hours
    return dt.replace(hour=hour, minute=0, second=0, microsecond=0)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def env_available(names: list[str]) -> bool:
    return any(os.getenv(name) for name in names)


def most_recent_cycle(reference_time: datetime, cycle_hours: tuple[int, ...]) -> datetime:
    candidate = reference_time.replace(minute=0, second=0, microsecond=0)
    while candidate.hour not in cycle_hours:
        candidate -= timedelta(hours=1)
    return candidate


def next_cycle(reference_time: datetime, cycle_hours: tuple[int, ...]) -> datetime:
    candidate = reference_time.replace(minute=0, second=0, microsecond=0)
    while candidate.hour not in cycle_hours:
        candidate += timedelta(hours=1)
    return candidate


@dataclass(frozen=True)
class RunContext:
    mode: str
    reference_time: datetime
    valid_from: datetime
    valid_to: datetime
    horizon_hours: int
    shift_hours: int
    seed: int
    scenario_name: str
    run_id: str
    mock_generated_at: datetime

    @property
    def reference_time_iso(self) -> str:
        return iso(self.reference_time)

    @property
    def valid_from_iso(self) -> str:
        return iso(self.valid_from)

    @property
    def valid_to_iso(self) -> str:
        return iso(self.valid_to)

    @property
    def mock_generated_at_iso(self) -> str:
        return iso(self.mock_generated_at)

    @property
    def time_mode(self) -> str:
        return self.mode

    @property
    def temporal_alignment_status(self) -> str:
        return "aligned"

    def shift_windows(self) -> list[tuple[datetime, datetime]]:
        windows: list[tuple[datetime, datetime]] = []
        cursor = align_shift_start(self.valid_from, self.shift_hours)
        while cursor < self.valid_to:
            end = cursor + timedelta(hours=self.shift_hours)
            clipped_start = max(cursor, self.valid_from)
            clipped_end = min(end, self.valid_to)
            if clipped_start < clipped_end:
                windows.append((clipped_start, clipped_end))
            cursor = end
        return windows

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_context_id": self.run_id,
            "mode": self.mode,
            "reference_time": self.reference_time_iso,
            "valid_from": self.valid_from_iso,
            "valid_to": self.valid_to_iso,
            "horizon_hours": self.horizon_hours,
            "shift_hours": self.shift_hours,
            "scenario_name": self.scenario_name,
            "seed": self.seed,
            "mock_generated_at": self.mock_generated_at_iso,
            "temporal_alignment_policy": "shared_reference_time",
            "temporal_alignment_status": self.temporal_alignment_status,
            "region_scope": "광주광역시·전라남도",
        }


def build_run_context(
    *,
    mode: str,
    reference_time_text: str | None = None,
    horizon_hours: int | None = None,
    shift_hours: int = DEFAULT_SHIFT_HOURS,
    seed: int = DEFAULT_SEED,
    scenario_name: str | None = None,
) -> RunContext:
    reference_time = parse_reference_time(reference_time_text, mode=mode)
    valid_from = floor_to_hour(reference_time)
    if horizon_hours is None:
        horizon_hours = DEFAULT_SCENARIO_HORIZON_HOURS if mode == "scenario" else DEFAULT_RUNTIME_HORIZON_HOURS
    valid_to = valid_from + timedelta(hours=horizon_hours)
    mock_generated_at = datetime.now(KST)
    run_id = f"{mode}_{valid_from:%Y%m%dT%H%M%S}"
    final_scenario_name = scenario_name or f"{mode}_gwangju_jeonnam_runtime"
    return RunContext(
        mode=mode,
        reference_time=reference_time,
        valid_from=valid_from,
        valid_to=valid_to,
        horizon_hours=horizon_hours,
        shift_hours=shift_hours,
        seed=seed,
        scenario_name=final_scenario_name,
        run_id=run_id,
        mock_generated_at=mock_generated_at,
    )


def add_run_context_arguments(
    parser: argparse.ArgumentParser,
    *,
    default_mode: str = "scenario",
    default_scenario_name: str = "scenario_baseline",
    default_seed: int = DEFAULT_SEED,
) -> None:
    parser.add_argument("--mode", choices=["scenario", "live", "hybrid"], default=default_mode)
    parser.add_argument(
        "--reference-time", default=None, help="ISO8601 KST reference time. Omit to use default per mode."
    )
    parser.add_argument("--horizon-hours", type=int, default=None)
    parser.add_argument("--shift-hours", type=int, default=DEFAULT_SHIFT_HOURS)
    parser.add_argument("--seed", type=int, default=default_seed)
    parser.add_argument("--scenario-name", default=default_scenario_name)


def run_context_from_args(args: argparse.Namespace) -> RunContext:
    return build_run_context(
        mode=args.mode,
        reference_time_text=args.reference_time,
        horizon_hours=args.horizon_hours,
        shift_hours=args.shift_hours,
        seed=args.seed,
        scenario_name=args.scenario_name,
    )


def build_source_cycle_status(reference_time: datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    official_cycle = most_recent_cycle(reference_time, FIRE_RISK_ANALYSIS_HOURS)
    official_next_valid = next_cycle(reference_time, FIRE_RISK_VALID_HOURS)
    kma_cycle = most_recent_cycle(reference_time, KMA_FORECAST_BASE_HOURS)
    observed_cycle = floor_to_hour(reference_time)
    for policy in SOURCE_CYCLE_POLICIES:
        row = dict(policy)
        row["reference_time"] = iso(reference_time)
        row["env_ready"] = env_available(policy["required_env_vars"])
        if policy["source_id"] == "SOURCE_OFFICIAL_FIRE_RISK_FORECAST":
            row["current_cycle_hint"] = {
                "latest_analysis_cycle": iso(official_cycle),
                "selected_valid_cycle": iso(official_next_valid),
            }
        elif policy["source_id"] == "SOURCE_KMA_SHORT_TERM_FORECAST":
            row["current_cycle_hint"] = {
                "latest_base_cycle": iso(kma_cycle),
            }
        elif policy["source_id"] == "SOURCE_KMA_OBSERVED_WEATHER":
            row["current_cycle_hint"] = {
                "latest_observation_hour": iso(observed_cycle),
            }
        elif policy["source_id"] == "SOURCE_SUN_EVENT_CALENDAR":
            row["current_cycle_hint"] = {
                "effective_date": reference_time.strftime("%Y-%m-%d"),
            }
        else:
            row["current_cycle_hint"] = {}
        rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
