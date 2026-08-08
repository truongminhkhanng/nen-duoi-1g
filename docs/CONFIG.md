# Cấu hình

Thiết lập GUI được lưu bằng `QSettings` dưới organization/application `ZipPartMaker`.

| Thiết lập | Mặc định | Ý nghĩa |
|---|---:|---|
| limit / unit | 950 MB | Giới hạn cứng; planner dùng 98% làm sức chứa |
| compression | Cân bằng | ZIP_DEFLATED level 6 |
| prefix | part | Sinh `part_001.zip`… |
| recursive | bật | Quét thư mục con |
| keep structure | bật | Giữ đường dẫn tương đối trong ZIP |
| skip hidden/system | bật | Loại file ẩn/hệ thống |
| open output | bật | Mở kết quả sau khi hoàn thành |

Không có telemetry hoặc cấu hình quyền administrator.
