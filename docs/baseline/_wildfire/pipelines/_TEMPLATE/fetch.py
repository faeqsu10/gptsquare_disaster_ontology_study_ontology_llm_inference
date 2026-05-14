#!/usr/bin/env python3
"""
Template fetcher for REAL Source AccessOptions.

This script is intentionally a scaffold. Source-specific copies should:
- read required API keys from environment variables,
- write the raw response/file under data/raw/<source_id>/snapshots/,
- preserve native CRS/time fields without transformation,
- write sample_request.json and sample_response.json for OpenAPI/WMS/WFS options.
"""

from pathlib import Path

SOURCE_ID = "source_id"
ACCESS_OPTION_ID = "access_option_id"
OUTPUT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / "sample_YYYYMMDD"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raise SystemExit(
        "Template only. Copy this file to pipelines/<source_id>/fetch.py and implement the source-specific request."
    )


if __name__ == "__main__":
    main()
