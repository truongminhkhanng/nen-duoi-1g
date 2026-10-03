# Durable project knowledge and decisions

Memory lưu why/constraint, không duplicate graph. Source/config/runtime hiện tại thắng memory. Decision dùng Date, Status, Reason và Source/reference; không biến Hypothesis thành Confirmed.

## Project identity

Zip Part Maker là desktop utility đóng gói **nhiều file trong thư mục vào nhiều ZIP độc lập**. Không phải công cụ bảo đảm nén một video/file lớn thành ZIP dưới limit. Identity được xác nhận từ README/source tại migration, không phải project mới. Version phải đọc source/manifest hiện tại.

## Confirmed business facts

Mục đích gửi/bàn giao/lưu trữ thư mục theo giới hạn dung lượng; `.001` là phương án phụ, cần đủ parts và ghép lại. Nguồn: README, oversize dialogs, split/join code. MIT license xác nhận; pricing/commercial owner/remote release status chưa xác nhận, không suy diễn.

## Architecture decisions

| Date | Status | Decision / Reason | Source/reference |
|---|---|---|---|
| 2026-10-03 (ngày xác nhận, không khẳng định ngày thiết kế ban đầu) | Confirmed | Giữ Qt UI/workers tách khỏi core để domain/filesystem được test độc lập và bảo toàn architecture đang có. | Source `app/core`, `app/workers`, legacy `docs/CLAUDE.md`; CLAUDE Architecture |
| 2026-10-03 | Confirmed | Migration chỉ context/tooling/history/cache, không rewrite project hoặc thay feature/API/schema/deploy/runtime. User yêu cầu bảo toàn project hiện hữu. | HISTORY/2026-10-03.md interaction 001 |

## Technical decisions

| Date | Status | Decision / Reason | Source/reference |
|---|---|---|---|
| 2026-10-03 | Confirmed | Codeintel dùng Python AST + SQLite stdlib vì project đã dùng Python; không cài global/runtime/dependency/cloud mới. | Tool README/indexer; history 001 |
| 2026-10-03 | Confirmed | Cache ignored/rebuildable, source là truth; heuristic có confidence, query stale bị từ chối. Tránh sửa theo derived data cũ. | AGENT hierarchy/workflow; `.gitignore`; codeintel status |
| 2026-10-03 | Confirmed | Khi source thay đổi, update rebuild graph đầy đủ; clean no-op. Repo nhỏ, lựa chọn này an toàn hơn partial invalidation chưa được chứng minh. | Tool README Storage and staleness; self-tests |
| 2026-10-03 | Deprecated | Rule legacy “chỉ zipfile” không còn đúng với engine source hiện tại. Giữ subprocess argument list/fallback/platform behavior, không xóa 7-Zip/WinRAR. | CLAUDE Legacy context migration; engines/compressor; CHANGELOG 0.0.2 |
| 2026-10-03 | Confirmed | Giữ tệp/ZIP sẵn có đến khi kết quả được verify; temporary phải thuộc tác vụ trước khi cleanup. Manifest chỉ dùng leaf filename, kiểm tra size/SHA-256 và không đọc symlink part. Tránh ghi đè hoặc xóa dữ liệu ngoài tác vụ. | core/splitter.py, compressor.py; tests; history 003 |
| 2026-10-03 | Confirmed | Qt byte progress dùng qlonglong; InterruptedError là OSError subclass, phải bắt riêng trước lỗi filesystem. Dialog ghép chỉ đóng sau thread finished. | workers, scanner/compressor, dialogs; tests/test_ui.py; history 003 |

## Product decisions

| Date | Status | Decision / Reason | Source/reference |
|---|---|---|---|
| 2026-10-03 | Confirmed | Bảo toàn ZIP độc lập và source bất biến; split parts không được quảng bá như ZIP độc lập. Đây là semantics hiện có cần giữ khi viết UI/docs. | README, ui/dialogs.py, core workflows |
| 2026-10-03 | Confirmed | Brief nội bộ không tự động trở thành product copy. Viết nội dung cho end user đúng mục đích/ngữ cảnh; chỉ giữ nguyên khi user yêu cầu rõ hoặc là dữ liệu hiển thị. | AGENT section QUY TẮC PHÂN BIỆT…; history interaction 002 |

CHANGELOG 0.0.4 ghi đã bỏ nút/dialog Trường hợp sử dụng theo phản hồi người dùng; đó là evidence trong changelog, không raw conversation. Không tự khôi phục UI này vì migration hoặc vì README vẫn có use cases.

## User preferences

Gọi một entry point `@AGENT.md`, agent tự tìm context có sẵn. Đọc selective, không load full history. Patch nhỏ, không tiện thể refactor/feature fix; dùng công cụ local, không global install/npm/CodeGraph/cloud service. Quy tắc brief/product copy là user instruction rõ ràng, có reference trên.

## Important constraints

Không sửa/xóa/di chuyển dữ liệu nguồn của user. Transactional archive temp/verify/rename, checksum/format compatibility, cancel cleanup và clean-ZIP confirmation phải được hiểu trước thay đổi. Giữ Python/PySide6/pip/setuptools/PyInstaller/native packaging khi chưa có yêu cầu khác. Không lưu secret, không thêm telemetry/paid service hoặc tự commit/publish. CONTRIBUTING/SECURITY vẫn áp dụng.

## Key workflows

Session: AGENT + MEMORY → classify → context sections → local index → source verification → minimal patch → targeted verify → update → append history/compress. Core regression, engine check và native build skills ở SKILL; facts/config references ở CONFIG. Lịch sử bắt đầu từ migration, index theo ngày; không dựng conversation từ git/changelog.

## Known pitfalls

Qt selectors/objectNames có thể shared/dynamic; graph không thay source hoặc render verification. Đổi `*`, QPushButton/global style có impact rộng hơn một header. Native build không cross-compile. Pause/cancel có checkpoint; ZIP Python không ngắt giữa file, split/join ngắt theo khối. Python callable/type binding và Qt runtime dispatch không resolve đầy đủ từ AST; missing edge không chứng minh không có caller. UI pytest đã có từ 0.0.6, không thay kiểm tra visual/native runtime.

## Experiments and results

2026-10-03: 22 existing tests pass trước/sau migration; 12 isolated tool tests pass. Real source confirms plan_archives callers, create_archive→verify_zip, compress workflow/tests và pageTitle→QSS. Fixtures confirm hash detection dù size/mtime giữ nguyên, deletion/update, stale refusal, policy/parser/schema invalidation, secret non-retention, corrupt-cache recovery. Không suy ra native release/UI visual đã verify từ các kết quả này. Evidence: history 001.

## Rejected approaches

| Date | Status | Reason | Source/reference |
|---|---|---|---|
| 2026-10-03 | Rejected | Global Node/npm/CodeGraph/cloud/daemon/vector DB không cần cho repo Python nhỏ và trái scope local/offline. | User migration brief; tool README |
| 2026-10-03 | Rejected | Load toàn context/history mỗi session làm context lớn, bỏ qua selective requirement. | AGENT selective loading; history 001 |
| 2026-10-03 | Rejected | Global replace màu/token hoặc rewrite feature ngoài scope có thể phá phần không liên quan. | User brief; AGENT minimal/UI protocols |

## Things future agents must not forget

AGENT là entry, source là truth, graph là cache, history là evidence. Không tin heuristic như fact. Không yêu cầu user cung cấp lại dữ liệu trong repo. Đừng coi words/examples trong brief là UI copy. Context cũ đã migrate qua wrappers, không load hai bộ trùng nhau. MEMORY giữ current state; long-term chỉ durable why/constraints; history append-only, secrets luôn redact.
