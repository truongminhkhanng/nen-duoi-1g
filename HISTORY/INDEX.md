# History index

Chỉ dùng khi cần truy lịch sử; không load toàn daily history mặc định. Records bắt đầu từ migration, không dựng hội thoại cũ từ CHANGELOG/git. Daily files append-only; index được cập nhật để tìm đúng ngày.

| Date | Topics | Important decisions | Files |
|---|---|---|---|
| 2026-10-03 | Migration context/memory/history; Python AST + SQLite local index; internal brief vs product copy | Giữ architecture/source; selective loading; cache ignored, update full rebuild; legacy zipfile-only Deprecated; không copy brief thành UI | [2026-10-03.md](2026-10-03.md) — interactions 001–003; review app/copy, chuẩn bị release 0.0.6 |
