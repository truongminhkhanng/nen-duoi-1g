# Local code intelligence — Zip Part Maker

Python 3.11+ standard library only: `ast`, `sqlite3`, hashes, JSON, argparse. No install, Node/npm, pip package, network, telemetry, daemon or cloud. Does not import/execute app code. Run from repository root with `python3` (or your existing environment's `python` on Windows/venv).

## Commands

```bash
python3 -m tools.codeintel status
python3 -m tools.codeintel index
python3 -m tools.codeintel update
python3 -m tools.codeintel search 'plan_archives'
python3 -m tools.codeintel explore 'MainWindow compress'
python3 -m tools.codeintel callers 'app.core.planner.plan_archives'
python3 -m tools.codeintel callees 'app.core.compressor.Compressor.create_archive'
python3 -m tools.codeintel impact 'app/ui/styles.py'
python3 -m tools.codeintel --limit 80 explore 'pageTitle'
python3 -m unittest tools.codeintel.test_indexer -v
```

All output is JSON, available as a shell/API navigation interface. Internal Python functions in `indexer.py` also expose status/build/update/search/explore/relations/impact for tests. `--root PATH` selects an isolated fixture checkout; default root derives from tool location. Global options go **before** the command. Queries require an argument; quote multiword tasks/selectors. Callers/callees require exact short/qualified symbol names; impact accepts exact symbol or file path. Ambiguous short names return all matches and flag ambiguity; prefer qualified names.

| Command | Result |
|---|---|
| status | Exists/schema version, stale, added/modified/deleted files, reasons, last indexed, tool/parser version, parse errors |
| index | Full rebuild; safe replacement of the index after construction |
| update | Clean → no-op; missing/stale/corrupt → full rebuild |
| search | Token/substring-ranked file, class/model/component, function/method/test, widget/objectName, constant, stylesheet/selector metadata |
| explore | Ranked symbols with source ranges, relevant files, relationships, styles, test links, desktop entry points and impact hint |
| callers/callees | Syntactic call candidates + signal callback registration; exact matches, line numbers, confidence |
| impact | Conservative transitive **file** dependency closure, callers/references/styles, source-test links, module boundaries |

Exit 0: successful command (including stale `status`); exit 2: query refused because cache missing/stale; exit 1: I/O/cache error. Invalid CLI options use argparse exit 2. Read `status.stale`, not its exit code, to decide freshness. Parse errors are reported per file without source/exception text; intact files remain searchable. A fresh index with parse errors is **partial**, not a complete graph. Always inspect parse_errors.

## Storage and staleness

`.agent/codegraph.sqlite` holds files (path/type/module/hash/mtime/size), symbols (name/qualified name/kind/path/line range/redacted signature/conventional visibility), relationships (source/target/kind/source location/target file/confidence), and build metadata. No full source bodies or duplicate source tree. `.agent/codegraph-state.json` is a human-readable sidecar; SQLite metadata is authoritative. Both generated artifacts are ignored by git and reproducible. Tool source, README and `.agent/codegraph-ignore` belong in version control. No changes to package installation/distribution configuration.

Freshness compares SHA-256 **content** hashes for all eligible files (including manifests, requirements and any future lockfile with a supported extension), ignore policy, tool source, parser version and schema version. mtime/size are metadata, not the only check. Added/deleted files are detected. Source is scanned once into an in-memory snapshot per build; if it changes during/after indexing, the next status detects changed content. No watcher. `status` hashes all eligible text files; this repo is small. The cache is written via a temporary SQLite file then replaced; no concurrent index writers are supported. Do not commit/cache-copy as proof of current source.

**Limitation:** update does not parse incrementally. It rebuilds the small graph whenever stale, which safely refreshes cross-file resolution/deletions without complex partial invalidation. No FTS/vector search: in-memory metadata ranking is sufficient for this project. Manifest/config/docs/scripts are indexed as **file metadata**, not source contents, secrets or parsed option values. Lockfiles with new extensions must be added deliberately if introduced; there is no lockfile currently.

## Relationships and confidence

- Python AST definitions, module constants, imports, relative imports/import aliases, names/attribute references, class inheritance and direct calls.
- Simple local `x = Class(); x.method()` and self-field constructor bindings provide **heuristic** method hints. `self.method` also remains heuristic because Python dispatch may differ.
- Test → source candidates are inferred from references/imports/calls in `tests/`; file closure can overestimate scope.
- Qt `setStyleSheet(LIGHT_STYLE)`, literal `setObjectName`, widget constructors, explicit layout child calls and signal `connect` registrations.
- QSS selectors/line ranges parsed **only from the existing `app/ui/styles.py` module**. Widget → selector candidates check widget type/objectName in an explicitly applied stylesheet; selector matching is heuristic. Colors/declaration values are not cached; read source to change them.

`static`: identifiable syntactic declaration/name link, not proof of runtime behavior. `heuristic`: inferred binding/UI/style/test-impact candidate. `unresolved`: no reliable local target file; raw identifier retained, no guessed same-name target. Search `heuristic_rank` is token ranking, not semantic certainty. Dynamic calls like `Compressor(...).run(...)`, arbitrary factories, callbacks passed as data, inheritance dispatch, monkeypatching, lambda/complex scoped bindings, star imports, explicit exports/`__all__` and nested import shadowing are not fully resolved. Do not infer absent callers from no result.

Desktop source has no HTTP routes, web component tree, CSS utility/token framework or database models/schema. `explore.routes` is empty, never fabricated. QSS dynamic objectNames inside conditional expressions/loops, Qt inheritance, selector specificity/state/polish and inline styles passed as strings are partial/unsupported. UI relationships indicate locations to inspect, not final render matching. Layout edges show enclosing scope → referenced child, not a complete runtime widget tree. No selector token/declaration parser is claimed.

For Vietnamese briefs, use domain keywords/names (`nén` has a small alias to `compress`; arbitrary natural language is not understood). Example header → `search 'pageTitle'` → `explore 'pageTitle'` → inspect `_build_ui`, objectName and `QLabel#pageTitle` source → inspect shared usage/impact → patch only that declaration. Increase limit if output is truncated. If graph misses a path, use `rg -n` and read actual source.

## Security / ignore policy

Default built-ins skip environments, git/cache/build/history/system credential directories, sensitive filenames (`.env*`, credentials/secrets/password/token/private-key patterns, PEM/key containers, auth.json) and **all symlinks**. Supported extensions are restricted to repo text/source formats. `.agent/codegraph-ignore` adds project-relative globs or directory prefixes, one per line; `#` lines are comments; no negation/re-include. Directory patterns apply recursively. Add private fixtures/local files **before indexing**. The policy hash invalidates caches after edits. This is a separate explicit policy, not a general `.gitignore` parser.

Index stores identifiers/type structure/path/hash/locations only: no function defaults, arbitrary string/numeric literals, string annotations, docstrings, log/error messages, QSS declaration values or config values. ObjectName identifiers and QSS selectors are the limited UI strings retained for navigation. That restriction is not a general secret detector: never put credentials inside symbol names/paths/objectNames/selectors; ignore any sensitive source file. Standard fixtures verify secret exclusion/non-retention. No global metadata/snippet copy or network access. Cache files are local, sensitive dirs ignored; memory/history independently require redaction.

## Self-tests

`python3 -m unittest tools.codeintel.test_indexer -v` uses temp fixture roots, with no production edits. It covers all CLI commands, direct/import-alias/instance call hints, ambiguity/unresolved/shadowing, impact/test links, QSS/widget links and line ranges, hash detection despite unchanged size/mtime, additions/deletions, no-op/rebuild, policy/manifest/schema/parser/tool changes, corrupt-cache recovery, partial parse errors, symlink exclusion, ignored credentials and literal non-retention.

Also run a first `status → index → search/explore → callers/callees/impact` on real repo symbols; confirm returned line ranges against source, and end with fresh `status`. Migration evidence is in HISTORY/2026-10-03.md. Tests do not validate every dynamic Python/Qt relationship or native application packaging.
