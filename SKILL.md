---
name: zip-part-maker
description: Project-local workflows for Zip Part Maker agents, memory and source verification.
---

# Project workflows

Chỉ đọc skill liên quan; entry và rule chung ở AGENT.md. Đây là hướng dẫn trong repo, không yêu cầu cài skill/global tool.

## start-new-session

1. Đọc AGENT.md và MEMORY.md.
2. Classify task; chọn section context/skill liên quan.
3. Đọc history hôm nay chỉ khi continuation; lịch sử cũ chỉ khi có nhu cầu/reference.
4. Task code: inspect index theo skill dưới; thực hiện scope đã xác minh.

## inspect-code-with-local-index

1. `python3 -m tools.codeintel status`; đọc `stale`, changed files, parse_errors.
2. Missing/stale: `python3 -m tools.codeintel update`; phục hồi corrupt cache bằng `index`.
3. `search` tên domain/symbol/path, `explore` workflow. Queries stale exit 2.
4. Lấy exact symbol/file/line; tăng `--limit` trước subcommand nếu bị truncate.
5. Mở source bằng `rg -n`/reader, kiểm tra caller/import/style/test thật.
6. Heuristic/unknown hoặc tool fail → tìm source bổ sung, ghi limitation, không giả định.

## make-minimal-change

1. Xác định exact scope và compatibility surface từ source.
2. Query `impact` khi shared module/style/config; closure chỉ là conservative hint.
3. Patch nhỏ nhất đúng yêu cầu, không global replace/refactor/cleanup ngoài scope.
4. Targeted test/verify theo file; không claim kiểm tra chưa chạy.
5. Update index sau thay đổi code/config/tool source; inspect diff rồi record/compress.

## ui-micro-change

1. Trace visible dashboard/dialog → layout/widget trong `main_window.py`/`dialogs.py`.
2. Trace objectName/property → QSS declaration thật; `explore 'pageTitle'` là ví dụ header.
3. `impact 'app/ui/styles.py'` + source usages; shared wildcard/type selectors ảnh hưởng rộng.
4. Scope theo objectName/convention hiện tại; không đổi token/global màu cho request cục bộ.
5. Chuyển brief nội bộ thành product copy theo AGENT.md; chỉ giữ nguyên khi user yêu cầu.
6. Chạy offscreen smoke trong môi trường config tạm nếu có Qt; visual verification riêng khi cần. Update index.

## end-session-and-compress

1. Inspect git diff/status, kết quả verify và phần chưa xác nhận.
2. Xác định decision mới, loại fact có thể query từ source/index.
3. Append daily interaction + cập nhật HISTORY/INDEX.
4. MEMORY là state gọn 400–700 từ tối đa, không transcript.
5. Extract durable why/constraint vào LONG_TERM_MEMORY, có Date/Status/Reason/Source.
6. CONFIG/CLAUDE chỉ đổi khi fact/rule/architecture đổi thật, không đồng bộ vô ích.

## record-daily-interaction

Lấy ngày/giờ thật Asia/Ho_Chi_Minh, tạo file `HISTORY/YYYY-MM-DD.md` nếu chưa có. Append interaction ID tiếp theo, không sửa record cũ. Ghi User Input (brief tóm tắt trung thực nếu dài), Agent Output, Actions Taken, Files Changed, Verification, Decisions, Memory Candidates; redact secret và không ghi raw dữ liệu người dùng. Cập nhật row HISTORY/INDEX để tìm đúng ngày. Không bịa history trước migration hoặc chuyển CHANGELOG thành conversation.

## manage-memory

- MEMORY.md: current objective/state, recent changes, active decisions/hypotheses/issues/next actions.
- LONG_TERM_MEMORY.md: durable knowledge/why; trạng thái Confirmed/Hypothesis/Deprecated/Rejected; reference source/history.
- HISTORY/: append-only chronological evidence, không override trạng thái hiện tại.

Conflict theo hierarchy AGENT.md. Chuyển knowledge dài hạn khỏi working memory; chưa xác minh giữ Hypothesis. Không copy call graph/code listing vào long-term.

## core-archive-safety

Giữ core độc lập Qt, immutable source, archive temp → verify → hard-limit check → rename. Trace Compressor/controller + verifier + path utilities; nếu split/join, inspect manifest compatibility/checksum/cancel cleanup. Thay planner/scanner/compressor/splitter phải có regression tương ứng; chạy test file liên quan rồi `python3 -m pytest` trước PR. Không dùng dữ liệu người dùng làm fixture; dùng temp dirs/bounded bytes.

## compression-engine-check

Đọc `core/engines.py`, `core/models.py`, `_engine_info`/settings UI, `_create_with_external_engine` và `tests/test_engines.py`/`test_compressor.py`. Giữ macOS Python, WinRAR Windows ZIP-only, AUTO 7-Zip và fallback/keep_structure hiện tại. Subprocess argument list, không shell interpolation. Test selection bằng monkeypatch platform/PATH và fake process; test thật với executable là integration riêng, không claim đã chạy nếu chỉ mock.

## native-build-release

Đọc build script target và `.github/workflows/build.yml`, version ở app/version.py/pyproject, README/CHANGELOG. Build đúng OS, không cross-compile PyInstaller. Test trước build; assets/resource_path phải có trong package. Release/push tag/publish chỉ khi user yêu cầu, không tự đổi version/artifact/flow. Không chạy full build có download/platform tooling cho docs/cache-only task.
