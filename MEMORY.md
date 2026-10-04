# Working memory

## Last updated

2026-10-04, Asia/Ho_Chi_Minh. README cho người dùng đã lên GitHub main, commit 4d6c73b; remote đã xác minh lúc 20:35:42 +0700. Evidence: HISTORY/2026-10-04.md, interactions 003–004.

## Current objective

Đã đẩy README và checkpoint lên GitHub theo yêu cầu mới; remote main khớp local commit 4d6c73baf6f9c10ca512e33fde7035efcdb577be. Release 0.0.7 đã hoàn tất ở interaction 002, không còn việc release phải tiếp tục.

## Current project state

Zip Part Maker 0.0.7, desktop Python >=3.11/PySide6, core độc lập Qt, manifest v1. Origin: https://github.com/truongminhkhanng/nen-duoi-1g.git, main. Source release: 1920d56d028d0a74dc208e28f1bb33ad7474655b; annotated tag v0.0.7 trỏ đúng commit. Release public đủ Windows EXE, macOS DMG Apple Silicon, Linux x64; đã xác minh ngày 2026-10-04.

AGENT/CLAUDE/CONFIG/SKILL canonical; AGENTS bootstrap. Codeintel stdlib AST/SQLite ignored/rebuildable, source thắng cache. Python local 3.12.3, PySide6 có sẵn; giữ stack/dependencies.

## Recent changes

README ưu tiên tải/mở app, các bước nén, gửi/mở ZIP, xử lý tệp vượt giới hạn và ghép lại. Bỏ thuật toán, setup source, build/test và workflow AI khỏi README. Giữ liên kết CONTRIBUTING/SECURITY/LICENSE. Ghi rõ bản tải sẵn không cần cài Python hay công cụ nén thêm; chỉ chạy mã nguồn mới cần Python. Không sửa source/version/build.

Lần trước đã chuẩn hóa copy UI, sửa cancellation/busy/invalidation và Qt thread/counters. Validate manifest/parts/hash streaming; bảo vệ target/temporary khi ghép; ZIP staging và kiểm tra trước thay thế; engine stdout streaming. Workflow test/build/release ba OS; 0.0.7 sửa Linux Qt runtime, Windows SQLite handle cleanup. Giữ tag 0.0.6.

## Verification

Lượt README: đối chiếu nhãn/defaults với MainWindow/JoinDialog, engine với source, cách đóng gói với ba build scripts. Kiểm tra liên kết/ảnh nội bộ, khối lệnh Markdown và git diff --check. Không chạy lại tests/build vì chỉ đổi docs; không kiểm thử lại thao tác GUI/binary.

Evidence trước: 76 pytest + 12 codeintel unittest pass; real 7-Zip Unicode integration, Qt offscreen đã kiểm tra. Main run 37138859033 và tag run 37138859403 completed/success; native tests/build/upload cả ba OS và release job success. Assets size >0, SHA-256 từ GitHub lưu trong history interaction 002. Release published 2026-10-04 00:01:16 +0700; public, không draft/prerelease.

## Active decisions

README là hướng dẫn sản phẩm cho người dùng; brief trao đổi là nội bộ, viết copy theo mục đích. Giữ nguồn người dùng bất biến, API/manifest v1/native OS build. Không tự commit/publish task mới, tăng version hoặc di chuyển tag. Không ghi secret/cache/data người dùng lên GitHub.

## Open issues

Không còn lỗi xác minh trong scope trước. Native CI không thay thao tác thủ công Windows/macOS; WinRAR mới mock. ZIP Python pause/cancel giữa file, split/join theo chunk. Không server/auth/production DB hoặc lint/typecheck config.

## Next actions

README đã đồng bộ; chờ yêu cầu mới. Không tự phát hành thêm. Release: https://github.com/truongminhkhanng/nen-duoi-1g/releases/tag/v0.0.7.
