import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from config import settings
from handlers.start import router as start_router
from handlers.check_sub import router as check_sub_router
from handlers.search import router as search_router
from handlers.admin_panel import router as admin_panel_router
from handlers.series import router as series_router
from middlewares.subscription_check import SubscriptionMiddleware
from services.api_client import api_client

logging.basicConfig(level=logging.INFO)

# Dummy web server to keep Render happy
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Dummy web server running on port {port}")

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Register Middlewares
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Include routers
    dp.include_router(admin_panel_router)
    dp.include_router(series_router)
    dp.include_router(start_router)
    dp.include_router(check_sub_router)
    dp.include_router(search_router)

    # Start dummy web server in the background
    await start_web_server()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await api_client.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
