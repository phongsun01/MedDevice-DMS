"""
MedDevice DMS - File upload and /get, /docs handlers
"""
import os
import tempfile

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from agents.parse_agent import process_upload
from agents.search_agent import get_device_profile
from db import client as db

router = Router()


# --- /docs <device_name> ---

@router.message(Command("docs"))
async def cmd_docs(message: Message):
    device_name = message.text.replace("/docs", "").strip()
    if not device_name:
        await message.answer("📄 Dùng: <code>/docs tên thiết bị</code>", parse_mode="HTML")
        return
    await _show_docs(message, device_name)


@router.callback_query(F.data.startswith("docs:"))
async def cb_docs(callback: CallbackQuery):
    dev_id = callback.data.split(":", 1)[1]
    profile = await get_device_profile(dev_id)
    if not profile:
        await callback.answer("Không tìm thấy", show_alert=True)
        return
    await _render_docs(callback.message, profile)
    await callback.answer()


async def _show_docs(message: Message, device_name: str):
    from agents.search_agent import search_devices
    results = await search_devices(device_name)
    if not results:
        await message.answer(f"❌ Không tìm thấy thiết bị: {device_name}")
        return
    profile = await get_device_profile(results[0]["id"])
    await _render_docs(message, profile)


async def _render_docs(message: Message, profile: dict):
    name = profile.get("name", "?")
    docs = profile.get("documents", {})
    lines = [f"📄 <b>Tài liệu: {name}</b>\n"]

    type_icons = {"technical": "📋", "config": "⚙️", "price": "💰",
                  "contract": "📝", "comparison": "📊", "link": "🔗", "other": "📎"}

    for doc_type, doc_list in docs.items():
        icon = type_icons.get(doc_type, "📄")
        lines.append(f"\n{icon} <b>{doc_type.capitalize()}</b>")
        for doc in doc_list:
            title = doc.get("metadata", {}).get("title", "file")
            sub = f" ({doc.get('sub_type')})" if doc.get("sub_type") else ""
            doc_id = doc.get("id", "")
            lines.append(f"  • {title}{sub}\n    /get_{doc_id.split(':')[-1] if ':' in str(doc_id) else doc_id}")

    if not docs:
        lines.append("  <i>Chưa có tài liệu nào.</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# --- /get <doc_id> ---

@router.message(Command("get"))
async def cmd_get(message: Message):
    doc_id_raw = message.text.replace("/get", "").strip().lstrip("_")
    if not doc_id_raw:
        await message.answer("📥 Dùng: <code>/get doc_id</code>", parse_mode="HTML")
        return

    doc_id = f"document:{doc_id_raw}" if ":" not in doc_id_raw else doc_id_raw
    results = await db.query("SELECT * FROM document WHERE id = $id", {"id": doc_id})
    docs = results[0] if results and results[0] else []

    if not docs:
        await message.answer("❌ Không tìm thấy tài liệu.")
        return

    doc = docs[0] if isinstance(docs, list) else docs
    file_path = doc.get("file_path", "")

    if file_path and os.path.exists(file_path):
        await message.answer_document(FSInputFile(file_path))
    elif doc.get("file_url"):
        await message.answer(f"🔗 Link: {doc['file_url']}")
    else:
        await message.answer("⚠️ File không tồn tại trên server.")


# --- File upload ---

@router.message(F.document)
async def handle_file_upload(message: Message, bot: Bot):
    """Handle file upload. Expects caption: type|device_name|sub_type (or just device name)."""
    caption = message.caption or ""
    file = message.document

    # Download to temp
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.file_name)
    await bot.download(file, tmp_path)

    # Parse caption to find device
    parts = [p.strip() for p in caption.split("|")] if "|" in caption else [caption.strip()]
    device_name = parts[1] if len(parts) >= 2 else parts[0]

    if not device_name:
        await message.answer(
            "⚠️ Vui lòng gửi file kèm caption:\n"
            "<code>type|tên_thiết_bị|sub_type</code>\n"
            "hoặc chỉ cần <code>tên_thiết_bị</code>",
            parse_mode="HTML",
        )
        return

    # Find device
    from agents.search_agent import search_devices
    devices = await search_devices(device_name)
    if not devices:
        await message.answer(f"❌ Không tìm thấy thiết bị: {device_name}")
        return

    device_id = devices[0]["id"]
    user_id = str(message.from_user.id) if message.from_user else None

    try:
        doc = await process_upload(tmp_path, device_id, caption, user_id)
        await message.answer(
            f"✅ Đã lưu: <b>{file.file_name}</b>\n"
            f"Loại: {doc.get('doc_type', '?')} | Thiết bị: {devices[0].get('name', '?')}",
            parse_mode="HTML",
        )
    except Exception as exc:
        await message.answer(f"❌ Lỗi upload: {exc}")
