"""
MedDevice DMS - Auth Middleware
Restricts bot access to allowed Telegram users only.
"""
import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

from config import settings

log = structlog.get_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Block unauthorized users. Log rejected attempts."""

    async def __call__(self, handler, event: Update, data: dict):
        user_id: int | None = None

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        allowed = settings.allowed_user_ids

        if allowed and user_id not in allowed:
            log.warning("auth.rejected", user_id=user_id)
            if isinstance(event, Message):
                await event.answer("⛔ Bạn không có quyền sử dụng bot này.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Không có quyền.", show_alert=True)
            return

        return await handler(event, data)
