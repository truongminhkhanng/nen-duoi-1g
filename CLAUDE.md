> **Đây là file luật nền của project. Agent không phải load toàn bộ file cho mọi task; chỉ đọc section liên quan khi cần.**

# Zip Part Maker — Architecture and rules

## Project overview

Desktop utility phân phối file trong thư mục vào nhiều ZIP độc lập dưới giới hạn dung lượng. File đơn quá lớn có chính sách skip/nén thử/chia parts phải ghép lại. Identity/version hiện tại: `app/version.py`, `pyproject.toml`, `README.md`; migration không tạo project/version mới.

## Stack

Python >=3.11; PySide6 >=6.7,<7; stdlib `zipfile`, `pathlib`, threading, hashing/JSON. Setuptools build backend, pip editable install. Dev dependencies pytest >=8, PyInstaller >=6.8. Không có lockfile trong repo lúc migration; `requirements.txt` chỉ PySide6, ranges trong `pyproject.toml` là manifest thật. Không Node/npm, server framework hoặc DB runtime. Codeintel chỉ dùng Python AST/sqlite3/stdlib, không thêm production dependency.

## Architecture

`app/core` không phụ thuộc Qt. `app/ui` điều phối worker, settings, validation/dialogs và hiển thị. `app/workers` là Qt QObject/Signal/Slot bridge chạy trong QThread. `app/utils` cung cấp paths, checksums, sizes, resources, logging. Giữ ranh giới này, không đưa Qt vào core. Index/tooling ở `tools/codeintel`, không được import từ ứng dụng, không đổi setuptools package discovery `app*`.

## Entry points

`main.py:main`: logging → QApplication → app name/organization/icon → MainWindow → Qt event loop. CLI package script `zip-part-maker = main:main` trong pyproject. Native build scripts đóng gói `main.py`. Codeintel: `python3 -m tools.codeintel`, chỉ chạy từ repo/checkout.

## Data flow

Quét: `MainWindow.scan` → `ScanWorker.run` → `scan_files` → ScanResult → `_scan_finished` → `plan_archives` → FileTableModel + groups/oversized.

Nén: `MainWindow.compress` xác nhận oversize/conflict, chọn engine/options → CompressWorker → Compressor.run/create_archive → `.zip.tmp` trong thư mục tạm riêng tại output → verify_zip/testzip + SHA-256 + hard limit → rename → report `zip_report.json`. ZIP cũ chỉ bị thay sau verify thành công; CLEAN vẫn xóa sau xác nhận. Nhóm ZIP quá lớn được chia đôi và thử lại. FFD planner dùng biên 98%, kích thước ZIP thật được kiểm tra sau nén.

Chia/ghép: split_file tạo `.001`… và manifest atomically; JoinDialog → JoinWorker → validate manifest/names → stream/checksum/size → `.joining.tmp` → target tên mới nếu trùng. Hủy ghép theo khối 1 MiB; cleanup chỉ tệp tạm thuộc tác vụ. Dialog chỉ kết thúc sau thread finished. Format manifest v1 giữ nguyên; report bổ sung field `split_files`, giữ các field cũ.

## Folder structure

| Path | Vai trò |
|---|---|
| `app/core/{models,scanner,planner,compressor,engines,splitter,verifier}.py` | Domain/data/filesystem/engine |
| `app/ui/{main_window,dialogs,file_table_model,styles}.py` | Dashboard, join dialog, Qt model/view, QSS |
| `app/workers/` | Scan/compress/join Qt background bridge |
| `app/utils/` | Utilities dùng chung |
| `tests/` | Core/engine/version pytest regression |
| `scripts/`, `.github/workflows/build.yml` | Native packaging/release |
| `docs/` | Legacy context paths nay chuyển tiếp root canonical files |
| `tools/codeintel/`, `.agent/` | Tool source và rebuildable ignored cache |
| `HISTORY/` | Evidence theo ngày, không phải current truth |

## Code conventions

Giữ convention hiện có: type hints, `from __future__ import annotations`, snake_case function/module, PascalCase class, `pathlib.Path` cho đường dẫn. Dataclasses với slots cho domain models; enums cho engine/status/policies. UI tiếng Việt. Không format/rename hàng loạt vì task nhỏ. Rule product copy/brief nằm trong `AGENT.md`.

## Error handling

Core raise ValueError/OSError/InterruptedError cho validation, filesystem và cancel; ArchiveTooLargeError là ValueError subclass. Compressor thu thập lỗi/repartition và cleanup temporary; BaseException cleanup được dùng trong archive/split/join. Workers chuyển exception thành failed/cancelled signals; CompressWorker có broad exception tại boundary để surface unexpected errors. UI dùng QMessageBox/log và callbacks cập nhật state. Không xóa cleanup/cancel semantics khi chưa trace source.

## Types

Domain dataclasses/enums ở `app/core/models.py`, EngineInfo ở `engines.py`; typed Path, Callable callbacks. Qt progress byte counters dùng `qlonglong` để không tràn trên 2 GB; các payload khác có `object` và một số `type: ignore` ở bridge. Chưa có lint/typecheck tool/config riêng trong repo.

## Components/modules

MainWindow dashboard + QTableView/FileTableModel; JoinDialog/JoinWorker chạy ghép nền. LIGHT_STYLE trong `app/ui/styles.py` áp dụng toàn MainWindow; objectName như pageTitle, sidebar, primary, engineStatus và property state tạo selector scope. Không web route, HTML template, CSS utility framework hoặc design-token system được xác nhận. Dùng UI micro-change protocol ở AGENT, xác minh inheritance/dynamic selectors bằng source.

## Testing

Core/planner/scanner/compressor/splitter thay đổi phải có regression phù hợp; dùng `python3 -m pytest` (22 tests baseline migration; 76 sau review 0.0.6). `tests/test_ui.py` chạy offscreen với QSettings tạm: scan invalidation, worker lifecycle/cancel và progress >2 GB. Ví dụ targeted: `python3 -m pytest tests/test_splitter.py tests/test_ui.py`. Tool self-tests nằm riêng `python3 -m unittest tools.codeintel.test_indexer -v`, không require PySide6/pytest.

Sau UI changes giữ workflow cũ:

```bash
QT_QPA_PLATFORM=offscreen python3 -c 'from PySide6.QtWidgets import QApplication; from app.ui.main_window import MainWindow; a=QApplication([]); w=MainWindow(); w.close()'
```

Smoke chỉ kiểm tra tạo/đóng window, không xác nhận screenshot/colors/interaction/thread lifecycle. Nếu chạy, tránh ghi đè settings người dùng bằng môi trường config tạm. Không có yêu cầu lint/typecheck không tồn tại. Giữ CONTRIBUTING: changes tập trung, test hành vi mới, test trước PR, mô tả platform/UI evidence khi cần.

## Deployment

PyInstaller native target OS only, không cross-compile. Windows onefile EXE; macOS app + hdiutil DMG; Linux onefile binary. Scripts tự cài `.[dev]`; full build có thể cần network/platform tools, không chạy cho docs migration. GitHub Actions test/build trên ba OS, upload artifact; `v*` tag kích hoạt release qua gh. Không đổi workflow/release/version trong migration. PyInstaller resources dùng `resource_path` và `_MEIPASS`. Không claim release mới nhất từ metadata local.

## Security

Source files người dùng bất biến, không sửa/di chuyển/xóa; symlink scan bị bỏ qua. Safe archive names/prefix validation và `.tmp` cleanup phải được giữ. Clean old ZIP có confirmation ở UI và chỉ match prefix/output, không mở rộng glob. External compression dùng subprocess argument list, không shell interpolation. Không lưu secrets trong context/history/cache, chỉ env name hoặc `[REDACTED SECRET]`. Không thêm telemetry, administrator requirement, paid service. Theo SECURITY.md, báo lỗ hổng dữ liệu riêng qua GitHub Security, không công khai dữ liệu nhạy cảm.

## Agent rules

Không đổi stack/public API/backward compatibility/DB/deploy nếu chưa được user yêu cầu. Không xóa logic chưa hiểu hoặc rewrite toàn project cho task nhỏ. Ưu tiên patch nhỏ, verify source, không bịa business facts, không thêm paid service/dependency lớn/secrets, không sửa ngoài scope. CONTRIBUTING issue/fork/PR guidance áp dụng khi đóng góp/publish; không yêu cầu hỏi lại để làm migration local đã được user ủy quyền. Không tự commit.

## Code intelligence rules

Query cache trước khi crawl rộng; source luôn là truth. Status/update khi stale, verify trước patch và update sau thay đổi. Heuristic chỉ là navigation hint. Không global tooling/daemon/network/telemetry. Cache ignored, rebuild từ tool source; docs/memory/history không thay call graph. Giới hạn đầy đủ trong tools/codeintel/README.md.

## Legacy context migration

Đã đọc `docs/CLAUDE.md`, `docs/CONFIG.md`, `docs/SKILL.md`, README, CHANGELOG, CONTRIBUTING và SECURITY. Giữ Python/type hints/Path, Qt/core separation, immutable inputs, transactional archives, core regression, UI smoke, native builds, settings defaults và security/PR guidance.

**Deprecated:** rule cũ “Không gọi command shell phụ thuộc nền tảng để nén; chỉ dùng thư viện chuẩn zipfile” không khớp source hiện tại: `engines.py`/`compressor.py` đã hỗ trợ 7-Zip và WinRAR, CHANGELOG 0.0.2 ghi thêm WinRAR. Thay bằng: giữ engine selection/fallback hiện hành, subprocess argument list không shell; Python zipfile là engine tích hợp, macOS luôn dùng Python. Không tự xóa hỗ trợ engine ngoài. Legacy paths chuyển tiếp root files, không duy trì hai bộ rule độc lập. Không dựng conversation/history từ CHANGELOG.
