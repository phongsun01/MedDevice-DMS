"""
MedDevice DMS - Reusable Inline Keyboards
"""
from math import ceil

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main bot menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Tìm kiếm", callback_data="menu:search"),
            InlineKeyboardButton(text="📁 Duyệt hồ sơ", callback_data="menu:browse"),
        ],
        [
            InlineKeyboardButton(text="➕ Thêm thiết bị", callback_data="menu:add"),
            InlineKeyboardButton(text="📊 So sánh", callback_data="menu:compare"),
        ],
        [
            InlineKeyboardButton(text="🌐 Wiki", callback_data="menu:wiki"),
        ],
    ])


def items_keyboard(
    items: list[dict],
    callback_prefix: str,
    id_field: str = "id",
    label_field: str = "name",
    page: int = 0,
    page_size: int = 10,
) -> InlineKeyboardMarkup:
    """Generic paginated keyboard from a list of items."""
    total_pages = max(1, ceil(len(items) / page_size))
    start = page * page_size
    page_items = items[start: start + page_size]

    buttons = []
    for item in page_items:
        buttons.append([InlineKeyboardButton(
            text=str(item.get(label_field, "?")),
            callback_data=f"{callback_prefix}:{item.get(id_field, '')}",
        )])

    # Pagination row
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Trước", callback_data=f"page:{callback_prefix}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Sau ➡️", callback_data=f"page:{callback_prefix}:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="🏠 Menu chính", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def device_actions_keyboard(device_id: str) -> InlineKeyboardMarkup:
    """Actions for a selected device."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 Xem tài liệu", callback_data=f"docs:{device_id}"),
            InlineKeyboardButton(text="🌐 Mở Wiki", callback_data=f"wiki:{device_id}"),
        ],
        [
            InlineKeyboardButton(text="📊 So sánh", callback_data=f"compare_start:{device_id}"),
            InlineKeyboardButton(text="🏠 Menu", callback_data="menu:home"),
        ],
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Yes / No confirmation."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Xác nhận", callback_data="confirm:yes"),
            InlineKeyboardButton(text="❌ Hủy", callback_data="confirm:no"),
        ],
    ])
