"""
MedDevice DMS - /search handler
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from agents.search_agent import search_documents, format_search_results_telegram

router = Router()


@router.callback_query(F.data == "menu:search")
async def search_prompt(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 Nhập từ khóa tìm kiếm:\n<i>Ví dụ: liều lượng bức xạ</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("search"))
async def cmd_search(message: Message):
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.answer("🔍 Dùng: <code>/search từ khóa</code>", parse_mode="HTML")
        return
    await _do_search(message, query)


async def _do_search(message: Message, query: str):
    await message.answer("⏳ Đang tìm kiếm...")
    results = await search_documents(query)
    text = format_search_results_telegram(results)
    await message.answer(text, parse_mode="HTML")
