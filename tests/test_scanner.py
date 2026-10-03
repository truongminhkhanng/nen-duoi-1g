from pathlib import Path

import pytest

from app.core.scanner import scan_files


def test_scans_unicode_and_empty_files(tmp_path: Path) -> None:
    source = tmp_path / "nguồn"
    nested = source / "thư mục"
    nested.mkdir(parents=True)
    (nested / "tiếng Việt.txt").write_text("xin chào", encoding="utf-8")
    (source / "rỗng.txt").touch()
    result = scan_files(source, source / "ZIP_PARTS")
    assert [x.relative_path.as_posix() for x in result.files] == ["rỗng.txt", "thư mục/tiếng Việt.txt"]


def test_empty_directory_and_ignored_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = source / "ZIP_PARTS"
    output.mkdir(parents=True)
    (output / "old.zip").write_bytes(b"old")
    (source / ".DS_Store").touch()
    assert scan_files(source, output).files == []


def test_non_recursive(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "top.txt").touch()
    (tmp_path / "sub" / "nested.txt").touch()
    result = scan_files(tmp_path, recursive=False, skip_hidden=False)
    assert [x.relative_path.as_posix() for x in result.files] == ["top.txt"]


def test_cancellation_is_not_returned_as_a_scan_error(tmp_path: Path) -> None:
    (tmp_path / "data.txt").write_text("data")
    with pytest.raises(InterruptedError):
        scan_files(tmp_path, cancelled=lambda: True)
