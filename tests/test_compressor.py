from pathlib import Path
import sys
from zipfile import ZIP_STORED, ZipFile

import pytest

from app.core.compressor import CompressionController, Compressor
from app.core.models import (ArchiveGroup, CompressionEngine, CompressionOptions,
                             ConflictAction, FileEntry, FileStatus, OversizeAction)


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


def test_winrar_command_creates_zip_with_unicode_list(monkeypatch, tmp_path: Path) -> None:
    source, output = tmp_path / "source", tmp_path / "out"
    path = source / "thư mục" / "tệp.txt"
    path.parent.mkdir(parents=True)
    path.write_text("nội dung", encoding="utf-8")
    item = FileEntry(path, path.relative_to(source), path.stat().st_size)

    class FakeProcess:
        returncode = 0

        def __init__(self, command, cwd, **_kwargs):
            assert "-afzip" in command
            assert "-scul" in command
            archive_path = Path(command[-2])
            names = Path(command[-1][1:]).read_text(encoding="utf-16").splitlines()
            with ZipFile(archive_path, "w") as archive:
                for name in names:
                    archive.write(Path(cwd) / name, name)

        def poll(self):
            return self.returncode

        def communicate(self, timeout=None):
            return ("", None)

    monkeypatch.setattr("app.core.compressor.subprocess.Popen", FakeProcess)
    options = CompressionOptions(source, output, 1024 * 1024,
                                 engine=CompressionEngine.WINRAR,
                                 engine_executable="WinRAR.exe")
    report = Compressor(options).run([ArchiveGroup([item], item.size)], [])
    with ZipFile(output / "part_001.zip") as archive:
        assert archive.read("thư mục/tệp.txt").decode() == "nội dung"
    assert report["compression_engine"] == "winrar"


def test_failed_overwrite_preserves_old_archive_and_unrelated_temporary(tmp_path: Path) -> None:
    source, output = tmp_path / "source", tmp_path / "out"
    source.mkdir()
    output.mkdir()
    path = source / "x.bin"
    path.write_bytes(b"x" * 100)
    old = output / "part_001.zip"
    old.write_bytes(b"previous archive")
    temporary = output / "part_001.zip.tmp"
    temporary.write_bytes(b"another task")
    item = FileEntry(path, Path("x.bin"), 100)
    options = CompressionOptions(source, output, 101, compression=ZIP_STORED,
                                 compresslevel=None, conflict_action=ConflictAction.OVERWRITE)
    report = Compressor(options).run([ArchiveGroup([item], 100)], [])
    assert report["errors"]
    assert old.read_bytes() == b"previous archive"
    assert temporary.read_bytes() == b"another task"
    assert item.status == FileStatus.ERROR
    assert not list(output.glob(".part_001.zip.*"))


def test_cancel_during_archive_propagates_and_cleans_staging(tmp_path: Path) -> None:
    path = tmp_path / "data.bin"
    path.write_bytes(b"abc")
    item = FileEntry(path, Path("data.bin"), 3)
    controller = CompressionController()
    options = CompressionOptions(tmp_path, tmp_path / "out", 1000)
    with pytest.raises(InterruptedError):
        Compressor(options, controller, on_progress=lambda *_args: controller.cancel()).run(
            [ArchiveGroup([item], 3)], [])
    assert list(options.output.iterdir()) == []
    assert path.read_bytes() == b"abc"


def test_split_failure_is_reported_and_later_files_still_processed(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    items = []
    for name in ("a.bin", "b.bin"):
        path = tmp_path / name
        path.write_bytes(b"abcdef")
        items.append(FileEntry(path, Path(name), 6))
    (output / "a.bin.manifest.json").write_bytes(b"existing manifest")
    options = CompressionOptions(tmp_path, output, 4, oversize_action=OversizeAction.SPLIT)
    progress = []
    report = Compressor(options, on_progress=lambda done, total, *_: progress.append((done, total))).run([], items)
    assert len(report["errors"]) == 1
    assert items[0].status == FileStatus.ERROR
    assert items[1].status == FileStatus.DONE
    assert (output / "a.bin.manifest.json").read_bytes() == b"existing manifest"
    assert (output / "b.bin.manifest.json").is_file()
    assert progress[-1] == (12, 12)
    assert report["split_files"] == [{"file": "b.bin", "manifest": "b.bin.manifest.json"}]


def test_clean_matches_a_literal_prefix_and_preserves_other_archives(tmp_path: Path) -> None:
    source, output = tmp_path / "source", tmp_path / "out"
    source.mkdir()
    output.mkdir()
    matching = output / "part[ab]_001.zip"
    unrelated = output / "parta_001.zip"
    matching.write_bytes(b"matching")
    unrelated.write_bytes(b"unrelated")
    options = CompressionOptions(source, output, 1000, prefix="part[ab]",
                                 conflict_action=ConflictAction.CLEAN)
    Compressor(options).run([], [])
    assert not matching.exists()
    assert unrelated.read_bytes() == b"unrelated"


def test_output_equal_to_source_is_rejected_before_cleaning(tmp_path: Path) -> None:
    original = tmp_path / "part_001.zip"
    original.write_bytes(b"source archive")
    options = CompressionOptions(tmp_path, tmp_path, 1000, conflict_action=ConflictAction.CLEAN)
    with pytest.raises(ValueError, match="khác"):
        Compressor(options).run([], [])
    assert original.read_bytes() == b"source archive"


def test_successful_overwrite_replaces_old_archive_after_verification(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    original = output / "part_001.zip"
    original.write_bytes(b"old archive")
    path = tmp_path / "data.bin"
    path.write_bytes(b"abc")
    item = FileEntry(path, Path("data.bin"), 3)
    options = CompressionOptions(tmp_path, output, 1000, conflict_action=ConflictAction.OVERWRITE)
    report = Compressor(options).run([ArchiveGroup([item], 3)], [])
    assert not report["errors"]
    with ZipFile(original) as archive:
        assert archive.read("data.bin") == b"abc"
    assert item.status == FileStatus.DONE


@pytest.mark.parametrize("action", [OversizeAction.TRY_COMPRESS, OversizeAction.SPLIT])
def test_cancellation_during_oversize_work_propagates(tmp_path: Path, action: OversizeAction) -> None:
    path = tmp_path / "data.bin"
    path.write_bytes(b"x" * 300)
    item = FileEntry(path, Path("data.bin"), 300)
    controller = CompressionController()
    options = CompressionOptions(tmp_path, tmp_path / "out", 200, oversize_action=action)
    with pytest.raises(InterruptedError):
        Compressor(options, controller, on_progress=lambda *_: controller.cancel()).run([], [item])
    assert list(options.output.iterdir()) == []


def test_external_engine_output_is_drained_without_deadlock(tmp_path: Path, monkeypatch) -> None:
    import subprocess

    helper = tmp_path / "verbose_engine.py"
    helper.write_text(
        "import os, sys, threading\n"
        "from zipfile import ZipFile\n"
        "watchdog = threading.Timer(5, lambda: os._exit(2))\n"
        "watchdog.daemon = True\n"
        "watchdog.start()\n"
        "sys.stdout.write('x' * 262144)\n"
        "sys.stdout.flush()\n"
        "with ZipFile(sys.argv[1], 'w') as archive:\n"
        "    archive.writestr('data.bin', b'abc')\n",
        encoding="utf-8",
    )
    real_popen = subprocess.Popen

    def verbose_process(command, **kwargs):
        return real_popen([sys.executable, str(helper), command[-2]], **kwargs)

    monkeypatch.setattr("app.core.compressor.subprocess.Popen", verbose_process)
    path = tmp_path / "data.bin"
    path.write_bytes(b"abc")
    item = FileEntry(path, Path("data.bin"), 3)
    options = CompressionOptions(tmp_path, tmp_path / "out", 1000,
                                 engine=CompressionEngine.SEVEN_ZIP, engine_executable="verbose-engine")
    report = Compressor(options).run([ArchiveGroup([item], 3)], [])
    assert not report["errors"]
    with ZipFile(options.output / "part_001.zip") as archive:
        assert archive.read("data.bin") == b"abc"
