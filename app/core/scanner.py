from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Callable

from app.core.models import FileEntry, ScanResult

IGNORED_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
IGNORED_DIRS = {"__MACOSX"}


def _hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if os.name == "nt":
        try:
            return bool(path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
        except (AttributeError, OSError):
            return False
    return False


def _system(path: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        return bool(path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM)
    except (AttributeError, OSError):
        return False


def scan_files(source: Path, output: Path | None = None, recursive: bool = True,
               skip_hidden: bool = True, skip_system: bool = True,
               cancelled: Callable[[], bool] | None = None,
               on_log: Callable[[str], None] | None = None) -> ScanResult:
    source = source.resolve()
    output_resolved = output.resolve() if output else None
    result = ScanResult()
    if not source.is_dir():
        raise ValueError("Thư mục nguồn không tồn tại")

    def on_error(error: OSError) -> None:
        message = f"Không thể truy cập: {error.filename or ''} ({error})"
        result.errors.append(message)
        if on_log:
            on_log(message)

    try:
        for root, dirs, names in os.walk(source, topdown=True, onerror=on_error,
                                         followlinks=False):
            if cancelled and cancelled():
                raise InterruptedError("Đã hủy quét")
            root_path = Path(root)
            kept_dirs: list[str] = []
            for dirname in dirs:
                directory = root_path / dirname
                try:
                    resolved = directory.resolve()
                    if directory.is_symlink() or dirname in IGNORED_DIRS:
                        continue
                    if output_resolved and (resolved == output_resolved or output_resolved in resolved.parents):
                        continue
                    if skip_hidden and _hidden(directory):
                        continue
                    if skip_system and _system(directory):
                        continue
                    kept_dirs.append(dirname)
                except (PermissionError, FileNotFoundError, OSError) as error:
                    on_error(error)
            dirs[:] = kept_dirs if recursive else []
            for name in names:
                if cancelled and cancelled():
                    raise InterruptedError("Đã hủy quét")
                path = root_path / name
                if name in IGNORED_NAMES or path.is_symlink():
                    continue
                try:
                    if skip_hidden and _hidden(path):
                        continue
                    if skip_system and _system(path):
                        continue
                    if path.is_file():
                        result.files.append(FileEntry(path, path.relative_to(source), path.stat().st_size))
                except (PermissionError, FileNotFoundError, OSError) as error:
                    on_error(error)
    except (PermissionError, FileNotFoundError, OSError) as error:
        on_error(error)
    result.files.sort(key=lambda item: item.relative_path.as_posix().casefold())
    return result
