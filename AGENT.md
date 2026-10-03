> **ĐÂY LÀ ENTRY POINT CHÍNH CỦA AI TRONG PROJECT. KHI USER GỌI `@AGENT.md`, AGENT PHẢI TỰ LOAD CONTEXT CẦN THIẾT, DÙNG PROJECT-LOCAL CODE INTELLIGENCE KHI PHÙ HỢP, XÁC MINH SOURCE THẬT, THỰC HIỆN TASK, VERIFY VÀ CẬP NHẬT MEMORY/HISTORY.**

# Zip Part Maker — Agent entry point

## Start here

Luôn đọc file này và [MEMORY.md](MEMORY.md). Đây là dự án desktop **đã tồn tại**, không scaffold lại. Phân loại task trước khi đọc thêm: UI micro change, bug fix, feature, API, database/schema, auth/security, config, integration, refactor, deployment, docs/content hoặc investigation.

User chỉ cần `@AGENT.md [yêu cầu]`. Tự lấy thông tin đã có trong repo/memory; chỉ hỏi khi thực sự thiếu quyết định cần thiết. Nếu context chưa xác nhận, ghi `[CHƯA XÁC NHẬN]`, không bịa business fact.

## Selective context loading

| Task | Context bổ sung | Tìm code / verify |
|---|---|---|
| UI micro change | `CLAUDE.md` → Components/modules, Code conventions; `SKILL.md` → ui-micro-change | Widget → objectName → QSS; offscreen smoke + inspect declaration |
| Core bug/feature/refactor | `CLAUDE.md` → Architecture, Data flow, Error handling, Testing; skill core-archive-safety | Exact function + impact + test hồi quy |
| Config/integration | `CONFIG.md` → section liên quan; skill compression-engine-check nếu liên quan engine | Config source, resolve_engine, test platform matrix mô phỏng |
| Auth/security/API/schema | `CLAUDE.md` → Security; `CONFIG.md` → Auth, Database, API | Source hiện tại không có server/auth/DB; xác minh scope trước khi thiết kế mới |
| Deployment | `CLAUDE.md` → Deployment; `CONFIG.md` → Deployment; skill native-build-release | Build script/workflow trên đúng target OS |
| Docs/content/investigation | Section tài liệu liên quan; index nếu cần code facts | Đối chiếu source, không mặc định chạy build |

Đọc đúng section trong [CLAUDE.md](CLAUDE.md), [CONFIG.md](CONFIG.md), [SKILL.md](SKILL.md), không mặc định load toàn bộ. [LONG_TERM_MEMORY.md](LONG_TERM_MEMORY.md) chỉ khi cần why/decision/constraint. [HISTORY/INDEX.md](HISTORY/INDEX.md) chỉ khi truy lịch sử; history hôm nay khi continuation. Chỉ đọc history cũ khi user nhắc lần trước, có conflict, cần output/decision cũ hoặc memory dẫn reference. Không đọc hết history ở đầu session.

## Source-of-truth hierarchy

1. User instruction mới nhất (trong phạm vi system/developer constraints).
2. Source/config/schema/tests hiện tại.
3. Kết quả runtime/build/test hiện tại.
4. Project-local code intelligence.
5. `CONFIG.md`.
6. `CLAUDE.md`.
7. `LONG_TERM_MEMORY.md`.
8. `MEMORY.md`.
9. `HISTORY/`.

Giữ bốn lớp riêng: source là current truth; SQLite là structural cache; Markdown context/memory là semantic state/decisions; history là evidence quá khứ. Cache/history không override source.

## Code intelligence workflow

Từ root repo, dùng Python 3.11+ hiện có (`python3` trên môi trường này; `python` nếu virtualenv/Windows cung cấp tên đó):

```bash
python3 -m tools.codeintel status
python3 -m tools.codeintel update
python3 -m tools.codeintel search 'plan_archives'
python3 -m tools.codeintel explore 'MainWindow compress'
python3 -m tools.codeintel callers 'app.core.planner.plan_archives'
python3 -m tools.codeintel callees 'app.core.compressor.Compressor.create_archive'
python3 -m tools.codeintel impact 'app/ui/styles.py'
```

Khi task liên quan code: status → update nếu stale/missing → search/explore → exact file/symbol/line → **mở source thật** → verify exact scope → impact nếu sửa shared code/style/config → patch nhỏ → targeted verify → update index. Không patch từ graph. Queries từ chối cache stale (exit 2); `status` trả JSON với `stale`, exit 0 không có nghĩa cache fresh. `index` rebuild lần đầu hoặc phục hồi. `update` rebuild khi đổi nội dung, không incremental; clean thì no-op. Xem [tool README](tools/codeintel/README.md) về giới hạn và confidence.

Nếu graph không chắc: dùng `rg -n` và đọc thêm source; không coi `heuristic`/`unresolved` là fact. `explore` dùng token ranking, không hiểu mọi brief ngôn ngữ tự nhiên; chuyển yêu cầu sang tên domain/symbol thực. Nếu cache/tool lỗi, ghi rõ và fallback source search/read để tiếp tục việc có thể làm. Không global install, daemon, network index hoặc paid service.

## Minimal correct change

Giữ stack Python/PySide6, public API, backward compatibility, data formats, package manager và deployment hiện tại trừ khi user yêu cầu thay đổi tương ứng. Không xóa logic chưa hiểu, rewrite module cho task nhỏ, refactor/cleanup ngoài scope, rename hàng loạt, global replace mù quáng, tự thêm dependency lớn hoặc runtime production. Giữ `app/core` độc lập Qt; file nguồn người dùng bất biến; archive `.tmp` → verify → rename.

Bug ngoài scope: ghi `MEMORY.md` → Open issues (đánh dấu mức xác nhận); vấn đề dài hạn đưa vào `LONG_TERM_MEMORY.md`. Không tiện thể sửa feature/UI/API trong migration này. Không tự commit, publish, gửi thông tin cho người khác hoặc đổi deployment chỉ vì đã sửa code.

## UI micro-change protocol

Đây là desktop Qt, không phải website: visible UI → `MainWindow`/`JoinDialog` → widget/layout → `setObjectName`/`setProperty` → selector trong `app/ui/styles.py` hoặc style thật khác → exact declaration. Ví dụ header Dashboard dùng `QLabel#pageTitle`/`#pageSubtitle`; không giả định có component Header.

Kiểm tra usages/impact trước khi đổi stylesheet chung. Rule theo loại widget (`QLabel`, `QPushButton`, `*`) có thể ảnh hưởng nhiều nơi. Khi chỉ đổi header, dùng scope theo objectName/convention hiện tại; không đổi màu global hay màu của Footer/Button/Alert không liên quan. Graph QSS là heuristic: dynamic objectName, vòng lặp, state và inheritance cần đọc source. Không global replace `red` → `blue`.

## QUY TẮC PHÂN BIỆT VĂN NỘI BỘ VÀ NỘI DUNG CHO NGƯỜI DÙNG

Những gì người dùng nói trong quá trình trao đổi là **NGÔN NGỮ NỘI BỘ** để mô tả yêu cầu, ý tưởng, ví dụ hoặc cách vận hành. Không mặc định sao chép nguyên văn vào giao diện website/app, placeholder, label, button, tooltip, thông báo, mô tả chức năng, heading, nội dung hướng dẫn hoặc bất kỳ nội dung nào người dùng cuối nhìn thấy.

Phải hiểu **mục đích** của brief rồi viết lại thành ngôn ngữ sản phẩm phù hợp ngữ cảnh và người dùng cuối. Số liệu/câu chữ được đưa ra để minh họa yêu cầu không tự động trở thành UI copy.

| Brief nội bộ | Nội dung sản phẩm phù hợp |
|---|---|
| “ví dụ 400.000đ đổi thành 150.000 VNĐ” để giải thích tìm/thay thế | Label “Chuỗi cần tìm”, placeholder “Nhập nội dung cần tìm”; label “Chuỗi thay thế”, placeholder “Nhập nội dung thay thế”. Không chèn hai số minh họa vào UI. |
| “cái nút này để bấm xóa hết” | “Xóa tất cả” |
| “chỗ này khách nhập sđt” | Label “Số điện thoại”; placeholder “Nhập số điện thoại” |

Chỉ giữ nguyên văn khi user nói rõ “giữ nguyên câu này”, “để đúng nội dung này”, “copy nguyên văn”, hoặc đó rõ ràng là dữ liệu cần hiển thị. Khi không chắc, ưu tiên coi câu đó là chỉ dẫn nội bộ. Rule này cũng áp dụng khi viết docs/hướng dẫn dành cho người dùng sản phẩm; history nội bộ có thể ghi brief đã làm sạch secret.

## Verify and close

Chọn verify theo scope: core test hồi quy tương ứng; UI offscreen smoke nếu có Qt; tooling `python3 -m unittest tools.codeintel.test_indexer -v`; trước PR chạy `python3 -m pytest` theo CONTRIBUTING. Không cần full release build cho docs/tooling; không claim UI/build đã verify nếu chưa chạy.

Sau task có ý nghĩa: inspect diff → append interaction vào `HISTORY/YYYY-MM-DD.md` (Asia/Ho_Chi_Minh, thời gian thực; không sửa interaction cũ) → cập nhật `HISTORY/INDEX.md` → nén working state vào `MEMORY.md` (tối đa khoảng 400–700 từ) → extract durable decision vào long-term nếu cần. Chỉ sửa CONFIG/CLAUDE khi truth/rule đổi thật. Không ghi secret, dữ liệu file người dùng hay raw transcript khổng lồ. Final báo outcome, files, verify và limitation rõ ràng.
