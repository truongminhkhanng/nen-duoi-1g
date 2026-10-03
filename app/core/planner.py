from __future__ import annotations

from app.core.models import ArchiveGroup, FileEntry, FileStatus

DEFAULT_SAFETY_RATIO = 0.98


def plan_archives(files: list[FileEntry], limit_bytes: int,
                  safety_ratio: float = DEFAULT_SAFETY_RATIO) -> tuple[list[ArchiveGroup], list[FileEntry]]:
    if limit_bytes <= 0 or not 0 < safety_ratio <= 1:
        raise ValueError("Giới hạn hoặc hệ số an toàn không hợp lệ")
    capacity = int(limit_bytes * safety_ratio)
    groups: list[ArchiveGroup] = []
    oversized: list[FileEntry] = []
    for entry in sorted(files, key=lambda item: (-item.size, item.relative_path.as_posix().casefold())):
        entry.status = FileStatus.READY
        entry.error = None
        if entry.size > capacity:
            entry.status = FileStatus.TOO_LARGE
            oversized.append(entry)
            continue
        for group in groups:
            if group.estimated_size + entry.size <= capacity:
                group.files.append(entry)
                group.estimated_size += entry.size
                break
        else:
            groups.append(ArchiveGroup([entry], entry.size))
    return groups, oversized
