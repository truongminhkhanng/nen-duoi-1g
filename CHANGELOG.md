# Changelog

## 0.0.2 - 2026-08-08

- Cho phép chọn Tự động, WinRAR, 7-Zip hoặc Python làm engine nén.
- WinRAR tạo ZIP trên Windows bằng `-afzip`; Linux/macOS fallback an toàn về Python.
- Cải thiện trạng thái engine bằng màu, biểu tượng, tooltip và lý do fallback tức thời.
- Thiết lập engine không hợp lệ tự trở về Tự động thay vì làm lỗi khởi động.

## 0.0.1 - 2026-08-08

- Thêm icon ứng dụng cho Windows, macOS, Linux và favicon dùng trên GitHub/web.
- Gắn icon vào cửa sổ và các gói PyInstaller.
- Bổ sung giấy phép MIT, hướng dẫn đóng góp và chính sách bảo mật.
- Tự động tạo GitHub Release kèm file cài đặt khi push version tag.

## 0.0.0 - 2026-08-08

- Giao diện dashboard cho Windows, macOS và Linux.
- Windows/Linux tự động ưu tiên 7-Zip để tạo các ZIP độc lập.
- macOS tiếp tục dùng engine Python tích hợp.
- Tự động fallback về Python khi không tìm thấy 7-Zip hoặc khi tắt giữ cấu trúc thư mục.
- Hiển thị engine nén đang dùng và lý do fallback trên dashboard.
- Hỗ trợ build EXE, DMG và Linux binary bằng GitHub Actions.
