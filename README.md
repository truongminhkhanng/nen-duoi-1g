<p align="center">
  <img src="assets/app-icon.png" width="128" alt="Zip Part Maker icon">
</p>

# Zip Part Maker

[![Build](https://github.com/truongminhkhanng/nen-duoi-1g/actions/workflows/build.yml/badge.svg)](https://github.com/truongminhkhanng/nen-duoi-1g/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Phiên bản hiện tại: **0.0.5**. Xem lịch sử thay đổi tại [CHANGELOG.md](CHANGELOG.md).

Ứng dụng desktop Python/PySide6 đóng gói một thư mục thành nhiều ZIP **độc lập**, mỗi ZIP nhỏ hơn giới hạn đã chọn (mặc định 950 MB). Ứng dụng dùng First Fit Decreasing, chừa 2% dung lượng an toàn, giữ file nguồn nguyên vẹn và hỗ trợ tên/đường dẫn Unicode.

## Tính năng chính

- Quét đệ quy ở background, không đi theo symlink và tự loại thư mục đầu ra.
- Bỏ qua `.DS_Store`, `Thumbs.db`, `desktop.ini`, `__MACOSX`, file ẩn/hệ thống tùy chọn.
- ZIP_STORED hoặc ZIP_DEFLATED mức nhanh/cân bằng/tối đa.
- Cho phép chọn Tự động, WinRAR, 7-Zip hoặc Python; macOS giữ engine Python tích hợp.
- Ghi `.zip.tmp`, kiểm tra `testzip()`, SHA-256 và dung lượng trước khi đổi tên.
- Bỏ qua, nén thử riêng hoặc chia file quá lớn thành `.001`… kèm manifest/checksum; có công cụ ghép lại.
- Xử lý xung đột bằng ghi đè, tên mới, hoặc xóa ZIP do ứng dụng đặt theo prefix sau khi xác nhận.
- Tạm dừng/hủy an toàn giữa các file, báo cáo `zip_report.json`, kéo-thả thư mục và lưu thiết lập.

## Tải ứng dụng

Tải bản mới nhất tại [GitHub Releases](https://github.com/truongminhkhanng/nen-duoi-1g/releases/latest):

| Hệ điều hành | File | Kiến trúc |
|---|---|---|
| Windows | `ZipPartMaker.exe` | x64 |
| macOS | `ZipPartMaker.dmg` | Apple Silicon (ARM64) |
| Linux | `ZipPartMaker` | x64 |

Ứng dụng chưa được ký chứng thư thương mại, vì vậy Windows SmartScreen hoặc macOS Gatekeeper có thể
hiển thị cảnh báo ở lần mở đầu tiên. Chỉ tải file từ trang Releases chính thức của repository này.

## Trường hợp sử dụng

- **Gửi cả thư mục qua Zalo:** đặt giới hạn khoảng `950 MB` để tạo nhiều ZIP độc lập dưới 1 GB,
  sau đó gửi lần lượt từng file. Người nhận có thể mở riêng từng ZIP, không cần tải đủ tất cả phần.
- **Gửi tài liệu qua email:** đặt giới hạn theo dung lượng tệp đính kèm của nhà cung cấp, chẳng hạn
  `20 MB` hoặc `25 MB`.
- **Tải lên cloud theo từng phần:** chia bộ ảnh, video, tài liệu hoặc source code thành các ZIP nhỏ
  để tải lại riêng phần bị lỗi thay vì tải lại toàn bộ.
- **Chép sang USB/FAT32:** đặt giới hạn dưới `4 GB` để tránh giới hạn kích thước một file của FAT32.
- **Bàn giao dữ liệu theo đợt:** mỗi ZIP độc lập, có SHA-256 và báo cáo `zip_report.json`, phù hợp
  khi cần kiểm tra file nào đã giao hoặc bị lỗi.
- **Lưu trữ và sao lưu:** gom nhiều file nhỏ thành các gói có kích thước đều, dễ sao chép, đánh số
  và lưu trên nhiều thiết bị.

### App không dùng để làm gì?

Nếu chỉ có một file đơn như video `2.5 GB`, ứng dụng không thể bảo đảm biến nó thành một ZIP độc lập
dưới 1 GB nếu dữ liệu không nén đủ nhỏ. Chế độ chia `.001`, `.002` là phương án phụ để truyền file;
người nhận phải tải đủ và ghép lại trước khi sử dụng. Mục tiêu chính của app là **phân phối nhiều file
trong một thư mục vào nhiều ZIP độc lập**, không phải cắt video hoặc chia một file lớn.

## Chạy từ source

Yêu cầu Python 3.11+:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
python main.py
```

Để dùng engine 7-Zip, cài `7z.exe` trên Windows hoặc `7zz`/`7z` trên Linux và bảo đảm
chương trình nằm trong `PATH`. Nếu không tìm thấy, ứng dụng tự dùng engine Python tích hợp.
WinRAR chỉ được hỗ trợ trên Windows và cần cài `WinRAR.exe`; ứng dụng chỉ yêu cầu WinRAR tạo
file ZIP, không tạo file RAR.

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
- Công cụ ghép chạy trong nền, hiển thị tiến trình và cho phép hủy an toàn khi xử lý file lớn.
- Dark mode riêng chưa ép buộc; widget vẫn kế thừa palette hệ điều hành, stylesheet sáng bảo đảm giao diện nhất quán.

## An toàn dữ liệu

Ứng dụng không sửa, di chuyển hoặc xóa file nguồn. Khi hủy/lỗi, chỉ `.tmp` đang tạo bị xóa. Chế độ dọn ZIP cũ chỉ khớp các tên `<prefix>_NNN*.zip` trong đúng thư mục đầu ra và luôn yêu cầu xác nhận.

## Đóng góp và giấy phép

Đọc [CONTRIBUTING.md](CONTRIBUTING.md) trước khi gửi pull request và báo cáo vấn đề bảo mật theo
[SECURITY.md](SECURITY.md). Dự án được phát hành theo giấy phép [MIT](LICENSE).
