import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import database as db
from config import (
    BOT_TOKEN,
    WEBHOOK_BASE_URL,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
    PORT,
)
from handlers import user, admin

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(admin.router)
dp.include_router(user.router)


async def on_startup(app: web.Application):
    await db.init_pool()
    if WEBHOOK_BASE_URL:
        url = WEBHOOK_BASE_URL.rstrip("/") + WEBHOOK_PATH
        await bot.set_webhook(url, secret_token=WEBHOOK_SECRET, drop_pending_updates=True)
        logging.info("Webhook set to %s", url)
    else:
        logging.warning(
            "WEBHOOK_BASE_URL/RENDER_EXTERNAL_URL not set — webhook was NOT configured."
        )


async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    await bot.session.close()


async def health(request: web.Request):
    return web.Response(text="ok")


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health)

    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(
        app, path=WEBHOOK_PATH
    )
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=PORT)
