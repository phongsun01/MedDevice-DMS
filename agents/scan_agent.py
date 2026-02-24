"""
MedDevice DMS — Scan Agent (Phase 2B)

Chịu trách nhiệm quét thư mục `storage/files/` và xây dựng cấu trúc DB.
- normalize_name(): Chuyển tiếng Việt có dấu -> kebab-case.
- infer_hierarchy(): Xác định Category, Group, Device, doc_type dựa vào đường dẫn.
- process_file(): Xử lý 1 file cụ thể (gọi parser và lưu DB).
- scan_directory(): Quét toàn bộ thư mục và trả về report (hỗ trợ dry-run).
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

import structlog
from unidecode import unidecode

log = structlog.get_logger()

# Import the parser
try:
    from agents.parse_agent import process_file as parse_file_content
except ImportError:
    # Fallback to older import path if needed
    try:
         from agents.parse_agent import process_file_gemini as parse_file_content
    except ImportError:
         log.error("scan.missing_parser", msg="Cannot import parse_file module")
         parse_file_content = None

def normalize_name(text: str) -> str:
    """Convert string to kebab-case slug."""
    # Handle empty or purely strange strings
    if not text: return "unknown"
    slug = re.sub(r"[^a-z0-9]+", "-", unidecode(text).lower()).strip("-")
    return slug if slug else "unknown"


def infer_hierarchy(file_path: Path, base_dir: Path) -> Dict[str, str]:
    """Phân tích cấu trúc thư mục từ file_path.
    
    Kỳ vọng cấu trúc: base_dir / category / group / device / doc_type / [sub_type] / file
    """
    rel_path = file_path.relative_to(base_dir)
    parts = rel_path.parts
    
    hierarchy = {
        "category": None,
        "group": None,
        "device": None,
        "doc_type": None,
        "sub_type": None,
        "filename": file_path.name,
        "is_unclassified": False
    }
    
    if len(parts) >= 4:
        hierarchy["category"] = parts[0]
        hierarchy["group"] = parts[1]
        hierarchy["device"] = parts[2]
        hierarchy["doc_type"] = parts[3]
        if len(parts) > 5:
             hierarchy["sub_type"] = parts[4]
    else:
        # Nếu file nằm nông hơn, đánh dấu để xem xét (hoặc Other)
        hierarchy["is_unclassified"] = True
        
    return hierarchy


async def process_file(file_path: Path, hierarchy: Dict[str, str], db, dry_run: bool = False) -> Dict[str, Any]:
    """Process a single file, insert into DB if not dry_run."""
    result = {
        "path": str(file_path),
        "status": "skipped",
        "action": "none",
        "error": None
    }
    
    if hierarchy["is_unclassified"]:
         result["status"] = "unclassified"
         return result

    cat_slug = normalize_name(hierarchy["category"])
    grp_slug = normalize_name(hierarchy["group"])
    dev_slug = normalize_name(hierarchy["device"])

    # Define DB IDs
    cat_id = f"category:{cat_slug}"
    grp_id = f"group:{grp_slug}"
    dev_id = f"device:{dev_slug}"

    if dry_run:
        result["status"] = "preview"
        result["action"] = f"Would create {dev_id} -> document"
        return result

    # -- Thực tế ghi DB --
    try:
        # 1. Đảm bảo Category tồn tại
        await db.query(
            "UPSERT type::thing($id) CONTENT { name: $name, display_name: $raw_name }",
            {"id": cat_id, "name": cat_slug, "raw_name": hierarchy["category"]}
        )

        # 2. Đảm bảo Group tồn tại
        await db.query(
            "UPSERT type::thing($id) CONTENT { name: $name, display_name: $raw_name, category: $cat }",
            {"id": grp_id, "name": grp_slug, "raw_name": hierarchy["group"], "cat": cat_id}
        )

        # 3. Đảm bảo Device tồn tại
        await db.query(
            "UPSERT type::thing($id) CONTENT { name: $name, display_name: $raw_name, device_group: $grp }",
            {"id": dev_id, "name": dev_slug, "raw_name": hierarchy["device"], "grp": grp_id}
        )
    except Exception as e:
        log.error("scan.db_setup_failed", error=str(e), path=str(file_path))
        result["error"] = f"DB setup failed: {e}"
        result["status"] = "error"
        return result

    # 4. Kiểm tra file này đã tồn tại trong document hay chưa (DEDUP CODE)
    existing_docs_query = """
        SELECT id, doc_type, is_primary FROM document 
        WHERE device = $dev_id AND filename = $filename
    """
    existing_docs = await db.query(existing_docs_query, {"dev_id": dev_id, "filename": file_path.name})
    
    if existing_docs and isinstance(existing_docs, list) and isinstance(existing_docs[0], dict):
         # v3 logic single item list wrapper
         pass
    elif existing_docs and isinstance(existing_docs, list) and len(existing_docs) > 0 and isinstance(existing_docs[0], list):
        existing_docs = existing_docs[0] # Unwrap nested list
    else:
        existing_docs = []

    if existing_docs:
        result["status"] = "skipped"
        result["action"] = "already_exists"
        return result

    # 5. Extract & Phân loại bằng Gemini (parse_agent)
    doc_data = {}
    if parse_file_content:
        log.info("scan.parsing", file=file_path.name)
        try:
             # Using asyncio to wrap sync parse function if it's synchronous, but assume it returns dict
             import inspect
             if inspect.iscoroutinefunction(parse_file_content):
                 doc_data = await parse_file_content(str(file_path))
             else:
                 doc_data = parse_file_content(str(file_path))
        except Exception as e:
             log.error("scan.parse_failed", error=str(e), path=str(file_path))
             doc_data = {}

    # Override doc_type from folder structure if Gemini failed or provided bad info
    if hierarchy["doc_type"]:
         # We trust folder structure more for doc_type
         # Map internal folder names to valid doc types
         folder_type = hierarchy["doc_type"].lower()
         valid_types = ['technical', 'price', 'contract', 'config', 'comparison', 'other']
         if folder_type in valid_types:
             doc_data["doc_type"] = folder_type

    # 6. Insert Document
    is_primary = True
    if file_path.suffix.lower() == ".doc" or file_path.suffix.lower() == ".docx":
        # Check if PDF exists in same folder
        pdf_path = file_path.with_suffix(".pdf")
        if pdf_path.exists():
            is_primary = False

    insert_data = {
        "device": dev_id,
        "filename": file_path.name,
        "doc_type": doc_data.get("doc_type", hierarchy["doc_type"] or "other"),
        "sub_type": hierarchy["sub_type"] or doc_data.get("sub_type"),
        "title": doc_data.get("title", file_path.stem),
        "content_text": doc_data.get("content_text", ""),
        "specs": doc_data.get("specs", {}),
        "is_primary": is_primary,
        "file_path": str(file_path)
    }

    try:
        await db.query("CREATE document CONTENT $data", {"data": insert_data})
        result["status"] = "success"
        result["action"] = "inserted"
        log.info("scan.document_inserted", filename=file_path.name, device=dev_id)
    except Exception as e:
        log.error("scan.insert_failed", error=str(e), path=str(file_path))
        result["error"] = f"Insert failed: {e}"
        result["status"] = "error"

    return result


async def scan_directory(base_dir: str = "storage/files", dry_run: bool = False) -> Dict[str, Any]:
    """Quét toàn bộ thư mục và xử lý file."""
    base_path = Path(base_dir)
    if not base_path.exists():
        log.error("scan.dir_not_found", path=base_dir)
        return {"error": "Directory not found"}

    db = None
    if not dry_run:
        from db import client as db_client
        await db_client.connect()
        db = db_client

    report = {
        "total_files": 0,
        "processed": 0,
        "skipped": 0,
        "errors": 0,
        "unclassified": 0,
        "dry_run": dry_run,
        "details": []
    }

    valid_extensions = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}

    log.info("scan.start", base_dir=str(base_path), dry_run=dry_run)

    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            
            # Skip hidden files
            if file.startswith(".") or file_path.suffix.lower() not in valid_extensions:
                continue
                
            report["total_files"] += 1
            hierarchy = infer_hierarchy(file_path, base_path)
            
            res = await process_file(file_path, hierarchy, db, dry_run=dry_run)
            
            if res["status"] == "success":
                 report["processed"] += 1
            elif res["status"] == "skipped":
                 report["skipped"] += 1
            elif res["status"] == "error":
                 report["errors"] += 1
                 report["details"].append(res)
            elif res["status"] == "unclassified":
                 report["unclassified"] += 1
                 report["details"].append(res)
            elif res["status"] == "preview":
                 report["processed"] += 1 # count as processed in dry run
                 
            if report["total_files"] % 50 == 0:
                 log.info("scan.progress", count=report["total_files"])

    log.info("scan.completed", stats=report)
    return report
