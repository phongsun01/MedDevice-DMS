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

1. Define all tables SCHEMAFULL:
   - category
   - device_group
   - device
   - document
   - audit_log

2. Define all fields with correct types (use record<link> for relations).

3. Define Vietnamese analyzer exactly:
   DEFINE ANALYZER vn_analyzer TOKENIZERS blank, class FILTERS lowercase, ascii;

4. Define INDEXES:
   - DEFINE INDEX idx_content ON document FIELDS content_text SEARCH ANALYZER vn_analyzer;
   - DEFINE INDEX idx_metadata ON document FIELDS metadata.title SEARCH ANALYZER vn_analyzer;
   - DEFINE INDEX idx_device_name ON device FIELDS name;
   - DEFINE INDEX idx_device_model ON device FIELDS model;
   - DEFINE INDEX idx_device_brand ON device FIELDS brand;
   - DEFINE INDEX idx_doc_type ON document FIELDS doc_type;
   - DEFINE INDEX idx_doc_device ON document FIELDS device;

5. Define audit_log table:
   id, action (string), table_name (string), record_id (string), telegram_user_id (string), timestamp (datetime), changes (object)

6. Define PERMISSIONS: only authenticated users can read/write all tables.

7. Also implement db/client.py:
   - AsyncSurreal singleton (from surrealdb import AsyncSurreal)
   - Helper functions: connect(), query(), create(), update(), delete(), create_audit_log()
   - Auto-reconnect logic with retry
   - All functions must be async
```

***

## Sub-Prompt 2 – Parse Agent

```
Implement agents/parse_agent.py with these functions (all async where possible):

1. extract_text_from_pdf(file_path: str) -> str
   - Use PyMuPDF (fitz)
   - Handle Vietnamese encoding properly
   - Clean text (remove excessive whitespace, fix line breaks)

2. classify_document(filename: str, caption: str = None) -> dict
   - Rules-based first (same as before)
   - Fallback to Gemini API (first 500 chars)
   - Return {doc_type, sub_type, confidence: float}

3. process_upload(file_path: str, device_id: str, caption: str = None, telegram_user_id: str = None) -> dict
   - Classify document
   - Extract text if PDF
   - Move file to correct storage path: STORAGE_BASE/{category}/{device_group}/{device_id}/{doc_type}/
   - Create document record in SurrealDB
   - Call db.client.create_audit_log("create", "document", new_doc_id, telegram_user_id)
   - Trigger wiki_agent.update_device_page(device_id)
   - Return document record
   - Use structlog for logging, raise custom exceptions on error
```

***

## Sub-Prompt 3 – Search Agent

```
Implement agents/search_agent.py (all functions async):

1. search_documents(query: str, filters: dict = {}) -> list[dict]
   - Use SurrealQL FULLTEXT with SEARCH ANALYZER vn_analyzer
   - Support filters: category_id, device_group_id, device_id, doc_type
   - Use search::highlight('<b>', '</b>', 1)
   - Return top 10 with highlight_snippet

2. search_devices(query: str) -> list[dict]
   - Search device.name, model, brand
   - Join with device_group and category

3. format_search_results_telegram(results: list) -> str
   - Telegram-friendly format

4. get_device_profile(device_id: str) -> dict
   - Fetch full device + documents grouped by doc_type
```

***

## Sub-Prompt 4 – Compare Agent

```
Implement agents/compare_agent.py (all async):

1. compare_devices(device_id_a: str, device_id_b: str, telegram_user_id: str = None) -> dict
   - Prefer existing "comparison" document
   - Otherwise use Gemini 1.5 to extract specs as JSON
   - After comparison, create audit_log entry

2. render_comparison_table_markdown(comparison: dict) -> str

3. export_comparison_xlsx(comparison: dict, output_path: str) -> str

4. compare_handler(device_name_a: str, device_name_b: str, telegram_user_id: str) -> tuple[str, str]
```

***

## Sub-Prompt 5 – Wiki Agent (Outline.dev)

```
Implement agents/wiki_agent.py:

1. OutlineClient class with all async methods (create_document, update_document, find_document_by_title, get_or_create_collection)

2. generate_device_page_markdown(device: dict, documents: list) -> str
   - Professional Markdown with sections by doc_type
   - Use emoji icons per type

3. update_device_page(device_id: str, telegram_user_id: str = None):
   - Fetch profile
   - Generate markdown
   - Update or create Outline page
   - Create audit_log for wiki update

4. generate_index_page(category_id: str = None)
   - Auto-update after any change
```

***

## Sub-Prompt 6 – Telegram Bot

```
Implement the complete Telegram bot using aiogram 3.x + FSM:

First create bot/states.py:
from aiogram.fsm.state import StatesGroup, State

class AddDeviceStates(StatesGroup):
    category = State()
    device_group = State()
    name = State()
    model = State()
    brand = State()
    origin = State()
    year = State()
    confirm = State()

class CompareStates(StatesGroup):
    device_a = State()
    device_b = State()

# (thêm các state khác nếu cần)

Then implement:

bot/handlers/browse.py, files.py, search.py, compare.py, wiki.py, add.py
- All handlers use FSM where multi-step is needed
- /start → main menu inline keyboard
- File upload + caption support
- /get <doc_id>, /docs <device>, /compare, /wiki, /add (full conversation with FSM)
- bot/middleware.py: strict check TELEGRAM_ALLOWED_USERS + log unauthorized attempts
- bot/keyboards.py: reusable + pagination
- main.py: 
  - async start with webhook (aiohttp)
  - register all handlers + states
  - start SurrealDB connection
  - structlog setup
```

***

## Sub-Prompt 7 – Docker & Deployment

```
Create docker-compose.yml, Dockerfile, .env.outline, setup.sh, README.md (Vietnamese):

docker-compose.yml phải bao gồm:
- surrealdb
- outline (với postgres, redis, minio)
- bot service (build from .)

setup.sh script:
- docker-compose up -d
- Apply SurrealDB schema
- Create initial Outline collections
- Start cloudflared tunnel
- Print all URLs

README.md: full setup instructions in Vietnamese, how to add first user, how to use commands, backup guide.
```

***

## Cách dùng sau khi chỉnh

1. **Paste Master Prompt** (giữ nguyên của bạn)
2. **Paste lần lượt 7 Sub-Prompt trên**
3. **Sau mỗi Sub, dùng lệnh fix**:  
   `"Refactor the code above to be fully async, add proper structlog, Pydantic models, error handling and audit log where missing."`
