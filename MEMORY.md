# Working memory

## Last updated

2026-10-03, Asia/Ho_Chi_Minh. Review app/copy + chuẩn bị release 0.0.6; evidence: HISTORY/2026-10-03.md, interaction 003. Migration/rule trước đó: interactions 001–002.

## Current objective

User đã yêu cầu rà/sửa dự án, sửa câu chữ trong app, đẩy GitHub và tạo bản phát hành. Code/copy/tests hoàn thành; đang chốt commit/push/tag v0.0.6 và theo dõi native CI/Release. Không báo release xong khi chưa có assets.

## Current project state

Zip Part Maker 0.0.6, Python >=3.11/PySide6 desktop; core độc lập Qt, workers nối GUI. Manifest v1 giữ nguyên, report bổ sung split_files và giữ các field cũ. Remote origin: https://github.com/truongminhkhanng/nen-duoi-1g.git, main; latest release được kiểm tra trước phát hành: v0.0.5. Local/remote main lúc bắt đầu cùng c872f9b. User yêu cầu publish nên commit/push/tag nằm trong scope session này.

Root AGENT/CLAUDE/CONFIG/SKILL canonical, AGENTS bootstrap và docs wrappers; migration chưa commit lúc review bắt đầu được giữ và sẽ đưa lên GitHub cùng công việc hiện tại. Codeintel stdlib AST/SQLite cache ignored/rebuildable; update full rebuild, source luôn thắng cache. Python môi trường này 3.12.3 qua python3, PySide6 có sẵn.

## Recent changes

Chuẩn hóa UI tiếng Việt: Đóng gói thư mục, Quét thư mục, tệp, tiền tố tên ZIP, công cụ tích hợp, danh sách ghép. Tooltip/oversize/clean confirmation nêu đúng hành vi; giữ layout/QSS/feature hiện có.

Sửa hủy scan/compression (InterruptedError bắt trước OSError), inputs busy/invalidation, empty source/output validation, replanning/status/pause reset. Qt byte counters qlonglong; JoinDialog đợi thread dừng trước accept/report, Escape/close yêu cầu cancel.

Manifest validation: shape, tên leaf, metadata/size/hash, duplicate/missing/symlink parts; hash streaming và cancel theo khối; empty-file roundtrip. Join tạo tên mới nếu trùng, không xóa temporary sẵn có. Split manifest xuất qua temporary exclusive, không ghi đè manifest cũ. ZIP staging riêng tại output, giữ ZIP cũ tới verify thành công; escape prefix cleanup. Engine stdout được đọc khi chạy; split failures báo theo tệp và report split_files.

Version/CHANGELOG/README cập nhật; workflow lấy version động, kiểm tra tag/source, chạy core/UI/tool tests, build ba OS và tạo release notes từ changelog.

## Verification

76 pytest pass + 12 codeintel unittest pass. Qt offscreen dùng settings tạm; test worker thực, cancel/lifecycle/input state/counters >2 GB. Real 7-Zip Unicode integration pass trên Linux; WinRAR mock, chưa kiểm tra executable thật. Đã xem ảnh MainWindow/JoinDialog offscreen, không claim Windows/macOS native UI. Python 3.11 grammar pass; diff whitespace pass. Cache fresh/parse_errors rỗng sau update. Native CI/build/Release đang chờ publish.

## Active decisions

Giữ stack/public API/source bất biến, manifest v1 và native OS build. Không thêm dependency/lint/global tooling. Brief là nội bộ; viết product copy theo mục đích. Không tự khôi phục use-case UI. Không tự commit/publish cho task sau nếu user chưa yêu cầu. Không ghi secret/cache/data người dùng lên GitHub.

## Open issues

Manifest review candidate cũ đã xử lý và có regression. Chưa có lỗi xác minh còn bỏ lại trong scope review. Giới hạn runtime: ZIP Python pause/cancel giữa file; split/join theo chunk. Native release/Windows/macOS cần evidence CI; Qt visual offscreen không thay thử thao tác native. Không có server/auth/production DB hoặc lint/typecheck config; không tự thêm.

## Next actions

Commit source + context/tooling hiện có, push main và tag v0.0.6 sau final check; theo dõi build/release đủ EXE/DMG/Linux. Nếu CI lỗi, sửa rồi rerun, không dừng ở tag-only. Append release evidence và cập nhật working memory sau khi có kết quả.
