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
6. Khi gặp PDF không có text layer → dùng Gemini Vision (gemini-2.0-flash với file upload)
7. File hợp đồng (contract/) > 10MB → chỉ extract metadata, không extract toàn bộ text
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
2b. Phát hiện và liệt kê các cặp folder trùng nội dung
2c. Với mỗi cặp: merge nội dung vào folder đích, xóa folder cũ
2d. Hỏi tôi xác nhận từng cặp trước khi merge
3. Hỏi tôi xác nhận trước khi thực hiện các thay đổi chung
4. Sau khi tôi xác nhận: python scripts/normalize_folders.py
5. Tạo Group folder theo bảng PRD Section 2.3
6. Báo cáo kết quả cuối cùng
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
5. Với các file không xác định được doc_type (confidence < 0.7):
   - Liệt kê riêng thành danh sách "Cần xem xét thủ công"
   - Di chuyển vào other/ tạm thời, KHÔNG ghi DB
   - Hỏi tôi có muốn chạy Prompt 5 để phân loại thủ công không

Lưu ý: Bỏ qua file .gitkeep, .DS_Store, thumbs.db
```

---

## Prompt 2 — Tìm kiếm thông minh

```
Tìm kiếm trong kho tài liệu. 

Quy trình:
0. Hỏi tôi có muốn giới hạn phạm vi tìm kiếm không:
   - Tất cả danh mục (mặc định)
   - Chỉ trong Category cụ thể
   - Chỉ loại tài liệu cụ thể (technical/config/price...)
   Sau đó build lệnh với filter tương ứng:
     python cli.py search "<từ khóa>" --category "..." --doc-type "..."
1. Chạy lệnh tìm kiếm. Sau khi có kết quả:
2. Hiển thị dạng bảng: Thiết bị | Loại tài liệu | Đoạn text match
3. Hỏi tôi có muốn xem file cụ thể không
4. Nếu có → đọc file và tróm tắt nội dung liên quan đến từ khóa
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
Hỏi tôi muốn làm gì với danh sách:
  [1] Xuất Excel để theo dõi
  [2] Gửi báo cáo qua Telegram Bot
  [3] Lưu vào Outline Wiki (trang "Thiếu tài liệu - cập nhật {ngày}")
  [4] Không làm gì thêm
```

---

## Prompt 4 — So sánh thiết bị

```
So sánh hai thiết bị: "<Thiết bị A>" vs "<Thiết bị B>"

Quy trình:
1. Chạy: python cli.py compare "<A>" "<B>"
2. Nếu đã có file so sánh sẵn → dùng file đó
3. Nếu không → Gemini trích xuất specs từ hồ sơ kỹ thuật
3b. Nếu có nhiều file cùng loại (nhiều IB) → hỏi tôi chọn file nào để so sánh
    hoặc dùng file mới nhất (theo ngày)
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
3. Trình bày danh sách đề xuất dạng bảng:
   | File | Đề xuất doc_type | Lý do | Confidence |
   Hỏi tôi:
   [A] Xác nhận tất cả đề xuất
   [B] Xem xét từng file (mode interactive)
   [C] Bỏ qua, giữ trong other/
4. Sau khi xác nhận → di chuyển file vào thư mục đúng và cập nhật DB
```

---

## Prompt 6 — Đồng bộ Wiki

```
Đồng bộ dữ liệu từ SurrealDB lên Outline Wiki.

Hỏi tôi muốn sync loại nào:
  [1] Full sync (toàn bộ) — chậm, ~vài phút
  [2] Incremental (chỉ thay đổi từ lần sync cuối) — nhanh, dùng updated_at
  [3] Sync 1 device cụ thể

Lệnh tương ứng:
  python cli.py wiki sync --full
  python cli.py wiki sync --since last
  python cli.py wiki sync --device "tên thiết bị"

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
1. Tổng số danh mục, nhóm, thiết bị, tài liệu
2. Phân bố tài liệu theo doc_type (dạng biểu đồ text)
3. Thiết bị có nhiều tài liệu nhất
4. Thiết bị được tra cứu nhiều nhất (nếu có log)
5. Dung lượng kho file (storage/files)
6. Nếu phát hiện bất thường → cảnh báo:
   ⚠️  Device không có tài liệu nào (0 docs)
   ⚠️  File trong storage/ không có record trong DB (orphan)
   ⚠️  DB record có file_path nhưng file không tồn tại
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

1b. Trước khi tạo → kiểm tra tên thiết bị đã tồn tại chưa:
    python cli.py device search --name "..."
    Nếu có kết quả tương tự → hiển thị và hỏi có phải thiết bị này không
    (tránh duplicate do gõ sai chính tả)

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
5. Với mỗi vấn đề tìm thấy → đề xuất lệnh fix:
   - Orphan docs: python cli.py orphans --fix (xóa record không có file)
   - File không có DB record: python cli.py reconcile (tạo record mới)
   - Duplicate: python cli.py dupes --report (chỉ báo cáo, không tự xóa)
6. Hỏi tôi xác nhận từng fix trước khi thực hiện
```

---

## Prompt 10 — Upgrade Gemini Model

```
Cập nhật model Gemini trong toàn bộ codebase:
1. Tìm tất cả chỗ dùng model string (gemini-1.5-flash, gemini-1.5-pro, v.v.)
2. Thay thành: gemini-2.0-flash
3. Chạy test suite:
   python -m pytest tests/test_gemini_classify.py -v
   Nếu chưa có test → tạo test đơn giản với 3 file mẫu:
   1 PDF kỹ thuật, 1 DOCX cấu hình, 1 file không xác định
4. Kiểm tra Gemini API response format có thay đổi không
5. Cập nhật CHANGELOG.md ghi lại thay đổi
```

---

## Prompt 11 — Onboard thiết bị mới từ thư mục

```
Tôi vừa tạo thư mục cho thiết bị mới tại:
storage/files/{category}/{group}/{device-name}/

Thực hiện:
1. Phát hiện thư mục mới chưa có trong DB: python cli.py orphans --type folder
2. Với thư mục mới → scan ngay: python cli.py scan --path "{path}" --dry-run
3. Xác nhận và import
4. Tạo Wiki page ngay lập tức
```

---

## Prompt 12 — Kiểm tra trước khi demo/báo cáo

```
Tôi cần chuẩn bị demo hệ thống. Thực hiện checklist:
1. python cli.py health          → kiểm tra tất cả service (DB, Wiki, Bot)
2. python cli.py stats           → in số liệu tổng quan
3. Mở http://localhost:3000      → xác nhận Wiki hiển thị đúng
4. Test Telegram Bot: gửi /start → xác nhận bot phản hồi
5. Chạy 1 search test: python cli.py search "CT scan"
6. Báo cáo: tất cả ✅ hay có ❌ cần xử lý
```
