import tomllib
from pathlib import Path

import app
from app.version import __version__


def test_package_versions_match() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert app.__version__ == __version__ == project["project"]["version"]
