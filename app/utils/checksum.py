from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable


def sha256_file(path: Path, chunk_size: int = 1024 * 1024,
                cancelled: Callable[[], bool] | None = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            if cancelled and cancelled():
                raise InterruptedError("Đã hủy")
            digest.update(chunk)
    return digest.hexdigest()
