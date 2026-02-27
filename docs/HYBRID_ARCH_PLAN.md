# Kế hoạch Kiến trúc Hybrid: Option A (Antigravity-Mediated) — v2.3.0

> **Phiên bản:** v2.3.0 | **Cập nhật:** 2026-02-27  
> **Mục tiêu:** Biến Bot Telegram thành giao diện quản trị thực sự — người dùng gửi file, nhận đề xuất phân loại từ AI, xác nhận, và hệ thống tự động xử lý.

---

## 1. Hai chế độ hoạt động (A vs B)

| | **Option B** (hiện tại — v2.2.0) | **Option A** (mục tiêu — v2.3.0) |
|---|---|---|
| **Luồng** | User → Bot → Gemini API → Bot → User | User → Bot → API Server → [AI Classify + CLI Execute] → Bot → User |
| **AI tham gia** | Chỉ trả lời chat | Ra quyết định + thực thi lệnh CLI thật |
| **Tác động hệ thống** | Không đổi file | Di chuyển file, cập nhật DB, đổi tên |
| **Quota** | Mỗi tin nhắn = 1 API call | Mỗi lần upload file = 1 API call duy nhất |
| **Kích hoạt** | `AGENT_MODE=B` trong `.env` | `AGENT_MODE=A` trong `.env` |

---

## 2. Use Case cốt lõi: Upload File → Phân loại có xác nhận

### Luồng đầy đủ (Option A)

```
1. User gửi file "arrieta60.pdf" vào Group Telegram
2. Bot nhận file → download về tmp/
3. Bot gọi api_server: POST /api/classify_file {filename, size, ...}
4. API Server gọi Gemini 1 lần: "Phân loại file này theo chuẩn DMS"
   → Gemini trả về: {device: "arrieta-60", category: "sieu-am", doc_type: "tech", lang: "vi"}
5. Bot hỏi lại User (Inline Keyboard):
   ┌────────────────────────────────────────┐
   │ 📁 Đề xuất phân loại:                 │
   │ Tên file: tech-arrieta-60-vi.pdf       │
   │ Thư mục: sieu-am/arrieta-60/           │
   │                                        │
   │  ✅ Xác nhận  │  ✏️ Sửa  │  ❌ Huỷ  │
   └────────────────────────────────────────┘
6. User nhắn: "đây là hợp đồng"
7. Bot cập nhật: {doc_type: "contract"} → tên mới: contract-arrieta-60-vi.pdf
8. Bot hỏi xác nhận lần 2
9. User: ✅ Xác nhận
10. Worker thực thi:
    - Rename file
    - Move vào D:\MedicalData\sieu-am\arrieta-60\
    - Chạy scan_agent → ghi vào SurrealDB
11. Bot phản hồi: "✅ Đã phân loại và nạp vào hệ thống!"
```

**Lưu ý quan trọng về quota:** Gemini chỉ được gọi đúng 1 lần tại bước 4. Toàn bộ vòng hỏi-sửa-xác nhận là pure Python, không tốn thêm API call.

---

## 3. Các thay đổi kỹ thuật cần thực hiện

### 3.1 API Server (`api_server.py`)
- Thêm endpoint: `POST /api/classify_file` — nhận tên file, gọi Gemini, trả về JSON đề xuất.
- Thêm endpoint: `POST /api/execute_task` — nhận lệnh đã được user xác nhận, gọi CLI Worker để rename+move+scan.

### 3.2 Bot Handlers (`bot/handlers/files.py`)
- Nâng cấp handler nhận file: thay vì chỉ download, sẽ gọi `/api/classify_file` và tạo Inline Keyboard xác nhận.
- Xử lý callback khi user sửa tên file / chọn doc_type khác.
- Khi xác nhận xong: gọi `/api/execute_task`.

### 3.3 CLI Worker (`cli.py` → expose as module)
- Chuyển `cmd_scan`, `cmd_normalize` thành pure Python async function (không phụ thuộc argparse) để API Server có thể import và gọi trực tiếp.

### 3.4 Config (`config.py`)
- Thêm biến `AGENT_MODE: str = "B"` — mặc định là Option B.
- Thêm biến `/switch_mode` trong Telegram: Admin có thể chuyển A/B runtime.

### 3.5 Naming Logic (`agents/normalize_agent.py`) — [NEW]
- Module mới: nhận `{filename, doc_type, lang, device}` → trả về tên file chuẩn hóa theo convention `{prefix}-{device-slug}-{lang}.{ext}`.

---

## 4. Lộ trình triển khai (v2.3.0)

| Bước | Công việc | File liên quan |
|---|---|---|
| 1 | Refactor CLI functions thành importable module | `cli.py` |
| 2 | Viết `normalize_agent.py` (naming logic) | `agents/normalize_agent.py` |
| 3 | Thêm `/api/classify_file` endpoint | `api_server.py` |
| 4 | Thêm `/api/execute_task` endpoint | `api_server.py` |
| 5 | Nâng cấp `bot/handlers/files.py` với Inline KB | `bot/handlers/files.py` |
| 6 | Thêm `AGENT_MODE` vào config + `/switch_mode` | `config.py`, `bot/handlers/relay.py` |
| 7 | Test end-to-end: upload → classify → confirm → execute | `tests/test_file_classify.py` |

---

## 5. Câu hỏi đã clarify

| Câu hỏi | Quyết định |
|---|---|
| Bridge type | **A1 (Subprocess/Import)** — Worker chạy ngay trong API Server, không cần Queue |
| Runtime của Agent | **Worker Python 24/7** do bạn chạy; IDE Antigravity lập trình hành vi |
| Tính năng đầu tiên | **Upload file → Chat điều phối → Bot xác nhận** |
| Quota | Gemini chỉ gọi 1 lần/upload — tiết kiệm tối đa |
