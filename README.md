# MedDevice DMS — Hệ thống Quản lý Tài liệu Thiết bị Y tế (v2.2.0)

> Tầm nhìn: Biến thư mục file lưu trữ tuỳ tiện và hỗn độn thành kho tri thức có cấu trúc (Knowledge Base) thông qua Antigravity IDE Agents. Người dùng cuối có thể chat bằng ngôn ngữ tự nhiên để tìm kiếm thay vì mở từng file thủ công.

---

## Tính năng chính
- **Tự động quét và chuẩn hoá:** Tự sửa tên file, quét toàn bộ cây thư mục `storage/files/` và gán thể loại thông minh.
- **Rút trích thông số bằng AI (Gemini 2.0 Flash):** Tự động đọc PDF kỹ thuật, rút trích 40+ thông số cấu hình phần cứng.
- **Tra cứu Vector & Full-text:** Tìm thiết bị theo tính năng ("Máy chụp CT có AI giảm liều tia") bằng CSDL Graph SurrealDB.
- **So sánh & Báo cáo:** Tự động so sánh hai dòng máy và xuất báo cáo chênh lệch ra file Excel định dạng đẹp.
- **Bot Telegram & Context Memory:** Chatbot Telegram có trí nhớ ngắn hạn. Hiểu đại từ nhân xưng và tự tiếp nối câu chuyện, tự định tuyến gọi tool.
- **Đồng bộ Wiki:** Đẩy toàn bộ thông số lên trang văn bản nội bộ Outline.dev.
- **Wiki (Outline)**: Trang Wiki tự động cập nhật từ cơ sở dữ liệu.
- **Bulk Import**: Nạp hàng loạt từ thư mục local bằng `import_local.py`.
- **Audit Log**: Ghi nhật ký toàn bộ thao tác.

## 🛠 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Database | SurrealDB 3.0.0 |
| AI/LLM | Google Gemini 1.5 |
| Bot | aiogram 3.x |
| Wiki | Outline.dev (self-hosted) |
| Logging | structlog |
| Deploy | Docker Compose |

## 📂 Cấu trúc thư mục

```
meddevice-dms/
├── main.py              # Entry point Bot
├── import_local.py      # Nạp dữ liệu hàng loạt
├── config.py            # Cấu hình hệ thống
├── setup.bat            # Cài đặt Windows (Admin)
├── QUICKSTART.md        # Hướng dẫn 5 bước
├── db/
│   ├── schema.surql     # Database schema
│   └── client.py        # Database client
├── agents/              # AI agents xử lý
├── bot/                 # Telegram handlers
├── storage/files/       # Kho hồ sơ cục bộ
└── docs/                # PRD, VIBE_PROMPTS, ANTIGRAVITY_AGENT
```

## 🚀 Cài đặt (Windows)

### Yêu cầu
- Docker Desktop
- Python 3.12+

### Bước 1: Chuẩn bị
```powershell
cp .env.example .env
# Điền: TELEGRAM_BOT_TOKEN, GEMINI_API_KEY
```

### Bước 2: Chạy Setup
```powershell
.\setup.bat   # Run as Administrator
```

### Bước 3: Wiki & Nạp dữ liệu
1. Truy cập `http://localhost:3000` → tạo Workspace.
2. **Settings > API Tokens** → tạo token → dán vào `OUTLINE_API_TOKEN` trong `.env`.
3. Nạp dữ liệu từ thư mục:
```powershell
python import_local.py
```

### Bước 4: Chạy Bot
```powershell
python main.py
```

## 🤖 Lệnh Telegram Bot

| Lệnh | Mô tả |
|---|---|
| `/start` | Menu chính |
| `/list` | Duyệt Category → Group → Device |
| `/search <từ khóa>` | Tìm kiếm toàn bộ tài liệu |
| `/add` | Thêm thiết bị mới (wizard) |
| `/wiki` | Mở link Outline Wiki |

## 📋 Changelog

- **v2.1.0** — Refactor Storage: Di chuyển kho dữ liệu sang `D:\MedicalData` (configurable via .env). Chuyển sang cấu trúc thư mục phẳng trong Device. Thêm hệ thống tự động phân loại tài liệu qua Prefix/Suffix (`config/data_naming.json`). Cập nhật `scan_agent.py` và `cli` để hỗ trợ logic mới. Chuẩn hóa 225 file hiện có.
- **v2.0.0** — Antigravity-First: Chuyển đổi Telegram Bot thành Relay, xử lý logic tập trung tại Headless Agent thông qua API Server.
- **v1.2.0** — Release: Fix RecordID format, nạp dữ liệu hàng loạt.
- **v1.1.1** — Security: Xóa file .env khỏi Git history. Fix Outline SECRET_KEY & SurrealDB v3 schema command trong setup.bat.
- **v1.1.0** — Release: Bot polling mode, sửa Docker volume error trên Windows.
- **v1.0.1** — Windows release: Thêm setup.bat.
