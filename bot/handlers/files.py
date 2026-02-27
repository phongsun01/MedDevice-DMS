"""
MedDevice DMS — File Upload Handler (v2.3.0)
Option A: AI phân loại → Inline Keyboard xác nhận → Execute
Option B: Upload trực tiếp (cũ)
"""
import os
import tempfile
import json
import aiohttp

from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command

from agents.search_agent import get_device_profile
from db import client as db
from config import settings

router = Router()

API_BASE = "http://127.0.0.1:8081"

# Lưu trạng thái phân loại đang chờ xác nhận (in-memory, đủ dùng cho 1 node)
_pending: dict[str, dict] = {}  # key = f"{user_id}_{filename}"


# ─── /docs <device_name> ─────────────────────────────────────────────────────

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


# ─── /get <doc_id> ───────────────────────────────────────────────────────────

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


# ─── File Upload (Option A: AI classify + confirm) ───────────────────────────

@router.message(F.document)
async def handle_file_upload(message: Message, bot: Bot):
    """
    Option A (AGENT_MODE=A): Gọi /api/classify_file → hỏi xác nhận.
    Option B (AGENT_MODE=B): Xử lý cũ — parse_agent trực tiếp.
    """
    file = message.document
    caption = (message.caption or "").strip()

    # Download file về tmp
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.file_name)
    await bot.download(file, tmp_path)

    if settings.AGENT_MODE == "A":
        await _handle_upload_option_a(message, file.file_name, tmp_path)
    else:
        await _handle_upload_option_b(message, file.file_name, tmp_path, caption)


async def _handle_upload_option_a(message: Message, filename: str, tmp_path: str):
    """Gọi API classify, lưu pending state, gửi Inline Keyboard."""
    status_msg = await message.answer(f"🤖 Đang phân tích <b>{filename}</b>...", parse_mode="HTML")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/api/classify_file",
                json={"filename": filename},
                timeout=aiohttp.ClientTimeout(total=90)  # gemini-cli cần tới 45s+
            ) as resp:
                result = await resp.json()
    except aiohttp.ServerTimeoutError:
        await status_msg.edit_text("⏱️ Phân tích quá lâu (>90s). Thử lại hoặc dùng caption để chỉ định thiết bị.")
        return
    except Exception as e:
        await status_msg.edit_text(f"❌ Lỗi kết nối API: {e}")
        return

    if result.get("error"):
        await status_msg.edit_text(
            f"⚠️ Không phân loại được: {result['error']}\n"
            f"Bạn có thể nhắn tên thiết bị/loại tài liệu để tôi thử lại."
        )
        return

    # Lưu pending state
    pending_key = f"{message.from_user.id}_{filename}"
    _pending[pending_key] = {
        "tmp_path": tmp_path,
        "filename": filename,
        "proposal": result,
        "user_id": message.from_user.id,
        "session_id": str(message.from_user.id),
    }

    await _send_confirm_keyboard(message, result, pending_key, edit_msg=status_msg)


def _build_confirm_keyboard(pending_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Xác nhận", callback_data=f"classify_confirm:{pending_key}"),
            InlineKeyboardButton(text="✏️ Sửa loại", callback_data=f"classify_edit_type:{pending_key}"),
            InlineKeyboardButton(text="❌ Huỷ", callback_data=f"classify_cancel:{pending_key}"),
        ]
    ])


async def _send_confirm_keyboard(message: Message, proposal: dict, pending_key: str, edit_msg=None):
    confidence = proposal.get("confidence", 0)
    conf_bar = "🟢" if confidence >= 0.8 else ("🟡" if confidence >= 0.5 else "🔴")

    text = (
        f"📁 <b>Đề xuất phân loại:</b>\n\n"
        f"  Tên mới: <code>{proposal['suggested_filename']}</code>\n"
        f"  Thiết bị: {proposal.get('device_display', proposal.get('device', '?'))}\n"
        f"  Thư mục: <code>{proposal.get('group', '?')}/{proposal.get('device', '?')}/</code>\n"
        f"  Loại: <b>{proposal.get('doc_type', '?')}</b> | Ngôn ngữ: {proposal.get('lang', '?')}\n"
        f"  Độ tin cậy: {conf_bar} {int(confidence * 100)}%\n\n"
        f"  <i>{proposal.get('reason', '')}</i>"
    )
    kb = _build_confirm_keyboard(pending_key)
    if edit_msg:
        await edit_msg.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


# ─── Callbacks: Xác nhận / Sửa / Huỷ ────────────────────────────────────────

@router.callback_query(F.data.startswith("classify_confirm:"))
async def cb_classify_confirm(callback: CallbackQuery):
    pending_key = callback.data.split(":", 1)[1]
    pending = _pending.get(pending_key)
    if not pending:
        await callback.answer("❌ Yêu cầu đã hết hạn.", show_alert=True)
        return
    await callback.message.edit_text("⏳ Đang thực thi...", reply_markup=None)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/api/execute_task",
                json={
                    "tmp_path": pending["tmp_path"],
                    "target_dir": pending["proposal"]["target_dir"],
                    "suggested_filename": pending["proposal"]["suggested_filename"],
                    "device": pending["proposal"]["device"],
                    "session_id": pending["session_id"],
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                result = await resp.json()
        if result.get("success"):
            await callback.message.edit_text(
                f"✅ <b>Hoàn tất!</b>\n\n"
                f"  File: <code>{pending['proposal']['suggested_filename']}</code>\n"
                f"  Thư mục: <code>{pending['proposal'].get('group', '?')}/{pending['proposal'].get('device', '?')}/</code>\n"
                f"  DB: +{result.get('docs_added', 0)} docs",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(f"❌ Lỗi thực thi: {result.get('error', 'Unknown')}")
    except Exception as e:
        await callback.message.edit_text(f"❌ Lỗi kết nối: {e}")
    finally:
        _pending.pop(pending_key, None)
    await callback.answer()


@router.callback_query(F.data.startswith("classify_edit_type:"))
async def cb_classify_edit_type(callback: CallbackQuery):
    """Hiển thị các loại tài liệu để user chọn lại."""
    pending_key = callback.data.split(":", 1)[1]
    pending = _pending.get(pending_key)
    if not pending:
        await callback.answer("❌ Yêu cầu đã hết hạn.", show_alert=True)
        return

    doc_types = [
        ("📋 Kỹ thuật (tech)", "tech"),
        ("⚙️ Cấu hình (config)", "config"),
        ("💰 Báo giá (price)", "price"),
        ("📝 Hợp đồng (contract)", "contract"),
        ("📎 Khác (other)", "other"),
    ]
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"set_type:{pending_key}:{code}")]
        for label, code in doc_types
    ]
    buttons.append([InlineKeyboardButton(text="← Quay lại", callback_data=f"classify_back:{pending_key}")])
    await callback.message.edit_text(
        "✏️ Chọn loại tài liệu:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_type:"))
async def cb_set_type(callback: CallbackQuery):
    _, pending_key, new_type = callback.data.split(":", 2)
    pending = _pending.get(pending_key)
    if not pending:
        await callback.answer("❌ Yêu cầu đã hết hạn.", show_alert=True)
        return

    # Cập nhật doc_type và tái tạo suggested_filename
    from agents.normalize_agent import normalize_proposal
    proposal = pending["proposal"]
    updated = normalize_proposal(
        original_filename=proposal["original"],
        doc_type=new_type,
        device_slug=proposal["device"],
        device_display=proposal.get("device_display", proposal["device"]),
        category=proposal["category"],
        group=proposal["group"],
        lang=proposal.get("lang", "vi"),
    )
    updated["confidence"] = proposal.get("confidence", 0)
    updated["reason"] = f"Người dùng chọn loại: {new_type}"
    pending["proposal"] = updated
    _pending[pending_key] = pending

    await _send_confirm_keyboard(callback.message, updated, pending_key, edit_msg=callback.message)
    await callback.answer(f"✅ Đã cập nhật loại: {new_type}")


@router.callback_query(F.data.startswith("classify_cancel:"))
async def cb_classify_cancel(callback: CallbackQuery):
    pending_key = callback.data.split(":", 1)[1]
    pending = _pending.pop(pending_key, None)
    filename = pending["filename"] if pending else "file"
    await callback.message.edit_text(f"❌ Đã huỷ phân loại <b>{filename}</b>.", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("classify_back:"))
async def cb_classify_back(callback: CallbackQuery):
    pending_key = callback.data.split(":", 1)[1]
    pending = _pending.get(pending_key)
    if not pending:
        await callback.answer("❌ Yêu cầu đã hết hạn.", show_alert=True)
        return
    await _send_confirm_keyboard(callback.message, pending["proposal"], pending_key, edit_msg=callback.message)
    await callback.answer()


# ─── Option B: Upload trực tiếp (fallback cũ) ────────────────────────────────

async def _handle_upload_option_b(message: Message, filename: str, tmp_path: str, caption: str):
    from agents.parse_agent import process_upload
    from agents.search_agent import search_devices

    parts = [p.strip() for p in caption.split("|")] if "|" in caption else [caption.strip()]
    device_name = parts[1] if len(parts) >= 2 else parts[0]

    if not device_name:
        await message.answer(
            "⚠️ Vui lòng gửi file kèm caption:\n"
            "<code>type|tên_thiết_bị</code>",
            parse_mode="HTML",
        )
        return

    devices = await search_devices(device_name)
    if not devices:
        await message.answer(f"❌ Không tìm thấy thiết bị: {device_name}")
        return

    device_id = devices[0]["id"]
    user_id = str(message.from_user.id) if message.from_user else None
    try:
        doc = await process_upload(tmp_path, device_id, caption, user_id)
        await message.answer(
            f"✅ Đã lưu: <b>{filename}</b>\n"
            f"Loại: {doc.get('doc_type', '?')} | Thiết bị: {devices[0].get('name', '?')}",
            parse_mode="HTML",
        )
    except Exception as exc:
        await message.answer(f"❌ Lỗi upload: {exc}")
