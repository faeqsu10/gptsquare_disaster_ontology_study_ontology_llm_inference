#!/usr/bin/env python3
"""Generate Jeonnam elderly-welfare vulnerable-facility mock baseline.

The real Jeonnam API remains unavailable in this session. This generator
creates a deterministic API-shaped baseline for the missing five elderly
welfare classes while preserving the existing real Gwangju snapshot.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from shapely import wkb
from shapely.geometry import Point, mapping
from shapely.validation import make_valid

SOURCE_ID = "SOURCE_VULNERABLE_FACILITIES"
OUT_DIR = Path("data/mock") / SOURCE_ID / "scenario_baseline"
REGION_CODE_PATH = Path("data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/national_legal_dong_gwangju_jeonnam.csv")
ADMIN_BOUNDARY_PATH = Path("data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/LP_AA_EMD_gwangju_jeonnam.csv")
REAL_SNAPSHOT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / "full_gwangju_jeonnam_20260430"

SCENARIO_ID = "scenario_baseline"
SCENARIO_TIME = "2026-05-01T02:00:00+09:00"
VALID_FROM = "2026-05-01T02:00:00+09:00"
VALID_TO = "2026-05-04T02:00:00+09:00"
GENERATED_AT = "2026-05-01T02:00:00+09:00"
SEED = 20260501

API_SOURCE_URL = "https://www.data.go.kr/data/15102882/openapi.do"
API_ENDPOINT = "https://apis.data.go.kr/6460000/jnOldManWelfare"

JOBS = [
    {
        "label": "jeonnam_elderly_welfare_type1",
        "function_name": "getJnOldManWelfare1List",
        "facility_scope": "노인양로복지시설",
        "file_suffix": "type1",
    },
    {
        "label": "jeonnam_elderly_welfare_type2",
        "function_name": "getJnOldManWelfare2List",
        "facility_scope": "노인의료복지시설",
        "file_suffix": "type2",
    },
    {
        "label": "jeonnam_elderly_welfare_type3",
        "function_name": "getJnOldManWelfare3List",
        "facility_scope": "노인여가복지시설",
        "file_suffix": "type3",
    },
    {
        "label": "jeonnam_elderly_welfare_type4",
        "function_name": "getJnOldManWelfare4List",
        "facility_scope": "경로당",
        "file_suffix": "type4",
    },
    {
        "label": "jeonnam_elderly_welfare_type5",
        "function_name": "getJnOldManWelfare5List",
        "facility_scope": "노인보호전문기관",
        "file_suffix": "type5",
    },
]

FIELDNAMES = [
    "mock_id",
    "apiSeq",
    "api_function",
    "facility_scope",
    "source_region",
    "city",
    "emd_code",
    "emd_name",
    "name",
    "location",
    "tel",
    "fax",
    "installDate",
    "institution",
    "manager",
    "residentAllcnt",
    "residentNowcnt",
    "posX",
    "posY",
    "scenario_id",
    "scenario_time",
    "valid_from",
    "valid_to",
    "space_key",
    "mock_source",
    "coordinate_semantics",
    "address_semantics",
    "native_crs",
]

API_FIELD_ORDER = [
    "apiSeq",
    "city",
    "fax",
    "installDate",
    "institution",
    "location",
    "manager",
    "name",
    "posX",
    "posY",
    "tel",
    "residentAllcnt",
    "residentNowcnt",
    "spaceKey",
    "scenarioTime",
    "validFrom",
    "validTo",
    "mockSource",
    "coordinateSemantics",
]

SIGUNGU_PRIORITY = {
    "목포시": 4,
    "여수시": 5,
    "순천시": 5,
    "나주시": 3,
    "광양시": 3,
    "무안군": 2,
    "해남군": 2,
    "화순군": 2,
}


def read_csv(path: Path, encoding: str) -> list[dict[str, str]]:
    csv.field_size_limit(sys.maxsize)
    with path.open(encoding=encoding, newline="") as fh:
        return list(csv.DictReader(fh))


def load_emd_rows() -> list[dict[str, Any]]:
    legal_rows = read_csv(REGION_CODE_PATH, "utf-8-sig")
    code_to_admin: dict[str, dict[str, str]] = {}
    for row in legal_rows:
        if row["삭제일자"] or row["시도명"] not in ("광주광역시", "전라남도"):
            continue
        if not row["시군구명"] or not row["읍면동명"] or row["리명"]:
            continue
        emd_code = row["법정동코드"][:8]
        code_to_admin[emd_code] = {
            "sido": row["시도명"],
            "sigungu": row["시군구명"],
            "emd_name": row["읍면동명"],
        }

    boundary_rows = read_csv(ADMIN_BOUNDARY_PATH, "cp949")
    emds: list[dict[str, Any]] = []
    for boundary in boundary_rows:
        emd_code = boundary["읍면동코드"]
        admin = code_to_admin.get(emd_code)
        if not admin:
            continue
        geom = wkb.loads(boundary["공간정보"], hex=True)
        if not geom.is_valid:
            geom = make_valid(geom)
        if geom.is_empty:
            continue
        point = geom.representative_point()
        emds.append(
            {
                "emd_code": emd_code,
                "sido": admin["sido"],
                "sigungu": admin["sigungu"],
                "emd_name": admin["emd_name"],
                "geometry": geom,
                "base_lon": point.x,
                "base_lat": point.y,
            }
        )
    emds.sort(key=lambda item: (item["sido"], item["sigungu"], item["emd_code"]))
    return emds


def count_rows(path: Path, encoding: str) -> int | None:
    if not path.exists():
        return None
    try:
        return len(read_csv(path, encoding))
    except Exception:
        return None


def synthetic_point(emd: dict[str, Any], rng: random.Random) -> Point:
    geom = emd["geometry"]
    minx, miny, maxx, maxy = geom.bounds
    for _ in range(40):
        lon = rng.uniform(minx, maxx)
        lat = rng.uniform(miny, maxy)
        point = Point(lon, lat)
        try:
            if geom.contains(point):
                return point
        except Exception:
            break
    return geom.representative_point()


def phone_for(sigungu: str, seq: int) -> str:
    if sigungu in {"목포시", "무안군", "신안군", "영암군", "해남군", "진도군", "완도군"}:
        prefix = "061-27"
    elif sigungu in {"여수시", "순천시", "광양시", "구례군", "보성군", "고흥군"}:
        prefix = "061-74"
    elif sigungu in {"나주시", "화순군", "담양군", "장성군", "함평군", "영광군"}:
        prefix = "061-33"
    else:
        prefix = "061-43"
    return f"{prefix}{seq % 10}-{1000 + (seq * 37) % 9000:04d}"


def install_date(seq: int) -> str:
    year = 1998 + (seq * 7) % 27
    month = 1 + (seq * 5) % 12
    day = 1 + (seq * 11) % 26
    return date(year, month, day).isoformat()


def capacity_for(scope: str, seq: int) -> tuple[str, str]:
    if scope == "노인양로복지시설":
        capacity = 24 + (seq * 13) % 66
        current = max(10, capacity - (seq * 5) % 14)
    elif scope == "노인의료복지시설":
        capacity = 29 + (seq * 17) % 120
        current = max(12, capacity - (seq * 7) % 23)
    else:
        return "", ""
    return str(capacity), str(current)


def facility_name(scope: str, sigungu: str, emd_name: str, seq: int) -> str:
    suffixes = {
        "노인양로복지시설": ["은빛양로원", "평안의집", "소망의집"],
        "노인의료복지시설": ["행복요양원", "효드림요양원", "늘봄요양원", "사랑요양원"],
        "노인여가복지시설": ["노인복지관", "시니어문화센터", "어르신쉼터"],
        "경로당": ["경로당", "마을경로당", "어르신회관"],
        "노인보호전문기관": ["노인보호전문기관"],
    }
    suffix = suffixes[scope][seq % len(suffixes[scope])]
    if scope == "경로당":
        return f"{emd_name}{seq % 17 + 1}리 {suffix} MOCK"
    if scope == "노인보호전문기관":
        return f"전남{sigungu[:2]}권역 {suffix} MOCK"
    return f"{sigungu} {emd_name} {suffix} MOCK"


def location_for(sigungu: str, emd_name: str, seq: int) -> str:
    road = ["복지로", "은빛길", "마을안길", "평안로", "돌봄길"][seq % 5]
    return f"전라남도 {sigungu} {emd_name} mock-{road} {10 + (seq * 19) % 230}"


def make_record(job: dict[str, str], emd: dict[str, Any], seq: int, rng: random.Random) -> dict[str, str]:
    point = synthetic_point(emd, rng)
    scope = job["facility_scope"]
    resident_all, resident_now = capacity_for(scope, seq)
    mock_id = f"MOCK_JN_EWF_{job['file_suffix'].upper()}_{seq:05d}"
    space_key = f"{emd['emd_code']}:{mock_id}"
    return {
        "mock_id": mock_id,
        "apiSeq": str(900000 + seq),
        "api_function": job["function_name"],
        "facility_scope": scope,
        "source_region": "전라남도",
        "city": emd["sigungu"],
        "emd_code": emd["emd_code"],
        "emd_name": emd["emd_name"],
        "name": facility_name(scope, emd["sigungu"], emd["emd_name"], seq),
        "location": location_for(emd["sigungu"], emd["emd_name"], seq),
        "tel": phone_for(emd["sigungu"], seq),
        "fax": phone_for(emd["sigungu"], seq + 3),
        "installDate": install_date(seq),
        "institution": ["사회복지법인", "재단법인", "사단법인", "개인", "지자체위탁"][seq % 5],
        "manager": ["민간위탁", "사회복지법인", "의료법인", "지자체", "비영리법인"][seq % 5],
        "residentAllcnt": resident_all,
        "residentNowcnt": resident_now,
        "posX": f"{point.x:.7f}",
        "posY": f"{point.y:.7f}",
        "scenario_id": SCENARIO_ID,
        "scenario_time": SCENARIO_TIME,
        "valid_from": VALID_FROM,
        "valid_to": VALID_TO,
        "space_key": space_key,
        "mock_source": "generated_mock_from_admin_boundary",
        "coordinate_semantics": "synthetic_point_inside_admin_boundary_not_geocoded",
        "address_semantics": "synthetic_admin_text_not_source_address",
        "native_crs": "EPSG:4326",
    }


def choose_by_sigungu(emds_by_sigungu: dict[str, list[dict[str, Any]]], sigungu: str, index: int) -> dict[str, Any]:
    emds = emds_by_sigungu[sigungu]
    return emds[index % len(emds)]


def build_records(emds: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    rng = random.Random(SEED)
    jeonnam_emds = [emd for emd in emds if emd["sido"] == "전라남도"]
    emds_by_sigungu: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for emd in jeonnam_emds:
        emds_by_sigungu[emd["sigungu"]].append(emd)

    records: dict[str, list[dict[str, str]]] = {job["file_suffix"]: [] for job in JOBS}
    sequence = 1
    sigungu_names = sorted(emds_by_sigungu)

    for sigungu in sigungu_names:
        repeats = 1 + (1 if SIGUNGU_PRIORITY.get(sigungu, 0) >= 4 else 0)
        for idx in range(repeats):
            records["type1"].append(
                make_record(JOBS[0], choose_by_sigungu(emds_by_sigungu, sigungu, idx), sequence, rng)
            )
            sequence += 1

    for sigungu in sigungu_names:
        repeats = 2 + SIGUNGU_PRIORITY.get(sigungu, 1) + max(0, len(emds_by_sigungu[sigungu]) // 18)
        for idx in range(repeats):
            records["type2"].append(
                make_record(JOBS[1], choose_by_sigungu(emds_by_sigungu, sigungu, idx * 3), sequence, rng)
            )
            sequence += 1

    for sigungu in sigungu_names:
        repeats = 1 + max(1, len(emds_by_sigungu[sigungu]) // 12)
        for idx in range(repeats):
            records["type3"].append(
                make_record(JOBS[2], choose_by_sigungu(emds_by_sigungu, sigungu, idx * 5), sequence, rng)
            )
            sequence += 1

    for emd in jeonnam_emds:
        repeats = 2 + (int(emd["emd_code"][-2:]) % 4)
        if emd["sigungu"] in {"여수시", "순천시", "목포시", "광양시", "나주시"}:
            repeats += 1
        for _ in range(repeats):
            records["type4"].append(make_record(JOBS[3], emd, sequence, rng))
            sequence += 1

    regional_centers = ["목포시", "순천시", "나주시", "해남군"]
    for idx, sigungu in enumerate(regional_centers):
        records["type5"].append(
            make_record(JOBS[4], choose_by_sigungu(emds_by_sigungu, sigungu, idx * 7), sequence, rng)
        )
        sequence += 1

    return records


def to_api_item(row: dict[str, str]) -> dict[str, str]:
    item = {
        "apiSeq": row["apiSeq"],
        "city": row["city"],
        "fax": row["fax"],
        "installDate": row["installDate"],
        "institution": row["institution"],
        "location": row["location"],
        "manager": row["manager"],
        "name": row["name"],
        "posX": row["posX"],
        "posY": row["posY"],
        "tel": row["tel"],
        "residentAllcnt": row["residentAllcnt"],
        "residentNowcnt": row["residentNowcnt"],
        "spaceKey": row["space_key"],
        "scenarioTime": row["scenario_time"],
        "validFrom": row["valid_from"],
        "validTo": row["valid_to"],
        "mockSource": row["mock_source"],
        "coordinateSemantics": row["coordinate_semantics"],
    }
    return {key: item[key] for key in API_FIELD_ORDER if item.get(key) != ""}


def write_api_response(job: dict[str, str], rows: list[dict[str, str]]) -> str:
    filename = f"{job['label']}_mock_response.json"
    response = {
        "header": {
            "resultCode": "00",
            "resultMsg": "MOCK SERVICE.",
        },
        "body": {
            "pageIndex": 1,
            "pageSize": len(rows),
            "startPage": 1,
            "totalCount": len(rows),
            "data": {
                "list": [to_api_item(row) for row in rows],
            },
        },
        "mock_metadata": {
            "source_id": SOURCE_ID,
            "source_url": API_SOURCE_URL,
            "endpoint": API_ENDPOINT,
            "function_name": job["function_name"],
            "facility_scope": job["facility_scope"],
            "generated_at": GENERATED_AT,
            "seed": SEED,
            "region_scope": ["전라남도"],
            "gwangju_generation": "skipped_existing_real_snapshot",
            "coordinate_semantics": "synthetic_point_inside_admin_boundary_not_geocoded",
            "address_semantics": "synthetic_admin_text_not_source_address",
            "time_key_fields": ["scenarioTime", "validFrom", "validTo"],
            "space_key_fields": ["spaceKey", "city", "location", "posX", "posY"],
        },
    }
    (OUT_DIR / filename).write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return filename


def write_flat_csv(rows: list[dict[str, str]]) -> str:
    filename = "vulnerable_facilities_elderly_welfare_mock.csv"
    with (OUT_DIR / filename).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return filename


def write_geojson(rows: list[dict[str, str]]) -> str:
    filename = "vulnerable_facilities_elderly_welfare_mock.geojson"
    features = []
    for row in rows:
        point = Point(float(row["posX"]), float(row["posY"]))
        properties = {key: value for key, value in row.items() if key not in {"posX", "posY"}}
        properties.update({"geometry_semantics": row["coordinate_semantics"]})
        features.append({"type": "Feature", "properties": properties, "geometry": mapping(point)})
    payload = {
        "type": "FeatureCollection",
        "name": SOURCE_ID,
        "metadata": {
            "generated_at": GENERATED_AT,
            "generator": "pipelines/SOURCE_VULNERABLE_FACILITIES/generate_elderly_welfare_mock.py",
            "native_crs": "EPSG:4326",
            "region_scope": ["전라남도"],
            "gwangju_generation": "skipped_existing_real_snapshot",
            "temporal_semantics": "scenario_time",
            "spatial_semantics": "synthetic point",
            "not_geocoded": True,
        },
        "features": features,
    }
    (OUT_DIR / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return filename


def write_coverage_index(flat_rows: list[dict[str, str]], real_counts: dict[str, int | None]) -> str:
    filename = "coverage_index.csv"
    by_region_scope: dict[tuple[str, str], int] = defaultdict(int)
    by_sigungu: dict[str, int] = defaultdict(int)
    for row in flat_rows:
        by_region_scope[(row["source_region"], row["facility_scope"])] += 1
        by_sigungu[row["city"]] += 1

    fieldnames = ["region", "coverage_mode", "scope", "row_count", "path", "notes"]
    coverage_rows = [
        {
            "region": "광주광역시",
            "coverage_mode": "real_snapshot_skipped_mock",
            "scope": "노인요양시설",
            "row_count": real_counts["gwangju_senior_nursing"] or 0,
            "path": str(REAL_SNAPSHOT_DIR / "gwangju_senior_nursing_facilities.csv"),
            "notes": "Existing real Gwangju file detected; mock generation skipped per request.",
        },
        {
            "region": "광주광역시",
            "coverage_mode": "real_snapshot_skipped_mock",
            "scope": "의료복지시설",
            "row_count": real_counts["gwangju_medical_welfare"] or 0,
            "path": str(REAL_SNAPSHOT_DIR / "gwangju_medical_welfare_facilities.csv"),
            "notes": "Existing real Gwangju file detected; mock generation skipped per request.",
        },
        {
            "region": "전라남도",
            "coverage_mode": "real_snapshot",
            "scope": "요양병원",
            "row_count": real_counts["jeonnam_nursing_hospitals"] or 0,
            "path": str(REAL_SNAPSHOT_DIR / "jeonnam_nursing_hospitals.csv"),
            "notes": "Existing real Jeonnam nursing-hospital file retained.",
        },
    ]
    for (region, scope), count in sorted(by_region_scope.items()):
        coverage_rows.append(
            {
                "region": region,
                "coverage_mode": "generated_mock",
                "scope": scope,
                "row_count": count,
                "path": str(OUT_DIR / "vulnerable_facilities_elderly_welfare_mock.csv"),
                "notes": "Synthetic Jeonnam elderly-welfare fallback for unavailable API.",
            }
        )
    for sigungu, count in sorted(by_sigungu.items()):
        coverage_rows.append(
            {
                "region": f"전라남도 {sigungu}",
                "coverage_mode": "generated_mock_sigungu_check",
                "scope": "전체 목업 취약시설",
                "row_count": count,
                "path": str(OUT_DIR / "vulnerable_facilities_elderly_welfare_mock.csv"),
                "notes": "Sigungu-level mock coverage check.",
            }
        )
    with (OUT_DIR / filename).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(coverage_rows)
    return filename


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    emds = load_emd_rows()
    records_by_type = build_records(emds)
    flat_rows = [row for job in JOBS for row in records_by_type[job["file_suffix"]]]

    response_files = [write_api_response(job, records_by_type[job["file_suffix"]]) for job in JOBS]
    csv_file = write_flat_csv(flat_rows)
    geojson_file = write_geojson(flat_rows)

    real_counts = {
        "gwangju_senior_nursing": count_rows(REAL_SNAPSHOT_DIR / "gwangju_senior_nursing_facilities.csv", "utf-8-sig"),
        "gwangju_medical_welfare": count_rows(
            REAL_SNAPSHOT_DIR / "gwangju_medical_welfare_facilities.csv", "utf-8-sig"
        ),
        "jeonnam_nursing_hospitals": count_rows(REAL_SNAPSHOT_DIR / "jeonnam_nursing_hospitals.csv", "cp949"),
    }
    coverage_file = write_coverage_index(flat_rows, real_counts)

    type_counts = {job["file_suffix"]: len(records_by_type[job["file_suffix"]]) for job in JOBS}
    sigungu_counts: dict[str, int] = defaultdict(int)
    for row in flat_rows:
        sigungu_counts[row["city"]] += 1

    manifest = {
        "source_id": SOURCE_ID,
        "availability_status": "MOCK_FALLBACK_FOR_REAL_API_GAP",
        "generated_at": GENERATED_AT,
        "generator": "pipelines/SOURCE_VULNERABLE_FACILITIES/generate_elderly_welfare_mock.py",
        "seed": SEED,
        "scenario_id": SCENARIO_ID,
        "scenario_time": SCENARIO_TIME,
        "valid_from": VALID_FROM,
        "valid_to": VALID_TO,
        "region_scope": ["광주광역시", "전라남도"],
        "mock_region_scope": ["전라남도"],
        "gwangju_generation": "skipped_existing_real_snapshot",
        "existing_real_snapshot_counts": real_counts,
        "jeonnam_mock_row_count": len(flat_rows),
        "jeonnam_mock_type_counts": type_counts,
        "jeonnam_mock_sigungu_count": len(sigungu_counts),
        "jeonnam_mock_sigungu_counts": dict(sorted(sigungu_counts.items())),
        "time_key_fields": ["scenario_time", "valid_from", "valid_to"],
        "space_key_fields": ["space_key", "city", "emd_code", "location", "posX", "posY"],
        "native_crs": "EPSG:4326",
        "coordinate_semantics": "synthetic_point_inside_admin_boundary_not_geocoded",
        "address_semantics": "synthetic_admin_text_not_source_address",
        "source_url": API_SOURCE_URL,
        "endpoint": API_ENDPOINT,
        "api_functions": [
            {
                "function_name": job["function_name"],
                "facility_scope": job["facility_scope"],
                "mock_response_file": f"{job['label']}_mock_response.json",
                "row_count": type_counts[job["file_suffix"]],
            }
            for job in JOBS
        ],
        "files": [*response_files, csv_file, geojson_file, coverage_file],
        "notes": [
            "The Jeonnam elderly welfare OpenAPI remained HTTP 404 after the 2026-05-01 retry, so this baseline is a generated mock fallback.",
            "Gwangju real vulnerable-facility snapshots already exist and were not overwritten or duplicated.",
            "Coordinates are synthetic points constrained to admin boundary polygons; they are not geocoded facility locations.",
            "Addresses are synthetic admin-text strings and must not be treated as official facility addresses.",
        ],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
