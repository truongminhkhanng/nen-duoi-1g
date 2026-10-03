"""Isolated stdlib tests. Fixtures never touch application sources."""
from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.codeintel.indexer import (build, connect, explore, impact, main,
                                     relations, search, status, update)


class CodeIntelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write(".agent/codegraph-ignore", "private/\n")
        self.write("app/core/logic.py", '''
SECRET_VALUE = "literal-must-not-enter-cache"
def leaf(value: int = 1) -> int:
    return value
def run() -> int:
    return leaf(1)
class Service:
    def execute(self):
        return run()
'''.lstrip())
        self.write("tests/test_logic.py", '''
from app.core.logic import run as pack, Service
def test_run():
    service = Service()
    service.execute()
    assert pack() == 1
'''.lstrip())
        self.write("app/ui/styles.py", '''LIGHT_STYLE = """
QLabel#pageTitle { color: #123456; }
QPushButton { background: #654321; }
"""
''')
        self.write("app/ui/main_window.py", '''
from PySide6.QtWidgets import QMainWindow, QLabel
from app.ui.styles import LIGHT_STYLE
class MainWindow(QMainWindow):
    def __init__(self):
        self.setStyleSheet(LIGHT_STYLE)
        self.title = QLabel("private-label-must-not-enter-cache")
        self.title.setObjectName("pageTitle")
        self.title.clicked.connect(self.activate)
    def activate(self):
        self.close()
'''.lstrip())

    def write(self, path: str, content: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def test_status_content_hash_add_delete_and_noop(self) -> None:
        self.assertFalse(status(self.root)["index_exists"])
        build(self.root)
        self.assertFalse(status(self.root)["stale"])
        self.assertEqual(update(self.root)["action"], "unchanged")
        path = self.root / "app/core/logic.py"
        old_stat = path.stat()
        original = path.read_bytes()
        path.write_bytes(original.replace(b"return value", b"return False"))
        import os
        os.utime(path, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
        self.assertEqual(path.stat().st_size, old_stat.st_size)
        self.assertIn({"path": "app/core/logic.py", "change": "modified"}, status(self.root)["changed_files"])
        self.assertEqual(update(self.root)["action"], "rebuilt")
        self.write("app/new.py", "def added(): pass\n")
        (self.root / "tests/test_logic.py").unlink()
        changes = status(self.root)["changed_files"]
        self.assertIn({"path": "app/new.py", "change": "added"}, changes)
        self.assertIn({"path": "tests/test_logic.py", "change": "deleted"}, changes)
        update(self.root)
        with connect(self.root) as db:
            self.assertTrue(search(db, "added")["matches"])
            self.assertFalse(search(db, "test_run")["matches"])

    def test_calls_import_alias_instances_and_impact(self) -> None:
        build(self.root)
        with connect(self.root) as db:
            callers = relations(db, "app.core.logic.run", "callers", 100)["relationships"]
            self.assertEqual({e["source"] for e in callers}, {"app.core.logic.Service.execute", "tests.test_logic.test_run"})
            callees = relations(db, "app.core.logic.run", "callees", 100)["relationships"]
            self.assertTrue(any(e["target"] == "app.core.logic.leaf" for e in callees))
            instance = relations(db, "app.core.logic.Service.execute", "callers", 100)["relationships"]
            self.assertTrue(any(e["confidence"] == "heuristic" for e in instance))
            result = impact(db, "app.core.logic.leaf", 100)
            self.assertIn("tests/test_logic.py", result["tests"])
            self.assertEqual(result["confidence"], "heuristic")

    def test_qt_style_links_and_lines(self) -> None:
        build(self.root)
        with connect(self.root) as db:
            result = explore(db, "pageTitle", 100)
            self.assertIn("app/ui/styles.py", result["relevant_files"])
            self.assertTrue(any(e["kind"] == "style_candidate" for e in result["styles"]))
            for edge in result["styles"]:
                if edge["kind"] == "style_candidate":
                    self.assertIn("pageTitle", edge["target"])
                    self.assertEqual(edge["confidence"], "heuristic")
            selector = next(s for s in search(db, "QLabel#pageTitle")["matches"] if s["kind"] == "selector")
            lines = (self.root / selector["path"]).read_text().splitlines()
            self.assertIn("QLabel#pageTitle", lines[selector["line_start"] - 1])
            component = next(s for s in search(db, "MainWindow")["matches"] if s["kind"] == "component")
            self.assertEqual(component["line_end"], 10)

    def test_sensitive_exclusion_and_no_literal_storage(self) -> None:
        marker = "credential-fixture-must-never-be-indexed"
        self.write("private/data.py", f'VALUE = "{marker}"\n')
        self.write("nested/.env.py", f'VALUE = "{marker}"\n')
        self.write("nested/credentials.py", f'VALUE = "{marker}"\n')
        self.write(".aws/config.py", f'VALUE = "{marker}"\n')
        self.write("app/annotated.py", 'def login(password="password-not-for-index") -> "annotation-secret": pass\n')
        build(self.root)
        with connect(self.root) as db:
            dump = "\n".join(db.iterdump())
            for secret in (marker, "literal-must-not-enter-cache", "private-label-must-not-enter-cache", "password-not-for-index", "annotation-secret"):
                self.assertNotIn(secret, dump)
            paths = [r[0] for r in db.execute("SELECT path FROM files")]
            self.assertNotIn("private/data.py", paths)
            self.assertNotIn("nested/credentials.py", paths)

    def test_policy_manifest_tool_and_parser_versions(self) -> None:
        self.write("pyproject.toml", '[project]\nname="fixture"\n')
        self.write("requirements.txt", "PySide6>=6.7,<7\n")
        build(self.root)
        self.write("requirements.txt", "PySide6>=6.8,<7\n")
        self.assertTrue(status(self.root)["stale"])
        update(self.root)
        self.write(".agent/codegraph-ignore", "private/\napp/core/\n")
        self.assertIn("policy_hash changed", status(self.root)["reasons"])
        update(self.root)
        with connect(self.root) as db:
            self.assertFalse(search(db, "leaf")["matches"])
        path = self.root / ".agent/codegraph.sqlite"
        with contextlib.closing(sqlite3.connect(path)) as db, db:
            state = json.loads(db.execute("SELECT value FROM metadata").fetchone()[0])
            state["schema"] = -1
            state["parser_version"] = "old"
            state["tool_hash"] = "old"
            db.execute("UPDATE metadata SET value=?", (json.dumps(state),))
        reasons = status(self.root)["reasons"]
        for expected in ("schema changed", "parser_version changed", "tool_hash changed"):
            self.assertIn(expected, reasons)

    def test_corrupt_cache_parse_error_and_stale_queries(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["--root", str(self.root), "search", "leaf"]), 2)
        self.assertIn("stale", output.getvalue())
        self.write("app/broken.py", 'def bad(: "error-secret"\n')
        build(self.root)
        self.assertEqual(status(self.root)["parse_errors"][0]["path"], "app/broken.py")
        with connect(self.root) as db:
            self.assertNotIn("error-secret", "\n".join(db.iterdump()))
        (self.root / ".agent/codegraph.sqlite").write_bytes(b"corrupt")
        self.assertTrue(status(self.root)["stale"])
        update(self.root)
        self.assertFalse(status(self.root)["stale"])

    def test_ambiguous_symbols_unresolved_receivers_and_shadowing(self) -> None:
        self.write("app/other.py", '''
from app.core.logic import run
def leaf(): pass
def ambiguous(run):
    run()
    unknown.leaf()
'''.lstrip())
        build(self.root)
        with connect(self.root) as db:
            self.assertTrue(relations(db, "leaf", "callers", 100)["ambiguous"])
            callees = relations(db, "app.other.ambiguous", "callees", 100)["relationships"]
            self.assertTrue(all(e["confidence"] == "unresolved" for e in callees))

    def test_bare_name_does_not_bind_to_unrelated_module(self) -> None:
        self.write("main.py", "def main(): pass\nmain()\n")
        self.write("app/cli.py", "def main(): pass\n")
        self.write("app/entry.py", "from app.cli import main\nmain()\n")
        build(self.root)
        with connect(self.root) as db:
            calls = relations(db, "app.cli.main", "callers", 100)["relationships"]
            self.assertEqual({e["source"] for e in calls}, {"app.entry"})
            self.assertFalse(list(db.execute("SELECT * FROM edges WHERE kind='calls' AND target='main'")))
            self.assertEqual(relations(db, "main.main", "callers", 100)["relationships"][0]["source"], "main")

    def test_narrow_explore_keeps_exact_files_and_styles(self) -> None:
        self.write("app/unrelated.py", "def unrelated(): pass\n")
        window = self.root / "app/ui/main_window.py"
        window.write_text("from app.unrelated import unrelated\n" + window.read_text(), encoding="utf-8")
        build(self.root)
        with connect(self.root) as db:
            result = explore(db, "pageTitle", 5)
            self.assertEqual(result["relevant_files"][:2], ["app/ui/main_window.py", "app/ui/styles.py"])
            self.assertNotIn("app/unrelated.py", result["relevant_files"])
            self.assertTrue(any(e["kind"] == "style_candidate" for e in result["relationships"]))

    def test_qt_core_objects_and_layouts_are_not_styled_widgets(self) -> None:
        self.write("app/ui/extra.py", '''
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QVBoxLayout
from app.ui.styles import LIGHT_STYLE
def build():
    settings = QSettings()
    layout = QVBoxLayout()
    window.setStyleSheet(LIGHT_STYLE)
'''.lstrip())
        build(self.root)
        with connect(self.root) as db:
            edges = list(db.execute("SELECT * FROM edges WHERE kind='style_candidate' AND path='app/ui/extra.py'"))
            self.assertFalse(edges)

    def test_symlinks_are_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            private = Path(outside) / "private.py"
            private.write_text('VALUE = "outside-secret"\n')
            try:
                (self.root / "app/link.py").symlink_to(private)
                (self.root / "linked").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unavailable on this platform")
            build(self.root)
            with connect(self.root) as db:
                paths = [r[0] for r in db.execute("SELECT path FROM files")]
                self.assertNotIn("app/link.py", paths)
                self.assertNotIn("linked/private.py", paths)

    def test_every_cli_command(self) -> None:
        for command in (["status"], ["index"], ["update"], ["search", "leaf"],
                        ["explore", "pageTitle"], ["callers", "run"],
                        ["callees", "run"], ["impact", "app/core/logic.py"]):
            with self.subTest(command=command), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["--root", str(self.root), *command]), 0)
                self.assertIsInstance(json.loads(output.getvalue()), dict)


if __name__ == "__main__":
    unittest.main()
