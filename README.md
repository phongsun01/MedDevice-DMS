# MedDevice DMS

**Hệ thống Quản lý Hồ sơ Thiết bị Y tế (Medical Device Document Management System)**

MedDevice DMS là giải pháp quản lý hồ sơ kỹ thuật, thông số và so sánh thiết bị y tế toàn diện dựa trên nền tảng AI và SurrealDB. Hệ thống cho phép người dùng tương tác từ xa qua Telegram Bot và tra cứu dữ liệu dạng Wiki.

## 🌟 Tính năng chính

- **Cấu trúc phân cấp**: Quản lý theo Category > Group > Device với các nhóm tài liệu chuẩn hóa.
- **Tìm kiếm AI**: Hỗ trợ tìm kiếm toàn văn (full-text) và ngữ nghĩa trong nội dung file PDF/Word.
- **So sánh tự động**: Tự động trích xuất và so sánh thông số kỹ thuật giữa các thiết bị.
- **Giao diện đa kênh**: 
  - **Telegram Bot**: Nhận file, tra cứu, tìm kiếm và điều khiển hệ thống từ xa.
  - **Wiki (Outline)**: Trang tra cứu tổng quát, tự động cập nhật từ cơ sở dữ liệu.
- **Lưu trữ bảo mật**: Hỗ trợ lưu trữ local, Google Drive hoặc S3.
- **Audit Log**: Ghi lại toàn bộ thao tác trên hệ thống (bắt buộc cho phần mềm y tế).

## 🛠 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Database | [SurrealDB](https://surrealdb.com/) (Multi-model graph database) |
| AI/LLM | Google Gemini 1.5 |
| Bot | aiogram 3.x + FSM |
| Wiki | Outline.dev (self-hosted) |
| PDF | PyMuPDF |
| Excel | openpyxl |
| Logging | structlog |
| Config | Pydantic Settings |
| Deploy | Docker Compose |

## 📂 Cấu trúc thư mục

```
meddevice-dms/
├── main.py              # Entry point (polling or webhook mode)
├── config.py            # Pydantic settings (.env loader)
├── requirements.txt     # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── setup.sh             # One-click setup script
├── db/
│   ├── schema.surql     # SurrealDB schema (5 tables + indexes)
│   └── client.py        # AsyncSurreal singleton + audit log
├── agents/
│   ├── parse_agent.py   # PDF extraction + classification
│   ├── search_agent.py  # Full-text search
│   ├── compare_agent.py # Device comparison + XLSX
│   └── wiki_agent.py    # Outline.dev integration
├── bot/
│   ├── states.py        # FSM StatesGroup definitions
│   ├── keyboards.py     # Reusable inline keyboards
│   ├── middleware.py     # Auth middleware
│   └── handlers/
│       ├── browse.py    # /start, /list
│       ├── search.py    # /search
│       ├── files.py     # File upload, /get, /docs
│       ├── compare.py   # /compare (FSM)
│       ├── wiki.py      # /wiki
│       └── add.py       # /add (FSM)
├── storage/files/       # Organized file storage
└── docs/                # PRD, Vibe Prompts, Workflow
```

## 🚀 Cài đặt

### Yêu cầu
- Docker & Docker Compose
- Python 3.12+ (nếu chạy local)
- Cloudflared hoặc ngrok (cho Telegram webhook)

### Bước 1: Clone & cấu hình

```bash
git clone https://github.com/phongsun01/MedDevice-DMS
cd MedDevice-DMS
cp .env.example .env
# Chỉnh sửa .env với các thông tin: BOT_TOKEN, GEMINI_API_KEY, etc.
```

### Bước 2: Chạy setup

```bash
chmod +x setup.sh
./setup.sh
```

Hoặc chạy thủ công:

```bash
docker-compose up -d
# Đợi SurrealDB khởi động, sau đó apply schema:
docker exec -i $(docker-compose ps -q surrealdb) \
  /surreal sql --conn ws://localhost:8000 --user root --pass root \
  --ns meddevice --db dms < db/schema.surql
```

### Bước 3: Thiết lập Webhook

```bash
# Dùng cloudflared
cloudflared tunnel --url http://localhost:8080

# Hoặc ngrok
ngrok http 8080
```

Cập nhật `WEBHOOK_URL` trong `.env` với URL tunnel.

## 🤖 Lệnh Telegram Bot

| Lệnh | Mô tả |
|---|---|
| `/start` | Menu chính |
| `/search <từ khóa>` | Tìm kiếm toàn bộ tài liệu |
| `/list` | Duyệt cây Category → Group → Device |
| `/docs <thiết bị>` | Xem hồ sơ tài liệu của thiết bị |
| `/compare <A> <B>` | So sánh 2 thiết bị |
| `/get <doc_id>` | Tải file tài liệu |
| `/add` | Thêm thiết bị mới (hội thoại từng bước) |
| `/wiki` | Mở Wiki Outline |
| **Gửi file** | Upload tài liệu cho thiết bị (kèm caption) |

### Upload file

Gửi file kèm caption theo format:
```
type|tên_thiết_bị|sub_type
```
Ví dụ: `technical|Máy X-quang CR Alpha|EN`

## 💾 Backup

```bash
# Backup SurrealDB
docker exec $(docker-compose ps -q surrealdb) \
  /surreal export --conn ws://localhost:8000 --user root --pass root \
  --ns meddevice --db dms > backup_$(date +%Y%m%d).surql

# Backup files
tar -czf storage_backup_$(date +%Y%m%d).tar.gz storage/
```

## 📋 Version

- **v1.1.0** — First working release: bot confirmed running in polling mode. Fixed SurrealDB v3 incompatibilities (memory mode, schema syntax). Fixed Box Drive Docker BuildKit issue. Added auto polling/webhook mode detection in `main.py`.
- **v1.0.3** — Docker fix: Added daemon check and removed obsolete version tag.
- **v1.0.2** — Docker fix: Switched to `docker compose` for better compatibility and fixed Windows encoding.
- **v1.0.1** — Windows release: Added `setup.bat`, updated credentials and audit flow.
