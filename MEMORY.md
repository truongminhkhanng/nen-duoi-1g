# Working memory

## Last updated

2026-10-04, Asia/Ho_Chi_Minh. Hoàn thành review app/copy và phát hành 0.0.7. Evidence: HISTORY/2026-10-04.md, interaction 002; công việc sửa app: HISTORY/2026-10-03.md, interaction 003.

## Current objective

User gọi lại qua AGENT.md để hoàn tất việc đang pause. Đã xác minh CI/main/tag và Release v0.0.7 thành công, đủ EXE/DMG/Linux. Checkpoint docs được đưa lên GitHub trong phạm vi yêu cầu publish trước đó. Không còn công việc release phải tiếp tục.

## Current project state

Zip Part Maker 0.0.7, Python >=3.11/PySide6 desktop; core độc lập Qt, manifest v1 giữ nguyên. Origin: https://github.com/truongminhkhanng/nen-duoi-1g.git, main. Source release tại commit 1920d56d028d0a74dc208e28f1bb33ad7474655b; tag annotated v0.0.7 trỏ đúng commit. Latest public release được xác minh ngày 2026-10-04 là v0.0.7.

AGENT/CLAUDE/CONFIG/SKILL canonical; AGENTS bootstrap, docs wrappers. Codeintel stdlib AST/SQLite cache ignored/rebuildable; source thắng cache. Python local 3.12.3, PySide6 có sẵn. Không thêm dependency hay thay stack.

## Recent changes

Chuẩn hóa nhãn, tooltip và thông báo tiếng Việt, giữ layout/QSS và feature. Sửa hủy scan/compression, inputs busy/invalidation, validation, replanning/status/pause. Qt counters qlonglong; JoinDialog đợi thread dừng trước đóng/báo kết quả.

Validate manifest/parts, hash streaming và cancel theo khối; empty-file roundtrip. Join tránh ghi đè target và temporary có sẵn. Manifest temporary exclusive; ZIP staging riêng, giữ ZIP cũ tới verify. Đọc stdout engine khi chạy; split failures báo theo tệp, report thêm split_files và giữ field cũ.

Workflow đọc version/tag, chạy core/UI/tool tests, build native ba OS, release notes từ CHANGELOG. v0.0.6 CI fail; 0.0.7 sửa Linux Qt runtime và Windows SQLite handle cleanup. Giữ nguyên tag 0.0.6.

## Verification

76 pytest + 12 codeintel unittest pass local từ lần sửa trước; real 7-Zip Unicode integration và Qt offscreen đã kiểm tra. Resume chỉ đổi docs, không lặp lại tests app.

Run tag 37138859403 completed/success: pytest, tool tests, native build và upload trên Windows/macOS/Linux đều success; release job success. Run main 37138859033 completed/success. Release public, không draft/prerelease, published 2026-10-04 00:01:16 +0700; đủ assets uploaded, size >0 và SHA-256 từ GitHub: EXE 49,229,522 B; DMG 43,991,598 B; Linux 77,446,168 B.

Codeintel update rebuilt, parse_errors rỗng. Checkpoint docs dùng [skip ci] vì source/tag đã kiểm thử và build thành công.

## Active decisions

Giữ source người dùng bất biến, public API/manifest v1/native OS build. Brief là nội bộ; viết product copy theo mục đích. Không tự khôi phục use-case UI. Không tự commit/publish task mới nếu chưa được yêu cầu. Không ghi secret/cache/data người dùng lên GitHub.

## Open issues

Không còn lỗi xác minh trong scope review/release. Native CI/build success không thay kiểm thử thao tác thủ công trên Windows/macOS; WinRAR mới mock. ZIP Python pause/cancel giữa file; split/join theo chunk. Không server/auth/production DB hoặc lint/typecheck config.

## Next actions

Chờ yêu cầu mới. Không tăng version, di chuyển tag hoặc phát hành thêm cho việc đã hoàn tất. Release: https://github.com/truongminhkhanng/nen-duoi-1g/releases/tag/v0.0.7.
