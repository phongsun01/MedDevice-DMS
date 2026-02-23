"""
MedDevice DMS - /add handler with FSM (full conversation)
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states import AddDeviceStates
from bot.keyboards import items_keyboard, confirm_keyboard
from db import client as db

router = Router()


@router.callback_query(F.data == "menu:add")
@router.message(Command("add"))
async def cmd_add(event: Message | CallbackQuery, state: FSMContext):
    results = await db.query("SELECT * FROM category ORDER BY name")
    cats = results[0] if results and results[0] else []

    kb = items_keyboard(cats, "add_cat")
    text = "➕ <b>Thêm thiết bị mới</b>\n\nChọn danh mục:"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")

    await state.set_state(AddDeviceStates.category)


@router.callback_query(F.data.startswith("add_cat:"), AddDeviceStates.category)
async def add_pick_category(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.split(":", 1)[1]
    await state.update_data(category_id=cat_id)

    results = await db.query(
        "SELECT * FROM device_group WHERE category = $cat ORDER BY name",
        {"cat": cat_id},
    )
    groups = results[0] if results and results[0] else []
    kb = items_keyboard(groups, "add_grp")
    await callback.message.edit_text("📂 Chọn nhóm thiết bị:", reply_markup=kb, parse_mode="HTML")
    await state.set_state(AddDeviceStates.device_group)
    await callback.answer()


@router.callback_query(F.data.startswith("add_grp:"), AddDeviceStates.device_group)
async def add_pick_group(callback: CallbackQuery, state: FSMContext):
    grp_id = callback.data.split(":", 1)[1]
    await state.update_data(group_id=grp_id)
    await callback.message.edit_text("📝 Nhập <b>tên thiết bị</b>:", parse_mode="HTML")
    await state.set_state(AddDeviceStates.name)
    await callback.answer()


@router.message(AddDeviceStates.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("📝 Nhập <b>model</b>:", parse_mode="HTML")
    await state.set_state(AddDeviceStates.model)


@router.message(AddDeviceStates.model)
async def add_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text.strip())
    await message.answer("📝 Nhập <b>hãng sản xuất</b>:", parse_mode="HTML")
    await state.set_state(AddDeviceStates.brand)


@router.message(AddDeviceStates.brand)
async def add_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text.strip())
    await message.answer("📝 Nhập <b>xuất xứ</b> (hoặc '-' để bỏ qua):", parse_mode="HTML")
    await state.set_state(AddDeviceStates.origin)


@router.message(AddDeviceStates.origin)
async def add_origin(message: Message, state: FSMContext):
    val = message.text.strip()
    await state.update_data(origin=val if val != "-" else None)
    await message.answer("📝 Nhập <b>năm sản xuất</b> (hoặc '-' để bỏ qua):", parse_mode="HTML")
    await state.set_state(AddDeviceStates.year)


@router.message(AddDeviceStates.year)
async def add_year(message: Message, state: FSMContext):
    val = message.text.strip()
    year = int(val) if val.isdigit() else None
    await state.update_data(year=year)

    data = await state.get_data()
    summary = (
        f"✅ <b>Xác nhận thông tin</b>\n\n"
        f"Tên: <b>{data.get('name')}</b>\n"
        f"Model: {data.get('model')}\n"
        f"Hãng: {data.get('brand')}\n"
        f"Xuất xứ: {data.get('origin', '—')}\n"
        f"Năm SX: {data.get('year', '—')}"
    )
    await message.answer(summary, reply_markup=confirm_keyboard(), parse_mode="HTML")
    await state.set_state(AddDeviceStates.confirm)


@router.callback_query(F.data == "confirm:yes", AddDeviceStates.confirm)
async def add_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    device = await db.create("device", {
        "name": data["name"],
        "model": data["model"],
        "brand": data["brand"],
        "origin": data.get("origin"),
        "year": data.get("year"),
        "device_group": data["group_id"],
    })

    user_id = str(callback.from_user.id) if callback.from_user else None
    await db.create_audit_log("create", "device", str(device.get("id")), user_id)

    # Trigger wiki
    try:
        from agents.wiki_agent import update_device_page
        await update_device_page(device["id"], user_id)
    except Exception:
        pass

    await callback.message.edit_text(
        f"✅ Đã tạo thiết bị: <b>{data['name']}</b>\nID: <code>{device.get('id')}</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "confirm:no", AddDeviceStates.confirm)
async def add_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Đã hủy thêm thiết bị.")
    await callback.answer()
