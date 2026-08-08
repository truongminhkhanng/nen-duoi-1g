# Zip Part Maker

Ứng dụng desktop Python/PySide6 đóng gói một thư mục thành nhiều ZIP **độc lập**, mỗi ZIP nhỏ hơn giới hạn đã chọn (mặc định 950 MB). Ứng dụng dùng First Fit Decreasing, chừa 2% dung lượng an toàn, giữ file nguồn nguyên vẹn và hỗ trợ tên/đường dẫn Unicode.

## Tính năng chính

- Quét đệ quy ở background, không đi theo symlink và tự loại thư mục đầu ra.
- Bỏ qua `.DS_Store`, `Thumbs.db`, `desktop.ini`, `__MACOSX`, file ẩn/hệ thống tùy chọn.
- ZIP_STORED hoặc ZIP_DEFLATED mức nhanh/cân bằng/tối đa.
- Ghi `.zip.tmp`, kiểm tra `testzip()`, SHA-256 và dung lượng trước khi đổi tên.
- Bỏ qua, nén thử riêng hoặc chia file quá lớn thành `.001`… kèm manifest/checksum; có công cụ ghép lại.
- Xử lý xung đột bằng ghi đè, tên mới, hoặc xóa ZIP do ứng dụng đặt theo prefix sau khi xác nhận.
- Tạm dừng/hủy an toàn giữa các file, báo cáo `zip_report.json`, kéo-thả thư mục và lưu thiết lập.

## Chạy từ source

Yêu cầu Python 3.11+:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
python main.py
```

Chạy test:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## Build riêng từng nền tảng

PyInstaller không cross-compile. Hãy chạy script trên đúng hệ điều hành đích:

- Windows PowerShell: `./scripts/build_windows.ps1` → `dist/ZipPartMaker.exe`
- macOS: `./scripts/build_macos.sh` → `dist/Zip Part Maker.app` và `dist/ZipPartMaker.dmg`
- Linux: `./scripts/build_linux.sh` → `dist/ZipPartMaker`

Trên Ubuntu tối giản, Qt có thể cần các runtime XCB/GL của hệ thống. Cài trước bằng `sudo apt install libgl1 libegl1 libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0` (desktop Ubuntu thông thường thường đã có phần lớn các gói này).

GitHub Actions chạy ba runner riêng và tải artifact tương ứng. Với AppImage, build binary Linux trước, tạo AppDir có `AppRun`, desktop file và icon, rồi chạy `appimagetool AppDir ZipPartMaker.AppImage`; nên thực hiện trên bản Linux cũ nhất cần hỗ trợ để tăng tương thích glibc.

## Cách dùng

1. Chọn hoặc kéo-thả thư mục nguồn; đầu ra mặc định là `ZIP_PARTS` bên trong nguồn.
2. Chọn giới hạn, mức nén, prefix và tùy chọn quét; bấm **Quét file**.
3. Xem số ZIP dự kiến và trạng thái file quá lớn; bấm **Bắt đầu nén**.
4. Nếu có file quá lớn hoặc ZIP cũ, chọn chính sách trong hộp thoại.
5. Kiểm tra ZIP và `zip_report.json` trong thư mục đầu ra.

## Giới hạn đã biết

- Dung lượng ZIP chỉ biết chính xác sau khi nén. Nếu một nhóm nhiều file vẫn vượt giới hạn sau biên an toàn 2%, ứng dụng xóa file tạm và tự chia đôi nhóm để thử lại; nếu chỉ còn một file thì ghi lỗi rõ ràng.
- Tạm dừng/hủy có hiệu lực sau khi `zipfile` ghi xong file hiện tại; Python `zipfile` không cung cấp ngắt an toàn giữa một file.
- Công cụ ghép chạy đồng bộ; phù hợp thao tác chủ động, nhưng file cực lớn có thể làm hộp thoại ít phản hồi trong lúc kiểm tra SHA-256.
- Dark mode riêng chưa ép buộc; widget vẫn kế thừa palette hệ điều hành, stylesheet sáng bảo đảm giao diện nhất quán.

## An toàn dữ liệu

Ứng dụng không sửa, di chuyển hoặc xóa file nguồn. Khi hủy/lỗi, chỉ `.tmp` đang tạo bị xóa. Chế độ dọn ZIP cũ chỉ khớp các tên `<prefix>_NNN*.zip` trong đúng thư mục đầu ra và luôn yêu cầu xác nhận.
