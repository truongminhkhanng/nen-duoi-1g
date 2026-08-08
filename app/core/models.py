from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileStatus(str, Enum):
    READY = "Sẵn sàng"
    TOO_LARGE = "Quá lớn"
    PROCESSING = "Đang xử lý"
    DONE = "Hoàn thành"
    SKIPPED = "Bỏ qua"
    ERROR = "Lỗi"


class OversizeAction(str, Enum):
    SKIP = "skip"
    TRY_COMPRESS = "try_compress"
    SPLIT = "split"


class ConflictAction(str, Enum):
    OVERWRITE = "overwrite"
    RENAME = "rename"
    CLEAN = "clean"


class CompressionEngine(str, Enum):
    AUTO = "auto"
    SEVEN_ZIP = "7zip"
    PYTHON = "python"


@dataclass(slots=True)
class FileEntry:
    path: Path
    relative_path: Path
    size: int
    status: FileStatus = FileStatus.READY
    error: str | None = None


@dataclass(slots=True)
class ScanResult:
    files: list[FileEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        return sum(item.size for item in self.files)


@dataclass(slots=True)
class ArchiveGroup:
    files: list[FileEntry] = field(default_factory=list)
    estimated_size: int = 0


@dataclass(slots=True)
class ArchiveResult:
    path: Path
    size: int
    sha256: str
    files: list[str]


@dataclass(slots=True)
class CompressionOptions:
    source: Path
    output: Path
    limit_bytes: int
    prefix: str = "part"
    compression: int = 8
    compresslevel: int | None = 6
    keep_structure: bool = True
    conflict_action: ConflictAction = ConflictAction.RENAME
    oversize_action: OversizeAction = OversizeAction.SKIP
    engine: CompressionEngine = CompressionEngine.AUTO
    engine_executable: str | None = None
