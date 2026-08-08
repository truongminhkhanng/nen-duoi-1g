# Hướng dẫn phát triển

- Python 3.11+, type hints và `pathlib.Path` cho mọi đường dẫn.
- `app/core` không phụ thuộc Qt; UI chỉ điều phối worker và hiển thị trạng thái.
- Không thao tác file nguồn. Mọi archive phải đi qua file `.tmp`, verifier và rename.
- Một thay đổi về planner/scanner/compressor/splitter phải kèm test hồi quy tương ứng.
- Không gọi command shell phụ thuộc nền tảng để nén; chỉ dùng thư viện chuẩn `zipfile`.
