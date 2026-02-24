# Workflow: Normalize & Scan (v2.0)

> Quy trình 2 giai đoạn: **Phase 0 (Normalize)** → **Phase 2 (Scan & Import)**  
> Phase 0 chỉ chạy 1 lần duy nhất.

---

## Phase 0 — Normalize (Chỉ chạy 1 lần)

### Bước 0.1 — Rename folder về kebab-case

```powershell
# Preview (không thay đổi gì)
python scripts/normalize_folders.py --dry-run

# Thực hiện nếu OK
python scripts/normalize_folders.py
```

Output mong đợi:
```
[DRY-RUN] Rename plan:
  storage/files/Thiet bi chan doan hinh anh → thiet-bi-chan-doan-hinh-anh
  storage/files/Thiet bi dieu tri → thiet-bi-dieu-tri
  ...
  MERGE: thiet_bi_chan_doan_hinh_anh → thiet-bi-chan-doan-hinh-anh (12 cặp)
```

### Bước 0.2 — Tạo Group folder và di chuyển Device

Thực hiện theo bảng phân nhóm (PRD Section 2.3):

```
thiet-bi-chan-doan-hinh-anh/
├── ct-scan/      ← Somatom Go Now, CT 128 Somatom Go Top, He thong CT dem photon
├── sieu-am/      ← Arietta 50, 6 Acuson/Resona/Arietta models
├── c-arm/        ← Cios Fit, Cios Select
├── dsa/          ← Azurion 7B20, DSA siemens
├── mri/          ← MRI Siemens 0.55
└── x-quang/      ← X Quang Examion, FDR 68S
```

**Chạy script tạo subfolder cho mỗi device:**
```powershell
python scripts/create_doc_subfolders.py
```

### Bước 0.3 — Di chuyển file hiện có vào subfolder đúng

Với **Somatom Go Now** làm mẫu đầu tiên:

| File gốc | Chuyển vào |
|---|---|
| `2. Chuong V...IB*.doc` | `config/compliance/` |
| `CT 32 SOMATOM*.xlsx` | `config/bidding/` |
| File `.doc` + `.pdf` cùng stem | Cả 2 vào cùng thư mục |
| `IB Download.zip` | Giải nén → phân loại → `other/archive/` (zip gốc) |

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
