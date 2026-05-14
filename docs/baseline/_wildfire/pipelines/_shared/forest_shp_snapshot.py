from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

import shapefile

ROOT = Path(__file__).resolve().parents[2]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_entry(path: Path, *, verify_sha256: bool = False) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
    }
    if path.exists():
        stat = path.stat()
        item.update({"size_bytes": stat.st_size})
        if verify_sha256:
            item["sha256"] = sha256(path)
    return item


def zip_summary(path: Path) -> dict[str, Any]:
    info = file_entry(path)
    if not path.exists():
        info["status"] = "missing"
        return info
    with zipfile.ZipFile(path) as archive:
        info["status"] = "ok"
        info["entry_count"] = len(archive.infolist())
        info["entries"] = [
            {
                "name": entry.filename,
                "size": entry.file_size,
                "compressed_size": entry.compress_size,
            }
            for entry in archive.infolist()
        ]
    return info


def shapefile_summary(path: Path, *, encoding: str = "cp949") -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(path), "status": "missing"}
    reader = shapefile.Reader(str(path), encoding=encoding)
    return {
        "path": rel(path),
        "status": "ok",
        "shape_type_code": reader.shapeType,
        "shape_type_name": reader.shapeTypeName,
        "feature_count": len(reader),
        "bbox_native_crs": list(reader.bbox),
        "fields": [field[0] for field in reader.fields[1:]],
    }


def ensure_symlink(link_path: Path, target_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink():
        if link_path.resolve() == target_path.resolve():
            return
        link_path.unlink()
    elif link_path.exists():
        if link_path.is_dir():
            shutil.rmtree(link_path)
        else:
            link_path.unlink()
    relative_target = os.path.relpath(target_path.resolve(), link_path.parent.resolve())
    link_path.symlink_to(relative_target, target_is_directory=target_path.is_dir())


def write_readme(path: Path, title: str, lines: list[str]) -> None:
    body = [f"# {title}", ""]
    body.extend(lines)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
