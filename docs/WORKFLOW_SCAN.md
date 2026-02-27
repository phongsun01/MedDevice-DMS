# Workflow: Normalize & Scan (v2.1)

> Quy trình chuẩn hóa dữ liệu cũ sang cấu trúc phẳng và nạp vào hệ thống.

---

## Phase 0 — Normalize (Dành cho dữ liệu cũ)

Bước này giúp đưa dữ liệu từ cấu trúc folder lộn xộn về cấu trúc chuẩn: `Category / Group / Device / tech-file-vi.pdf`.

### Bước 0.1 — Chuẩn hóa Folder & File

Sử dụng script `normalize_data_v2.py`:
- Tự động đổi tên folder sang `kebab-case`.
- Tự động nhận diện `Group` (`ct-scan`, `sieu-am`...) dựa trên PRD.
- Làm phẳng thư mục: Toàn bộ file từ thư mục con (ví dụ: `QĐTT`) được đưa ra thư mục gốc của Device.
- Tự động thêm tiền tố/hậu tố (`tech-`, `-vi`) dựa vào từ khóa tại `config/data_naming.json`.

```powershell
# Preview (Dry-run)
python scripts/normalize_data_v2.py

# Thực hiện thật
python scripts/normalize_data_v2.py --run
```

Output mong đợi:
```
MOVE: Thiet bi chan doan hinh anh\Somatom Go Now\QDTT\compliance.pdf 
  -> thiet-bi-chan-doan-hinh-anh\ct-scan\somatom-go-now\config-compliance-vi.pdf
```

---

## Phase 2 — Scan & Import

### Bước 2.1 — Dry Run

```powershell
python cli.py scan --dry-run
```

```
📁 Scan Preview
────────────────────────────────────
Category: 7 | Group: ~30 | Device: 114
Files: 486
  - technical: 223
  - config (compliance): 120 | (bidding): 80 | (quotation): 35
  - price: 47 | contract: 62 | comparison: 34
  - other/unclassified: 31
─────────────────────────────────────
Dedup: 28 cặp .doc+.pdf cùng nội dung → giữ cả 2, PDF is_primary=True
⚠️  31 file unclassified → xem storage/import_log.jsonl
```

### Bước 2.2 — Import thật sự

```powershell
python cli.py scan
```

### Bước 2.3 — Wiki Sync

```powershell
python cli.py wiki sync
```

### Bước 2.4 — Kiểm tra

```powershell
python cli.py stats
python cli.py health
python cli.py missing
```

Mở `http://localhost:3000` → kiểm tra Collections và trang device.

---

## Tóm tắt thứ tự thực hiện

```
[Phase 0.1] normalize_folders.py → rename + merge
[Phase 0.2] Tạo Group folder theo bảng PRD 2.3
[Phase 0.3] create_doc_subfolders.py → tạo technical/, config/, price/...
[Phase 0.4] Di chuyển file vào subfolder đúng (Somatom Go Now trước)
     ↓
[Phase 2.1] cli.py scan --dry-run → preview
[Phase 2.2] cli.py scan → import thật
[Phase 2.3] cli.py wiki sync → Outline Wiki
[Phase 2.4] Kiểm tra: stats, health, missing, /list bot
```
