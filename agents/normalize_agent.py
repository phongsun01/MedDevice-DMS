"""
MedDevice DMS — Normalize Agent (v2.3.0)
Nhận metadata file thô, trả về tên file chuẩn hóa theo DMS convention.
"""
import re
import unicodedata
from pathlib import Path
from config import settings


def slugify(text: str) -> str:
    """Chuyển text sang kebab-case ASCII: 'Arietta 50' → 'arietta-50'."""
    # Normalize unicode (bỏ dấu tiếng Việt)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Lowercase + replace spaces/underscores/dots with hyphen
    text = re.sub(r"[\s_\.]+", "-", text.lower())
    # Remove non-alphanumeric except hyphen
    text = re.sub(r"[^a-z0-9\-]", "", text)
    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def build_filename(doc_type: str, device_slug: str, lang: str, ext: str) -> str:
    """
    Tạo tên file chuẩn: {prefix}-{device_slug}-{lang}.{ext}
    Nếu không có lang → {prefix}-{device_slug}.{ext}
    """
    naming = settings.data_naming
    prefix = naming["prefixes"].get(doc_type, "other-")
    suffix = naming["suffixes"].get(lang, "") if lang else ""

    # prefix đã có dấu '-' ở cuối trong data_naming.json
    parts = [prefix.rstrip("-"), device_slug]
    if suffix:
        parts.append(suffix.lstrip("-"))
    return "-".join(parts) + "." + ext.lstrip(".")


def build_target_path(category: str, group: str, device: str) -> Path:
    """Trả về đường dẫn thư mục đích dựa trên STORAGE_BASE_PATH."""
    base = Path(settings.STORAGE_BASE_PATH)
    return base / slugify(category) / slugify(group) / slugify(device)


def normalize_proposal(
    original_filename: str,
    doc_type: str,
    device_slug: str,
    device_display: str,
    category: str,
    group: str,
    lang: str = "vi",
) -> dict:
    """
    Nhận thông tin AI đề xuất → trả về dict đầy đủ để Bot hiển thị và thực thi.

    Returns:
        {
            "original": "arrieta60.pdf",
            "suggested_filename": "tech-arietta-60-vi.pdf",
            "target_dir": "D:\\MedicalData\\thiet-bi-chan-doan-hinh-anh\\sieu-am\\arietta-60",
            "doc_type": "tech",
            "device": "arietta-60",
            "device_display": "Arietta 60",
            "lang": "vi",
        }
    """
    ext = Path(original_filename).suffix  # .pdf
    suggested = build_filename(doc_type, device_slug, lang, ext)
    target_dir = build_target_path(category, group, device_slug)

    return {
        "original": original_filename,
        "suggested_filename": suggested,
        "target_dir": str(target_dir),
        "doc_type": doc_type,
        "device": device_slug,
        "device_display": device_display,
        "category": category,
        "group": group,
        "lang": lang,
    }
