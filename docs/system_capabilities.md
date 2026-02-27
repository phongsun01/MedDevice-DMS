# MedDevice DMS — Khả năng Hệ thống (v2.3.0)

> **Cập nhật:** 2026-02-27 | Phản ánh kiến trúc Hybrid Option A & B.

---

## 🤖 1. AI Agents (`agents/`)

| Agent | Nhiệm vụ |
|---|---|
| `scan_agent.py` | Quét cây thư mục, phân loại file theo Prefix/Suffix, ghi vào DB |
| `parse_agent.py` | Trích xuất thông số kỹ thuật từ PDF/Word (Gemini Vision cho file scan) |
| `search_agent.py` | Tìm kiếm ngữ nghĩa và full-text trong SurrealDB |
| `compare_agent.py` | So sánh specs 2 thiết bị, xuất Excel |
| `wiki_agent.py` | Đồng bộ dữ liệu tự động lên Outline Wiki |
| `normalize_agent.py` *(v2.3 — sắp có)* | Nhận tên file thô → trả về tên chuẩn hóa theo convention |

---

## ⚡ 2. Lệnh Telegram Bot

### Option B (Standalone — hiện tại)
| Lệnh / Hành động | Mô tả |
|---|---|
| `/start` | Menu chính |
| `/ask <câu hỏi>` | Chat tự do với AI (có trí nhớ ngắn hạn) |
| `/list` | Duyệt Category > Group > Device |
| `/docs` | Xem tài liệu một thiết bị |
| `/wiki` | Link nhanh Outline Wiki |
| `/add` | Wizard thêm thiết bị mới |

### Option A (Antigravity-Mediated — v2.3)
| Hành động | Mô tả |
|---|---|
| Upload file | AI đề xuất phân loại → Bot hỏi xác nhận → Tự động move + index |
| Nhắn lệnh quản trị | "Quét lại thư mục", "Đồng bộ Wiki", "Báo cáo thiếu hồ sơ" |
| `/switch_mode` | Admin chuyển A/B runtime |

---

## 🛠 3. CLI Commands (`cli.py`)

```bash
python cli.py stats          # Thống kê tổng (Categories/Groups/Devices/Docs)
python cli.py scan           # Quét & nạp dữ liệu từ D:\MedicalData
python cli.py scan --dry-run # Preview, không ghi DB
python cli.py health         # Kiểm tra SurrealDB + Wiki
python cli.py search "<từ>"  # Tìm kiếm
python cli.py missing        # Thiết bị thiếu hồ sơ/báo giá
python cli.py normalize      # Chuẩn hóa tên thư mục + file
python cli.py wiki sync      # Đồng bộ lên Outline Wiki
```

---

## 🖥 4. API Server (`api_server.py`)

| Endpoint | Mô tả |
|---|---|
| `POST /api/chat` | Nhận tin nhắn từ Bot, xử lý bằng Gemini + Memory |
| `POST /api/classify_file` *(v2.3)* | Nhận thông tin file, trả về đề xuất phân loại |
| `POST /api/execute_task` *(v2.3)* | Thực thi lệnh CLI đã được user xác nhận |
