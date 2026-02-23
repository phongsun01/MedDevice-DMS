"""
MedDevice DMS - /compare handler with FSM
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states import CompareStates
from agents.compare_agent import compare_handler

import os

router = Router()


@router.callback_query(F.data == "menu:compare")
async def compare_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📊 Nhập tên thiết bị thứ <b>nhất</b>:", parse_mode="HTML")
    await state.set_state(CompareStates.device_a)
    await callback.answer()


@router.message(Command("compare"))
async def cmd_compare(message: Message, state: FSMContext):
    args = message.text.replace("/compare", "").strip()
    if not args:
        await message.answer("📊 Nhập tên thiết bị thứ <b>nhất</b>:", parse_mode="HTML")
        await state.set_state(CompareStates.device_a)
        return

    # Try to parse inline: /compare "A" "B"
    parts = [p.strip().strip('"').strip("'") for p in args.split('" "')]
    if len(parts) == 2:
        await _run_compare(message, parts[0], parts[1])
    else:
        await state.update_data(device_a=args)
        await message.answer("📊 Nhập tên thiết bị thứ <b>hai</b>:", parse_mode="HTML")
        await state.set_state(CompareStates.device_b)


@router.message(CompareStates.device_a)
async def compare_set_a(message: Message, state: FSMContext):
    await state.update_data(device_a=message.text.strip())
    await message.answer("📊 Nhập tên thiết bị thứ <b>hai</b>:", parse_mode="HTML")
    await state.set_state(CompareStates.device_b)


@router.message(CompareStates.device_b)
async def compare_set_b(message: Message, state: FSMContext):
    data = await state.get_data()
    device_a = data.get("device_a", "")
    device_b = message.text.strip()
    await state.clear()
    await _run_compare(message, device_a, device_b)


async def _run_compare(message: Message, name_a: str, name_b: str):
    await message.answer("⏳ Đang so sánh...")
    user_id = str(message.from_user.id) if message.from_user else None
    md_text, xlsx_path = await compare_handler(name_a, name_b, user_id)

    await message.answer(f"<pre>{md_text}</pre>", parse_mode="HTML")

    if xlsx_path and os.path.exists(xlsx_path):
        await message.answer_document(FSInputFile(xlsx_path))
