from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from typing import Callable

from app.utils.paths import unique_path


COPY_CHUNK_SIZE = 1024 * 1024


def _manifest_name(value: object) -> str:
    if (not isinstance(value, str) or not value or value in {".", ".."}
            or any(character in value for character in '/\\:')
            or any(ord(character) < 32 for character in value)
            or PureWindowsPath(value).is_reserved()
            or value.endswith((".", " "))):
        raise ValueError("Tên tệp trong danh sách ghép không hợp lệ")
    return value


def _manifest_size(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("Dung lượng trong danh sách ghép không hợp lệ")
    return value


def _manifest_digest(value: object) -> str:
    if (not isinstance(value, str) or len(value) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in value)):
        raise ValueError("Mã kiểm tra trong danh sách ghép không hợp lệ")
    return value.lower()


def split_file(source: Path, output: Path, part_size: int,
               cancelled: Callable[[], bool] | None = None,
               progress: Callable[[int, int], None] | None = None) -> Path:
    if part_size <= 0:
        raise ValueError("Dung lượng phần phải lớn hơn 0")
    _manifest_name(source.name)
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / f"{source.name}.manifest.json"
    if manifest.exists() or manifest.is_symlink():
        raise FileExistsError(f"Danh sách ghép đã tồn tại: {manifest.name}")
    manifest_temporary = manifest.with_suffix(manifest.suffix + ".tmp")
    manifest_created = False
    total = source.stat().st_size
    original_digest = sha256()
    parts: list[dict[str, object]] = []
    created: list[Path] = []
    processed = 0
    try:
        with source.open("rb") as reader:
            index = 1
            while processed < total:
                if cancelled and cancelled():
                    raise InterruptedError("Đã hủy chia tệp")
                part_path = output / f"{source.name}.{index:03d}"
                part_digest = sha256()
                part_written = 0
                with part_path.open("xb") as writer:
                    created.append(part_path)
                    while part_written < part_size:
                        if cancelled and cancelled():
                            raise InterruptedError("Đã hủy chia tệp")
                        chunk = reader.read(min(COPY_CHUNK_SIZE, part_size - part_written))
                        if not chunk:
                            break
                        writer.write(chunk)
                        original_digest.update(chunk)
                        part_digest.update(chunk)
                        part_written += len(chunk)
                        processed += len(chunk)
                        if progress:
                            progress(processed, total)
                if not part_written:
                    part_path.unlink(missing_ok=True)
                    created.pop()
                    break
                parts.append({"name": part_path.name, "size": part_written,
                              "sha256": part_digest.hexdigest()})
                index += 1
        if processed != total:
            raise OSError("Dung lượng tệp nguồn thay đổi trong lúc chia")
        payload = {
            "format": "zip-part-maker-split-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "original_name": source.name,
            "original_size": total,
            "original_sha256": original_digest.hexdigest(),
            "parts": parts,
        }
        if cancelled and cancelled():
            raise InterruptedError("Đã hủy chia tệp")
        with manifest_temporary.open("x", encoding="utf-8") as writer:
            manifest_created = True
            writer.write(json.dumps(payload, ensure_ascii=False, indent=2))
        manifest_temporary.replace(manifest)
        return manifest
    except BaseException:
        if manifest_created:
            manifest_temporary.unlink(missing_ok=True)
        for path in created:
            path.unlink(missing_ok=True)
        raise


def join_file(manifest_path: Path, output: Path,
              cancelled: Callable[[], bool] | None = None,
              progress: Callable[[int, int], None] | None = None) -> Path:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("format") != "zip-part-maker-split-v1":
        raise ValueError("Danh sách ghép không đúng định dạng")
    name = _manifest_name(payload.get("original_name"))
    total = _manifest_size(payload.get("original_size"))
    original_digest = _manifest_digest(payload.get("original_sha256"))
    parts = payload.get("parts")
    if not isinstance(parts, list) or (not parts and total != 0):
        raise ValueError("Danh sách ghép thiếu các phần của tệp")
    checked_parts: list[tuple[Path, int, str]] = []
    names: set[str] = set()
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError("Thông tin phần tệp không hợp lệ")
        part_name = _manifest_name(part.get("name"))
        if part_name in names:
            raise ValueError("Danh sách ghép có phần tệp trùng lặp")
        names.add(part_name)
        part_path = manifest_path.parent / part_name
        if part_path.is_symlink() or not part_path.is_file():
            raise ValueError(f"Phần tệp bị thiếu hoặc không hợp lệ: {part_name}")
        checked_parts.append((part_path, _manifest_size(part.get("size")),
                              _manifest_digest(part.get("sha256"))))
    if sum(size for _, size, _ in checked_parts) != total:
        raise ValueError("Tổng dung lượng các phần không khớp danh sách ghép")
    if cancelled and cancelled():
        raise InterruptedError("Đã hủy ghép tệp")
    output.mkdir(parents=True, exist_ok=True)
    target = unique_path(output / name)
    temporary = target.with_name(target.name + ".joining.tmp")
    created = False
    processed = 0
    digest = sha256()
    try:
        with temporary.open("xb") as writer:
            created = True
            for part_path, expected_size, expected_digest in checked_parts:
                part_digest = sha256()
                part_size = 0
                with part_path.open("rb") as reader:
                    while True:
                        if cancelled and cancelled():
                            raise InterruptedError("Đã hủy ghép tệp")
                        chunk = reader.read(COPY_CHUNK_SIZE)
                        if not chunk:
                            break
                        part_size += len(chunk)
                        if part_size > expected_size:
                            raise ValueError(f"Dung lượng phần tệp không khớp: {part_path.name}")
                        part_digest.update(chunk)
                        digest.update(chunk)
                        writer.write(chunk)
                        processed += len(chunk)
                        if progress:
                            progress(processed, total)
                if part_size != expected_size:
                    raise ValueError(f"Dung lượng phần tệp không khớp: {part_path.name}")
                if part_digest.hexdigest() != expected_digest:
                    raise ValueError(f"Mã kiểm tra (SHA-256) phần tệp không khớp: {part_path.name}")
        if processed != total or digest.hexdigest() != original_digest:
            raise ValueError("Tệp ghép không khớp danh sách ghép")
        if cancelled and cancelled():
            raise InterruptedError("Đã hủy ghép tệp")
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Tệp kết quả đã tồn tại: {target.name}. Hãy ghép lại để tạo tên mới.")
        temporary.replace(target)
        return target
    except BaseException:
        if created:
            temporary.unlink(missing_ok=True)
        raise
