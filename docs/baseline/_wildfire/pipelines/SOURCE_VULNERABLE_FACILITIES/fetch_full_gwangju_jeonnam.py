#!/usr/bin/env python3
"""Download full Gwangju/Jeonnam vulnerable-facility source evidence."""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.message import Message
from pathlib import Path

SOURCE_ID = "SOURCE_VULNERABLE_FACILITIES"
SNAPSHOT = "full_gwangju_jeonnam_20260430"
OUT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / SNAPSHOT
DATA_GO_KR_ENV = "DATA_GO_KR_SERVICE_KEY"

FILE_DATASETS = [
    {
        "id": "15043855",
        "label": "gwangju_senior_nursing_facilities",
        "name": "광주광역시_노인요양시설 현황_20241231",
        "source_url": "https://www.data.go.kr/data/15043855/fileData.do",
        "region": "광주광역시",
        "facility_scope": "senior_nursing",
    },
    {
        "id": "3041921",
        "label": "gwangju_medical_welfare_facilities",
        "name": "광주광역시_의료복지 시설 현황_20241231",
        "source_url": "https://www.data.go.kr/data/3041921/fileData.do",
        "region": "광주광역시",
        "facility_scope": "medical_welfare",
    },
    {
        "id": "15103609",
        "label": "jeonnam_nursing_hospitals",
        "name": "전라남도_요양병원 현황_20250615",
        "source_url": "https://www.data.go.kr/data/15103609/fileData.do",
        "region": "전라남도",
        "facility_scope": "nursing_hospital",
    },
]

JEONNAM_ELDERLY_WELFARE_ENDPOINT = "https://apis.data.go.kr/6460000/jnOldManWelfare"
JEONNAM_ELDERLY_WELFARE_JOBS = [
    ("jeonnam_elderly_welfare_type1", "getJnOldManWelfare1List", "노인양로복지시설"),
    ("jeonnam_elderly_welfare_type2", "getJnOldManWelfare2List", "노인의료복지시설"),
    ("jeonnam_elderly_welfare_type3", "getJnOldManWelfare3List", "노인여가복지시설"),
    ("jeonnam_elderly_welfare_type4", "getJnOldManWelfare4List", "경로당"),
    ("jeonnam_elderly_welfare_type5", "getJnOldManWelfare5List", "노인보호전문기관"),
]


def request(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 TX05 source acquisition",
            "Referer": "https://www.data.go.kr/",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def decode_text(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def content_url_from_page(source_url: str) -> str:
    html_bytes = request(source_url)
    html, _ = decode_text(html_bytes)
    match = re.search(r'"contentUrl"\s*:\s*"([^"]+)"', html)
    if not match:
        raise RuntimeError(f"contentUrl not found in {source_url}")
    return match.group(1).replace("\\/", "/")


def extension_from_headers(headers: Message | None, default: str = ".csv") -> str:
    if not headers:
        return default
    disposition = headers.get("content-disposition", "")
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', disposition)
    if match:
        name = urllib.parse.unquote(match.group(1).strip('"'))
        suffix = Path(name).suffix
        if suffix:
            return suffix
    content_type = headers.get("content-type", "").lower()
    if "json" in content_type:
        return ".json"
    if "excel" in content_type or "spreadsheet" in content_type:
        return ".xlsx"
    return default


def download_file_dataset(dataset: dict[str, str], out_dir: Path) -> dict[str, object]:
    content_url = content_url_from_page(dataset["source_url"])
    req = urllib.request.Request(
        content_url,
        headers={
            "User-Agent": "Mozilla/5.0 TX05 source acquisition",
            "Referer": dataset["source_url"],
        },
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        body = response.read()
        suffix = extension_from_headers(response.headers)

    raw_path = out_dir / f"{dataset['label']}{suffix}"
    raw_path.write_bytes(body)

    row_count = None
    fieldnames = None
    encoding = None
    if suffix.lower() in (".csv", ".txt") or b"," in body[:500]:
        text, encoding = decode_text(body)
        try:
            reader = csv.DictReader(text.splitlines())
            rows = list(reader)
            row_count = len(rows)
            fieldnames = reader.fieldnames
        except csv.Error:
            pass

    return {
        **dataset,
        "download_url": content_url,
        "path": str(raw_path),
        "bytes": len(body),
        "encoding_detected": encoding,
        "row_count": row_count,
        "fields": fieldnames,
        "status": "downloaded",
    }


def api_url(endpoint: str, function_name: str, service_key: str, page_size: int, start_page: int) -> str:
    params = {
        "serviceKey": service_key,
        "pageSize": str(page_size),
        "startPage": str(start_page),
        "resultType": "json",
    }
    return f"{endpoint}/{function_name}?{urllib.parse.urlencode(params, safe='%')}"


def api_url_template(endpoint: str, function_name: str, page_size: int, start_page: int) -> str:
    params = {
        "serviceKey": f"${{{DATA_GO_KR_ENV}}}",
        "pageSize": str(page_size),
        "startPage": str(start_page),
        "resultType": "json",
    }
    return f"{endpoint}/{function_name}?{urllib.parse.urlencode(params, safe='${}%')}"


def capture_elderly_api(
    label: str, function_name: str, facility_scope: str, out_dir: Path, service_key: str | None
) -> dict[str, object]:
    result: dict[str, object] = {
        "label": label,
        "facility_scope": facility_scope,
        "source_url": "https://www.data.go.kr/data/15102882/openapi.do",
        "endpoint": JEONNAM_ELDERLY_WELFARE_ENDPOINT,
        "function_name": function_name,
        "request_url_template": api_url_template(JEONNAM_ELDERLY_WELFARE_ENDPOINT, function_name, 1000, 1),
        "auth_env": DATA_GO_KR_ENV,
        "auth_env_present": bool(service_key),
    }
    if not service_key:
        result["status"] = "skipped_missing_key"
        return result

    url = api_url(JEONNAM_ELDERLY_WELFARE_ENDPOINT, function_name, service_key, 1000, 1)
    response_path = out_dir / f"{label}_api_response.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TX05 source acquisition"})
        with urllib.request.urlopen(req, timeout=45) as response:
            body = response.read()
            response_path.write_bytes(body)
            result.update(
                {
                    "status": "fetched",
                    "path": str(response_path),
                    "bytes": len(body),
                    "content_type": response.headers.get("content-type", ""),
                }
            )
            try:
                parsed = json.loads(body.decode("utf-8"))
                result["keys"] = list(parsed.keys()) if isinstance(parsed, dict) else None
            except Exception:
                pass
    except urllib.error.HTTPError as exc:
        body = exc.read()
        error_path = out_dir / f"{label}_api_error_response.txt"
        error_path.write_bytes(body)
        result.update(
            {
                "status": "http_error",
                "http_status": exc.code,
                "path": str(error_path),
                "bytes": len(body),
                "message": str(exc),
            }
        )
    except Exception as exc:
        result.update({"status": "failed", "error": type(exc).__name__, "message": str(exc)})
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "source_id": SOURCE_ID,
        "snapshot": SNAPSHOT,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "region_scope": ["광주광역시", "전라남도"],
        "notes": [
            "Native files/API responses are preserved without geocoding or address standardization.",
            "The Jeonnam elderly welfare OpenAPI requires DATA_GO_KR_SERVICE_KEY approval for this specific service.",
        ],
        "file_datasets": [],
        "api_captures": [],
    }

    for dataset in FILE_DATASETS:
        print(f"download file dataset {dataset['label']}", flush=True)
        try:
            manifest["file_datasets"].append(download_file_dataset(dataset, OUT_DIR))  # type: ignore[union-attr]
        except Exception as exc:
            manifest["file_datasets"].append(  # type: ignore[union-attr]
                {**dataset, "status": "failed", "error": type(exc).__name__, "message": str(exc)}
            )
        time.sleep(0.2)

    service_key = os.environ.get(DATA_GO_KR_ENV)
    for label, function_name, facility_scope in JEONNAM_ELDERLY_WELFARE_JOBS:
        print(f"capture api {label}", flush=True)
        manifest["api_captures"].append(  # type: ignore[union-attr]
            capture_elderly_api(label, function_name, facility_scope, OUT_DIR, service_key)
        )
        time.sleep(0.2)

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
