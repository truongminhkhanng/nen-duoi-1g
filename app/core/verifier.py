from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile, ZipFile

from app.utils.checksum import sha256_file


def verify_zip(path: Path) -> tuple[int, str]:
    try:
        with ZipFile(path, "r") as archive:
            bad = archive.testzip()
            if bad:
                raise BadZipFile(f"File lỗi trong ZIP: {bad}")
    except BadZipFile:
        raise
    return path.stat().st_size, sha256_file(path)
