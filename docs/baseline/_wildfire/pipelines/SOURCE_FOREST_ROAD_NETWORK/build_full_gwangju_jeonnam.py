#!/usr/bin/env python3
"""Promote acquired FGIS forest-road SHP archive to a regional full snapshot.

FGIS returned a 전라남도 임도망도 extract and no 광주광역시 data for this layer
in the recorded manual acquisition. This pipeline verifies the preserved
Jeonnam SHP archive/layer and records the Gwangju no-data evidence so the
source is reproducible at 광주·전남 scope without deriving a road graph or
performing spatial joins.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines._shared.forest_shp_snapshot import (
    ensure_symlink,
    read_json,
    rel,
    shapefile_summary,
    write_json,
    write_readme,
    zip_summary,
)

SOURCE_ID = "SOURCE_FOREST_ROAD_NETWORK"
ACCESS_OPTION_ID = "ACCESS_FOREST_ROAD_NETWORK_PRIMARY"
DEFAULT_INPUT_DIR = ROOT / "data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/regional_clip"
DEFAULT_OUTPUT_DIR = ROOT / "data/raw/SOURCE_FOREST_ROAD_NETWORK/snapshots/full_gwangju_jeonnam_20260430"
JEONNAM_DIR_NAME = "jeonnam_sido"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--snapshot-name", default=DEFAULT_OUTPUT_DIR.name)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jeonnam_dir = args.input_dir / JEONNAM_DIR_NAME
    metadata_path = jeonnam_dir / "metadata_summary.json"
    metadata = read_json(metadata_path)
    ensure_symlink(args.output_dir / "raw_links" / JEONNAM_DIR_NAME, jeonnam_dir)

    archive_path = jeonnam_dir / "archives" / "임도망도.zip"
    layer_path = jeonnam_dir / "layers" / "46.shp"
    archive = zip_summary(archive_path)
    expected_sha = metadata.get("archive", {}).get("sha256")
    if expected_sha:
        archive["expected_sha256_from_prior_acquisition"] = expected_sha

    layer = shapefile_summary(layer_path, encoding="cp949")
    layer["feature_count_source"] = "direct_shp_dbf_header"

    gwangju_no_data = {
        "sido_name": "광주광역시",
        "sido_code": "29",
        "coverage_status": "no_data_confirmed_in_recorded_fgis_flow",
        "evidence": "SOURCE_FOREST_ROAD_NETWORK dossier and manual acquisition notes record that FGIS returned no 임도망도(국유림) data for 광주광역시.",
        "raw_file_expected": False,
    }

    jeonnam = {
        "sido_name": "전라남도",
        "sido_code": "46",
        "coverage_status": "acquired",
        "raw_source_dir": rel(jeonnam_dir),
        "metadata_summary": rel(metadata_path),
        "native_crs": metadata.get("native_crs"),
        "archive": archive,
        "layer": layer,
        "poc_coverage": metadata.get("poc_coverage"),
    }

    missing = []
    if not archive.get("exists"):
        missing.append(archive.get("path"))
    if layer.get("status") != "ok":
        missing.append(layer.get("path"))

    manifest = {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "snapshot": args.snapshot_name,
        "snapshot_type": "full_gwangju_jeonnam",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "region_scope": ["광주광역시", "전라남도"],
        "source_phase": "raw snapshot registration from acquired FGIS SHP archive plus no-data evidence",
        "acquisition_method": "manual_download_ingest_pipeline",
        "native_format": "ESRI Shapefile ZIP",
        "native_crs": "Korea 2000 / Unified CS, EPSG:5179",
        "temporal_semantics": ["static", "registry_updated_at"],
        "time_key_field": "registry_updated_at",
        "regions": [gwangju_no_data, jeonnam],
        "feature_count_total": layer.get("feature_count"),
        "coverage_result": "pass_with_gwangju_no_data_evidence",
        "coverage_note": "전라남도 forest-road SHP is acquired. 광주광역시 is recorded as no-data for this FGIS layer, so no synthetic road lines are created.",
        "missing_required_files": missing,
        "raw_phase_constraints": [
            "no CRS normalization",
            "no clipping",
            "no line-network topology generation",
            "no routing graph derivation",
            "no feature-level spatial join",
            "no Feature/Signal calculation",
        ],
    }
    if missing:
        manifest["coverage_result"] = "fail_missing_required_file"

    write_json(args.output_dir / "manifest.json", manifest)
    write_json(args.output_dir / "gwangju_no_data_evidence.json", gwangju_no_data)
    write_json(
        args.output_dir / "region_coverage_assessment.json",
        {
            "source_id": SOURCE_ID,
            "assessment_scope": "광주광역시·전라남도",
            "assessment_result": manifest["coverage_result"],
            "regions": [
                gwangju_no_data,
                {
                    "sido_name": jeonnam["sido_name"],
                    "coverage_status": jeonnam["coverage_status"],
                    "feature_count": layer.get("feature_count"),
                    "raw_source_dir": jeonnam["raw_source_dir"],
                },
            ],
            "raw_phase_constraints": manifest["raw_phase_constraints"],
        },
    )
    write_readme(
        args.output_dir / "README.md",
        "SOURCE_FOREST_ROAD_NETWORK Full Gwangju-Jeonnam Snapshot",
        [
            "This snapshot is generated by `pipelines/SOURCE_FOREST_ROAD_NETWORK/build_full_gwangju_jeonnam.py`.",
            "",
            "It registers the acquired Jeonnam FGIS forest-road SHP ZIP and records the Gwangju no-data evidence from the acquisition flow.",
            "The original archive remains under `snapshots/regional_clip/jeonnam_sido`; `raw_links/` contains a symlink only.",
            "",
            "No CRS normalization, clipping, road graph construction, routing, spatial join, or Feature/Signal calculation was performed.",
        ],
    )
    print(f"wrote {args.output_dir / 'manifest.json'}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
