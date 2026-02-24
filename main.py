"""
MedDevice DMS - Entry Point
Runs in polling mode when WEBHOOK_URL is not configured.
"""
import asyncio
import logging

import structlog
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from db import client as db_client
from bot.middleware import AuthMiddleware

# Handler routers
from bot.handlers.browse import router as browse_router
from bot.handlers.search import router as search_router
from bot.handlers.files import router as files_router
from bot.handlers.compare import router as compare_router
from bot.handlers.wiki import router as wiki_router
from bot.handlers.add import router as add_router
from aiogram.types import BotCommand

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Menu chính"),
        BotCommand(command="search", description="Tìm kiếm thiết bị"),
        BotCommand(command="list", description="Duyệt danh mục"),
        BotCommand(command="compare", description="So sánh thiết bị"),
        BotCommand(command="docs", description="Xem tài liệu thiết bị"),
        BotCommand(command="wiki", description="Mở Outline Wiki"),
        BotCommand(command="add", description="Thêm thiết bị mới"),
    ]
    await bot.set_my_commands(commands)
    structlog.get_logger("bot").info("bot.commands.set")


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def _is_webhook_configured() -> bool:
    """Return True only when a real webhook URL is set."""
    url = settings.WEBHOOK_URL or ""
    return url.startswith("https://") and "your-tunnel" not in url


# ---------------------------------------------------------------------------
# Polling mode (development)
# ---------------------------------------------------------------------------

async def run_polling():
    log = structlog.get_logger("startup")
    log.info("bot.mode", mode="polling")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    dp.include_router(browse_router)
    dp.include_router(search_router)
    dp.include_router(files_router)
    dp.include_router(compare_router)
    dp.include_router(wiki_router)
    dp.include_router(add_router)

    await db_client.connect()
    await db_client.apply_schema()
    await set_commands(bot)

    # Remove any old webhook before polling
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("bot.polling.started")
    await dp.start_polling(bot)


# ---------------------------------------------------------------------------
# Webhook mode (production)
# ---------------------------------------------------------------------------

def create_app() -> web.Application:
    """Build the aiohttp application with aiogram webhook."""
    setup_logging()

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    dp.include_router(browse_router)
    dp.include_router(search_router)
    dp.include_router(files_router)
    dp.include_router(compare_router)
    dp.include_router(wiki_router)
    dp.include_router(add_router)

    async def on_startup(app: web.Application):
        log = structlog.get_logger("startup")
        await db_client.connect()
        await db_client.apply_schema()
        await set_commands(bot)
        webhook_url = f"{settings.WEBHOOK_URL}/webhook"
        await bot.set_webhook(webhook_url)
        log.info("webhook.set", url=webhook_url)

    async def on_shutdown(app: web.Application):
        log = structlog.get_logger("shutdown")
        await bot.delete_webhook()
        await db_client.disconnect()
        log.info("shutdown.complete")

    app = web.Application()
    app["bot"] = bot
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    setup_logging()
    if _is_webhook_configured():
        app = create_app()
        web.run_app(app, host="0.0.0.0", port=8080)
    else:
        structlog.get_logger("startup").info(
            "webhook.not_configured",
            msg="WEBHOOK_URL not set – falling back to polling mode"
        )
        asyncio.run(run_polling())

