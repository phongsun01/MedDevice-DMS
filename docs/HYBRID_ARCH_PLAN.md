# Kế hoạch Kiến trúc Hybrid — v2.3.0

> **Phiên bản:** v2.3.0 | **Cập nhật:** 2026-02-27

---

## 1. So sánh ba chế độ hoạt động

| | **Option B** *(đang chạy)* | **Option A** *(ưu tiên làm)* | **Option C** *(tương lai)* |
|---|---|---|---|
| **Luồng** | User → Bot → Gemini API → User | User → Bot → **gemini-cli** → CLI Tools → User | User → Bot → **Antigravity IDE** → User |
| **AI xử lý** | Gemini Flash (trả lời chat) | gemini-cli (Agentic, chạy terminal) | Tôi (Antigravity IDE agent) |
| **Thực thi file/DB** | Không | ✅ Có (rename, move, scan DB) | ✅ Có (toàn quyền) |
| **Chạy 24/7** | ✅ Có | ✅ Có (terminal chạy nền) | ❌ Cần IDE mở |
| **Quota** | ~15 RPM free | **60 RPM / 1000 req/ngày** (OAuth) | Quota IDE riêng |
| **Kích hoạt** | `AGENT_MODE=B` | `AGENT_MODE=A` | `AGENT_MODE=C` |

---

## 2. Option A: gemini-cli làm Agentic Worker

### Tại sao gemini-cli phù hợp hơn API key thuần?
- **Quota cao hơn nhiều:** Login OAuth → 60 RPM / 1,000 req/ngày MIỄN PHÍ (so với ~15 RPM của API key free)
- **Agentic loop:** gemini-cli tự quyết định gọi tool (file system, terminal) không cần prompt phức tạp
- **Non-interactive mode:** Bot có thể pipe lệnh thẳng vào gemini-cli, nhận JSON output trở về
- **GEMINI.md context:** Tiêm toàn bộ cấu trúc DMS, naming convention → AI hiểu ngay không cần giải thích

### Luồng Upload File (Option A với gemini-cli)

```
1. User gửi file "arrieta60.pdf" vào Telegram Group
2. Bot nhận file, download về tmp/
3. Bot gọi API Server: POST /api/classify_file {filename}
4. API Server pipe vào gemini-cli:
   echo "Classify file: arrieta60.pdf theo chuẩn MedDevice DMS" | gemini -p @GEMINI.md
   → Output: {device: "arrieta-60", category: "sieu-am", doc_type: "tech", lang: "vi"}
5. Bot hỏi User (Inline Keyboard):
   📁 Đề xuất: tech-arrieta-60-vi.pdf → sieu-am/arrieta-60/
   [✅ Xác nhận] [✏️ Sửa] [❌ Huỷ]
6. User sửa: "đây là hợp đồng"
7. Bot cập nhật: contract-arrieta-60-vi.pdf → sieu-am/arrieta-60/
8. User: ✅ Xác nhận
9. API Server thực thi:
   - Rename + Move file
   - python cli.py scan --path "sieu-am/arrieta-60/"
   - Ghi SurrealDB
10. Bot: "✅ Đã phân loại và nạp vào hệ thống!"
```

**Tiết kiệm Quota:** gemini-cli chỉ gọi 1 lần tại bước 4. Toàn bộ vòng sửa-xác nhận là pure Python.

### Setup gemini-cli cho Option A

```bash
# Đăng nhập OAuth (60 RPM / 1000 req/ngày miễn phí)
gemini auth login

# Tạo GEMINI.md (context file cho dự án)
# → Tiêm naming convention, cấu trúc thư mục, danh sách Category/Group

# Test non-interactive mode
echo "Classify file: somatom-datasheet.pdf" | gemini --output-format json
```

---

## 3. Option C: Antigravity IDE trực tiếp xử lý

### Cơ chế hoạt động
Option C là khi **bạn đang ngồi làm việc** và muốn Bot Telegram kết nối thẳng với tôi (Antigravity đang chạy trong IDE) để tôi trực tiếp phân tích và ra quyết định.

```
User nhắn Bot: "Phân loại file arrieta60.pdf"
  ↓
Bot ghi yêu cầu vào "inbox queue" (file JSON hoặc SQLite)
  ↓
Antigravity IDE (tôi) đọc queue → phân tích → thực thi
  ↓
Tôi ghi kết quả vào "outbox queue"
  ↓
Bot đọc outbox → gửi trả lời cho User
```

### Khác Option A ở điểm nào?
- Option A: gemini-cli chạy **tự động theo lệnh cứng**, không cần tôi ngồi xem.
- Option C: **Tôi ngồi review và quyết định** — phù hợp cho tác vụ phức tạp cần suy xét nhiều hơn (vd: tái cơ cấu toàn bộ thư mục, phân tích bất thường).

### Giới hạn thực tế
⚠️ **Option C chỉ hoạt động khi IDE đang mở.** Không phù hợp cho 24/7 production, nhưng rất phù hợp cho Admin sessions (sáng bật IDE lên, xử lý batch, chiều tắt).

---

## 4. Lộ trình triển khai (v2.3.0)

### Ưu tiên 1: Option A với gemini-cli

| Bước | Công việc | File |
|---|---|---|
| 1 | Tạo `GEMINI.md` — context file DMS cho gemini-cli | `GEMINI.md` |
| 2 | Viết `agents/normalize_agent.py` (naming logic) | `agents/normalize_agent.py` |
| 3 | Thêm `/api/classify_file` endpoint (gọi gemini-cli) | `api_server.py` |
| 4 | Thêm `/api/execute_task` endpoint (chạy CLI tools) | `api_server.py` |
| 5 | Nâng cấp `bot/handlers/files.py` với Inline Keyboard | `bot/handlers/files.py` |
| 6 | Thêm `AGENT_MODE` vào config + `/switch_mode` lệnh | `config.py` |
| 7 | Test end-to-end | `tests/test_file_classify.py` |

### Ưu tiên 2: Option C (Queue Bridge)
*(Tiếp theo sau khi Option A hoàn thành)*

| Bước | Công việc | File |
|---|---|---|
| 1 | Viết `core/queue.py` — đọc/ghi inbox/outbox | `core/queue.py` |
| 2 | Thêm `/api/chat_to_ide` endpoint trong API Server | `api_server.py` |
| 3 | Bot polling queue outbox mỗi 5s và gửi trả lời | `bot/handlers/relay.py` |

---

## 5. Quyết định đã chốt

| Câu hỏi | Quyết định |
|---|---|
| Option A dùng AI gì? | **gemini-cli** (OAuth, 60 RPM free) — không phải API key |
| Thực thi lệnh | Import trực tiếp CLI functions — không cần Queue |
| Quota | gemini-cli gọi 1 lần/upload |
| Option C runtime | Queue file (inbox/outbox pattern) |
| Thứ tự ưu tiên | **A trước → C sau** |
