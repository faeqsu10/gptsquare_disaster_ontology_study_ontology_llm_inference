from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

from shapely import wkb

ADMIN_BOUNDARY_PATH = Path("data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/LP_AA_EMD_gwangju_jeonnam.csv")
LEGAL_CODE_PATH = Path("data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/national_legal_dong_gwangju_jeonnam.csv")
TARGET_SIDO_PREFIXES = {
    "29": "광주광역시",
    "46": "전라남도",
}
RENAMED_BOUNDARY_CODE_FALLBACKS = {
    "46710335": {
        "boundary_code_8": "46710330",
        "note": "가사문학면 current legal code uses previous 남면 boundary geometry from SOURCE_ADMIN_BOUNDARIES.",
    },
    "46790395": {
        "boundary_code_8": "46790390",
        "note": "백아면 current legal code uses previous 북면 boundary geometry from SOURCE_ADMIN_BOUNDARIES.",
    },
    "46790415": {
        "boundary_code_8": "46790410",
        "note": "사평면 current legal code uses previous 남면 boundary geometry from SOURCE_ADMIN_BOUNDARIES.",
    },
}
POINT_FALLBACKS = {
    "46170134": {
        "longitude": 126.7891164,
        "latitude": 35.0184372,
        "geometry_source": "VWorld search API, query='전라남도 나주시 빛가람동', type=place, category=읍면동구역경계 > 법정동",
        "note": "빛가람동 is present in the current legal code table but absent from the acquired SOURCE_ADMIN_BOUNDARIES file.",
    }
}


def _read_legal_code_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _active_legal_emd_by_code(path: Path) -> dict[str, dict[str, str]]:
    rows = _read_legal_code_rows(path)
    active_emd_rows = [
        row for row in rows if not row["삭제일자"] and row["시군구명"] and row["읍면동명"] and not row["리명"]
    ]
    return {row["법정동코드"][:8]: row for row in active_emd_rows}


def _active_legal_emd_rows(path: Path) -> list[dict[str, str]]:
    rows = _read_legal_code_rows(path)
    return [row for row in rows if not row["삭제일자"] and row["시군구명"] and row["읍면동명"] and not row["리명"]]


def _sigungu_names_by_code(path: Path) -> dict[str, str]:
    rows = _read_legal_code_rows(path)
    sigungu_rows = [
        row for row in rows if not row["삭제일자"] and row["시군구명"] and not row["읍면동명"] and not row["리명"]
    ]
    return {row["법정동코드"][:5]: row["시군구명"] for row in sigungu_rows}


def load_coverage_units(
    boundary_path: Path = ADMIN_BOUNDARY_PATH,
    legal_code_path: Path = LEGAL_CODE_PATH,
) -> list[dict[str, Any]]:
    """Return current 광주·전남 legal 읍면동 rows as mock coverage units.

    Coordinates are representative points decoded from source WKB values when
    available. Known legal-code/boundary-version gaps use explicit fallback
    points or previous boundary geometries. No CRS conversion is performed.
    """
    csv.field_size_limit(sys.maxsize)
    legal_rows = _active_legal_emd_rows(legal_code_path)
    units: list[dict[str, Any]] = []
    boundary_by_code: dict[str, dict[str, Any]] = {}

    with boundary_path.open("r", encoding="cp949", newline="") as handle:
        for row in csv.DictReader(handle):
            emd_code_8 = row["읍면동코드"]
            sigungu_code = row["객체시군구코드"]
            sido_prefix = sigungu_code[:2]
            if sido_prefix not in TARGET_SIDO_PREFIXES:
                continue

            geom = wkb.loads(bytes.fromhex(row["공간정보"]))
            point = geom.representative_point()
            boundary_by_code[emd_code_8] = {
                "longitude": round(point.x, 7),
                "latitude": round(point.y, 7),
                "boundary_bbox": [round(value, 7) for value in geom.bounds],
                "geometry_source": str(boundary_path),
                "geometry_source_field": "공간정보",
                "geometry_source_code_8": emd_code_8,
            }

    for legal_row in legal_rows:
        code_8 = legal_row["법정동코드"][:8]
        sigungu_code = legal_row["법정동코드"][:5]
        sido_prefix = legal_row["법정동코드"][:2]
        coverage_unit_id = legal_row["법정동코드"]
        coverage_unit_name = f"{legal_row['시도명']} {legal_row['시군구명']} {legal_row['읍면동명']}"
        boundary = boundary_by_code.get(code_8)
        code_match_status = "active_legal_code_boundary_geometry_match"
        fallback_note = ""

        if boundary is None and code_8 in RENAMED_BOUNDARY_CODE_FALLBACKS:
            fallback = RENAMED_BOUNDARY_CODE_FALLBACKS[code_8]
            boundary = boundary_by_code[fallback["boundary_code_8"]]
            code_match_status = "active_legal_code_previous_boundary_geometry_fallback"
            fallback_note = fallback["note"]

        if boundary is None and code_8 in POINT_FALLBACKS:
            fallback_point = POINT_FALLBACKS[code_8]
            boundary = {
                "longitude": fallback_point["longitude"],
                "latitude": fallback_point["latitude"],
                "boundary_bbox": [
                    fallback_point["longitude"],
                    fallback_point["latitude"],
                    fallback_point["longitude"],
                    fallback_point["latitude"],
                ],
                "geometry_source": fallback_point["geometry_source"],
                "geometry_source_field": "point",
                "geometry_source_code_8": code_8,
            }
            code_match_status = "active_legal_code_vworld_point_fallback"
            fallback_note = fallback_point["note"]

        if boundary is None:
            raise ValueError(f"No geometry or fallback point for active legal emd code {coverage_unit_id}")

        units.append(
            {
                "coverage_unit_id": coverage_unit_id,
                "coverage_unit_code_8": code_8,
                "coverage_unit_name": coverage_unit_name,
                "sido_code_prefix": sido_prefix,
                "sido_name": TARGET_SIDO_PREFIXES[sido_prefix],
                "sigungu_code": sigungu_code,
                "sigungu_name": legal_row["시군구명"],
                "eupmyeondong_name": legal_row["읍면동명"],
                "longitude": boundary["longitude"],
                "latitude": boundary["latitude"],
                "boundary_bbox": boundary["boundary_bbox"],
                "geometry_source": boundary["geometry_source"],
                "geometry_source_field": boundary["geometry_source_field"],
                "geometry_source_code_8": boundary["geometry_source_code_8"],
                "code_match_status": code_match_status,
                "fallback_note": fallback_note,
                "coverage_basis": "SOURCE_REGION_CODE_TABLE current legal 읍면동 row with SOURCE_ADMIN_BOUNDARIES/VWorld representative coordinates",
            }
        )

    units.sort(key=lambda item: item["coverage_unit_id"])
    return units


def coverage_summary(units: list[dict[str, Any]]) -> dict[str, Any]:
    counts_by_sido: dict[str, int] = {}
    sigungu_codes_by_sido: dict[str, set[str]] = {}
    code_match_counts: dict[str, int] = {}

    for unit in units:
        sido_name = unit["sido_name"]
        counts_by_sido[sido_name] = counts_by_sido.get(sido_name, 0) + 1
        sigungu_codes_by_sido.setdefault(sido_name, set()).add(unit["sigungu_code"])
        status = unit["code_match_status"]
        code_match_counts[status] = code_match_counts.get(status, 0) + 1

    return {
        "coverage_scope": "광주광역시·전라남도",
        "coverage_unit_grain": "current legal 읍면동 row",
        "coverage_unit_count": len(units),
        "coverage_counts_by_sido": counts_by_sido,
        "sigungu_counts_by_sido": {sido_name: len(codes) for sido_name, codes in sigungu_codes_by_sido.items()},
        "code_match_counts": code_match_counts,
        "coverage_unit_source": str(ADMIN_BOUNDARY_PATH),
        "legal_code_reference": str(LEGAL_CODE_PATH),
        "raw_phase_constraints": [
            "no nearest-distance calculation",
            "no road or Segment join",
            "no CRS conversion",
        ],
    }
