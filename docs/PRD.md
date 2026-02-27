# PRD v2.0 — MedDevice DMS (Antigravity-First Architecture)

> **Phiên bản:** 2.0 | **Cập nhật:** 2026-02-24  
> **Tầm nhìn:** Antigravity IDE là trung tâm quản lý tài liệu. Bot/Wiki là kênh phụ.

---

## 1. Tầm nhìn sản phẩm

### 1.1 Vấn đề cần giải quyết
Tổ chức y tế lưu trữ hàng trăm tài liệu thiết bị trong thư mục tùy tiện, không có cấu trúc, không thể tìm kiếm thông minh. Tra cứu thủ công, so sánh thiết bị tốn nhiều thời gian.

### 1.2 Giải pháp
**MedDevice DMS** biến thư mục file hỗn độn thành kho tri thức có cấu trúc, tìm kiếm được bằng ngôn ngữ tự nhiên — thông qua 2 lớp:

| Lớp | Công cụ | Người dùng |
|---|---|---|
| **Quản lý** | Antigravity IDE + CLI | Quản lý hệ thống |
| **Tra cứu** | Telegram Bot + Outline Wiki | Nhân viên, lãnh đạo |

---

## 2. Cấu trúc dữ liệu

### 2.1 Phân cấp
```
Category → Group → Device → Documents
```

### 2.2 Cấu trúc thư mục chuẩn (Refactored - v2.1)

```
STORAGE_BASE_PATH (D:\MedicalData)
├── thiet-bi-chan-doan-hinh-anh/       # Category (kebab-case)
│   ├── ct-scan/                        # Group
│   │   ├── somatom-go-now/            # Device
│   │   │   ├── tech-datasheet-vi.pdf   # File phẳng với Prefix/Suffix
│   │   │   ├── config-bidding-en.xlsx
│   │   │   └── archive/                # Tài liệu chưa phân loại
```

### 2.3 Phân nhóm Device đề xuất — "thiet-bi-chan-doan-hinh-anh"

| Group | Device |
|---|---|
| `ct-scan` | Somatom Go Now, CT 128 Somatom Go Top, He thong CT dem photon |
| `sieu-am` | Arietta 50, Sieu am ACUSON Juniper, Sieu am Acuson Maple, Sieu am ACUSON Redwood, Sieu am ACUSON Sequoia Select, Sieu am arietta 750v, Sieu am Resona I9 Exp |
| `c-arm` | C-Arm Siemens Cios Fit, C-Arm Siemens Cios Select |
| `dsa` | DSA Azurion 7B20, DSA siemens |
| `mri` | MRI Siemens 0.55 |
| `x-quang` | X Quang Examion, X quang FDR 68S |

### 2.4 Naming Convention & Classification (v2.1)

Hệ thống sử dụng Tiền tố (Prefix) và Hậu tố (Suffix) để phân loại tài liệu thay vì thư mục con.

**Prefix (Tiền tố):**
- `tech-`: Tài liệu kỹ thuật (Technical)
- `config-`: Tài liệu cấu hình (Configuration)
- `price-`: Tài liệu giá (Price)
- `contract-`: Hợp đồng tương tự (Contract)
- `other-`: Các loại khác

**Suffix (Hậu tố):**
- `-vi`: Tiếng Việt
- `-en`: Tiếng Anh
- `-bidding`: Hồ sơ thầu
- `-compliance`: Bảng đáp ứng
- `-quotation`: Báo giá
- `-comparison`: Bảng so sánh

**Ví dụ:** `tech-manual-vi.pdf`, `config-bidding-en.xlsx`

### 2.5 Dedup Policy (đã xác nhận)

Khi có cả `.doc` lẫn `.pdf` cùng nội dung:
- **Giữ cả 2** trong cùng thư mục
- Trong DB: file PDF có `is_primary=true`, file DOC có `is_primary=false`
- Trường hợp file ZIP: giải nén → phân loại từng file bên trong → lưu vào `other/archive/` gốc

---

## 3. Module Requirements (v2.0)

### Prerequisite — Normalize (TRƯỚC KHI SCAN)

**P0: Normalize folder & Auto-Grouping** (chạy 1 lần duy nhất trước khi import):
- `python cli.py normalize --dry-run` → preview kế hoạch đổi tên và phân nhóm
- `python cli.py normalize` → thực hiện chuỗi hành động:
  1. Đổi tên folder sang định dạng `kebab-case`.
  2. Xóa bỏ các cấp độ thư mục thừa như `chung` hoặc `other-group`.
  3. Tự động nhận diện Group dựa trên tiền tố của thiết bị (VD: `sieu-am-acuson` → đưa vào group `sieu-am`).
  4. Gom toàn bộ file kỹ thuật, cấu hình, hợp đồng lên ngang hàng trong thư mục Device.

---

### Module A — File Scanner & Classifier (Antigravity Core)

- **A0:** Normalize folder names & groupings — see Prerequisite
- **A1:** Quét cây thư mục `storage/files` theo cấu trúc `cat/group/device/type/`
- **A2:** Đọc nội dung file (PDF → PyMuPDF, DOCX → python-docx, XLSX → openpyxl)
- **A3:** Phân loại `doc_type`, `sub_type` từ tên file + nội dung (Gemini 2.0 Flash)
- **A4:** Ghi vào SurrealDB — field `is_primary=true` cho PDF khi có cả hai định dạng
- **A5:** Tạo/cập nhật trang Wiki trên Outline
- **A6:** Output report: số file xử lý, lỗi, file không xác định

---

### Module B — CLI Interface

```bash
python cli.py stats                             # Thống kê tổng quan
python cli.py normalize [--dry-run]            # Rename folder sang kebab-case
python cli.py merge-dupes [--dry-run]          # Gộp folder trùng lặp
python cli.py scan [--dry-run] [--path]        # Quét và import file
python cli.py search "từ khóa" [--json]        # Tìm kiếm full-text
python cli.py device "tên"                     # Thông tin 1 thiết bị
python cli.py missing [--group] [--doc-type]   # Thiết bị thiếu tài liệu
python cli.py compare "A" "B" [--export xlsx]  # So sánh 2 thiết bị
python cli.py wiki sync [--device]             # Đẩy lên Outline Wiki
python cli.py health                           # Kiểm tra kết nối
python cli.py classify --file <path>           # Phân loại 1 file cụ thể
```

---

### Module C — Search Engine (giữ nguyên từ v1)

- Full-text BM25 trên `content_text` (SurrealDB native)
- Filter: category, group, device, doc_type
- Highlight đoạn text match

---

### Module D — Telegram Bot (Antigravity Relay)

- **Trạm trung chuyển (Dumb Client):** Trở thành Webhook Relay đẩy toàn bộ tin nhắn đa phương tiện (Tin nhắn text tự do, Upload file) lên mạng lưới Antigravity API (Headless Agent).
- **Zero Hardcoding:** Xóa bỏ hoàn toàn các cấu trúc lệnh cũ (`/search`, `/compare`, FSM rắc rối).
- **Luồng xử lý mới:** User chat tự do → Bot đẩy JSON lên Antigravity API → Antigravity tự quyết định gọi Tools (quét file, đọc PDF, query DB) → Antigravity trả Markdown/File cho Bot → Bot gửi cho User.

---

### Module E — Outline Wiki

- Collection theo Category
- Trang riêng cho mỗi Device (có Group breadcrumb)
- Auto-update khi DB thay đổi

---

## 4. Use Cases (v2.0)

### UC-00: Normalize thư mục lần đầu (NEW)
1. Antigravity thực thi: `python cli.py normalize --dry-run`
2. Đọc output, xác nhận với người dùng
3. Chạy thật: `python cli.py normalize`
4. Tạo Group folder theo bảng 2.3
5. Chạy: `python cli.py scan`

### UC-01: Antigravity phân loại thư mục file cũ
1. Nói với Antigravity: *"Phân loại thư mục `storage/files` và nạp vào hệ thống"*
2. Antigravity chạy `python cli.py scan --dry-run` → báo cáo preview
3. Xác nhận → `python cli.py scan` → `python cli.py wiki sync`

### UC-02: Truy vấn bằng ngôn ngữ tự nhiên
1. *"Liệt kê thiết bị nhóm CT-Scan chưa có báo giá"*
2. `python cli.py missing --group "ct-scan" --doc-type price`

### UC-03 → UC-06: Giữ nguyên từ v1 (browse, search, compare, wiki)

---

## 5. Kiến trúc kỹ thuật (v2.0 - Antigravity First)

```text
┌──────────────── QUẢN LÝ & XỬ LÝ (Antigravity Core) ──────────────┐
│  Headless Antigravity Agent (API) ◀┐                             │
│       ├── Bộ Tools (list_dir, python, read_pdf,...)  │           │
│       ├── Logic Agents (scan, parse, search, compare)│           │
│       └── storage/files/ & SurrealDB                 │           │
└────────────────────────────────────┴─────────────────────────────┘
                                     │ (JSON request/response)
┌──────────────── GIAO TIẾP (Bot & Wiki) ──────────────────────────┐
│  Telegram Bot (Webhook Relay) ─────┘                             │
│   - Nhận tin nhắn tự do, đẩy lên AI                              │
│  Outline Wiki (Read-only knowledge base)                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Database | SurrealDB 3.0+ |
| AI/LLM | Google Gemini 2.0 Flash |
| CLI | Python argparse + rich |
| Bot | aiogram 3.x |
| Wiki | Outline.dev (Docker) |
| PDF | PyMuPDF |
| Excel | openpyxl |
| Normalize | unidecode |
| Logging | structlog |

---

## 7. Roadmap

| Phase | Scope | Trạng thái |
|---|---|---|
| **Phase 0** | Normalize folder + merge dupes + thêm Group | 🔲 Tiếp theo |
| **Phase 1** | DB Schema + Docker + Bot cơ bản | ✅ Hoàn thành |
| **Phase 2** | CLI (`cli.py`) + Scan Agent nâng cấp | 🔲 Kế tiếp |
| **Phase 3** | Gemini 2.0 + Phân loại thông minh | 🔲 Phase sau |
| **Phase 4** | Compare Agent + XLSX export | 🔲 Phase sau |
| **Phase 5** | Semantic search + RAG | 🔲 Tương lai |

---

## 8. Rủi ro & Lưu ý

- **Folder trùng lặp:** Đang có 12 cặp (`Thiet bi...` + `thiet_bi_...`) — cần merge trước khi scan.
- **File trùng định dạng:** Giữ cả .doc lẫn .pdf, đánh dấu `is_primary` trong metadata.
- **File ZIP (`IB Download.zip`):** Cần giải nén thủ công → phân loại → đưa vào đúng thư mục.
- **Nhiều file IB:** `bid_code` lưu sau (Phase 3+). Tạm thời tên file gốc đã chứa mã IB.
- **PDF không có text layer:** Cần OCR (Gemini Vision fallback) — Phase 3.
- **PC luôn bật:** Bot polling cần máy tính online. Có thể deploy VPS sau.

---

## 9. Constraints (Prerequisite bắt buộc)

> [!IMPORTANT]
> Bước normalize + thêm Group folder phải hoàn tất TRƯỚC khi chạy `python cli.py scan`.  
> Ước tính: ~16 device ở "thiet-bi-chan-doan-hinh-anh", ~10-15 file/device → ~200 file cần phân loại cho 1 category.
