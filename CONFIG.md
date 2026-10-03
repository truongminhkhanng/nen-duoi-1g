# Zip Part Maker — Confirmed facts and configuration

Facts dựa source local lúc migration 2026-10-03; source hiện tại luôn thắng bảng này. Không duplicate toàn config kỹ thuật, đọc file được reference khi sửa. Chưa biết dùng `[CHƯA XÁC NHẬN]`; secret chỉ env name/`[SECRET - ENV ONLY]`.

## Business

Đóng gói thư mục nhiều file thành ZIP **độc lập**, phục vụ gửi/bàn giao/sao lưu theo giới hạn dung lượng (README). Không hứa nén file đơn lớn dưới limit nếu không nén đủ. `.001` cần đủ parts và ghép lại. Business owner, kế hoạch thương mại: `[CHƯA XÁC NHẬN]`.

## Product / Service

Tên Zip Part Maker, package zip-part-maker; version local 0.0.6 (`app/version.py`, `pyproject.toml`). Desktop Windows/macOS/Linux, MIT (LICENSE). Remote GitHub `truongminhkhanng/nen-duoi-1g` đã xác minh bằng gh ngày 2026-10-03; lúc chuẩn bị release, bản mới nhất là v0.0.5. Trạng thái v0.0.6 phải kiểm tra GitHub hoặc working memory.

## Features

Scanner recursive/no symlink/output exclusion; FFD packing; engine auto/Python/7-Zip/WinRAR; oversize skip/try/split; conflict overwrite/rename/clean; verify/checksum/report; background workers, pause/cancel; drag-drop source; join dialog; model/view file table. Trace ở `app/ui/main_window.py`, `app/core/`, `app/workers/`.

## Limits and settings

QSettings organization/application **ZipPartMaker/ZipPartMaker** (`MainWindow.__init__`, `_restore_settings`, `_save_settings`). Lưu local theo Qt/platform, không có database config riêng.

| Option | Default | Source |
|---|---|---|
| limit/unit | 950 MB, MB = 1024² bytes; GB = 1024³ | `main_window.py`, `utils/sizes.py` |
| planner safety | 0.98; archive thật phải **nhỏ hơn** limit | `core/planner.py`, `core/compressor.py` |
| compression | Cân bằng, ZIP_DEFLATED level 6; các mức None/1/6/9 | `_compression_settings` |
| engine | AUTO ưu tiên 7-Zip khi đủ điều kiện; macOS luôn Python | `core/engines.py` |
| prefix/output | part; `<source>/ZIP_PARTS` | `_build_ui`, `_set_source` |
| recursive/structure/skip hidden/skip system/open output | true | `_restore_settings` |
| core conflict/oversize | RENAME / SKIP; GUI có dialog cho user chọn | `core/models.py`, `ui/dialogs.py` |
| split streaming chunk | 1 MiB | `core/splitter.py:COPY_CHUNK_SIZE` |

Hard limit được kiểm tra sau ZIP overhead; pause/cancel Python giữa file, engine ngoài không pause an toàn. Style sáng hiện có, không ép dark mode (README, styles.py).

## Auth

Không có account/login/auth backend trong source hiện tại. Desktop local app. Thay đổi auth mới cần yêu cầu/scope tương ứng.

## Database

Không có DB/schema/migrations production được tìm thấy. Generated SQLite `.agent/codegraph.sqlite` chỉ phục vụ agent navigation, không lưu settings/domain data.

## API

Không HTTP API/routes. Python callables, enum/dataclass, split manifest `zip-part-maker-split-v1` và `zip_report.json` là surfaces cần kiểm tra compatibility (`core/models.py`, `splitter.py`, `compressor.py`).

## Integrations and external services

7-Zip `7z.exe`/`7z` Windows, `7zz`/`7z` Linux; WinRAR Windows tìm PATH/ProgramFiles/ProgramFiles(x86), chỉ tạo ZIP. Thiếu engine hoặc không keep structure → Python fallback; macOS Python. GitHub Actions/Releases cho distribution. Không cloud indexing, network business service hoặc daemon trong hệ thống agent.

## Pricing

MIT license được xác nhận; pricing/subscription/revenue `[CHƯA XÁC NHẬN]`. Không suy diễn miễn phí thương mại chỉ từ license.

## Analytics / SEO

Không telemetry/analytics code được tìm thấy, phù hợp docs cũ. Không website SEO runtime; README mô tả sản phẩm và use cases. Không thêm tracking.

## Feature flags

Các tùy chọn GUI/QSettings là flags hiện có. Không remote flag service/config được tìm thấy. Đọc source khi cần danh sách settings đầy đủ.

## Deployment

Native PyInstaller scripts + GitHub Actions; `v*` tags release. Workflow lấy version từ source, kiểm tra tag, chạy pytest/offscreen + codeintel tests, build Windows EXE/macOS DMG/Linux binary; release notes lấy section tương ứng trong CHANGELOG. Workflow dùng env **GH_TOKEN** từ GitHub token, không copy value. Không production runtime env secrets được xác nhận.

## Important paths

`main.py` (entry), `app/core` (domain), `app/ui/styles.py` (shared QSS), `app/workers` (thread bridge), `tests` (regression), `scripts` (native build), `.github/workflows/build.yml` (release), `tools/codeintel` (agent tool), `.agent/codegraph-ignore` (index policy). Chạy `search/explore`, rồi mở source thật thay vì lấy đường dẫn/bảng này làm đủ context.
