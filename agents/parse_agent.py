"""
MedDevice DMS - Parse Agent
PDF text extraction, document classification, upload processing.
"""
import os
import re
import shutil
from pathlib import Path

import structlog

from config import settings
from db import client as db

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# 1. PDF Text Extraction
# ---------------------------------------------------------------------------

async def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF. Handles Vietnamese encoding."""
    import fitz  # PyMuPDF - lazy import

    text_parts: list[str] = []
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text_parts.append(page.get_text("text"))
        doc.close()
    except Exception as exc:
        log.error("pdf.extract_failed", file=file_path, error=str(exc))
        raise

    raw = "\n".join(text_parts)
    # Clean: collapse whitespace, fix broken Vietnamese line breaks
    cleaned = re.sub(r"[ \t]+", " ", raw)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()
    log.info("pdf.extracted", file=file_path, chars=len(cleaned))
    return cleaned


# ---------------------------------------------------------------------------
# 2. Document Classification
# ---------------------------------------------------------------------------

_RULES: list[tuple[str, str, str | None]] = [
    # (pattern, doc_type, sub_type)
    (r"huong_dan|manual|ifu|hướng.dẫn", "technical", "VI"),
    (r"specification|spec|thong_so", "technical", "EN"),
    (r"bao_gia|quotation|quote|báo.giá", "price", "quotation"),
    (r"trung_thau|bid.result|kết.quả", "price", "bid_result"),
    (r"hop_dong|contract|hợp.đồng", "contract", None),
    (r"so_sanh|compar", "comparison", None),
    (r"quang_cao|advertising|quảng.cáo", "config", "advertising"),
    (r"cau_hinh|config|cấu.hình", "config", "basic"),
    (r"moi_thau|bidding|mời.thầu", "config", "bidding"),
    (r"dap_ung|compliance|đáp.ứng", "config", "compliance"),
]


async def classify_document(filename: str, caption: str | None = None) -> dict:
    """Classify a document by filename patterns, then Gemini fallback.

    Returns: {doc_type: str, sub_type: str | None, confidence: float}
    """
    # Caption override: "type|device_name|sub_type"
    if caption and "|" in caption:
        parts = [p.strip() for p in caption.split("|")]
        if len(parts) >= 1:
            return {
                "doc_type": parts[0],
                "sub_type": parts[2] if len(parts) >= 3 else None,
                "confidence": 1.0,
            }

    # Rules-based matching
    lower_name = filename.lower()
    for pattern, doc_type, sub_type in _RULES:
        if re.search(pattern, lower_name):
            log.info("classify.rules", filename=filename, doc_type=doc_type)
            return {"doc_type": doc_type, "sub_type": sub_type, "confidence": 0.85}

    # Gemini fallback
    try:
        result = await _classify_with_gemini(filename)
        return result
    except Exception as exc:
        log.warning("classify.gemini_failed", error=str(exc))
        return {"doc_type": "other", "sub_type": None, "confidence": 0.1}


async def _classify_with_gemini(filename: str) -> dict:
    """Use Google Gemini to classify a document by filename."""
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = (
        f"Classify this medical device document filename into one of these types: "
        f"technical, config, price, contract, comparison, link, other. "
        f"Also guess the sub_type if applicable. Filename: '{filename}'. "
        f"Return JSON: {{\"doc_type\": \"...\", \"sub_type\": \"...\", \"confidence\": 0.0-1.0}}"
    )
    response = await model.generate_content_async(prompt)
    import json
    return json.loads(response.text.strip().strip("```json").strip("```"))


# ---------------------------------------------------------------------------
# 3. Upload Processing
# ---------------------------------------------------------------------------

async def process_upload(
    file_path: str,
    device_id: str,
    caption: str | None = None,
    telegram_user_id: str | None = None,
) -> dict:
    """Full upload pipeline: classify → extract → store → record → audit → wiki."""

    # Classify
    filename = os.path.basename(file_path)
    classification = await classify_document(filename, caption)
    doc_type = classification["doc_type"]
    sub_type = classification.get("sub_type")

    # Extract text if PDF
    content_text = ""
    if filename.lower().endswith(".pdf"):
        content_text = await extract_text_from_pdf(file_path)

    # Resolve storage path
    device_info = await db.query(
        "SELECT *, device_group.name AS group_name, device_group.category.name AS cat_name FROM device WHERE id = $id",
        {"id": device_id},
    )
    if not device_info or not device_info[0]:
        raise ValueError(f"Device not found: {device_id}")

    dev = device_info[0][0] if isinstance(device_info[0], list) else device_info[0]
    cat_name = _safe_name(dev.get("cat_name", "uncategorized"))
    grp_name = _safe_name(dev.get("group_name", "ungrouped"))
    dev_id_short = str(device_id).split(":")[-1]

    dest_dir = Path(settings.STORAGE_BASE_PATH) / cat_name / grp_name / dev_id_short / doc_type
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    shutil.move(file_path, str(dest_path))

    # Create document record
    doc_record = await db.create("document", {
        "device": device_id,
        "doc_type": doc_type,
        "sub_type": sub_type,
        "file_path": str(dest_path),
        "content_text": content_text[:50_000],  # cap at 50k chars
        "metadata": {
            "title": filename,
            "original_name": filename,
            "confidence": classification["confidence"],
        },
    })

    # Audit log
    new_doc_id = doc_record.get("id", "unknown")
    await db.create_audit_log("create", "document", str(new_doc_id), telegram_user_id)

    # Trigger wiki update (non-blocking)
    try:
        from agents import wiki_agent
        await wiki_agent.update_device_page(device_id, telegram_user_id)
    except Exception as exc:
        log.warning("wiki.update_skipped", error=str(exc))

    log.info("upload.processed", doc_id=new_doc_id, doc_type=doc_type)
    return doc_record


def _safe_name(name: str) -> str:
    """Sanitize a string for use as a directory name."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip().lower().replace(" ", "_")
