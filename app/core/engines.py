from __future__ import annotations

import platform
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

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


def find_winrar(system: str | None = None) -> str | None:
    if (system or platform.system()) != "Windows":
        return None
    candidates = [shutil.which("WinRAR.exe"), shutil.which("WinRAR")]
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        if base := os.environ.get(variable):
            candidates.append(str(Path(base) / "WinRAR" / "WinRAR.exe"))
    return next((path for path in candidates if path and Path(path).is_file()), None)


def resolve_engine(requested: CompressionEngine, keep_structure: bool = True,
                   system: str | None = None) -> EngineInfo:
    current = system or platform.system()
    if current == "Darwin":
        return EngineInfo(CompressionEngine.PYTHON, "Công cụ tích hợp",
                          fallback_reason="macOS sử dụng công cụ nén tích hợp")
    if requested == CompressionEngine.PYTHON:
        return EngineInfo(CompressionEngine.PYTHON, "Công cụ tích hợp")
    if not keep_structure:
        return EngineInfo(CompressionEngine.PYTHON, "Công cụ tích hợp",
                          fallback_reason="7-Zip và WinRAR cần bật Giữ cấu trúc thư mục")
    if requested == CompressionEngine.WINRAR:
        if current != "Windows":
            return EngineInfo(CompressionEngine.PYTHON, "Công cụ tích hợp",
                              fallback_reason="WinRAR tạo ZIP chỉ được hỗ trợ trên Windows")
        executable = find_winrar(current)
        if executable:
            return EngineInfo(CompressionEngine.WINRAR, "WinRAR", executable)
        return EngineInfo(CompressionEngine.PYTHON, "Công cụ tích hợp",
                          fallback_reason="Không tìm thấy WinRAR")
    executable = find_7zip(current)
    if executable:
        return EngineInfo(CompressionEngine.SEVEN_ZIP, "7-Zip", executable)
    return EngineInfo(CompressionEngine.PYTHON, "Công cụ tích hợp",
                      fallback_reason="Không tìm thấy 7-Zip")
