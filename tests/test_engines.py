from app.core import engines
from app.core.models import CompressionEngine


def test_auto_uses_7zip_on_windows_when_available(monkeypatch) -> None:
    monkeypatch.setattr(engines.shutil, "which",
                        lambda name: "C:/7-Zip/7z.exe" if name == "7z.exe" else None)
    info = engines.resolve_engine(CompressionEngine.AUTO, system="Windows")
    assert info.engine == CompressionEngine.SEVEN_ZIP
    assert info.executable == "C:/7-Zip/7z.exe"


def test_auto_falls_back_when_7zip_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(engines.shutil, "which", lambda _name: None)
    info = engines.resolve_engine(CompressionEngine.AUTO, system="Linux")
    assert info.engine == CompressionEngine.PYTHON
    assert info.fallback_reason == "Không tìm thấy 7-Zip"


def test_macos_always_uses_python(monkeypatch) -> None:
    monkeypatch.setattr(engines.shutil, "which", lambda _name: "/usr/local/bin/7zz")
    info = engines.resolve_engine(CompressionEngine.SEVEN_ZIP, system="Darwin")
    assert info.engine == CompressionEngine.PYTHON


def test_flat_archives_use_python_to_preserve_names(monkeypatch) -> None:
    monkeypatch.setattr(engines.shutil, "which", lambda _name: "/usr/bin/7zz")
    info = engines.resolve_engine(CompressionEngine.AUTO, keep_structure=False, system="Linux")
    assert info.engine == CompressionEngine.PYTHON
    assert "Giữ cấu trúc" in (info.fallback_reason or "")
