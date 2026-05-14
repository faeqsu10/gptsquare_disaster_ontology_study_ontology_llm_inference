#!/usr/bin/env python3
"""Promote acquired FGIS forest-stand SHP archives to a regional full snapshot.

The FGIS download itself is a login/application workflow. This pipeline starts
after the original ZIP/SHP files have been acquired and preserved under
`snapshots/regional_clip/*_sido`. It verifies the raw archives/layers, creates a
stable full-region snapshot manifest, and links back to the preserved source
files without CRS conversion, clipping, dissolving, or spatial joining.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

SOURCE_ID = "SOURCE_FOREST_STAND_MAP"
ACCESS_OPTION_ID = "ACCESS_FOREST_STAND_MAP_PRIMARY"
DEFAULT_INPUT_DIR = ROOT / "data/raw/SOURCE_FOREST_STAND_MAP/snapshots/regional_clip"
DEFAULT_OUTPUT_DIR = ROOT / "data/raw/SOURCE_FOREST_STAND_MAP/snapshots/full_gwangju_jeonnam_20260430"
VINTAGES = ("2013", "2019", "2024", "2025")


REGIONS = {
    "gwangju_sido": {
        "sido_name": "광주광역시",
        "sido_code": "29",
        "layer_name": "29",
        "coverage_status": "acquired",
    },
    "jeonnam_sido": {
        "sido_name": "전라남도",
        "sido_code": "46",
        "layer_name": "46",
        "coverage_status": "acquired",
    },
}


def expected_archive(region_dir: Path, year: str) -> Path:
    return region_dir / "archives" / f"{year}.zip"


def layer_path(region_dir: Path, year: str, layer_name: str) -> Path | None:
    candidates = [
        region_dir / "layers" / year / f"{layer_name}.shp",
        region_dir / "extracted" / year / f"{layer_name}.shp",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def metadata_layer_by_year(metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for layer in metadata.get("layers", []):
        year = str(layer.get("year", ""))
        if year:
            out[year] = layer
    return out


def build_region(region_key: str, input_dir: Path, output_dir: Path) -> dict[str, Any]:
    config = REGIONS[region_key]
    region_dir = input_dir / region_key
    metadata_path = region_dir / "metadata_summary.json"
    metadata = read_json(metadata_path)
    metadata_layers = metadata_layer_by_year(metadata)
    ensure_symlink(output_dir / "raw_links" / region_key, region_dir)

    archives = []
    layers = []
    for year in VINTAGES:
        archive_path = expected_archive(region_dir, year)
        archive = zip_summary(archive_path)
        expected_sha = next(
            (item.get("sha256") for item in metadata.get("archives", []) if str(item.get("year")) == year),
            None,
        )
        if expected_sha:
            archive["expected_sha256_from_prior_acquisition"] = expected_sha
        archives.append({"year": year, **archive})

        shp_path = layer_path(region_dir, year, config["layer_name"])
        if shp_path:
            layer = shapefile_summary(shp_path, encoding="cp949")
            layer["feature_count_source"] = "direct_shp_dbf_header"
        else:
            prior = dict(metadata_layers.get(year, {}))
            layer = {
                "path": prior.get("path") or prior.get("path_in_archive"),
                "status": "metadata_only_from_preserved_archive",
                "shape_type_code": metadata.get("shape_type", {}).get("code"),
                "shape_type_name": metadata.get("shape_type", {}).get("name"),
                "feature_count": prior.get("feature_count_from_dbf"),
                "bbox_native_crs": prior.get("bbox_native_crs"),
                "fields": prior.get("fields", []),
                "feature_count_source": "metadata_summary_from_prior_raw_inspection",
            }
        layer["year"] = year
        layers.append(layer)

    feature_counts = {
        year: item.get("feature_count") for year, item in ((str(layer["year"]), layer) for layer in layers)
    }
    return {
        "region_key": region_key,
        "sido_name": config["sido_name"],
        "sido_code": config["sido_code"],
        "layer_name": config["layer_name"],
        "coverage_status": config["coverage_status"],
        "raw_source_dir": rel(region_dir),
        "metadata_summary": rel(metadata_path),
        "native_crs": metadata.get("native_crs"),
        "archives": archives,
        "layers": layers,
        "latest_vintage": max(VINTAGES),
        "latest_feature_count": feature_counts.get(max(VINTAGES)),
        "feature_counts_by_vintage": feature_counts,
        "poc_coverage": metadata.get("poc_coverage"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--snapshot-name", default=DEFAULT_OUTPUT_DIR.name)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    regions = [build_region(key, args.input_dir, args.output_dir) for key in REGIONS]

    missing = [
        f"{region['region_key']}:{archive['year']}:{archive['path']}"
        for region in regions
        for archive in region["archives"]
        if not archive.get("exists")
    ]
    latest_total = sum(int(region.get("latest_feature_count") or 0) for region in regions)

    manifest = {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "snapshot": args.snapshot_name,
        "snapshot_type": "full_gwangju_jeonnam",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "region_scope": ["광주광역시", "전라남도"],
        "source_phase": "raw snapshot registration from acquired FGIS SHP ZIP archives",
        "acquisition_method": "manual_download_ingest_pipeline",
        "native_format": "ESRI Shapefile ZIP",
        "native_crs": "Korea 2000 / Unified CS, EPSG:5179",
        "temporal_semantics": ["static", "registry_updated_at"],
        "time_key_field": "registry_updated_at; archive/vintage year",
        "latest_vintage": max(VINTAGES),
        "latest_vintage_feature_count_total": latest_total,
        "regions": regions,
        "coverage_result": "pass",
        "coverage_note": "광주광역시 and 전라남도 시도 단위 FGIS forest-stand extracts are both present as preserved source ZIP/SHP archives.",
        "missing_required_files": missing,
        "raw_phase_constraints": [
            "no CRS normalization",
            "no clipping",
            "no dissolve",
            "no derived forest boundary generation",
            "no feature-level spatial join",
            "no Feature/Signal calculation",
        ],
    }
    if missing:
        manifest["coverage_result"] = "fail_missing_required_archive"

    write_json(args.output_dir / "manifest.json", manifest)
    write_json(
        args.output_dir / "region_coverage_assessment.json",
        {
            "source_id": SOURCE_ID,
            "assessment_scope": "광주광역시·전라남도",
            "assessment_result": manifest["coverage_result"],
            "latest_vintage": manifest["latest_vintage"],
            "latest_vintage_feature_count_total": latest_total,
            "regions": [
                {
                    "sido_name": region["sido_name"],
                    "coverage_status": region["coverage_status"],
                    "latest_feature_count": region["latest_feature_count"],
                    "raw_source_dir": region["raw_source_dir"],
                }
                for region in regions
            ],
            "raw_phase_constraints": manifest["raw_phase_constraints"],
        },
    )
    write_readme(
        args.output_dir / "README.md",
        "SOURCE_FOREST_STAND_MAP Full Gwangju-Jeonnam Snapshot",
        [
            "This snapshot is generated by `pipelines/SOURCE_FOREST_STAND_MAP/build_full_gwangju_jeonnam.py`.",
            "",
            "It registers already acquired FGIS manual-download SHP ZIP archives as a full project-region raw snapshot.",
            "The original archives remain under `snapshots/regional_clip/*_sido`; `raw_links/` contains symlinks only.",
            "",
            "No CRS normalization, clipping, dissolve, forest-boundary derivation, spatial join, or Feature/Signal calculation was performed.",
        ],
    )
    print(f"wrote {args.output_dir / 'manifest.json'}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
