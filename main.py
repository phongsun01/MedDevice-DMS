"""
MedDevice DMS - Entry Point
Telegram Bot webhook server with SurrealDB connection.
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


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

async def on_startup(app: web.Application):
    """Connect to SurrealDB and apply schema on startup."""
    log = structlog.get_logger("startup")
    await db_client.connect()
    await db_client.apply_schema()

    bot: Bot = app["bot"]
    webhook_url = f"{settings.WEBHOOK_URL}/webhook"
    await bot.set_webhook(webhook_url)
    log.info("webhook.set", url=webhook_url)


async def on_shutdown(app: web.Application):
    """Cleanup on shutdown."""
    log = structlog.get_logger("shutdown")
    bot: Bot = app["bot"]
    await bot.delete_webhook()
    await db_client.disconnect()
    log.info("shutdown.complete")


def create_app() -> web.Application:
    """Build the aiohttp application with aiogram webhook."""
    setup_logging()

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Register middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register routers
    dp.include_router(browse_router)
    dp.include_router(search_router)
    dp.include_router(files_router)
    dp.include_router(compare_router)
    dp.include_router(wiki_router)
    dp.include_router(add_router)

    # aiohttp app
    app = web.Application()
    app["bot"] = bot
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Webhook handler
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8080)
