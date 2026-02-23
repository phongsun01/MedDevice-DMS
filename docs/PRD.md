# PRD – Hệ thống Quản lý Hồ sơ Thiết bị Y tế (MedDevice DMS)

***

## 1. Overview

**Tên sản phẩm:** MedDevice DMS
**Mục tiêu:** Hệ thống quản lý toàn bộ hồ sơ, tài liệu thiết bị y tế theo cấu trúc phân cấp, hỗ trợ tìm kiếm AI, so sánh tự động, wiki tổng quát, giao tiếp từ xa qua Telegram.
**Nền tảng:** Antigravity IDE (agents/runtime) + SurrealDB (database) + Telegram Bot (remote UI) + Foam/Dendron (wiki) + File Storage (local hoặc Google Drive/S3).

***

## 2. Yêu cầu nghiệp vụ

### 2.1 Cấu trúc phân cấp dữ liệu
```
Category
  └── Group
        └── Device
              ├── Thông tin chung
              ├── Tài liệu kỹ thuật
              ├── Bản cấu hình
              ├── Đường link liên quan
              ├── Tài liệu giá
              ├── Hợp đồng tương tự
              ├── Bản so sánh
              └── Tài liệu khác
```
Ví dụ: **Category** "Thiết bị chẩn đoán hình ảnh" → **Group** "X-quang" → **Device** "Máy X-quang CR XYZ". SurrealDB hỗ trợ cấu trúc này natively qua graph relations và nested documents. [linode](https://www.linode.com/docs/guides/surrealdb-interdocument-modeling/)

### 2.2 Cấu trúc tài liệu của mỗi Device

| Nhóm tài liệu | Nội dung | Định dạng | Ghi chú |
|---|---|---|---|
| **Thông tin chung** | Model, hãng, xuất xứ, năm SX | Fields trực tiếp | Text fields |
| **Tài liệu kỹ thuật** | Specs, hướng dẫn | PDF | Phân biệt EN/VN |
| **Bản cấu hình** | Quảng cáo, cơ bản, chào giá, mời thầu, đáp ứng | DOC/XLSX | Nhiều version |
| **Đường link** | Trang chủ, FDA, CE, chứng chỉ | URL | Metadata type |
| **Tài liệu giá** | Báo giá, kết quả trúng thầu | DOC/PDF/Link | |
| **Hợp đồng tương tự** | PDF | PDF | File lớn → chunked |
| **Bản so sánh** | So sánh vs hãng khác | DOC/XLSX | |
| **Tài liệu khác** | Phụ kiện, misc | Any | |

***

## 3. SurrealDB Schema Design

SurrealDB cho phép kết hợp SCHEMAFULL và SCHEMALESS linh hoạt cho bài toán này. [dev](https://dev.to/sebastian_wessel/how-to-design-a-surrealdb-schema-and-create-a-basic-client-for-typescript-o6o)

```sql
-- Hierarchy tables
DEFINE TABLE category SCHEMAFULL;
DEFINE FIELD name ON category TYPE string;
DEFINE FIELD description ON category TYPE option<string>;

DEFINE TABLE device_group SCHEMAFULL;
DEFINE FIELD name ON device_group TYPE string;
DEFINE FIELD category ON device_group TYPE record<category>;

-- Main device table
DEFINE TABLE device SCHEMAFULL;
DEFINE FIELD name ON device TYPE string;
DEFINE FIELD model ON device TYPE string;
DEFINE FIELD brand ON device TYPE string;
DEFINE FIELD origin ON device TYPE string;
DEFINE FIELD group ON device TYPE record<device_group>;

-- Documents table (polymorphic)
DEFINE TABLE document SCHEMAFULL;
DEFINE FIELD device ON document TYPE record<device>;
DEFINE FIELD doc_type ON document TYPE string; -- 'technical','config','price',...
DEFINE FIELD sub_type ON document TYPE option<string>; -- 'VI','EN','quotation',...
DEFINE FIELD file_path ON document TYPE option<string>;
DEFINE FIELD file_url ON document TYPE option<string>;
DEFINE FIELD content_text ON document TYPE option<string>; -- extracted text
DEFINE FIELD metadata ON document FLEXIBLE TYPE object;

-- Full-text search indexes
DEFINE ANALYZER vn_analyzer TOKENIZERS class, blank
  FILTERS lowercase, ascii;
DEFINE INDEX doc_content_idx ON document
  FIELDS content_text FULLTEXT ANALYZER vn_analyzer BM25 HIGHLIGHTS;
DEFINE INDEX doc_name_idx ON document
  FIELDS metadata.title FULLTEXT ANALYZER vn_analyzer BM25 HIGHLIGHTS;
```


***

## 4. Module Requirements

### Module A – Core Data Manager (Antigravity Agent)
**Nhiệm vụ:** Toàn bộ CRUD cho device, group, category, document.

**Requirements:**
- A1: Tạo/sửa/xóa Category, Group, Device
- A2: Upload file → lưu vào local storage/Drive → lưu path vào SurrealDB `document` record
- A3: Tự động extract text từ PDF bằng PDF-parser/Gemini → lưu vào field `content_text` để search
- A4: Classify loại tài liệu khi upload (agent nhận diện tên file/nội dung → gán `doc_type`, `sub_type`)
- A5: Validate file format theo từng nhóm (config chỉ nhận DOC/XLSX, technical chỉ PDF)

**Tasks:**
- [ ] Setup SurrealDB schema (script migration)
- [ ] Viết CRUD functions bằng Rust/Python SDK
- [ ] Tích hợp PDF text extraction (PyMuPDF hoặc Gemini File API)
- [ ] Agent classify tài liệu tự động (Gemini prompt + rules-based fallback)
- [ ] File storage abstraction (local FS trước, S3 sau)

***

### Module B – Search Agent (Tìm kiếm tài liệu)
**Nhiệm vụ:** Tìm kiếm full-text + semantic trong tài liệu thiết bị.

**Requirements:**
- B1: Tìm theo từ khoá trong toàn bộ nội dung tài liệu (full-text BM25)
- B2: Tìm theo device name, model, hãng
- B3: Filter theo: category / group / doc_type / sub_type / brand
- B4: Trả về kết quả có **highlight** đoạn text match
- B5: Semantic search (tuỳ chọn Phase 2) dùng vector embeddings

**SurrealQL mẫu:** [surrealdb](https://surrealdb.com/docs/surrealdb/models/full-text-search)
```sql
SELECT *, search::highlight('<b>', '</b>', 1)
  AS highlight
FROM document
WHERE content_text @@ 'liều lượng bức xạ'
  AND device.group.category.name = 'Thiết bị chẩn đoán hình ảnh';
```

**Tasks:**
- [ ] Định nghĩa FULLTEXT indexes trên SurrealDB
- [ ] Search agent nhận input từ Telegram → query SurrealDB → format kết quả
- [ ] Implement filter pipeline (category → group → device → doc_type)
- [ ] Format kết quả trả về Telegram (text + file path link)

***

### Module C – Compare Agent (So sánh thiết bị)
**Nhiệm vụ:** So sánh 2 thiết bị từ tài liệu có sẵn.

**Requirements:**
- C1: User chọn 2 device → agent extract specs từ tài liệu kỹ thuật
- C2: Agent tạo bảng so sánh structured (tên spec, giá trị A, giá trị B)
- C3: Ưu tiên dùng file "Bản so sánh" có sẵn nếu tồn tại
- C4: Nếu không có file so sánh → Gemini extract từ technical docs
- C5: Output: Markdown table gửi về Telegram hoặc export XLSX

**Tasks:**
- [ ] Compare agent: query 2 device records + documents
- [ ] Gemini prompt: "Extract thông số kỹ thuật từ đoạn text sau thành JSON"
- [ ] Merge và diff 2 JSON specs → render table
- [ ] Export XLSX qua openpyxl, gửi file về Telegram

***

### Module D – Telegram Bot (Remote Interface)
**Nhiệm vụ:** Cầu nối duy nhất giữa user và hệ thống khi không ở máy tính.

**Requirements:**
- D1: Nhận file upload → trigger Module A (parse & store)
- D2: Xử lý lệnh tìm kiếm: `/search [từ khoá]`
- D3: Xử lý lệnh so sánh: `/compare [device A] [device B]`
- D4: Browse theo cây: `/list categories` → `/list groups [cat]` → `/list devices [group]`
- D5: Xem danh sách tài liệu: `/docs [device_name]`
- D6: Tải file: `/get [doc_id]` → bot gửi file về chat
- D7: Điều khiển Antigravity IDE từ xa: `/run [prompt]` → agent thực thi, gửi ảnh kết quả

**Command map:**
```
/start          - Menu chính
/search <query> - Tìm kiếm toàn bộ
/list           - Duyệt cây category
/docs <device>  - Xem hồ sơ thiết bị
/compare A B    - So sánh 2 thiết bị
/get <id>       - Tải file
/add            - Upload tài liệu mới (gửi file kèm)
/run <prompt>   - Điều khiển IDE từ xa
/wiki           - Link tới trang wiki
```

**Tasks:**
- [ ] Setup python-telegram-bot hoặc aiogram
- [ ] Webhook server local + ngrok expose
- [ ] Implement command handlers (mỗi lệnh = 1 handler function)
- [ ] File download: bot forward file về Telegram chat
- [ ] Remote IDE control: inject prompt + screenshot (Ricochet/pyautogui) [reddit](https://www.reddit.com/r/google_antigravity/comments/1q31qxa/made_a_tool_to_control_my_ide_from_telegram/)

***

### Module E – Wiki Page
**Nhiệm vụ:** Trang tổng quát dạng wiki, tự cập nhật từ DB.

**Requirements:**
- E1: Trang index theo Category → Group → Device (dạng outline/tree)
- E2: Mỗi device có trang riêng: thông tin chung + danh sách tài liệu dạng link
- E3: Auto-regenerate khi có thay đổi trong DB
- E4: Có graph view (như Lark wiki)
- E5: Search trong wiki

**Lựa chọn tool:** [youtube](https://www.youtube.com/watch?v=P2lcCvt2RYw)

| Option | Ưu | Nhược |
|---|---|---|
| **Foam (VSCode ext)** | Built-in Antigravity, graph view | Manual tạo file MD |
| **Obsidian** | Graph đẹp, search tốt | Tách biệt IDE |
| **MkDocs + Material** | Web public, đẹp | Không có graph |
| **Outline.dev (self-host)** | Gần giống Lark nhất | Cần Docker |

**Khuyến nghị:** Dùng **Outline.dev** self-hosted (Docker) cho giao diện gần Larksuite nhất, agents tự-generate/update pages qua Outline API khi DB thay đổi.

**Tasks:**
- [ ] Deploy Outline.dev bằng Docker Compose
- [ ] Agent generate Markdown pages cho mỗi device khi create/update
- [ ] POST lên Outline API tự động
- [ ] Link Outline URL vào Telegram bot response (`/wiki device_name`)

***

## 5. Use Cases

### UC-01: Thêm thiết bị mới
1. User gửi `/add` lên Telegram
2. Bot hỏi: tên device, group, category
3. User trả lời từng bước (conversation flow)
4. Agent tạo record trong SurrealDB
5. Bot xác nhận + tạo wiki page tự động

### UC-02: Upload tài liệu kỹ thuật
1. User gửi file PDF trực tiếp lên Telegram chat, kèm caption: `ky_thuat|máy X-quang CR|EN`
2. Bot parse caption → xác định device + doc_type + sub_type
3. Agent download file → lưu storage → extract text PDF → index SurrealDB
4. Bot confirm: "✅ Đã lưu tài liệu kỹ thuật (EN) cho máy X-quang CR"

### UC-03: Tìm kiếm thông số
1. User: `/search liều lượng bức xạ tối đa CR`
2. Search agent query SurrealDB full-text với BM25
3. Trả về top 5 kết quả với highlight text + tên device + tên file
4. User chọn → `/get doc_id` để tải file gốc

### UC-04: So sánh 2 thiết bị
1. User: `/compare "Máy X-quang CR Alpha" "Máy X-quang CR Beta"`
2. Agent kiểm tra file so sánh có sẵn → nếu có, dùng file đó
3. Nếu không có → Gemini extract specs từ technical docs của cả 2
4. Trả về bảng Markdown trong Telegram + file XLSX đính kèm

### UC-05: Duyệt hồ sơ từ xa
1. User: `/list` → chọn category "Thiết bị chẩn đoán hình ảnh"
2. → `/list groups TBCDHA` → chọn "X-quang"
3. → `/list devices xquang` → chọn device
4. → `/docs "Máy X-quang CR Alpha"` → xem danh sách 8 nhóm tài liệu + status (có/chưa có)

### UC-06: Xem Wiki
1. User: `/wiki "Máy X-quang CR Alpha"`
2. Bot trả link Outline.dev: `http://yourserver/doc/may-xquang-cr-alpha`
3. User mở trên điện thoại, xem trang đầy đủ

***

## 6. Technical Architecture

```
[Telegram App (điện thoại)]
          │  HTTPS
          ▼
[Telegram Bot Server - Python]
          │
    ┌─────┴──────┐
    │            │
    ▼            ▼
[File Storage]  [Antigravity Agents]
 Local/S3        ├── Parse Agent (PDF→text)
                 ├── Search Agent
                 ├── Compare Agent
                 └── Wiki Agent
                          │
                          ▼
                    [SurrealDB]
                    (Document+Graph
                     Full-text index)
                          │
                          ▼
                   [Outline.dev Wiki]
                   (auto-updated pages)
```

***

## 7. Phase Roadmap

| Phase | Scope | Mục tiêu |
|---|---|---|
| **Phase 1** | Schema + CRUD + Telegram basic | Lưu & duyệt hồ sơ qua Telegram  [surrealdb](https://surrealdb.com/docs/surrealdb/models/document) |
| **Phase 2** | PDF extraction + Full-text search | Tìm kiếm trong tài liệu  [surrealdb](https://surrealdb.com/blog/create-a-search-engine-with-surrealdb-full-text-search) |
| **Phase 3** | Compare agent + XLSX export | So sánh thiết bị tự động  [theverge](https://www.theverge.com/news/822833/google-antigravity-ide-coding-agent-gemini-3-pro) |
| **Phase 4** | Outline wiki + auto-generate | Wiki tổng quát  [youtube](https://www.youtube.com/watch?v=P2lcCvt2RYw) |
| **Phase 5** | Remote IDE control + semantic search | Điều khiển Antigravity từ xa  [reddit](https://www.reddit.com/r/google_antigravity/comments/1qhocbz/presenting_antigravity_remote_work_from_literally/) |

***

## 8. Rủi ro & Lưu ý

- **File lớn (hợp đồng):** Telegram giới hạn 50MB/file → cần lưu storage, chỉ gửi link qua bot. [reddit](https://www.reddit.com/r/google_antigravity/comments/1q31qxa/made_a_tool_to_control_my_ide_from_telegram/)
- **PDF tiếng Việt:** Cần cấu hình tokenizer phù hợp (dùng `blank` + `class` filter) trong SurrealDB analyzer. [surrealdb](https://surrealdb.com/docs/surrealdb/models/full-text-search)
- **Bảo mật:** SurrealDB hỗ trợ row-level permissions → giới hạn ai được xem tài liệu nào. [antigravityide](https://www.antigravityide.app/features)
- **PC luôn bật:** Toàn bộ hệ thống chạy local → cần PC ổn định + ngrok/Cloudflare Tunnel để expose webhook Telegram. [reddit](https://www.reddit.com/r/google_antigravity/comments/1qhocbz/presenting_antigravity_remote_work_from_literally/)
