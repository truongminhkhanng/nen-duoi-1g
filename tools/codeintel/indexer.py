"""Offline Python AST + SQLite navigation cache for Zip Part Maker.

Never imports application code or stores source bodies, docstrings or literal
values. Static resolution is deliberately conservative; unresolved calls stay
unresolved. Qt relationships are navigation hints, not runtime guarantees.
"""
from __future__ import annotations

import argparse
import ast
from collections.abc import Iterator
from contextlib import contextmanager
import fnmatch
import hashlib
import json
import os
import platform
import re
import sqlite3
import tempfile
import tokenize
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

VERSION = "1.0"
SCHEMA = 1
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".agent", ".agents", ".codex", ".aws", ".venv", "venv",
             "__pycache__", ".pytest_cache", "build", "dist", "node_modules",
             "HISTORY", ".ssh", ".gnupg"}
SUFFIXES = {".py", ".toml", ".md", ".txt", ".sh", ".ps1", ".yml", ".yaml"}
SENSITIVE = (".env*", "*secret*", "*credential*", "*password*", "*token*",
             "*private*key*", "auth.json", "*.pem", "*.key", "*.p12", "*.pfx")
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ignored(path: str, patterns: list[str]) -> bool:
    parts = Path(path).parts
    if any(p in SKIP_DIRS or p.endswith(".egg-info") for p in parts):
        return True
    if any(fnmatch.fnmatch(p.lower(), pat) for p in parts for pat in SENSITIVE):
        return True
    for pattern in patterns:
        pattern = pattern.strip("/")
        if fnmatch.fnmatchcase(path, pattern) or path.startswith(pattern + "/"):
            return True
        if "/" not in pattern and any(fnmatch.fnmatchcase(p, pattern) for p in parts):
            return True
    return False


def snapshot(root: Path) -> tuple[dict, dict[str, bytes]]:
    policy_path = root / ".agent/codegraph-ignore"
    policy = policy_path.read_bytes() if policy_path.is_file() else b""
    patterns = [line.strip() for line in policy.decode("utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
    files, sources = {}, {}
    for directory, dirs, names in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = sorted(d for d in dirs if not (base / d).is_symlink()
                         and not ignored((base / d).relative_to(root).as_posix(), patterns))
        for name in sorted(names):
            path = base / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink() or path.suffix not in SUFFIXES or ignored(rel, patterns):
                continue
            data = path.read_bytes()
            stat = path.stat()
            files[rel] = {"hash": digest(data), "size": len(data), "mtime_ns": stat.st_mtime_ns}
            sources[rel] = data
    return {"schema": SCHEMA, "tool_version": VERSION,
            "parser_version": "Python ast " + platform.python_version(),
            "tool_hash": digest(Path(__file__).read_bytes()), "policy_hash": digest(policy),
            "files": files}, sources


def cache_dir(root: Path) -> Path:
    path = root / ".agent"
    if path.is_symlink():
        raise ValueError(".agent must be a real project-local directory")
    return path


@contextmanager
def connect(root: Path) -> Iterator[sqlite3.Connection]:
    path = cache_dir(root) / "codegraph.sqlite"
    if path.is_symlink():
        raise ValueError("Index must not be a symlink")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def status(root: Path) -> dict:
    current, _ = snapshot(root)
    path = cache_dir(root) / "codegraph.sqlite"
    result = {"index_exists": path.is_file(), "index_version": None, "stale": True,
              "last_indexed": None, "tool_version": VERSION,
              "parser_version": current["parser_version"], "changed_files": [],
              "reasons": [], "parse_errors": []}
    previous = {}
    if path.is_file():
        try:
            with connect(root) as db:
                previous = json.loads(db.execute("SELECT value FROM metadata WHERE key='state'").fetchone()[0])
                # Validate the usable schema, not just a JSON sidecar.
                for table in ("files", "symbols", "edges"):
                    db.execute(f"SELECT * FROM {table} LIMIT 0")
            result.update(index_version=previous["schema"], last_indexed=previous["last_indexed"],
                          parse_errors=previous.get("parse_errors", []))
        except (sqlite3.Error, TypeError, KeyError, ValueError) as error:
            result["reasons"].append("Unreadable/incompatible cache: " + type(error).__name__)
            previous = {}
    else:
        result["reasons"].append("Index missing; run index")
    old_files, new_files = previous.get("files", {}), current["files"]
    for path in sorted(old_files.keys() | new_files.keys()):
        change = "added" if path not in old_files else "deleted" if path not in new_files else "modified"
        if old_files.get(path, {}).get("hash") != new_files.get(path, {}).get("hash"):
            result["changed_files"].append({"path": path, "change": change})
    for field in ("schema", "tool_version", "parser_version", "tool_hash", "policy_hash"):
        if previous.get(field) != current[field]:
            result["reasons"].append(field + " changed")
    result["stale"] = bool(result["reasons"] or result["changed_files"])
    return result


def dotted(node: ast.AST | None) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return base + "." + node.attr if base else ""
    return ""


def safe_type(node: ast.AST | None) -> str:
    # Retain type shape, never strings/default expressions (which may contain credentials).
    if node is None:
        return ""
    if isinstance(node, (ast.Name, ast.Attribute)):
        return dotted(node)
    if isinstance(node, ast.Subscript):
        return safe_type(node.value) + "[" + safe_type(node.slice) + "]"
    if isinstance(node, ast.Tuple):
        return ", ".join(safe_type(x) for x in node.elts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return safe_type(node.left) + " | " + safe_type(node.right)
    if isinstance(node, ast.Constant) and node.value is None:
        return "None"
    return "…"


def signature(node: ast.AST) -> str:
    if isinstance(node, ast.ClassDef):
        return "class " + node.name + "(" + ", ".join(safe_type(x) for x in node.bases) + ")"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = node.args
        items = [a.arg + (": " + safe_type(a.annotation) if a.annotation else "")
                 for a in args.posonlyargs + args.args]
        if args.posonlyargs:
            items.insert(len(args.posonlyargs), "/")
        if args.vararg:
            items.append("*" + args.vararg.arg)
        elif args.kwonlyargs:
            items.append("*")
        items.extend(a.arg + (": " + safe_type(a.annotation) if a.annotation else "") for a in args.kwonlyargs)
        if args.kwarg:
            items.append("**" + args.kwarg.arg)
        return node.name + "(" + ", ".join(items) + ")" + (" -> " + safe_type(node.returns) if node.returns else "")
    return ""


class Collector(ast.NodeVisitor):
    def __init__(self, path: str, tree: ast.AST):
        self.path = path
        self.module = path.removesuffix(".py").replace("/", ".").removesuffix(".__init__")
        self.symbols: list[dict] = []
        self.edges: list[dict] = []
        self.imports: dict[str, str] = {}
        self.scope: list[str] = []
        self.classes: list[str] = []
        self.bindings: dict[tuple[str, str], str] = {}
        self.locals: set[tuple[str, str]] = set()
        self.styles: dict[str, list[dict]] = {}
        self.widgets: list[dict] = []
        self.add_symbol(self.module, "module", tree, self.module)
        self.symbols[-1]["line_end"] = max((getattr(n, "end_lineno", 1) or 1 for n in getattr(tree, "body", [])), default=1)
        self.visit(tree)

    @property
    def owner(self) -> str:
        return ".".join([self.module] + self.scope)

    def add_symbol(self, name: str, kind: str, node: ast.AST, qname: str | None = None,
                   description: str = "") -> str:
        qname = qname or self.owner + "." + name
        self.symbols.append({"name": name, "qname": qname, "kind": kind, "path": self.path,
                             "line_start": getattr(node, "lineno", 1),
                             "line_end": getattr(node, "end_lineno", 1) or 1,
                             "signature": description or signature(node),
                             "visibility": "private_convention" if name.startswith("_") else "public_convention"})
        return qname

    def edge(self, kind: str, target: str, node: ast.AST, confidence: str = "static",
             source: str | None = None) -> None:
        if target:
            self.edges.append({"source": source or self.owner, "target": target,
                               "kind": kind, "path": self.path,
                               "line": getattr(node, "lineno", 1), "confidence": confidence,
                               "target_file": None})

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports[alias.asname or alias.name.split(".")[0]] = alias.name if alias.asname else alias.name.split(".")[0]
            self.edge("imports", alias.name, node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        package = self.module.split(".") if self.path.endswith("/__init__.py") else self.module.split(".")[:-1]
        base = ".".join(package[:len(package) - node.level + 1]) if node.level else ""
        module = ".".join(x for x in (base, node.module) if x)
        for alias in node.names:
            target = module + "." + alias.name
            self.imports[alias.asname or alias.name] = target
            self.edge("imports", target, node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        kind = "component" if self.path.startswith("app/ui/") else "model" if self.path == "app/core/models.py" else "class"
        qname = self.add_symbol(node.name, kind, node)
        for base in node.bases:
            self.edge("inherits", dotted(base), base, source=qname)
        self.scope.append(node.name)
        self.classes.append(qname)
        for child in node.body:
            self.visit(child)
        self.classes.pop()
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        kind = "test" if node.name.startswith("test_") else "method" if self.classes else "function"
        self.add_symbol(node.name, kind, node)
        # Decorators/default expressions execute in enclosing scope.
        for child in node.decorator_list + node.args.defaults + [x for x in node.args.kw_defaults if x]:
            self.visit(child)
        self.scope.append(node.name)
        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            self.locals.add((self.owner, arg.arg))
        for child in node.body:
            self.visit(child)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def assignment(self, target: ast.AST, value: ast.AST | None, node: ast.AST) -> None:
        name = dotted(target)
        if isinstance(target, ast.Name):
            self.locals.add((self.owner, name))
        if not self.scope and isinstance(target, ast.Name):
            kind = "stylesheet" if self.path == "app/ui/styles.py" and isinstance(value, ast.Constant) and isinstance(value.value, str) else "constant"
            qname = self.add_symbol(name, kind, node)
            if kind == "stylesheet":
                self.qss(qname, value)
        if isinstance(value, ast.Call) and name:
            constructor = dotted(value.func)
            # Same-scope locals/self fields only; resolved as a low-confidence type hint later.
            self.bindings[(self.owner, name)] = constructor
            if name.startswith("self.") and self.classes:
                self.bindings[(self.classes[-1], name)] = constructor
            qt_type = self.imports.get(constructor, "")
            if self.path.startswith("app/ui/") and qt_type.startswith("PySide6.QtWidgets.") and not qt_type.endswith(".QApplication"):
                kind = "layout" if qt_type.endswith("Layout") else "widget"
                qname = self.add_symbol(name, kind, node, description=constructor)
                if kind == "widget":
                    self.widgets.append({"qname": qname, "owner": self.owner, "receiver": name,
                                         "type": qt_type.split(".")[-1], "node": node})
                self.edge("contains_" + kind, qname, node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self.assignment(target, node.value, node)
        if node.value:
            self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.assignment(node.target, node.value, node)
        if node.value:
            self.visit(node.value)

    def qss(self, sheet: str, node: ast.Constant) -> None:
        # Only the established stylesheet module; retain selectors, never declarations/colors.
        for match in re.finditer(r"([^{}]+)\{[^{}]*\}", node.value):
            for selector in match[1].split(","):
                selector = selector.strip()
                if not re.fullmatch(r'[A-Za-z0-9_#*:\[\]="\-\s.>]+', selector):
                    continue
                leading = len(match[1]) - len(match[1].lstrip())
                start = node.lineno + node.value[:match.start(1) + leading].count("\n")
                end = node.lineno + node.value[:match.end()].count("\n")
                location = ast.Constant()
                location.lineno, location.end_lineno = start, end
                qname = self.add_symbol(selector, "selector", location, sheet + "::" + selector)
                self.styles.setdefault(sheet, []).append({"selector": selector, "qname": qname})
                self.edge("defines_selector", qname, location, source=sheet)

    def visit_Call(self, node: ast.Call) -> None:
        self.edge("calls", dotted(node.func), node)
        if isinstance(node.func, ast.Attribute):
            receiver = dotted(node.func.value)
            method = node.func.attr
            if self.path.startswith("app/ui/") and method == "setObjectName" and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str) and IDENTIFIER.fullmatch(value.value):
                    qname = self.add_symbol("#" + value.value, "object_name", node,
                                            self.owner + "." + receiver + "#" + value.value)
                    self.edge("object_name", qname, node)
                    for widget in self.widgets:
                        if widget["owner"] == self.owner and widget["receiver"] == receiver:
                            widget["object_name"] = value.value
                            self.edge("names_widget", qname, node, source=widget["qname"])
            if method == "setStyleSheet" and node.args and dotted(node.args[0]):
                self.edge("uses_style", dotted(node.args[0]), node)
            if method == "connect" and node.args and dotted(node.args[0]):
                self.edge("signal_connect", dotted(node.args[0]), node, "heuristic")
            if method in {"addWidget", "addLayout", "setCentralWidget", "setModel"} and node.args:
                child = dotted(node.args[0])
                if child:
                    self.edge("ui_child", child, node, "heuristic")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.edge("references", node.id, node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load):
            self.edge("references", dotted(node), node)
        self.generic_visit(node)


def resolve(collector: Collector, target: str, source: str, known: dict,
            modules: dict) -> tuple[str, str, str | None]:
    """Return qualified name, confidence and project file (None for unresolved)."""
    # Bare names must resolve lexically first: main() may mean main.main(),
    # or an imported CLI main, not the unrelated main.py module.
    if ("." in target or "::" in target) and target in known:
        return target, "static", known[target]["path"]
    if "." in target and target in modules:
        return target, "static", modules[target]
    head, _, tail = target.partition(".")
    scope = source
    shadowed = False
    while scope.startswith(collector.module):
        candidate = scope + "." + target
        if candidate in known:
            return candidate, "static", known[candidate]["path"]
        if (scope, head) in collector.locals:
            shadowed = True
            break  # A local shadows an import/module name.
        if scope == collector.module:
            break
        scope = scope.rsplit(".", 1)[0]
    # self.method is a static syntactic link, runtime dispatch may differ.
    if head == "self":
        scope = source
        while scope.startswith(collector.module + "."):
            candidate = scope + "." + tail
            if candidate in known:
                return candidate, "heuristic", known[candidate]["path"]
            scope = scope.rsplit(".", 1)[0]
    # Imported names; don't resolve names shadowed by function arguments/assignments.
    if head in collector.imports and not shadowed:
        candidate = collector.imports[head] + ("." + tail if tail else "")
        if candidate in known:
            return candidate, "static", known[candidate]["path"]
        module = candidate
        while module:
            if module in modules:
                return candidate, "heuristic", modules[module]
            module = module.rpartition(".")[0]
        return candidate, "unresolved", None
    # Simple x = Class(); x.method(), including self fields assigned in __init__.
    if tail:
        receiver, _, method = target.rpartition(".")
        scope = source
        while scope.startswith(collector.module):
            if constructor := collector.bindings.get((scope, receiver)):
                cls, _, _ = resolve(collector, constructor, collector.module, known, modules)
                candidate = cls + "." + method
                if candidate in known:
                    return candidate, "heuristic", known[candidate]["path"]
            if scope == collector.module:
                break
            scope = scope.rsplit(".", 1)[0]
    return target, "unresolved", None


def build(root: Path) -> dict:
    state, sources = snapshot(root)
    collectors, parse_errors = [], []
    for path, data in sources.items():
        if path.endswith(".py"):
            try:
                encoding, _ = tokenize.detect_encoding(BytesIO(data).readline)
                collectors.append(Collector(path, ast.parse(data.decode(encoding))))
            except (SyntaxError, UnicodeError, LookupError) as error:
                # Don't echo the source line or exception message (could include secrets).
                parse_errors.append({"path": path, "line": getattr(error, "lineno", None),
                                     "error": type(error).__name__})
    symbols = [symbol for c in collectors for symbol in c.symbols]
    known = {s["qname"]: s for s in symbols}
    modules = {c.module: c.path for c in collectors}
    edges = []
    for collector in collectors:
        for edge in collector.edges:
            target, confidence, target_file = resolve(collector, edge["target"], edge["source"], known, modules)
            edge.update(target=target, target_file=target_file,
                        confidence="heuristic" if edge["confidence"] == "heuristic" and target_file else confidence)
            edges.append(edge)
            if collector.path.startswith("tests/") and target_file and not target_file.startswith("tests/"):
                edges.append({**edge, "kind": "test_source"})
    # Widget -> selector candidates in styles explicitly imported/applied by its file.
    sheets = {sheet: selectors for c in collectors for sheet, selectors in c.styles.items()}
    for collector in collectors:
        applied = {e["target"] for e in edges if e["path"] == collector.path and e["kind"] == "uses_style"}
        for widget in collector.widgets:
            for sheet in applied:
                for entry in sheets.get(sheet, []):
                    selector = entry["selector"]
                    object_match = re.search(r"#([A-Za-z_][A-Za-z0-9_]*)", selector)
                    type_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", selector)
                    if object_match and object_match[1] != widget.get("object_name"):
                        continue
                    if type_match and type_match[1] != widget["type"]:
                        continue
                    edges.append({"source": widget["qname"], "target": entry["qname"],
                                  "kind": "style_candidate", "path": collector.path,
                                  "line": widget["node"].lineno, "confidence": "heuristic",
                                  "target_file": known[entry["qname"]]["path"]})
    state.update(last_indexed=datetime.now(timezone.utc).isoformat(), parse_errors=parse_errors)
    directory = cache_dir(root)
    directory.mkdir(exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix="codegraph-", suffix=".sqlite", dir=directory)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with sqlite3.connect(temporary) as db:
            db.executescript("""
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE files (path TEXT PRIMARY KEY, language TEXT, module TEXT,
                                    hash TEXT, size INTEGER, mtime_ns INTEGER);
                CREATE TABLE symbols (name TEXT, qname TEXT, kind TEXT, path TEXT,
                                      line_start INTEGER, line_end INTEGER,
                                      signature TEXT, visibility TEXT);
                CREATE TABLE edges (source TEXT, target TEXT, kind TEXT, path TEXT,
                                    line INTEGER, confidence TEXT, target_file TEXT);
                CREATE INDEX symbol_name ON symbols(name);
                CREATE INDEX symbol_qname ON symbols(qname);
                CREATE INDEX edge_source ON edges(source);
                CREATE INDEX edge_target ON edges(target);
                CREATE INDEX edge_file ON edges(target_file);
            """)
            db.execute("INSERT INTO metadata VALUES ('state', ?)", (json.dumps(state),))
            db.executemany("INSERT INTO files VALUES (?, ?, ?, ?, ?, ?)",
                           [(p, Path(p).suffix.lstrip("."), next((c.module for c in collectors if c.path == p), ""),
                             f["hash"], f["size"], f["mtime_ns"]) for p, f in state["files"].items()])
            db.executemany("INSERT INTO symbols VALUES (:name, :qname, :kind, :path, :line_start, :line_end, :signature, :visibility)", symbols)
            db.executemany("INSERT INTO edges VALUES (:source, :target, :kind, :path, :line, :confidence, :target_file)", edges)
        db.close()
        destination = directory / "codegraph.sqlite"
        if destination.is_symlink():
            raise ValueError("Index must not be a symlink")
        temporary.replace(destination)
        # Sidecar is for human inspection; DB metadata is authoritative for status.
        sidecar = directory / "codegraph-state.json"
        if sidecar.is_symlink():
            raise ValueError("State must not be a symlink")
        sidecar.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        sidecar.chmod(0o600)
    finally:
        temporary.unlink(missing_ok=True)
    return {"action": "rebuilt", "files": len(sources), "symbols": len(symbols),
            "relationships": len(edges), "parse_errors": parse_errors,
            "last_indexed": state["last_indexed"]}


def update(root: Path) -> dict:
    current = status(root)
    return build(root) if current["stale"] else {"action": "unchanged", "last_indexed": current["last_indexed"]}


def rows(db: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in db.execute(query, params)]


def search(db: sqlite3.Connection, query: str, limit: int = 20) -> dict:
    tokens = [t.casefold() for t in re.split(r"\s+", query.strip()) if t]
    aliases = {"nén": "compress", "quét": "scan", "ghép": "join", "chia": "split",
               "màu": "style", "giao diện": "ui"}
    tokens += [aliases[t] for t in tokens if t in aliases]
    candidates = rows(db, "SELECT * FROM symbols") + [
        {"name": f["path"], "qname": f["module"], "kind": "file", "path": f["path"],
         "line_start": 1, "line_end": 1, "signature": "", "visibility": ""}
        for f in rows(db, "SELECT * FROM files")]
    hits = []
    for item in candidates:
        fields = (item["name"].casefold(), item["qname"].casefold(), item["path"].casefold(), item["kind"])
        score = sum(10 if t == fields[0] or t == fields[1] or t == fields[2]
                    else 3 if t in fields[0] else 1 if any(t in f for f in fields) else 0 for t in tokens)
        if score:
            hits.append({**item, "score": score, "confidence": "heuristic_rank"})
    hits.sort(key=lambda item: (-item["score"], item["path"], item["line_start"], item["qname"]))
    return {"query": query, "matches": hits[:limit], "total": len(hits), "truncated": len(hits) > limit}


def exact_matches(db: sqlite3.Connection, query: str) -> list[dict]:
    return rows(db, "SELECT * FROM symbols WHERE qname=? OR name=?", (query, query))


def relations(db: sqlite3.Connection, query: str, direction: str, limit: int) -> dict:
    matches = exact_matches(db, query)
    targets = {s["qname"] for s in matches} or {query}
    field = "target" if direction == "callers" else "source"
    items = []
    for target in sorted(targets):
        items.extend(rows(db, f"SELECT * FROM edges WHERE {field}=? AND kind IN ('calls', 'signal_connect')", (target,)))
    return {"query": query, "matched_symbols": matches, "ambiguous": len(targets) > 1,
            "relationships": items[:limit], "total": len(items), "truncated": len(items) > limit,
            "note": "Static candidates; signal_connect means callback registration, not a synchronous call. Unresolved receivers remain unresolved."}


def impact(db: sqlite3.Connection, query: str, limit: int) -> dict:
    matches = exact_matches(db, query)
    files = {s["path"] for s in matches}
    if rows(db, "SELECT path FROM files WHERE path=?", (query,)):
        files.add(query)
    symbols = {s["qname"] for s in matches}
    edges = rows(db, "SELECT * FROM edges")
    dependents = set(files)
    # File-level closure is intentionally conservative (imports/references/calls/styles/tests).
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if (edge["target_file"] in dependents or edge["target"] in symbols) and edge["path"] not in dependents:
                dependents.add(edge["path"])
                changed = True
    relationships = [e for e in edges if e["target_file"] in dependents or e["target"] in symbols]
    relationships.sort(key=lambda e: (e["target"] not in symbols,
                                      e["target_file"] not in files,
                                      e["kind"] == "references", e["path"], e["line"]))
    affected = sorted(dependents)
    return {"query": query, "matched_symbols": matches, "affected_files": affected[:limit],
            "affected_total": len(affected), "tests": sorted(f for f in dependents if f.startswith("tests/")),
            "module_boundaries": sorted({"/".join(f.split("/")[:2]) for f in dependents}),
            "relationships": relationships[:limit], "relationship_total": len(relationships),
            "truncated": len(affected) > limit or len(relationships) > limit,
            "confidence": "heuristic", "note": "Conservative file dependency closure; dynamic dispatch, callbacks passed as data and Qt runtime behavior may add impact. Inspect real usages before changing shared styles/config."}


def explore(db: sqlite3.Connection, query: str, limit: int) -> dict:
    found = search(db, query, limit)
    symbols = {s["qname"] for s in found["matches"]}
    files = {s["path"] for s in found["matches"]}
    broad_files = {s["path"] for s in found["matches"] if s["kind"] in {"file", "module"}}
    containers = {s["qname"] for s in found["matches"] if s["kind"] in {"class", "component", "model", "module"}}
    all_edges = rows(db, "SELECT * FROM edges")
    # Expand objectName <-> widget <-> selector only; don't crawl a whole UI file
    # for one selector. Preserve exact hits ahead of contextual imports.
    for edge in all_edges:
        if edge["kind"] in {"names_widget", "style_candidate"} and edge["target"] in symbols:
            symbols.add(edge["source"])
    sheets = {s.partition("::")[0] for s in symbols if "::" in s}
    relationships = [e for e in all_edges if e["source"] in symbols or e["target"] in symbols
                     or any(e["source"].startswith(c + ".") for c in containers)
                     or e["path"] in broad_files or e["target_file"] in broad_files
                     or (e["kind"] == "uses_style" and e["target"] in sheets)]
    linked_files = {e["path"] for e in relationships} | {e["target_file"] for e in relationships if e["target_file"]}
    test_edges = [e for e in all_edges if e["kind"] == "test_source" and e["target_file"] in files | linked_files]
    ordered = sorted(relationships, key=lambda e: (e["source"] not in symbols and e["target"] not in symbols,
                                                   e["kind"] in {"references", "imports"},
                                                   e["confidence"] == "unresolved", e["path"], e["line"]))
    styles = [e for e in relationships if e["kind"] in {"uses_style", "style_candidate", "defines_selector", "names_widget", "object_name"}]
    relevant_files = sorted(files) + sorted(linked_files - files)
    return {**found, "relevant_files": relevant_files[:limit],
            "relevant_files_total": len(relevant_files), "relevant_files_truncated": len(relevant_files) > limit,
            "relationships": ordered[:limit], "relationship_total": len(relationships),
            "relationships_truncated": len(relationships) > limit,
            "styles": styles[:limit], "styles_total": len(styles),
            "tests": sorted({e["path"] for e in test_edges} | {f for f in files | linked_files if f.startswith("tests/")}),
            "entry_points": ["main.py:main", "pyproject.toml:project.scripts.zip-part-maker"],
            "routes": [], "impact_hint": "Use impact with the exact symbol/path; read source at returned lines before patching.",
            "note": "Token ranking, not semantic task understanding. No HTTP routes in this desktop project. Narrow broad queries and increase --limit if truncated."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Project root (mainly for isolated self-tests)")
    parser.add_argument("--limit", type=int, default=20, help="Maximum results per section")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("status", "index", "update"):
        commands.add_parser(command)
    for command in ("search", "explore", "callers", "callees", "impact"):
        commands.add_parser(command).add_argument("query")
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be positive")
    root = args.root.resolve()
    try:
        if args.command == "status":
            result = status(root)
        elif args.command == "index":
            result = build(root)
        elif args.command == "update":
            result = update(root)
        else:
            current = status(root)
            if current["stale"]:
                print(json.dumps({"error": "Index missing/stale; run update before querying", "status": current}, ensure_ascii=False, indent=2))
                return 2
            with connect(root) as db:
                if args.command in ("callers", "callees"):
                    result = relations(db, args.query, args.command, args.limit)
                else:
                    result = {"search": search, "explore": explore, "impact": impact}[args.command](db, args.query, args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, sqlite3.Error, ValueError) as error:
        print(json.dumps({"error": type(error).__name__, "message": "Cannot read/build project cache; check permissions, ignore policy and run index to rebuild."}))
        return 1
