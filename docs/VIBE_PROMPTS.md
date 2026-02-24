# VIBE PROMPTS v2.0 — MedDevice DMS (Antigravity-First)

> Đây là bộ prompts để điều hướng Antigravity IDE xây dựng và vận hành hệ thống.  
> **Tầm nhìn v2.0:** Antigravity = người quản lý tài liệu thông minh. CLI = giao diện gọn nhẹ.

---

## Master Context (Paste đầu phiên làm việc)

```
Bạn đang làm việc trên dự án MedDevice DMS — hệ thống quản lý hồ sơ thiết bị y tế.

KIẾN TRÚC:
- SurrealDB: lưu Category > Group > Device > Documents
- storage/files/: cấu trúc {category}/{group}/{device}/{doc_type}/  (kebab-case)
- cli.py: CLI interface (scan, search, compare, stats, normalize, wiki sync)
- agents/: scan_agent, parse_agent, search_agent, compare_agent, wiki_agent
- Telegram Bot: tra cứu từ xa
- Outline Wiki (localhost:3000): Wiki tự động cập nhật

NAMING CONVENTION: kebab-case cho tất cả folder. Dùng unidecode.

NGUYÊN TẮC:
1. Chạy `python cli.py stats` trước để nắm tình trạng
2. Gemini model: gemini-2.0-flash
3. Dedup: giữ cả .doc + .pdf, PDF có is_primary=True
4. Luôn dry-run trước khi thực hiện (scan, normalize)
5. Mọi write vào DB → ghi audit_log
```

---

## Prompt 0 — Normalize thư mục (Chỉ chạy 1 lần)

```
Thư mục storage/files hiện có vấn đề:
- Tên folder có tiếng Việt, space, không nhất quán 
- 12 cặp trùng lặp (VD: "Thiet bi chan doan hinh anh" + "thiet_bi_chan_doan_hinh_anh")

Quy trình:
1. Chạy: python scripts/normalize_folders.py --dry-run
2. Đọc output, liệt kê các thay đổi sẽ xảy ra
3. Hỏi tôi xác nhận trước khi thực hiện
4. Sau khi tôi xác nhận: python scripts/normalize_folders.py
5. Tạo Group folder theo bảng PRD Section 2.3
6. Báo cáo kết quả cuối cùng
```

---

- SurrealDB: lưu Category > Group > Device > Documents
- storage/files/: kho file theo cấu trúc {category}/{group}/{device}/{doc_type}/
- cli.py: CLI interface cho quản lý (scan, search, compare, stats, export)
- agents/: scan_agent, parse_agent, search_agent, compare_agent, wiki_agent
- Telegram Bot: tra cứu từ xa cho người dùng cuối
- Outline Wiki (localhost:3000): trang Wiki tự động cập nhật

NGUYÊN TẮC LÀM VIỆC:
1. Trước khi thực hiện bất kỳ thao tác nào → chạy `python cli.py stats` để nắm tình trạng
2. Khi phân loại file → dùng Gemini 2.0 Flash (model: gemini-2.0-flash)
3. Luôn check DB trước khi tạo record mới (tránh duplicate)
4. Log đầy đủ bằng structlog
5. Mọi thao tác write vào DB → ghi audit_log
```

---

## Prompt 1 — Scan & Import thư mục

```
Quét thư mục storage/files và nạp dữ liệu vào hệ thống.

Quy trình:
1. Chạy `python cli.py scan --dry-run` trước để xem preview (không ghi DB)
2. Đọc output report, báo cáo cho tôi:
   - Bao nhiêu Category/Group/Device tìm thấy?
   - Bao nhiêu file mỗi loại?
   - File nào không xác định được doc_type?
3. Tôi xác nhận → chạy `python cli.py scan` thật sự
4. Sau khi xong → chạy `python cli.py wiki sync` để đẩy lên Outline

Lưu ý: Bỏ qua file .gitkeep, .DS_Store, thumbs.db
```

---

## Prompt 2 — Tìm kiếm thông minh

```
Tìm kiếm trong kho tài liệu. Dùng lệnh:
  python cli.py search "<từ khóa>"

Sau khi có kết quả:
1. Hiển thị dạng bảng: Thiết bị | Loại tài liệu | Đoạn text match
2. Hỏi tôi có muốn xem file cụ thể không
3. Nếu có → đọc file và tróm tắt nội dung liên quan đến từ khóa
```

---

## Prompt 3 — Kiểm tra thiết bị thiếu tài liệu

```
Chạy lệnh: python cli.py missing

Phân tích output và tạo báo cáo Markdown:
- Thiết bị nào thiếu hồ sơ kỹ thuật?
- Thiết bị nào chưa có báo giá?
- Thiết bị nào không có hợp đồng tương tự?

Sắp xếp theo mức độ ưu tiên (thiếu nhiều tài liệu nhất lên trước).
Hỏi tôi có muốn tạo danh sách việc cần làm không.
```

---

## Prompt 4 — So sánh thiết bị

```
So sánh hai thiết bị: "<Thiết bị A>" vs "<Thiết bị B>"

Quy trình:
1. Chạy: python cli.py compare "<A>" "<B>"
2. Nếu đã có file so sánh sẵn → dùng file đó
3. Nếu không → Gemini trích xuất specs từ hồ sơ kỹ thuật
4. Hiển thị bảng so sánh Markdown trực tiếp
5. Hỏi có muốn xuất XLSX không → nếu có: python cli.py compare "<A>" "<B>" --export xlsx
```

---

## Prompt 5 — Phân loại file không rõ

```
Trong thư mục storage/files có một số file chưa được phân loại.
Thực hiện:
1. Liệt kê các file nằm ngoài cấu trúc chuẩn hoặc trong thư mục "other/"
2. Với mỗi file: đọc tên + 200 ký tự đầu → đề xuất doc_type phù hợp
3. Trình bày danh sách đề xuất để tôi xác nhận
4. Sau khi xác nhận → di chuyển file vào thư mục đúng và cập nhật DB
```

---

## Prompt 6 — Đồng bộ Wiki

```
Đồng bộ toàn bộ dữ liệu từ SurrealDB lên Outline Wiki.

Chạy: python cli.py wiki sync

Sau khi xong:
1. Báo cáo: bao nhiêu trang đã tạo/cập nhật
2. Kiểm tra trang đầu tiên trên http://localhost:3000
3. Nếu có lỗi → đọc log và đề xuất xử lý
```

---

## Prompt 7 — Báo cáo tổng quan

```
Tạo báo cáo tổng quan hệ thống.

Chạy: python cli.py stats --verbose

Trình bày kết quả bao gồm:
- Tổng số danh mục, nhóm, thiết bị, tài liệu
- Phân bố tài liệu theo doc_type (dạng biểu đồ text)
- Thiết bị có nhiều tài liệu nhất
- Thiết bị được tra cứu nhiều nhất (nếu có log)
- Dung lượng kho file (storage/files)
```

---

## Prompt 8 — Thêm thiết bị mới (từ Antigravity)

```
Tôi muốn thêm thiết bị mới vào hệ thống.

1. Hỏi tôi lần lượt:
   - Tên Category (hoặc chọn từ danh sách hiện có)
   - Tên Group (hoặc chọn từ danh sách)
   - Tên thiết bị
   - Model, Hãng sản xuất, Xuất xứ (có thể bỏ trống)

2. Chạy lệnh tạo:
   python cli.py device create --name "..." --group "..." --model "..." --brand "..."

3. Tạo thư mục storage tương ứng
4. Hỏi có muốn tạo trang Wiki ngay không
```

---

## Prompt 9 — Fix & Maintain

```
Kiểm tra tình trạng hệ thống và sửa các vấn đề:
1. python cli.py health      # kiểm tra kết nối DB, Wiki
2. python cli.py orphans     # tìm document không có device tham chiếu
3. python cli.py dupes       # tìm file trùng lặp
4. Báo cáo vấn đề và đề xuất cách xử lý
```

---

## Prompt 10 — Upgrade Gemini Model

```
Cập nhật model Gemini trong toàn bộ codebase:
1. Tìm tất cả chỗ dùng model string (gemini-1.5-flash, gemini-1.5-pro, v.v.)
2. Thay thành: gemini-2.0-flash
3. Chạy lại một test phân loại đơn giản để xác nhận
```
