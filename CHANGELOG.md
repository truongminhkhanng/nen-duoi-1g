# Changelog

## 0.0.6 - 2026-10-03

- Chuẩn hóa nội dung tiếng Việt trên màn hình chính, tùy chọn nén và hộp thoại ghép tệp.
- Sửa hủy quét/nén, đặt lại trạng thái tạm dừng và tiến trình với dữ liệu trên 2 GB.
- Yêu cầu quét lại khi thay thư mục hoặc tùy chọn quét; khóa thiết lập khi tác vụ đang chạy.
- Kiểm tra danh sách ghép, dung lượng và SHA-256; hỗ trợ tệp rỗng và hủy giữa các khối dữ liệu.
- Giữ nguyên tệp kết quả sẵn có khi ghép; chỉ dọn tệp tạm do tác vụ tạo.
- Giữ ZIP cũ cho đến khi ZIP thay thế được kiểm tra thành công; sửa lọc ZIP theo tiền tố có dấu ngoặc.
- Sửa vòng đời worker khi đóng hộp thoại ghép và bổ sung báo cáo các tệp đã chia.
- Bổ sung quy trình Agent/Memory/History và công cụ tra cứu source cục bộ.
- Build và Release lấy số phiên bản từ ứng dụng, kiểm tra tag và chạy test trên ba hệ điều hành.

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
