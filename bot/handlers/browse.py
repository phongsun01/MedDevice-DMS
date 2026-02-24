"""
MedDevice DMS - /start, /list, browse handlers
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from bot.keyboards import main_menu_keyboard, items_keyboard, device_actions_keyboard
from db import client as db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🏥 <b>MedDevice DMS</b>\nHệ thống Quản lý Hồ sơ Thiết bị Y tế\n\nChọn chức năng:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:home")
async def menu_home(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏥 <b>MedDevice DMS</b>\nChọn chức năng:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Browse: Categories → Groups → Devices ---

@router.callback_query(F.data == "menu:browse")
@router.message(Command("list"))
async def browse_categories(event: Message | CallbackQuery):
    results = await db.query("SELECT * FROM category ORDER BY name")
    cats = results if results else []
    kb = items_keyboard(cats, "cat")
    text = "📁 <b>Chọn danh mục</b>:"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("cat:"))
async def browse_groups(callback: CallbackQuery):
    cat_record_id = callback.data.split(":", 1)[1]
    # Rebuild full SurrealDB record ID for querying
    full_cat_id = f"category:{cat_record_id}"
    results = await db.query(
        "SELECT * FROM device_group WHERE category = $cat ORDER BY name",
        {"cat": full_cat_id},
    )
    groups = results if results else []
    kb = items_keyboard(groups, "grp")
    text = f"📂 <b>Nhóm</b> ({len(groups)} nhóm):"
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("grp:"))
async def browse_devices(callback: CallbackQuery):
    grp_record_id = callback.data.split(":", 1)[1]
    full_grp_id = f"device_group:{grp_record_id}"
    results = await db.query(
        "SELECT * FROM device WHERE device_group = $grp ORDER BY name",
        {"grp": full_grp_id},
    )
    devices = results if results else []
    kb = items_keyboard(devices, "dev")
    text = f"📋 <b>Thiết bị</b> ({len(devices)} máy):"
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("dev:"))
async def device_detail(callback: CallbackQuery):
    dev_record_id = callback.data.split(":", 1)[1]
    full_dev_id = f"device:{dev_record_id}"
    from agents.search_agent import get_device_profile
    profile = await get_device_profile(full_dev_id)

    if not profile:
        await callback.answer("Không tìm thấy thiết bị", show_alert=True)
        return

    text = (
        f"🏥 <b>{profile.get('name', '?')}</b>\n"
        f"Model: {profile.get('model', '—')}\n"
        f"Hãng: {profile.get('brand', '—')}\n"
        f"Xuất xứ: {profile.get('origin', '—')}\n"
        f"Tài liệu: {profile.get('total_docs', 0)} file"
    )
    await callback.message.edit_text(
        text,
        reply_markup=device_actions_keyboard(dev_id),
        parse_mode="HTML",
    )
    await callback.answer()
