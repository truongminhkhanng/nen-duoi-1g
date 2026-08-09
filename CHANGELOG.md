# Changelog

## 0.0.5 - 2026-08-09

- Chia file lớn theo luồng 1 MiB, giảm RAM và tránh đọc lại dữ liệu để tính checksum.
- Ghép file trong worker nền với tiến trình và hủy an toàn, không làm treo giao diện.
- Chuyển danh sách file sang model/view để giảm RAM và tăng tốc khi quét nhiều file.
- Sửa lưu lựa chọn engine với các phiên bản PySide6 trả về dữ liệu combo dạng chuỗi.

## 0.0.4 - 2026-08-08

- Xóa nút và hộp thoại Trường hợp sử dụng khỏi giao diện theo phản hồi người dùng.
- Giữ nguyên toàn bộ logic chia thư mục thành ZIP độc lập và các engine nén.

## 0.0.3 - 2026-08-08

- Thêm mục Trường hợp sử dụng ngay trong ứng dụng.
- Làm rõ mục tiêu chia thư mục nhiều file thành các ZIP độc lập để gửi qua Zalo/email/cloud.
- Cảnh báo rõ file đơn vượt giới hạn không thể trở thành ZIP độc lập nếu không nén đủ nhỏ.
- Đổi nhãn chia `.001` để người dùng biết các phần phải được ghép lại.

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
