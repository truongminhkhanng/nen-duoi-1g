from pathlib import Path

import pytest

from app.core.models import FileEntry, FileStatus
from app.core.planner import plan_archives


def entry(name: str, size: int) -> FileEntry:
    return FileEntry(Path("/source") / name, Path(name), size)


def test_first_fit_decreasing_reduces_groups() -> None:
    groups, oversized = plan_archives([entry("a", 60), entry("b", 40), entry("c", 60), entry("d", 40)], 102, 1.0)
    assert [group.estimated_size for group in groups] == [100, 100]
    assert oversized == []


def test_stable_tie_order_and_empty_file() -> None:
    groups, _ = plan_archives([entry("ổ.txt", 0), entry("b", 5), entry("a", 5)], 10, 1.0)
    assert [item.relative_path.name for item in groups[0].files] == ["a", "b", "ổ.txt"]


def test_oversized_file_is_marked() -> None:
    huge = entry("huge.bin", 101)
    groups, oversized = plan_archives([huge], 100, 1.0)
    assert not groups and oversized == [huge]
    assert huge.status == FileStatus.TOO_LARGE


def test_invalid_limit() -> None:
    with pytest.raises(ValueError):
        plan_archives([], 0)


def test_replanning_resets_old_statuses() -> None:
    item = entry("data.bin", 101)
    plan_archives([item], 100)
    assert item.status == FileStatus.TOO_LARGE
    groups, oversized = plan_archives([item], 200)
    assert groups and not oversized
    assert item.status == FileStatus.READY
