from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

from app.core.models import (ArchiveGroup, ArchiveResult, CompressionOptions,
                             ConflictAction, FileEntry, FileStatus, OversizeAction)
from app.core.splitter import split_file
from app.core.verifier import verify_zip
from app.utils.paths import safe_archive_name, unique_path, validate_prefix


class ArchiveTooLargeError(ValueError):
    """A completed temporary archive exceeded the configured hard limit."""


class CompressionController:
    def __init__(self) -> None:
        self._cancelled = threading.Event()
        self._paused = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()
        self._paused.clear()

    def set_paused(self, paused: bool) -> None:
        self._paused.set() if paused else self._paused.clear()

    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def checkpoint(self) -> None:
        while self._paused.is_set() and not self._cancelled.is_set():
            time.sleep(0.1)
        if self._cancelled.is_set():
            raise InterruptedError("Đã hủy")


class Compressor:
    def __init__(self, options: CompressionOptions, controller: CompressionController | None = None,
                 on_log: Callable[[str], None] | None = None,
                 on_progress: Callable[[int, int, str, str, int], None] | None = None) -> None:
        self.options = options
        self.controller = controller or CompressionController()
        self.on_log = on_log or (lambda _message: None)
        self.on_progress = on_progress or (lambda *_args: None)

    def _target(self, index: int) -> Path:
        prefix = validate_prefix(self.options.prefix)
        path = self.options.output / f"{prefix}_{index:03d}.zip"
        if self.options.conflict_action == ConflictAction.RENAME:
            path = unique_path(path)
        elif path.exists() and self.options.conflict_action == ConflictAction.OVERWRITE:
            path.unlink()
        elif path.exists():
            raise FileExistsError(f"File đã tồn tại: {path.name}")
        return path

    def _arcname(self, entry: FileEntry, used: set[str]) -> str:
        relative = entry.relative_path if self.options.keep_structure else Path(entry.path.name)
        name = safe_archive_name(relative)
        if name not in used:
            used.add(name)
            return name
        base = Path(name)
        index = 1
        while True:
            candidate = safe_archive_name(base.with_name(f"{base.stem}_{index}{base.suffix}"))
            if candidate not in used:
                used.add(candidate)
                return candidate
            index += 1

    def create_archive(self, group: ArchiveGroup, index: int,
                       completed_before: int, total_bytes: int) -> ArchiveResult:
        self.options.output.mkdir(parents=True, exist_ok=True)
        target = self._target(index)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.unlink(missing_ok=True)
        archived: list[str] = []
        used: set[str] = set()
        current_total = max(group.estimated_size, 1)
        current_done = 0
        try:
            kwargs: dict[str, object] = {"mode": "x", "compression": self.options.compression,
                                         "allowZip64": True}
            if self.options.compresslevel is not None:
                kwargs["compresslevel"] = self.options.compresslevel
            with ZipFile(temporary, **kwargs) as archive:
                for entry in group.files:
                    self.controller.checkpoint()
                    entry.status = FileStatus.PROCESSING
                    arcname = self._arcname(entry, used)
                    self.on_progress(completed_before + current_done, total_bytes,
                                     entry.relative_path.as_posix(), target.name,
                                     int(current_done * 100 / current_total))
                    archive.write(entry.path, arcname)
                    archived.append(arcname)
                    current_done += entry.size
                    entry.status = FileStatus.DONE
            self.controller.checkpoint()
            size, digest = verify_zip(temporary)
            if size >= self.options.limit_bytes:
                raise ArchiveTooLargeError(
                    f"{target.name} có dung lượng {size} byte, vượt giới hạn"
                )
            temporary.replace(target)
            return ArchiveResult(target, size, digest, archived)
        except BaseException:
            temporary.unlink(missing_ok=True)
            for entry in group.files:
                if entry.status == FileStatus.PROCESSING:
                    entry.status = FileStatus.ERROR
            raise

    def run(self, groups: list[ArchiveGroup], oversized: list[FileEntry],
            scan_errors: list[str] | None = None) -> dict[str, object]:
        self.options.output.mkdir(parents=True, exist_ok=True)
        started = datetime.now(timezone.utc)
        total_bytes = sum(group.estimated_size for group in groups)
        completed = 0
        archives: list[ArchiveResult] = []
        skipped: list[str] = []
        errors = list(scan_errors or [])
        if self.options.conflict_action == ConflictAction.CLEAN:
            prefix = validate_prefix(self.options.prefix)
            for old in self.options.output.glob(f"{prefix}_[0-9][0-9][0-9]*.zip"):
                old.unlink()
        pending = list(groups)
        index = 1
        while pending:
            group = pending.pop(0)
            deferred = False
            self.controller.checkpoint()
            try:
                result = self.create_archive(group, index, completed, max(total_bytes, 1))
                archives.append(result)
                self.on_log(f"Đã tạo {result.path.name}")
                index += 1
            except ArchiveTooLargeError as error:
                if len(group.files) > 1:
                    midpoint = len(group.files) // 2
                    halves = (group.files[:midpoint], group.files[midpoint:])
                    pending[0:0] = [ArchiveGroup(items, sum(x.size for x in items)) for items in halves]
                    deferred = True
                    self.on_log(f"{error}; đang chia lại nhóm thành 2 ZIP")
                else:
                    group.files[0].status = FileStatus.ERROR
                    errors.append(str(error))
                    self.on_log(f"Lỗi: {error}")
            except (OSError, ValueError) as error:
                errors.append(str(error))
                self.on_log(f"Lỗi: {error}")
            if not deferred:
                completed += group.estimated_size
                self.on_progress(completed, max(total_bytes, 1), "", "", 100)
        next_index = index
        for entry in oversized:
            self.controller.checkpoint()
            if self.options.oversize_action == OversizeAction.SKIP:
                entry.status = FileStatus.SKIPPED
                skipped.append(entry.relative_path.as_posix())
            elif self.options.oversize_action == OversizeAction.SPLIT:
                manifest = split_file(entry.path, self.options.output,
                                      max(1, int(self.options.limit_bytes * 0.98)),
                                      self.controller.cancelled)
                entry.status = FileStatus.DONE
                self.on_log(f"Đã chia {entry.relative_path}: {manifest.name}")
            else:
                try:
                    result = self.create_archive(ArchiveGroup([entry], entry.size), next_index,
                                                 completed, max(total_bytes + entry.size, 1))
                    archives.append(result)
                    next_index += 1
                except (OSError, ValueError) as error:
                    entry.status = FileStatus.ERROR
                    errors.append(str(error))
        finished = datetime.now(timezone.utc)
        report: dict[str, object] = {
            "started_at": started.isoformat(), "finished_at": finished.isoformat(),
            "source": str(self.options.source), "output": str(self.options.output),
            "limit_bytes": self.options.limit_bytes,
            "total_files": sum(len(group.files) for group in groups) + len(oversized),
            "total_size": sum(group.estimated_size for group in groups) + sum(x.size for x in oversized),
            "archives": [{"name": x.path.name, "size": x.size, "sha256": x.sha256,
                           "files": x.files} for x in archives],
            "skipped_files": skipped, "errors": errors,
            "oversized_files": [x.relative_path.as_posix() for x in oversized],
        }
        report_path = self.options.output / "zip_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report
