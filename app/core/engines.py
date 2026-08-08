from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass

from app.core.models import CompressionEngine


@dataclass(frozen=True, slots=True)
class EngineInfo:
    engine: CompressionEngine
    label: str
    executable: str | None = None
    fallback_reason: str | None = None


def find_7zip(system: str | None = None) -> str | None:
    current = system or platform.system()
    candidates = ("7z.exe", "7z") if current == "Windows" else ("7zz", "7z")
    return next((path for name in candidates if (path := shutil.which(name))), None)


def resolve_engine(requested: CompressionEngine, keep_structure: bool = True,
                   system: str | None = None) -> EngineInfo:
    current = system or platform.system()
    if current == "Darwin":
        return EngineInfo(CompressionEngine.PYTHON, "Python tích hợp",
                          fallback_reason="macOS luôn dùng engine Python")
    if requested == CompressionEngine.PYTHON:
        return EngineInfo(CompressionEngine.PYTHON, "Python tích hợp")
    if not keep_structure:
        return EngineInfo(CompressionEngine.PYTHON, "Python tích hợp",
                          fallback_reason="7-Zip cần bật Giữ cấu trúc thư mục")
    executable = find_7zip(current)
    if executable:
        return EngineInfo(CompressionEngine.SEVEN_ZIP, "7-Zip", executable)
    return EngineInfo(CompressionEngine.PYTHON, "Python tích hợp",
                      fallback_reason="Không tìm thấy 7-Zip")
