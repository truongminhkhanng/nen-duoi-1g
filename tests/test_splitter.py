import json
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
    with pytest.raises(ValueError, match="SHA-256"):
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


def test_empty_file_can_be_split_and_joined(tmp_path: Path) -> None:
    source = tmp_path / "empty.bin"
    source.touch()
    manifest = split_file(source, tmp_path / "parts", 10)
    joined = join_file(manifest, tmp_path / "joined")
    assert joined.read_bytes() == b""


def test_join_preserves_existing_target_and_temporary(tmp_path: Path) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"original")
    manifest = split_file(source, tmp_path / "parts", 3)
    joined = join_file(manifest, tmp_path)
    assert joined.name == "data_1.bin"
    assert source.read_bytes() == joined.read_bytes() == b"original"
    output = tmp_path / "joined"
    output.mkdir()
    temporary = output / "data.bin.joining.tmp"
    temporary.write_bytes(b"another task")
    with pytest.raises(FileExistsError):
        join_file(manifest, output)
    assert temporary.read_bytes() == b"another task"
    assert not (output / "data.bin").exists()


@pytest.mark.parametrize("field", ["original_name", "part_name"])
@pytest.mark.parametrize("name", ["../outside.bin", "/tmp/outside.bin", "..\\outside.bin",
                                  "C:\\outside.bin", "nested/file.bin", "", "..", "NUL", "x\x00y"])
def test_join_rejects_unsafe_names_before_creating_output(tmp_path: Path, field: str, name: str) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"abc")
    manifest = split_file(source, tmp_path / "parts", 3)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if field == "original_name":
        payload[field] = name
    else:
        payload["parts"][0]["name"] = name
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        join_file(manifest, tmp_path / "joined")
    assert not (tmp_path / "joined").exists()
    assert source.read_bytes() == b"abc"


@pytest.mark.parametrize("payload", [[], None, {"format": "zip-part-maker-split-v1"},
                                    {"format": "wrong"}])
def test_join_rejects_invalid_manifest_shape(tmp_path: Path, payload: object) -> None:
    manifest = tmp_path / "bad.manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        join_file(manifest, tmp_path / "joined")
    assert not (tmp_path / "joined").exists()


def test_join_rejects_symlink_part(tmp_path: Path) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"abc")
    manifest = split_file(source, tmp_path / "parts", 3)
    part = manifest.parent / "data.bin.001"
    part.unlink()
    try:
        part.symlink_to(source)
    except OSError:
        pytest.skip("Symlink creation is unavailable on this platform")
    with pytest.raises(ValueError):
        join_file(manifest, tmp_path / "joined")
    assert source.read_bytes() == b"abc"


def test_join_cancels_within_a_large_part(tmp_path: Path) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"x" * (COPY_CHUNK_SIZE * 3))
    manifest = split_file(source, tmp_path / "parts", source.stat().st_size)
    progress: list[int] = []
    with pytest.raises(InterruptedError):
        join_file(manifest, tmp_path / "joined", lambda: bool(progress),
                  lambda done, _total: progress.append(done))
    assert progress == [COPY_CHUNK_SIZE]
    assert list((tmp_path / "joined").iterdir()) == []
    assert (manifest.parent / "data.bin.001").stat().st_size == COPY_CHUNK_SIZE * 3


def test_split_preserves_existing_manifest_and_cleans_only_owned_parts(tmp_path: Path) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"abc")
    output = tmp_path / "parts"
    output.mkdir()
    temporary = output / "data.bin.manifest.json.tmp"
    temporary.write_bytes(b"another task")
    with pytest.raises(FileExistsError):
        split_file(source, output, 2)
    assert list(output.iterdir()) == [temporary]
    assert temporary.read_bytes() == b"another task"
    temporary.unlink()
    manifest = split_file(source, output, 2)
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        split_file(source, output, 2)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == before
    assert manifest.is_file()


@pytest.mark.parametrize("field,value", [("original_size", -1), ("original_size", True),
                                          ("original_sha256", "bad"), ("parts", None)])
def test_join_validates_metadata(tmp_path: Path, field: str, value: object) -> None:
    source = tmp_path / "data.bin"
    source.write_bytes(b"abc")
    manifest = split_file(source, tmp_path / "parts", 3)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload[field] = value
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        join_file(manifest, tmp_path / "joined")
    assert not (tmp_path / "joined").exists()
