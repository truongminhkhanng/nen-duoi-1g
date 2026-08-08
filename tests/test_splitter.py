from pathlib import Path

import pytest

from app.core.splitter import join_file, split_file


def test_split_manifest_and_join_unicode(tmp_path: Path) -> None:
    source = tmp_path / "video tiếng Việt.bin"
    content = bytes(range(256)) * 20
    source.write_bytes(content)
    parts = tmp_path / "parts"
    manifest = split_file(source, parts, 777)
    assert len(list(parts.glob("*.0??"))) == 7
    source.unlink()
    joined = join_file(manifest, tmp_path / "joined")
    assert joined.read_bytes() == content


def test_join_detects_corrupt_part(tmp_path: Path) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"abcdef")
    manifest = split_file(source, tmp_path / "parts", 3)
    (manifest.parent / "data.bin.001").write_bytes(b"bad")
    with pytest.raises(ValueError, match="Checksum"):
        join_file(manifest, tmp_path / "joined")
    assert not (tmp_path / "joined" / "data.bin.joining.tmp").exists()
