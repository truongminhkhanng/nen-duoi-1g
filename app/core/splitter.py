from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.utils.checksum import sha256_file


def split_file(source: Path, output: Path, part_size: int,
               cancelled: Callable[[], bool] | None = None,
               progress: Callable[[int, int], None] | None = None) -> Path:
    if part_size <= 0:
        raise ValueError("Dung lượng phần phải lớn hơn 0")
    output.mkdir(parents=True, exist_ok=True)
    total = source.stat().st_size
    original_hash = sha256_file(source, cancelled=cancelled)
    parts: list[dict[str, object]] = []
    created: list[Path] = []
    processed = 0
    try:
        with source.open("rb") as reader:
            index = 1
            while True:
                if cancelled and cancelled():
                    raise InterruptedError("Đã hủy chia file")
                chunk = reader.read(part_size)
                if not chunk:
                    break
                part_path = output / f"{source.name}.{index:03d}"
                with part_path.open("xb") as writer:
                    writer.write(chunk)
                created.append(part_path)
                parts.append({"name": part_path.name, "size": len(chunk),
                              "sha256": sha256_file(part_path)})
                processed += len(chunk)
                if progress:
                    progress(processed, total)
                index += 1
        manifest = output / f"{source.name}.manifest.json"
        payload = {
            "format": "zip-part-maker-split-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "original_name": source.name,
            "original_size": total,
            "original_sha256": original_hash,
            "parts": parts,
        }
        manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise


def join_file(manifest_path: Path, output: Path,
              cancelled: Callable[[], bool] | None = None,
              progress: Callable[[int, int], None] | None = None) -> Path:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("format") != "zip-part-maker-split-v1":
        raise ValueError("Manifest không đúng định dạng")
    parts = payload.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("Manifest không có danh sách phần")
    output.mkdir(parents=True, exist_ok=True)
    target = output / str(payload["original_name"])
    temporary = target.with_name(target.name + ".joining.tmp")
    processed = 0
    total = int(payload["original_size"])
    try:
        with temporary.open("xb") as writer:
            for part in parts:
                if cancelled and cancelled():
                    raise InterruptedError("Đã hủy ghép file")
                if not isinstance(part, dict):
                    raise ValueError("Mục part không hợp lệ")
                part_path = manifest_path.parent / str(part["name"])
                if sha256_file(part_path) != part["sha256"]:
                    raise ValueError(f"Checksum phần không khớp: {part_path.name}")
                with part_path.open("rb") as reader:
                    while chunk := reader.read(1024 * 1024):
                        writer.write(chunk)
                        processed += len(chunk)
                        if progress:
                            progress(processed, total)
        if temporary.stat().st_size != total or sha256_file(temporary) != payload["original_sha256"]:
            raise ValueError("File ghép không khớp manifest")
        temporary.replace(target)
        return target
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
