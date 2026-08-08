from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


def safe_archive_name(relative_path: Path) -> str:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Đường dẫn archive không an toàn: {relative_path}")
    parts = [p for p in relative_path.parts if p not in ("", ".", "..")]
    if not parts:
        raise ValueError(f"Đường dẫn archive không an toàn: {relative_path}")
    name = PurePosixPath(*parts).as_posix()
    if name.startswith("/") or ".." in PurePosixPath(name).parts:
        raise ValueError(f"Đường dẫn archive không an toàn: {relative_path}")
    return name


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(1, 10_000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise OSError("Không thể tạo tên file duy nhất")


def validate_prefix(prefix: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", prefix.strip())
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("Prefix tên ZIP không hợp lệ")
    return cleaned


def open_folder(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])
