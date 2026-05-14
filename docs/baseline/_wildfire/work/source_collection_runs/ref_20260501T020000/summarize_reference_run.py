#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "ref_20260501T020000"
REFERENCE_TIME = "2026-05-01T02:00:00+09:00"
RUN_DIR = ROOT / "work/source_collection_runs" / RUN_ID
OUT_JSON = RUN_DIR / "collection_run_summary.json"
OUT_MD = RUN_DIR / "collection_run_summary.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def csv_count(path: str | Path, encodings: tuple[str, ...] = ("utf-8-sig", "utf-8", "cp949", "euc-kr")) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    csv.field_size_limit(sys.maxsize)
    for encoding in encodings:
        try:
            with p.open(encoding=encoding, newline="") as handle:
                return sum(1 for _ in csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
        except csv.Error:
            return None
    return None


def path_exists(path: str | Path) -> bool:
    return Path(path).exists()


def load_optional_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return read_json(p)


def schema_validation(items: list[dict[str, Any]], schema_path: Path) -> tuple[bool, list[str]]:
    schema = read_json(schema_path)
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for idx, item in enumerate(items):
        source_label = item.get("source_id") or item.get("access_option_id") or f"index:{idx}"
        for error in validator.iter_errors(item):
            errors.append(f"{source_label}: {error.message}")
    return not errors, errors


def validation_checks(
    sources: list[dict[str, Any]],
    options: list[dict[str, Any]],
    dossiers: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    source_ids = {item["source_id"] for item in sources}
    option_ids = {item["access_option_id"] for item in options}
    option_by_id = {item["access_option_id"]: item for item in options}

    def add(name: str, status: str, detail: Any) -> None:
        checks.append({"check": name, "status": status, "detail": detail})

    add(
        "JSON parse",
        "PASS",
        {
            "source_inventory": len(sources),
            "source_access_options": len(options),
            "source_dossiers": len(dossiers),
        },
    )

    ok, errors = schema_validation(sources, ROOT / "schemas/source_item.schema.json")
    add("schema validation: source_item", "PASS" if ok else "FAIL", errors or f"{len(sources)} items")

    ok, errors = schema_validation(options, ROOT / "schemas/source_access_option.schema.json")
    add("schema validation: source_access_option", "PASS" if ok else "FAIL", errors or f"{len(options)} items")

    ok, errors = schema_validation(list(dossiers.values()), ROOT / "schemas/source_dossier.schema.json")
    add("schema validation: source_dossier", "PASS" if ok else "FAIL", errors or f"{len(dossiers)} dossiers")

    option_source_errors = [
        f"{item['access_option_id']} -> {item['source_id']}" for item in options if item["source_id"] not in source_ids
    ]
    source_option_errors: list[str] = []
    for source in sources:
        refs = []
        refs.extend(source.get("access_option_ids", []))
        refs.extend(source.get("candidate_access_option_ids", []))
        refs.extend(source.get("fallback_access_option_ids", []))
        if source.get("selected_access_option_id"):
            refs.append(source["selected_access_option_id"])
        for ref in refs:
            if ref and ref not in option_ids:
                source_option_errors.append(f"{source['source_id']} -> {ref}")
    add(
        "Source <-> AccessOption cross-reference",
        "PASS" if not option_source_errors and not source_option_errors else "FAIL",
        {"option_source_errors": option_source_errors, "source_option_errors": source_option_errors},
    )

    selected_errors = []
    for source in sources:
        selected = source.get("selected_access_option_id")
        if selected and selected not in option_ids:
            selected_errors.append(f"{source['source_id']} selected {selected}")
        if selected and selected in option_by_id and option_by_id[selected]["source_id"] != source["source_id"]:
            selected_errors.append(f"{source['source_id']} selected source mismatch {selected}")
    add(
        "selected_access_option_id exists",
        "PASS" if not selected_errors else "FAIL",
        selected_errors or "all selected options resolve",
    )

    real_without_option = [
        source["source_id"]
        for source in sources
        if source["availability_status"] == "REAL"
        and not (source.get("selected_access_option_id") or source.get("fallback_access_option_ids"))
    ]
    add(
        "REAL source has selected or fallback option",
        "PASS" if not real_without_option else "FAIL",
        real_without_option or "all REAL sources have acquisition options",
    )

    mock_option_errors = []
    for source in sources:
        if source["availability_status"] != "MOCK":
            continue
        selected = option_by_id.get(source.get("selected_access_option_id", ""))
        if (
            not selected
            or selected.get("acquisition_method") != "generated_mock"
            or selected.get("option_status") != "SELECTED"
        ):
            mock_option_errors.append(source["source_id"])
    add(
        "MOCK source has generated_mock selected option",
        "PASS" if not mock_option_errors else "FAIL",
        mock_option_errors or "all MOCK sources use generated_mock selected options",
    )

    exclude_dependency_errors = [
        source["source_id"]
        for source in sources
        if source["availability_status"] == "EXCLUDE"
        and (source.get("derived_outputs") or source.get("used_by_features"))
    ]
    add(
        "EXCLUDE source has no active dependency",
        "PASS" if not exclude_dependency_errors else "FAIL",
        exclude_dependency_errors or "all EXCLUDE sources have empty derived_outputs/used_by_features",
    )

    # Avoid matching SOURCE_* embedded inside ACCESS_* or DERIVED_* identifiers.
    pattern = re.compile(r"(?<![A-Z0-9_])SOURCE_[A-Z0-9_]+")
    unknown: dict[str, list[str]] = {}
    for base in (ROOT / "data/reference", ROOT / "docs"):
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".md", ".csv", ".txt"}:
                continue
            refs = set(pattern.findall(path.read_text(encoding="utf-8", errors="ignore")))
            missing = sorted(refs - source_ids - {"SOURCE_ID"})
            if missing:
                unknown[str(path.relative_to(ROOT))] = missing
    add("unknown SOURCE_* refs", "PASS" if not unknown else "FAIL", unknown or "none")

    snapshot_contract_errors = []
    for source in sources:
        storage = source.get("storage_path", "")
        sid = source["source_id"]
        if source["availability_status"] == "REAL" and "data/raw/" not in storage:
            snapshot_contract_errors.append(f"{sid}: {storage}")
        if source["availability_status"] == "MOCK" and not storage.startswith(f"data/mock/{sid}/"):
            snapshot_contract_errors.append(f"{sid}: {storage}")
    add(
        "snapshot path contract",
        "PASS" if not snapshot_contract_errors else "FAIL",
        snapshot_contract_errors or "catalog storage paths match raw/mock convention",
    )

    placeholder_url_errors = []
    bad_url_tokens = ("${", "example.com", "TODO", "placeholder")
    for source in sources:
        url = source.get("source_url", "")
        if source.get("acquisition_method") == "to_be_verified":
            continue
        if any(token.lower() in url.lower() for token in bad_url_tokens):
            placeholder_url_errors.append(f"{source['source_id']}: {url}")
    add(
        "placeholder URL",
        "PASS" if not placeholder_url_errors else "FAIL",
        placeholder_url_errors or "none in source_url fields",
    )

    six_keys = [
        "time_key_field",
        "time_parse_result",
        "space_key_field",
        "space_validation_result",
        "native_crs",
        "native_time_format",
    ]
    dossier_key_errors = [
        f"{sid}: {key}"
        for sid, dossier in dossiers.items()
        for key in six_keys
        if key not in dossier or dossier.get(key) in (None, "")
    ]
    missing_dossiers = sorted(source_ids - set(dossiers))
    non_exclude_missing = [
        sid
        for sid in missing_dossiers
        if next(source for source in sources if source["source_id"] == sid)["availability_status"] != "EXCLUDE"
    ]
    add(
        "time/space key 6-item completeness",
        "PASS" if not dossier_key_errors and not non_exclude_missing else "FAIL",
        {
            "missing_key_errors": dossier_key_errors,
            "missing_dossiers": missing_dossiers,
            "missing_dossiers_note": "missing dossier files are acceptable only for EXCLUDE sources",
        },
    )

    poc_errors = [
        sid
        for sid, dossier in dossiers.items()
        if not dossier.get("poc_coverage_result") or not dossier.get("poc_region") or not dossier.get("poc_time_window")
    ]
    add(
        "PoC coverage result recorded",
        "PASS" if not poc_errors else "FAIL",
        poc_errors or "all existing dossiers record poc_region, poc_time_window, poc_coverage_result",
    )

    return checks


def collection_results(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {
        source["source_id"]: {
            "availability_status": source["availability_status"],
            "collection_status": "excluded_not_collected"
            if source["availability_status"] == "EXCLUDE"
            else "not_collected_this_run",
            "temporal_collection_meaning": "",
            "regional_coverage_meaning": "",
            "paths": [],
            "counts": {},
            "issues": [],
        }
        for source in sources
    }

    def update(source_id: str, **values: Any) -> None:
        results[source_id].update(values)

    official_status = load_optional_json(
        ROOT
        / "data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/live_live_20260501T020000/live_fire_risk_status.json"
    )
    update(
        "SOURCE_OFFICIAL_FIRE_RISK_FORECAST",
        collection_status="collected_reference_time_live",
        temporal_collection_meaning="reference_time=02:00 KST, selected official forecast valid time is the next available 03:00 KST cycle",
        regional_coverage_meaning="sigungu rows for Gwangju 5 + Jeonnam 22",
        paths=["data/raw/SOURCE_OFFICIAL_FIRE_RISK_FORECAST/snapshots/live_live_20260501T020000/"],
        counts={
            "row_count": official_status.get("row_count"),
            "selected_valid_time_range": official_status.get("selected_valid_time_range"),
        },
    )

    api_summary = load_optional_json(RUN_DIR / "reference_time_api_collection_manifest.json")
    kma_fcst = api_summary.get("sources", {}).get("SOURCE_KMA_SHORT_TERM_FORECAST", {})
    update(
        "SOURCE_KMA_SHORT_TERM_FORECAST",
        collection_status="collected_reference_time_api",
        temporal_collection_meaning="base_date=20260501/base_time=0200; forecast valid times remain provider fcstDate/fcstTime",
        regional_coverage_meaning="623 regional anchor rows mapped to 276 unique KMA nx/ny grids",
        paths=["data/raw/SOURCE_KMA_SHORT_TERM_FORECAST/snapshots/reference_20260501T020000_gwangju_jeonnam/"],
        counts={
            "unique_grid_count": kma_fcst.get("unique_grid_count"),
            "success_count": kma_fcst.get("success_count"),
            "failed_count": kma_fcst.get("failed_count"),
        },
    )

    kma_obs_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/reference_20260501T020000_all_stations/manifest.json"
    )
    obs_path = (
        ROOT
        / "data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/reference_20260501T020000_all_stations/kma_observed_all_stations_202605010000_202605010200.txt"
    )
    data_lines = None
    if obs_path.exists():
        lines = obs_path.read_text(encoding="cp949", errors="replace").splitlines()
        data_lines = sum(1 for line in lines if line.strip() and not line.startswith("#"))
    update(
        "SOURCE_KMA_OBSERVED_WEATHER",
        collection_status="collected_reference_time_api",
        temporal_collection_meaning="observed window tm1=202605010000, tm2=202605010200 KST",
        regional_coverage_meaning="raw all-station national response retained; regional station filtering is downstream and not performed here",
        paths=["data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/reference_20260501T020000_all_stations/"],
        counts={"bytes": kma_obs_manifest.get("bytes"), "data_lines": data_lines},
    )

    warn_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_KMA_WEATHER_WARNINGS/snapshots/reference_20260501T020000/manifest.json"
    )
    update(
        "SOURCE_KMA_WEATHER_WARNINGS",
        collection_status="collected_reference_time_api",
        temporal_collection_meaning="warning history query window=2026-05-01 00:00~02:00 KST; area table tmfc=02:00",
        regional_coverage_meaning="national warning/area raw response retained for downstream regional filtering",
        paths=["data/raw/SOURCE_KMA_WEATHER_WARNINGS/snapshots/reference_20260501T020000/"],
        counts={
            item.get("label", f"request_{idx}"): item.get("bytes")
            for idx, item in enumerate(warn_manifest.get("requests", []), start=1)
        },
    )

    sun_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_SUN_EVENT_CALENDAR/snapshots/reference_20260501_gwangju_jeonnam/manifest.json"
    )
    update(
        "SOURCE_SUN_EVENT_CALENDAR",
        collection_status="collected_reference_date_api",
        temporal_collection_meaning="daily effective date locdate=20260501",
        regional_coverage_meaning="provider accepted broad place aliases; 22 Jeonnam sigungu aliases plus 광주 returned items",
        paths=["data/raw/SOURCE_SUN_EVENT_CALENDAR/snapshots/reference_20260501_gwangju_jeonnam/"],
        counts={
            "original_location_count": sun_manifest.get("location_count"),
            "expanded_location_item_count": sun_manifest.get("expanded_location_item_count"),
        },
        issues=[
            "행정명 with 시/군 suffix mostly returned no item; alias responses are preserved separately as sun_event_alias_*.xml"
        ],
    )

    update(
        "SOURCE_ADMIN_BOUNDARIES",
        collection_status="collected_static_latest",
        temporal_collection_meaning="static/admin registry snapshot; no instant-time query exists for 02:00",
        regional_coverage_meaning="622 legal EMD polygons in raw boundary CSV; runtime coverage anchor has 623 rows with explicit fallback for code gaps",
        paths=["data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/"],
        counts={"region_feature_count": 622},
    )
    update(
        "SOURCE_REGION_CODE_TABLE",
        collection_status="collected_static_latest",
        temporal_collection_meaning="legal/admin code registry latest files captured",
        regional_coverage_meaning="Gwangju/Jeonnam legal and KOSTAT admin code tables retained",
        paths=["data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/"],
        counts={
            "legal_dong_gwangju_jeonnam_rows": csv_count(
                ROOT / "data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/national_legal_dong_gwangju_jeonnam.csv",
                ("utf-8-sig", "cp949"),
            ),
            "kostat_admin_dong_gwangju_jeonnam_rows": csv_count(
                ROOT / "data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/kostat_admin_dong_gwangju_jeonnam.csv",
                ("cp949", "utf-8-sig"),
            ),
        },
    )
    update(
        "SOURCE_LARGE_FIRE_RISK_FORECAST",
        collection_status="collected_file_latest",
        temporal_collection_meaning="provider exposes downloadable file snapshot, not arbitrary 02:00 backfill",
        regional_coverage_meaning="full CSV retained for downstream region filtering",
        paths=["data/raw/SOURCE_LARGE_FIRE_RISK_FORECAST/snapshots/reference_20260501T020000_file/"],
        counts={
            "row_count": csv_count(
                ROOT
                / "data/raw/SOURCE_LARGE_FIRE_RISK_FORECAST/snapshots/reference_20260501T020000_file/large_fire_risk_forecast_20260331.csv",
                ("cp949", "utf-8-sig"),
            )
        },
    )

    building_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_BUILDING_FOOTPRINTS/snapshots/full_gwangju_jeonnam_20260430/manifest.json"
    )
    update(
        "SOURCE_BUILDING_FOOTPRINTS",
        collection_status="collected_static_wfs_full_region",
        temporal_collection_meaning="VWorld WFS current layer capture; no provider-native historical 02:00 query",
        regional_coverage_meaning="622 legal EMD bboxes processed; no failed tiles",
        paths=["data/raw/SOURCE_BUILDING_FOOTPRINTS/snapshots/full_gwangju_jeonnam_20260430/"],
        counts={
            "admin_emd_count": building_manifest.get("admin_emd_count"),
            "features_written": building_manifest.get("features_written"),
            "count_requests": building_manifest.get("count_requests"),
            "fetch_requests": building_manifest.get("fetch_requests"),
            "overflow_tiles": len(building_manifest.get("overflow_tiles", [])),
            "failed_tiles": len(building_manifest.get("failed_tiles", [])),
        },
    )

    heritage_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_HERITAGE_SPATIAL/snapshots/full_gwangju_jeonnam_20260430/manifest.json"
    )
    update(
        "SOURCE_HERITAGE_SPATIAL",
        collection_status="collected_static_featureserver_full_region",
        temporal_collection_meaning="current ArcGIS FeatureServer capture",
        regional_coverage_meaning="query where 시도명 IN ('광주광역시','전라남도')",
        paths=["data/raw/SOURCE_HERITAGE_SPATIAL/snapshots/full_gwangju_jeonnam_20260430/"],
        counts={
            "total_feature_count": heritage_manifest.get("total_feature_count"),
            "layer_feature_counts": {
                key: value.get("feature_count") for key, value in heritage_manifest.get("layers", {}).items()
            },
        },
    )

    public_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_PUBLIC_FACILITIES/snapshots/full_gwangju_jeonnam_20260430/manifest.json"
    )
    update(
        "SOURCE_PUBLIC_FACILITIES",
        collection_status="collected_static_file_and_api",
        temporal_collection_meaning="file datasets use each provider's latest data 기준일; HIRA/school APIs are current responses",
        regional_coverage_meaning="Gwangju/Jeonnam public health files plus HIRA hospital pages retained",
        paths=["data/raw/SOURCE_PUBLIC_FACILITIES/snapshots/full_gwangju_jeonnam_20260430/"],
        counts={
            "file_rows": {item["label"]: item.get("row_count") for item in public_manifest.get("file_datasets", [])},
            "api_counts": {
                item["label"]: item.get("total_count") or item.get("api_result_msg") or item.get("status")
                for item in public_manifest.get("api_captures", [])
            },
        },
        issues=["school_locations_gwangju/jeonnam returned NODATA_ERROR with current address filter"],
    )

    vulnerable_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_VULNERABLE_FACILITIES/snapshots/full_gwangju_jeonnam_20260430/manifest.json"
    )
    vulnerable_mock = load_optional_json(
        ROOT / "data/mock/SOURCE_VULNERABLE_FACILITIES/scenario_baseline/manifest.json"
    )
    update(
        "SOURCE_VULNERABLE_FACILITIES",
        collection_status="collected_real_with_mock_fallback",
        temporal_collection_meaning="real files use provider 기준일; unavailable Jeonnam elderly welfare API fallback is scenario_time=2026-05-01T02:00",
        regional_coverage_meaning="real Gwangju/Jeonnam facility files plus generated Jeonnam elderly-welfare fallback",
        paths=[
            "data/raw/SOURCE_VULNERABLE_FACILITIES/snapshots/full_gwangju_jeonnam_20260430/",
            "data/mock/SOURCE_VULNERABLE_FACILITIES/scenario_baseline/",
        ],
        counts={
            "real_file_rows": {
                item["label"]: item.get("row_count") for item in vulnerable_manifest.get("file_datasets", [])
            },
            "api_status": {
                item["label"]: item.get("http_status") or item.get("status")
                for item in vulnerable_manifest.get("api_captures", [])
            },
            "jeonnam_mock_row_count": vulnerable_mock.get("jeonnam_mock_row_count"),
        },
        issues=["Jeonnam elderly welfare OpenAPI functions returned HTTP 404; generated mock fallback created"],
    )

    update(
        "SOURCE_POPULATION_STATISTICS",
        collection_status="existing_monthly_full_region_snapshot_validated",
        temporal_collection_meaning="resident registry monthly 기준연월=2026-03-31; not real-time at 02:00",
        regional_coverage_meaning="Gwangju 96 + Jeonnam 323 administrative dong rows in both age/gender and household-size files",
        paths=["data/raw/SOURCE_POPULATION_STATISTICS/snapshots/full_gwangju_jeonnam_20260331/"],
        counts={
            "age_gender_rows": csv_count(
                ROOT
                / "data/raw/SOURCE_POPULATION_STATISTICS/snapshots/full_gwangju_jeonnam_20260331/age_gender_haengjeongdong_gj_jn_20260331.csv",
                ("cp949", "utf-8-sig"),
            ),
            "household_size_rows": csv_count(
                ROOT
                / "data/raw/SOURCE_POPULATION_STATISTICS/snapshots/full_gwangju_jeonnam_20260331/household_size_haengjeongdong_gj_jn_20260331.csv",
                ("cp949", "utf-8-sig"),
            ),
        },
    )

    road_coverage = load_optional_json(
        ROOT / "data/raw/SOURCE_ROAD_NETWORK/snapshots/full/region_coverage_assessment.json"
    )
    update(
        "SOURCE_ROAD_NETWORK",
        collection_status="existing_manual_full_national_snapshot",
        temporal_collection_meaning="static road-network package dated by source archive, not a 02:00 API",
        regional_coverage_meaning=road_coverage.get("assessment_result", "full national raw package retained"),
        paths=["data/raw/SOURCE_ROAD_NETWORK/snapshots/full/"],
        counts=road_coverage.get("coverage_unit_summary", {}),
        issues=["no routing, clipping, road-width inference, travel-time calculation, or spatial join performed"],
    )

    forest_stand_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_FOREST_STAND_MAP/snapshots/full_gwangju_jeonnam_20260430/manifest.json"
    )
    if forest_stand_manifest:
        update(
            "SOURCE_FOREST_STAND_MAP",
            collection_status="collected_manual_archive_pipeline_full_region",
            temporal_collection_meaning="manual FGIS SHP archives promoted to full regional static snapshot; latest vintage=2025",
            regional_coverage_meaning="Gwangju and Jeonnam sido-level FGIS forest-stand extracts are both registered",
            paths=["data/raw/SOURCE_FOREST_STAND_MAP/snapshots/full_gwangju_jeonnam_20260430/"],
            counts={
                "latest_vintage": forest_stand_manifest.get("latest_vintage"),
                "latest_vintage_feature_count_total": forest_stand_manifest.get("latest_vintage_feature_count_total"),
                "coverage_result": forest_stand_manifest.get("coverage_result"),
            },
        )
    else:
        update(
            "SOURCE_FOREST_STAND_MAP",
            collection_status="manual_source_sample_only",
            temporal_collection_meaning="manual/static forest stand layer; no automated full-region run available in repo",
            regional_coverage_meaning="not proven full Gwangju/Jeonnam in current run",
            paths=["data/raw/SOURCE_FOREST_STAND_MAP/snapshots/sample_20260430/"],
            issues=["full regional forest stand snapshot still requires manual acquisition"],
        )

    forest_road_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/full_gwangju_jeonnam_20260430/manifest.json"
    )
    if forest_road_manifest:
        update(
            "SOURCE_FOREST_ROAD_NETWORK",
            collection_status="collected_manual_archive_pipeline_with_no_data_evidence",
            temporal_collection_meaning="manual FGIS SHP archive promoted to full regional static snapshot; Gwangju no-data evidence recorded",
            regional_coverage_meaning="Jeonnam forest-road extract registered; Gwangju recorded as no-data for this FGIS layer",
            paths=["data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/full_gwangju_jeonnam_20260430/"],
            counts={
                "feature_count_total": forest_road_manifest.get("feature_count_total"),
                "coverage_result": forest_road_manifest.get("coverage_result"),
            },
            issues=[
                "Gwangju has no FGIS forest-road line data in the recorded acquisition flow; no synthetic road lines were generated"
            ],
        )
    else:
        update(
            "SOURCE_FOREST_ROAD_NETWORK",
            collection_status="manual_source_sample_only",
            temporal_collection_meaning="manual/static forest road layer; no automated full-region run available in repo",
            regional_coverage_meaning="not proven full Gwangju/Jeonnam in current run",
            paths=["data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/sample_20260430/"],
            issues=["full regional forest road snapshot still requires manual acquisition"],
        )

    extinguishing_manifest = load_optional_json(
        ROOT / "data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/full/manifest.json"
    )
    update(
        "SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES",
        collection_status="existing_real_plus_generated_coverage_supplement",
        temporal_collection_meaning="official CSV registry plus reference-time mock supplement valid_from=2026-05-01T02:00",
        regional_coverage_meaning="official rows cover Jeonnam 13 and Gwangju 0; generated supplement covers 623 coverage units",
        paths=[
            "data/raw/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/snapshots/full/",
            "data/mock/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/runs/live_20260501T020000/",
        ],
        counts={
            "official_full_row_count": extinguishing_manifest.get("row_count"),
            "official_gwangju_jeonnam_row_count": extinguishing_manifest.get("gwangju_jeonnam_row_count"),
            "supplement_rows": csv_count(
                ROOT
                / "data/mock/SOURCE_FOREST_FIRE_EXTINGUISHING_FACILITIES/runs/live_20260501T020000/forest_fire_extinguishing_facilities_coverage_supplement.csv"
            ),
        },
        issues=["regional full coverage depends on generated supplement, not official point coverage"],
    )

    station_rows = csv_count(
        ROOT / "data/raw/SOURCE_FIRE_STATION_CENTERS/snapshots/full/source_fire_station_centers_20250701.csv",
        ("cp949", "utf-8-sig"),
    )
    update(
        "SOURCE_FIRE_STATION_CENTERS",
        collection_status="collected_static_latest",
        temporal_collection_meaning="registry snapshot, not real-time availability",
        regional_coverage_meaning="national center registry retained; Gwangju/Jeonnam rows are filterable by 시도본부",
        paths=["data/raw/SOURCE_FIRE_STATION_CENTERS/snapshots/full/"],
        counts={"national_rows": station_rows, "gwangju_rows": 27, "jeonnam_rows": 68},
    )

    mock_csvs = {
        "SOURCE_FIRE_RESOURCE_AVAILABILITY": "data/mock/SOURCE_FIRE_RESOURCE_AVAILABILITY/runs/live_20260501T020000/fire_resource_availability_mock.csv",
        "SOURCE_PREWATERING_EQUIPMENT_CAPACITY": "data/mock/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/runs/live_20260501T020000/prewatering_equipment_capacity_mock.csv",
        "SOURCE_SURFACE_FUEL_CONDITION": "data/mock/SOURCE_SURFACE_FUEL_CONDITION/runs/live_20260501T020000/surface_fuel_condition_mock.csv",
        "SOURCE_WORKSITE_HAZARD_CONDITIONS": "data/mock/SOURCE_WORKSITE_HAZARD_CONDITIONS/runs/live_20260501T020000/worksite_hazard_conditions_mock.csv",
        "SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES": "data/mock/SOURCE_MUNICIPAL_FIRE_WATER_FACILITIES/runs/live_20260501T020000/municipal_fire_water_facilities.csv",
        "SOURCE_ROAD_ACCESS_CONSTRAINTS": "data/mock/SOURCE_ROAD_ACCESS_CONSTRAINTS/runs/live_20260501T020000/road_access_constraints.csv",
    }
    for sid, rel_path in mock_csvs.items():
        update(
            sid,
            collection_status="generated_reference_time_mock",
            temporal_collection_meaning="scenario/live mock valid_from=2026-05-01T02:00; valid_to typically 2026-05-04T02:00",
            regional_coverage_meaning="generated for Gwangju/Jeonnam coverage anchors; synthetic values are not official observations",
            paths=[str(Path(rel_path).parent) + "/"],
            counts={"row_count": csv_count(ROOT / rel_path)},
        )

    # EXCLUDE rows: make the reason explicit.
    for sid in [
        "SOURCE_DEM_ELEVATION",
        "SOURCE_SETTLEMENT_BOUNDARIES",
        "SOURCE_CRITICAL_INFRASTRUCTURE_DETAIL",
        "SOURCE_NATURAL_WATER_SOURCES",
        "SOURCE_NATURAL_BARRIERS",
    ]:
        update(
            sid,
            collection_status="excluded_not_collected",
            temporal_collection_meaning="catalog EXCLUDE; not part of current active source collection",
            regional_coverage_meaning="no active Feature/Derived dependency in source inventory",
            paths=[],
        )

    return results


def main() -> None:
    sources: list[dict[str, Any]] = read_json(ROOT / "data/reference/source_inventory.json")
    options: list[dict[str, Any]] = read_json(ROOT / "data/reference/source_access_options.json")
    dossiers: dict[str, dict[str, Any]] = {
        path.stem: read_json(path) for path in sorted((ROOT / "data/reference/source_dossiers").glob("SOURCE_*.json"))
    }

    results = collection_results(sources)
    validation = validation_checks(sources, options, dossiers)
    status_counts = Counter(item["collection_status"] for item in results.values())
    availability_counts = Counter(source["availability_status"] for source in sources)

    hard_gaps = [
        sid
        for sid, item in results.items()
        if item["collection_status"] in {"manual_source_sample_only", "not_collected_this_run"}
    ]
    fallback_or_partial = [
        sid
        for sid, item in results.items()
        if item["collection_status"]
        in {
            "collected_real_with_mock_fallback",
            "existing_real_plus_generated_coverage_supplement",
        }
        or item.get("issues")
    ]

    if hard_gaps:
        completeness_reason = (
            "Most API/static/file/WFS and all generated MOCK snapshots were collected, but some sources remain "
            "sample-only or not collected in this workspace."
        )
    else:
        completeness_reason = (
            "No hard source-collection gaps remain after the remaining-gap pipelines. Full actual collection is still "
            "not marked complete because some provider responses require no-data evidence, generated fallback, or "
            "coverage supplement handling rather than pure official regional data."
        )

    summary = {
        "run_id": RUN_ID,
        "reference_time": REFERENCE_TIME,
        "region_scope": "광주광역시·전라남도",
        "phase": "Source snapshot collection/verification only",
        "guardrails": [
            "no Clean Zone transformation",
            "no CRS normalization",
            "no time grid alignment",
            "no spatial join",
            "no Feature/Signal calculation",
        ],
        "catalog_counts": {
            "sources": len(sources),
            "access_options": len(options),
            "source_dossiers": len(dossiers),
            "availability": dict(availability_counts),
        },
        "collection_status_counts": dict(status_counts),
        "validation_checks": validation,
        "regional_completeness_assessment": {
            "full_actual_collection_complete": False,
            "reason": completeness_reason,
            "hard_gaps": hard_gaps,
            "fallback_or_partial_sources": fallback_or_partial,
        },
        "source_results": results,
    }
    write_json(OUT_JSON, summary)

    lines = [
        "# Reference-time collection summary",
        "",
        f"- run_id: `{RUN_ID}`",
        f"- reference_time: `{REFERENCE_TIME}`",
        "- scope: `광주광역시·전라남도`",
        "- phase: Source snapshot collection only; no Clean Zone, CRS normalization, time-grid alignment, spatial join, or Feature/Signal calculation.",
        "",
        "## Catalog / validation",
        "",
    ]
    for check in validation:
        lines.append(f"- {check['check']}: **{check['status']}**")
    lines.extend(
        [
            "",
            "## Completeness assessment",
            "",
            "- Full actual collection complete: **NO**",
            "- Main hard gaps: "
            + (", ".join(f"`{sid}`" for sid in hard_gaps) if hard_gaps else "**none after remaining-gap pipelines**"),
            "- Important fallback/partial cases: vulnerable facilities Jeonnam elderly welfare API 404 -> mock fallback; forest fire extinguishing facilities official regional rows are sparse -> generated supplement; public school location API returned NODATA for current filters.",
            "",
            "## Source results",
            "",
            "| source_id | status | counts | issue |",
            "|---|---|---:|---|",
        ]
    )
    for sid in sorted(results):
        item = results[sid]
        counts = json.dumps(item.get("counts", {}), ensure_ascii=False, separators=(",", ":"))
        if len(counts) > 120:
            counts = counts[:117] + "..."
        issue = "; ".join(item.get("issues", []))
        lines.append(f"| `{sid}` | {item['collection_status']} | `{counts}` | {issue} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"summary": str(OUT_JSON), "markdown": str(OUT_MD), "status_counts": dict(status_counts)},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
