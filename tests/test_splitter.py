from pathlib import Path

import pytest

from app.core.splitter import COPY_CHUNK_SIZE, join_file, split_file


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


def test_split_streams_large_parts_in_bounded_chunks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "large.bin"
    source.write_bytes(b"x" * (COPY_CHUNK_SIZE * 2 + 17))
    requested_sizes: list[int] = []
    original_open = Path.open

    class TrackingReader:
        def __init__(self, stream: object) -> None:
            self.stream = stream

        def __enter__(self) -> "TrackingReader":
            self.stream.__enter__()
            return self

        def __exit__(self, *args: object) -> object:
            return self.stream.__exit__(*args)

        def read(self, size: int = -1) -> bytes:
            requested_sizes.append(size)
            return self.stream.read(size)

    def tracking_open(path: Path, *args: object, **kwargs: object) -> object:
        stream = original_open(path, *args, **kwargs)
        return TrackingReader(stream) if path == source and args[:1] == ("rb",) else stream

    monkeypatch.setattr(Path, "open", tracking_open)
    split_file(source, tmp_path / "parts", COPY_CHUNK_SIZE * 2)

    assert requested_sizes
    assert max(requested_sizes) <= COPY_CHUNK_SIZE
