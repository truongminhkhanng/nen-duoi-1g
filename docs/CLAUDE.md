# Hướng dẫn phát triển — legacy path

Canonical rules đã hợp nhất vào [../CLAUDE.md](../CLAUDE.md); entry point là [../AGENT.md](../AGENT.md).

Giữ Python 3.11+/type hints/Path, Qt-core separation, immutable inputs, `.tmp` → verify → rename và core regression. Rule cũ “chỉ dùng zipfile” được đánh dấu **Deprecated** trong section Legacy context migration vì source đã hỗ trợ 7-Zip/WinRAR; không loại bỏ các engine hiện có. Đọc section liên quan ở file canonical, không duy trì một bộ rule thứ hai tại đây.
