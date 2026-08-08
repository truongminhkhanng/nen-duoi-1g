from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import pytest

from app.core.compressor import Compressor
from app.core.models import ArchiveGroup, CompressionOptions, FileEntry


def test_creates_independent_unicode_zip_and_report(tmp_path: Path) -> None:
    source, output = tmp_path / "nguồn", tmp_path / "out"
    source.mkdir()
    path = source / "thư mục" / "tệp.txt"
    path.parent.mkdir()
    path.write_text("nội dung", encoding="utf-8")
    item = FileEntry(path, path.relative_to(source), path.stat().st_size)
    options = CompressionOptions(source, output, 1024 * 1024, compression=ZIP_STORED, compresslevel=None)
    report = Compressor(options).run([ArchiveGroup([item], item.size)], [])
    archive_path = output / "part_001.zip"
    with ZipFile(archive_path) as archive:
        assert archive.read("thư mục/tệp.txt").decode() == "nội dung"
    assert report["archives"][0]["sha256"]
    assert (output / "zip_report.json").is_file()
    assert not (output / "part_001.zip.tmp").exists()


def test_rejects_archive_that_exceeds_limit(tmp_path: Path) -> None:
    source, output = tmp_path / "source", tmp_path / "out"
    source.mkdir()
    path = source / "x.bin"
    path.write_bytes(b"x" * 100)
    item = FileEntry(path, Path("x.bin"), 100)
    options = CompressionOptions(source, output, 101, compression=ZIP_STORED, compresslevel=None)
    report = Compressor(options).run([ArchiveGroup([item], 100)], [])
    assert not list(output.glob("*.zip"))
    assert report["errors"]


def test_repartitions_group_when_zip_metadata_exceeds_limit(tmp_path: Path) -> None:
    source, output = tmp_path / "source", tmp_path / "out"
    source.mkdir()
    entries = []
    for name in ("a.bin", "b.bin"):
        path = source / name
        path.write_bytes(b"x" * 100)
        entries.append(FileEntry(path, Path(name), 100))
    options = CompressionOptions(source, output, 300, compression=ZIP_STORED, compresslevel=None)
    report = Compressor(options).run([ArchiveGroup(entries, 200)], [])
    assert len(report["archives"]) == 2
    assert all(item["size"] < 300 for item in report["archives"])


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "x"
    path.write_text("x")
    item = FileEntry(path, Path("../x"), 1)
    options = CompressionOptions(tmp_path, tmp_path / "out", 1000)
    with pytest.raises(ValueError):
        Compressor(options).create_archive(ArchiveGroup([item], 1), 1, 0, 1)
