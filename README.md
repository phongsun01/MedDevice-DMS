# MedDevice DMS

**Hệ thống Quản lý Hồ sơ Thiết bị Y tế (Medical Device Document Management System)**

MedDevice DMS là giải pháp quản lý hồ sơ kỹ thuật, thông số và so sánh thiết bị y tế toàn diện dựa trên nền tảng AI và SurrealDB. Hệ thống cho phép người dùng tương tác từ xa qua Telegram Bot và tra cứu dữ liệu dạng Wiki.

## 🌟 Tính năng chính

- **Cấu trúc phẳng (v2.1)**: Category > Group > Device với tài liệu được phân loại tự động qua Prefix/Suffix.
- **Lưu trữ tùy chỉnh**: Cho phép cấu hình đường dẫn lưu trữ ngoài (ví dụ: `D:\MedicalData`).
- **Tìm kiếm AI**: Full-text search trong PDF, Word & Excel (SurrealDB + Gemini).
- **So sánh tự động**: Trích xuất và so sánh thông số kỹ thuật giữa các thiết bị.
- **Telegram Bot**: Tra cứu qua Relay mode, đẩy yêu cầu tới Headless Agent.
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
