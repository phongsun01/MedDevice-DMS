Đây là prompt vibe code hoàn chỉnh, chia làm **1 Master Prompt** và các **Sub-prompts theo module** để paste vào Antigravity IDE:

***

## Master Prompt (Paste đầu tiên)

```
You are a senior full-stack developer. Build a Medical Device Document Management System called "MedDevice DMS".

## Tech Stack
- Runtime: Python 3.12
- Database: SurrealDB (via surrealdb Python SDK)
- Telegram Bot: aiogram 3.x
- PDF Extraction: PyMuPDF (fitz)
- Excel handling: openpyxl
- Wiki: Outline.dev (REST API integration)
- File Storage: local filesystem with structured folders
- AI/LLM: Google Gemini API (for text extraction, classification, comparison)
- Tunnel: cloudflared or ngrok (for Telegram webhook)
- Environment: .env file for all secrets

## Project Structure
meddevice-dms/
├── main.py                  # Entry point
├── .env                     # Secrets
├── config.py                # Config loader
├── db/
│   ├── schema.surql         # SurrealDB schema definitions
│   ├── client.py            # SurrealDB connection + helpers
│   └── migrations/          # Schema migration scripts
├── agents/
│   ├── parse_agent.py       # PDF/DOCX text extraction + classify
│   ├── search_agent.py      # Full-text search queries
│   ├── compare_agent.py     # Device comparison + XLSX export
│   └── wiki_agent.py        # Outline.dev page generator
├── bot/
│   ├── handlers/
│   │   ├── add.py           # /add command
│   │   ├── search.py        # /search command
│   │   ├── compare.py       # /compare command
│   │   ├── browse.py        # /list, /docs commands
│   │   ├── files.py         # /get command + file upload
│   │   └── wiki.py          # /wiki command
│   ├── keyboards.py         # Inline keyboards / menus
│   └── middleware.py        # Auth middleware
├── storage/
│   └── files/               # Uploaded files organized by device
│       └── {category}/{group}/{device_id}/
│           ├── technical/
│           ├── config/
│           ├── price/
│           ├── contract/
│           ├── comparison/
│           └── other/
└── wiki/
    └── templates/           # Markdown templates for Outline pages

## .env variables needed
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASS=root
SURREAL_NS=meddevice
SURREAL_DB=dms
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USERS=123456789,987654321
GEMINI_API_KEY=
OUTLINE_API_URL=http://localhost:3000/api
OUTLINE_API_TOKEN=
STORAGE_BASE_PATH=./storage/files
WEBHOOK_URL=https://your-tunnel-url.com/webhook

## Core Data Model (implement exactly)
Category → Group → Device → Documents

Category fields: id, name, description, created_at
Group fields: id, name, description, category (record<category>), created_at
Device fields: id, name, model, brand, origin, year, group (record<group>), notes, created_at, updated_at
Document fields: id, device (record<device>), doc_type (enum), sub_type, file_path, file_url, content_text, metadata (object), uploaded_at

doc_type enum values:
- "technical" (sub_type: "VI" | "EN")
- "config" (sub_type: "advertising" | "basic" | "quotation" | "bidding" | "compliance")
- "link" (sub_type: "homepage" | "fda" | "ce" | "other")
- "price" (sub_type: "quotation" | "bid_result")
- "contract"
- "comparison"
- "other"

Start by creating all files and folder structure. Do not write any code yet, just scaffold.
```

***

## Sub-Prompt 1 – SurrealDB Schema

```
Now implement db/schema.surql with the following requirements:

1. Define all tables SCHEMAFULL: category, device_group, device, document
2. Define all fields with correct types
3. Define INDEXES:
   - Full-text search index on document.content_text using custom analyzer
   - Full-text search index on document.metadata.title
   - Index on device.name, device.model, device.brand
   - Index on document.doc_type, document.device
4. Define Vietnamese-compatible text ANALYZER named "vn_analyzer" using tokenizers: blank, class — with filters: lowercase, ascii
5. Define PERMISSIONS: only authenticated users can read/write
6. Also implement db/client.py:
   - Async SurrealDB client singleton using surrealdb Python SDK
   - Helper functions: connect(), query(), create_record(), update_record(), delete_record()
   - Auto-reconnect on disconnect
```

***

## Sub-Prompt 2 – Parse Agent

```
Implement agents/parse_agent.py with these functions:

1. extract_text_from_pdf(file_path: str) -> str
   - Use PyMuPDF (fitz) to extract all text
   - Handle Vietnamese encoding
   - Return cleaned text (remove excessive whitespace)

2. classify_document(filename: str, caption: str = None) -> dict
   - Use rules-based first: match filename patterns to doc_type/sub_type
   - Rules examples:
     * filename contains "huong_dan|manual|IFU" → technical
     * filename contains "bao_gia|quotation|quote" → price/quotation
     * filename contains "hop_dong|contract" → contract
     * filename contains "quang_cao|advertising" → config/advertising
     * caption format "type|device_name|sub_type" overrides rules
   - Fallback: call Gemini API with first 500 chars of content to classify
   - Return: {doc_type, sub_type, confidence}

3. process_upload(file_path: str, device_id: str, caption: str = None) -> dict
   - Classify document
   - Extract text if PDF
   - Move file to correct storage path: STORAGE_BASE/{category}/{group}/{device_id}/{doc_type}/
   - Create document record in SurrealDB
   - Trigger wiki_agent.update_device_page(device_id)
   - Return document record
```

***

## Sub-Prompt 3 – Search Agent

```
Implement agents/search_agent.py:

1. search_documents(query: str, filters: dict = {}) -> list[dict]
   - Build SurrealQL with FULLTEXT search on content_text
   - Apply filters: category_id, group_id, device_id, doc_type
   - Use search::highlight('<b>', '</b>', 1) for highlights
   - Return top 10 results with: device_name, doc_type, sub_type, highlight_snippet, file_path, doc_id

2. search_devices(query: str) -> list[dict]
   - Search on device.name, device.model, device.brand
   - Return device list with group and category info

3. format_search_results_telegram(results: list) -> str
   - Format as numbered list for Telegram
   - Each item: "1. [device_name] - [doc_type] ([sub_type])\n   📄 ...highlight...\n   ID: doc_id"
   - Max 10 results, show count

4. get_device_profile(device_id: str) -> dict
   - Fetch device + all documents grouped by doc_type
   - Return structured dict for display
```

***

## Sub-Prompt 4 – Compare Agent

```
Implement agents/compare_agent.py:

1. compare_devices(device_id_a: str, device_id_b: str) -> dict
   - Check if "comparison" doc exists for either device → use it first
   - Otherwise: fetch technical docs (EN preferred) for both devices
   - Call Gemini with both content_texts:
     Prompt: "Extract all technical specifications from the following two documents as JSON. 
     Return format: {specs: [{name: string, value_a: string, value_b: string}], 
     device_a: string, device_b: string}"
   - Return structured comparison dict

2. render_comparison_table_markdown(comparison: dict) -> str
   - Render as Telegram-friendly markdown table
   - Header: device names
   - Rows: each spec with both values
   - Highlight differences with emoji ⚠️

3. export_comparison_xlsx(comparison: dict, output_path: str) -> str
   - Use openpyxl to create formatted Excel file
   - Sheet 1: comparison table with header row styled
   - Return file path

4. compare_handler(device_name_a: str, device_name_b: str) -> tuple[str, str]
   - Fuzzy match device names to IDs
   - Run comparison
   - Export XLSX
   - Return (markdown_text, xlsx_path)
```

***

## Sub-Prompt 5 – Wiki Agent (Outline.dev)

```
Implement agents/wiki_agent.py using Outline.dev REST API:

1. OutlineClient class:
   - __init__(api_url, api_token)
   - async create_document(title, content, collection_id, parent_id=None) -> str (doc_id)
   - async update_document(doc_id, title, content) -> bool
   - async find_document_by_title(title) -> str | None
   - async get_or_create_collection(name) -> str (collection_id)

2. generate_device_page_markdown(device: dict, documents: list) -> str
   - Generate full Markdown page for a device
   - Sections: Overview table (model/brand/origin/year), then one section per doc_type
   - Each doc section lists files with emoji icons by type: 📄 PDF, 📊 Excel, 🔗 Link
   - Include breadcrumb: Category > Group > Device

3. update_device_page(device_id: str):
   - Fetch device profile from SurrealDB
   - Generate markdown
   - Find existing Outline page → update, or create new
   - Collections structure: one collection per Category, pages nested by Group

4. generate_index_page(category_id: str = None):
   - Generate master index page listing all devices in a category/all categories
   - Auto-update after any device change

Setup collection hierarchy in Outline:
  Collection: [Category Name]
    Page: [Group Name] (index of devices in group)
      Sub-page: [Device Name] (full device profile)
```

***

## Sub-Prompt 6 – Telegram Bot

```
Implement the complete Telegram bot using aiogram 3.x:

bot/handlers/browse.py:
- /start → show main menu inline keyboard: [🔍 Tìm kiếm] [📁 Duyệt hồ sơ] [➕ Thêm thiết bị] [📊 So sánh]
- /list → show categories as inline buttons
- On category select → show groups
- On group select → show devices (paginated, 10/page)
- On device select → show device summary + inline buttons: [📄 Xem tài liệu] [🌐 Mở Wiki] [📊 So sánh]

bot/handlers/files.py:
- Handle file upload: user sends file → bot asks for device name (or caption format "type|device|subtype")
- /get <doc_id> → send file from storage path back to user (use bot.send_document)
- /docs <device_name> → show all documents grouped by type, each with /get link

bot/handlers/search.py:
- /search <query> → call search_agent → format + reply
- Handle follow-up: "xem thêm" → next page of results

bot/handlers/compare.py:
- /compare <A> <B> or /compare then ask step by step
- Send markdown table first, then send XLSX file

bot/handlers/wiki.py:
- /wiki → link to Outline index
- /wiki <device_name> → find device, return direct Outline page URL

bot/handlers/add.py:
- /add → start conversation: ask category (inline buttons) → group → device name → model → brand → origin → confirm
- Create device record in SurrealDB, trigger wiki page creation

bot/middleware.py:
- Check user ID against TELEGRAM_ALLOWED_USERS
- Block unauthorized users

bot/keyboards.py:
- Reusable inline keyboard builders
- Pagination keyboard builder

main.py:
- Start SurrealDB connection
- Register all handlers
- Set webhook (not polling) using WEBHOOK_URL
- Start aiohttp webhook server on port 8080
```

***

## Sub-Prompt 7 – Docker & Deployment

```
Create docker-compose.yml to run the full stack locally:

services:
  surrealdb:
    image: surrealdb/surrealdb:latest
    command: start --log trace --user root --pass root file://data/database.db
    ports: ["8000:8000"]
    volumes: ["./data/surreal:/data"]

  outline:
    image: outlinewiki/outline:latest
    env_file: .env.outline
    ports: ["3000:3000"]
    depends_on: [postgres, redis, minio]

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: outline
      POSTGRES_USER: outline
      POSTGRES_PASSWORD: outline_pass
    volumes: ["./data/postgres:/var/lib/postgresql/data"]

  redis:
    image: redis:7

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    volumes: ["./data/minio:/data"]

  bot:
    build: .
    env_file: .env
    volumes: ["./storage:/app/storage"]
    depends_on: [surrealdb, outline]
    restart: unless-stopped

Also create:
- Dockerfile for the bot service
- .env.outline template with all required Outline env vars
- setup.sh script that: starts docker-compose, applies SurrealDB schema, creates initial Outline collections, starts cloudflared tunnel
- README.md with full setup instructions in Vietnamese
```

***

## Cách dùng

1. **Paste Master Prompt** → để Antigravity scaffold toàn bộ cấu trúc thư mục
2. **Paste lần lượt Sub-Prompt 1→7**, đợi từng bước hoàn tất
3. Sau mỗi sub-prompt, kiểm tra và prompt tiếp: `"Fix any errors in the code above, then run tests"`
4. Cuối cùng: `"Run the project with docker-compose and confirm all services start correctly"`
