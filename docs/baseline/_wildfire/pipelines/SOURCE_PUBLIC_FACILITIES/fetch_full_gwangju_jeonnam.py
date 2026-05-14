#!/usr/bin/env python3
"""Download full Gwangju/Jeonnam public-facility source evidence.

The script preserves source-native files and API responses. It does not
geocode, normalize addresses, or join facilities to decision segments.
"""

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
import xml.etree.ElementTree as ET
from email.message import Message
from pathlib import Path

SOURCE_ID = "SOURCE_PUBLIC_FACILITIES"
SNAPSHOT = "full_gwangju_jeonnam_20260430"
OUT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / SNAPSHOT
DATA_GO_KR_ENV = "DATA_GO_KR_SERVICE_KEY"

FILE_DATASETS = [
    {
        "id": "15056455",
        "label": "gwangju_public_health_facilities",
        "name": "광주광역시_공공보건의료기관 현황_20240313",
        "source_url": "https://www.data.go.kr/data/15056455/fileData.do",
        "region": "광주광역시",
        "facility_scope": "public_health",
    },
    {
        "id": "3068470",
        "label": "jeonnam_public_health_centers",
        "name": "전라남도_보건소현황_20250620",
        "source_url": "https://www.data.go.kr/data/3068470/fileData.do",
        "region": "전라남도",
        "facility_scope": "public_health_center",
    },
    {
        "id": "15037304",
        "label": "jeonnam_public_health_posts",
        "name": "전라남도_보건진료소현황_20250620",
        "source_url": "https://www.data.go.kr/data/15037304/fileData.do",
        "region": "전라남도",
        "facility_scope": "public_health_post",
    },
    {
        "id": "15129779",
        "label": "jeonnam_health_life_support_centers",
        "name": "전라남도_건강생활지원센터 현황_20250616",
        "source_url": "https://www.data.go.kr/data/15129779/fileData.do",
        "region": "전라남도",
        "facility_scope": "public_health_support",
    },
    {
        "id": "15069181",
        "label": "jeonnam_hospitals_and_clinics",
        "name": "전라남도_병원 의원현황_20250723",
        "source_url": "https://www.data.go.kr/data/15069181/fileData.do",
        "region": "전라남도",
        "facility_scope": "hospital_clinic",
    },
    {
        "id": "15069196",
        "label": "jeonnam_hospital_grade_or_higher",
        "name": "전라남도_병원급이상의료기관현황_20250908",
        "source_url": "https://www.data.go.kr/data/15069196/fileData.do",
        "region": "전라남도",
        "facility_scope": "hospital_grade_or_higher",
    },
    {
        "id": "15119121",
        "label": "jeonnam_non_emergency_medical_institutions",
        "name": "전라남도_응급의료기관 외의 의료기관_20250617",
        "source_url": "https://www.data.go.kr/data/15119121/fileData.do",
        "region": "전라남도",
        "facility_scope": "medical_institution",
    },
]

SCHOOL_ENDPOINT = "https://api.data.go.kr/openapi/tn_pubr_public_elesch_mskul_lc_api"
HIRA_ENDPOINT = "https://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"

API_JOBS = [
    {
        "label": "school_locations_gwangju",
        "endpoint": SCHOOL_ENDPOINT,
        "key_param": "serviceKey",
        "params": {"pageNo": "1", "numOfRows": "1000", "type": "json", "rdnmadr": "광주광역시"},
        "source_url": "https://www.data.go.kr/data/15021148/standard.do",
    },
    {
        "label": "school_locations_jeonnam",
        "endpoint": SCHOOL_ENDPOINT,
        "key_param": "serviceKey",
        "params": {"pageNo": "1", "numOfRows": "1000", "type": "json", "rdnmadr": "전라남도"},
        "source_url": "https://www.data.go.kr/data/15021148/standard.do",
    },
    {
        "label": "hira_hospitals_gwangju",
        "endpoint": HIRA_ENDPOINT,
        "key_param": "ServiceKey",
        "params": {"pageNo": "1", "numOfRows": "1000", "sidoCd": "240000"},
        "source_url": "https://www.data.go.kr/data/15001698/openapi.do",
    },
    {
        "label": "hira_hospitals_jeonnam",
        "endpoint": HIRA_ENDPOINT,
        "key_param": "ServiceKey",
        "params": {"pageNo": "1", "numOfRows": "1000", "sidoCd": "360000"},
        "source_url": "https://www.data.go.kr/data/15001698/openapi.do",
    },
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


def build_api_url(endpoint: str, key_param: str, service_key: str, params: dict[str, str]) -> str:
    secret = urllib.parse.quote(service_key, safe="%")
    query = urllib.parse.urlencode(params)
    return f"{endpoint}?{key_param}={secret}&{query}"


def api_url_template(endpoint: str, key_param: str, params: dict[str, str]) -> str:
    query = urllib.parse.urlencode(params)
    return f"{endpoint}?{key_param}=${{{DATA_GO_KR_ENV}}}&{query}"


def capture_api(job: dict[str, object], out_dir: Path, service_key: str | None) -> dict[str, object]:
    params = dict(job["params"])  # type: ignore[arg-type]
    template = api_url_template(str(job["endpoint"]), str(job["key_param"]), params)
    result: dict[str, object] = {
        "label": job["label"],
        "source_url": job["source_url"],
        "endpoint": job["endpoint"],
        "params": params,
        "request_url_template": template,
        "auth_env": DATA_GO_KR_ENV,
        "auth_env_present": bool(service_key),
    }
    if not service_key:
        result["status"] = "skipped_missing_key"
        return result

    url = build_api_url(str(job["endpoint"]), str(job["key_param"]), service_key, params)
    suffix = ".json" if params.get("type") == "json" else ".xml"
    response_path = out_dir / f"{job['label']}_api_response{suffix}"
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
            if suffix == ".json":
                try:
                    parsed = json.loads(body.decode("utf-8"))
                    header = parsed.get("response", {}).get("header", {})
                    body_doc = parsed.get("response", {}).get("body", {})
                    result["api_result_code"] = header.get("resultCode")
                    result["api_result_msg"] = header.get("resultMsg")
                    result["total_count"] = body_doc.get("totalCount") or body_doc.get("total_count")
                    if header.get("resultCode") not in (None, "00", "0"):
                        result["status"] = "api_error"
                except Exception:
                    pass
            elif suffix == ".xml":
                try:
                    root = ET.fromstring(body)
                    total_count = int(root.findtext(".//totalCount") or "0")
                    num_rows = int(root.findtext(".//numOfRows") or params.get("numOfRows", "1000"))
                    page_no = int(root.findtext(".//pageNo") or params.get("pageNo", "1"))
                    item_count = len(root.findall(".//item"))
                    result["api_result_code"] = root.findtext(".//resultCode")
                    result["api_result_msg"] = root.findtext(".//resultMsg")
                    result["total_count"] = total_count
                    result["item_count"] = item_count
                    result["page_no"] = page_no
                    result["num_of_rows"] = num_rows

                    if total_count > item_count and num_rows > 0:
                        page_paths = [str(response_path)]
                        total_items = item_count
                        page_count = (total_count + num_rows - 1) // num_rows
                        for next_page in range(page_no + 1, page_count + 1):
                            next_params = {**params, "pageNo": str(next_page), "numOfRows": str(num_rows)}
                            next_url = build_api_url(
                                str(job["endpoint"]), str(job["key_param"]), service_key, next_params
                            )
                            next_path = out_dir / f"{job['label']}_api_response_page_{next_page:03d}.xml"
                            next_req = urllib.request.Request(
                                next_url,
                                headers={"User-Agent": "Mozilla/5.0 TX05 source acquisition"},
                            )
                            with urllib.request.urlopen(next_req, timeout=45) as next_response:
                                next_body = next_response.read()
                            next_path.write_bytes(next_body)
                            page_paths.append(str(next_path))
                            try:
                                next_root = ET.fromstring(next_body)
                                total_items += len(next_root.findall(".//item"))
                            except ET.ParseError:
                                pass
                            time.sleep(0.2)
                        result["status"] = "fetched_all_pages"
                        result["page_count"] = page_count
                        result["page_paths"] = page_paths
                        result["item_count"] = total_items
                except Exception:
                    pass
    except urllib.error.HTTPError as exc:
        body = exc.read()
        response_path = out_dir / f"{job['label']}_api_error_response.txt"
        response_path.write_bytes(body)
        result.update(
            {
                "status": "http_error",
                "http_status": exc.code,
                "path": str(response_path),
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
            "School and HIRA OpenAPI captures depend on DATA_GO_KR_SERVICE_KEY approval state.",
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
    for job in API_JOBS:
        print(f"capture api {job['label']}", flush=True)
        manifest["api_captures"].append(capture_api(job, OUT_DIR, service_key))  # type: ignore[union-attr]
        time.sleep(0.2)

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
