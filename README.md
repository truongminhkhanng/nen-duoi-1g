<p align="center">
  <img src="assets/app-icon.png" width="128" alt="Biểu tượng Zip Part Maker">
</p>

# Zip Part Maker

[![Build](https://github.com/truongminhkhanng/nen-duoi-1g/actions/workflows/build.yml/badge.svg)](https://github.com/truongminhkhanng/nen-duoi-1g/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Đóng gói thư mục thành nhiều tệp ZIP nhỏ, dễ gửi và lưu trữ.**

Chọn thư mục, đặt dung lượng tối đa cho mỗi ZIP và bắt đầu nén. Zip Part Maker tự sắp xếp các tệp vào từng ZIP để kết quả nhỏ hơn giới hạn bạn chọn. Mỗi ZIP có thể mở và giải nén riêng, thuận tiện khi gửi nhiều tài liệu, ảnh hoặc bàn giao dữ liệu theo từng đợt.

Ứng dụng giữ nguyên các tệp trong thư mục nguồn và hỗ trợ tên tệp tiếng Việt.

Phiên bản **0.0.7** · [Xem thay đổi](CHANGELOG.md)

## Tải và mở ứng dụng

Tải bản phù hợp với máy của bạn tại **[trang tải Zip Part Maker](https://github.com/truongminhkhanng/nen-duoi-1g/releases/latest)**. Bạn không cần cài Python để sử dụng các bản này.

| Máy của bạn | Tệp cần tải | Cách mở |
|---|---|---|
| Windows 64-bit | `ZipPartMaker.exe` | Mở tệp `.exe`. |
| macOS dùng chip Apple Silicon | `ZipPartMaker.dmg` | Mở tệp `.dmg`, kéo ứng dụng vào Applications rồi mở ứng dụng. |
| Linux 64-bit | `ZipPartMaker` | Cấp quyền chạy cho tệp rồi mở ứng dụng. |

Trên Linux, mở Terminal tại thư mục chứa tệp đã tải và chạy:

```bash
chmod +x ZipPartMaker
./ZipPartMaker
```

Ứng dụng chưa có chứng thư ký thương mại, nên Windows hoặc macOS có thể hiển thị cảnh báo khi mở lần đầu. Hãy tải từ trang chính thức được liên kết ở trên.

## Tạo các tệp ZIP

1. **Chọn thư mục cần nén.** Bạn cũng có thể kéo thả thư mục vào ứng dụng.
2. **Chọn nơi lưu kết quả.** Mặc định, ứng dụng tạo thư mục `ZIP_PARTS` bên trong thư mục nguồn.
3. **Đặt giới hạn dung lượng cho mỗi ZIP.** Mặc định là **950 MB**. Nếu nơi nhận có giới hạn dung lượng, hãy chọn mức thấp hơn giới hạn đó.
4. **Chọn mức nén.** Dùng **Cân bằng** để bắt đầu; chọn **Nhanh** nếu ưu tiên thời gian hoặc **Tối đa** nếu muốn thử giảm dung lượng hơn nữa.
5. Bấm **Quét thư mục** để xem danh sách tệp, số ZIP dự kiến và các tệp vượt giới hạn.
6. Bấm **Bắt đầu nén**. Nếu có tệp quá lớn hoặc ZIP trùng tên, ứng dụng sẽ hỏi cách xử lý.
7. Khi hoàn tất, mở thư mục kết quả để lấy các ZIP. Tệp `zip_report.json` ghi lại kết quả, các tệp bị bỏ qua và lỗi nếu có.

Bạn có thể đổi **Tiền tố tên ZIP** để dễ nhận biết từng đợt đóng gói, chọn quét thư mục con, giữ cấu trúc thư mục hoặc bỏ qua tệp ẩn và tệp hệ thống.

### Gửi và mở kết quả

Gửi lần lượt các ZIP trong thư mục kết quả. Người nhận có thể giải nén từng ZIP bằng công cụ mở ZIP trên máy của họ; không cần tải đủ tất cả ZIP để mở một ZIP riêng lẻ.

## Khi có tệp vượt giới hạn

Một tệp lớn có thể vẫn vượt giới hạn sau khi nén. Khi gặp trường hợp này, bạn có ba lựa chọn:

| Lựa chọn | Kết quả |
|---|---|
| **Bỏ qua** | Tiếp tục đóng gói các tệp còn lại. |
| **Nén thử riêng** | Thử tạo một ZIP riêng cho tệp đó; chỉ giữ ZIP nếu nhỏ hơn giới hạn. |
| **Chia tệp để ghép lại** | Tạo các phần `.001`, `.002`… cùng tệp `.manifest.json` để ghép lại sau. |

**Nếu chọn chia tệp, hãy gửi đầy đủ các phần và tệp `.manifest.json`.** Người nhận cần ghép lại trước khi sử dụng tệp gốc. Cách này hữu ích khi truyền một tệp lớn, chẳng hạn video, nhưng không làm mỗi phần trở thành một tệp có thể mở riêng.

### Ghép lại tệp đã chia

1. Đặt tệp `.manifest.json` và đầy đủ các phần `.001`, `.002`… trong cùng một thư mục.
2. Mở Zip Part Maker, chọn **Ghép tệp đã chia…**.
3. Bấm **Chọn danh sách ghép…** và chọn tệp `.manifest.json`.
4. Chọn thư mục lưu kết quả, rồi bấm **Ghép tệp**.

Ứng dụng kiểm tra các phần trước khi hoàn tất. Nếu tên tệp kết quả đã tồn tại, ứng dụng tạo tên mới để giữ nguyên tệp cũ.

## Chọn công cụ nén

Bạn có thể giữ tùy chọn **Tự động (khuyên dùng)** để bắt đầu. Ứng dụng có sẵn công cụ nén tích hợp và có thể dùng 7-Zip khi đã được cài trên Windows hoặc Linux. WinRAR được hỗ trợ trên Windows để tạo ZIP. Trên macOS, ứng dụng dùng công cụ tích hợp.

Bạn không cần cài thêm công cụ nén để sử dụng ứng dụng.

## Những điều cần biết

- **Dung lượng sau khi nén tùy thuộc nội dung tệp.** Số ZIP sau khi quét là dự kiến; ứng dụng kiểm tra dung lượng thực tế và có thể chia lại nhóm tệp khi cần.
- **Tệp gốc được giữ nguyên.** Ứng dụng không sửa, di chuyển hay xóa tệp trong thư mục nguồn. Thư mục lưu kết quả phải khác thư mục nguồn; có thể dùng thư mục con `ZIP_PARTS` mặc định.
- **ZIP trùng tên có nhiều cách xử lý.** Chọn **Tạo tên mới** nếu muốn giữ các ZIP đã có. Nếu chọn **Ghi đè**, ZIP cũ chỉ được thay thế sau khi ZIP mới đã nén và kiểm tra thành công. Tùy chọn dọn ZIP cũ luôn yêu cầu xác nhận.
- **Tạm dừng hoặc hủy có thể cần chờ.** Khi dùng công cụ nén tích hợp, thao tác có hiệu lực sau khi xử lý xong tệp đang nén. Các tệp tạm của tác vụ được dọn khi hủy hoặc gặp lỗi.

## Góp ý và báo lỗi

Nếu gặp lỗi, hãy [gửi báo lỗi tại đây](https://github.com/truongminhkhanng/nen-duoi-1g/issues), kèm hệ điều hành, phiên bản ứng dụng và các bước để gặp lại lỗi. Bạn có thể đính kèm thông báo lỗi hoặc phần liên quan trong `zip_report.json`; hãy bỏ thông tin riêng tư trước khi gửi.

Nếu muốn đóng góp mã nguồn, xem [hướng dẫn đóng góp](CONTRIBUTING.md). Các vấn đề bảo mật được tiếp nhận theo [hướng dẫn bảo mật](SECURITY.md).

Zip Part Maker được phát hành theo giấy phép [MIT](LICENSE).
