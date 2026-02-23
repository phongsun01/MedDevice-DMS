"""
MedDevice DMS - /wiki handler
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import settings

router = Router()


@router.callback_query(F.data == "menu:wiki")
async def wiki_menu(callback: CallbackQuery):
    url = settings.OUTLINE_API_URL.replace("/api", "")
    await callback.message.edit_text(
        f"🌐 <b>Wiki MedDevice DMS</b>\n\n"
        f"🔗 <a href=\"{url}\">Mở Wiki</a>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("wiki"))
async def cmd_wiki(message: Message):
    device_name = message.text.replace("/wiki", "").strip()

    if not device_name:
        url = settings.OUTLINE_API_URL.replace("/api", "")
        await message.answer(f"🌐 Wiki: {url}")
        return

    # Find device and link to Outline page
    from agents.search_agent import search_devices
    results = await search_devices(device_name)

    if not results:
        await message.answer(f"❌ Không tìm thấy thiết bị: {device_name}")
        return

    dev = results[0]
    url = settings.OUTLINE_API_URL.replace("/api", "")
    dev_slug = dev.get("name", "").lower().replace(" ", "-")
    await message.answer(
        f"🌐 <b>{dev.get('name', '?')}</b>\n"
        f"🔗 <a href=\"{url}/doc/{dev_slug}\">Mở trang Wiki</a>",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("wiki:"))
async def cb_wiki(callback: CallbackQuery):
    dev_id = callback.data.split(":", 1)[1]
    url = settings.OUTLINE_API_URL.replace("/api", "")
    await callback.message.answer(f"🌐 Wiki: {url}")
    await callback.answer()
