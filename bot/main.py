import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from config import settings
from handlers.start import router as start_router
from handlers.check_sub import router as check_sub_router
from handlers.search import router as search_router
from middlewares.subscription_check import SubscriptionMiddleware
from services.api_client import api_client

async def run_bot():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Register Middlewares
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Include routers
    dp.include_router(start_router)
    dp.include_router(check_sub_router)
    dp.include_router(search_router)
    
    from handlers.episode import router as episode_router
    dp.include_router(episode_router)
    
    from handlers.translation_callback import router as translation_router
    dp.include_router(translation_router)

    retry_delay = 5
    max_delay = 60

    try:
        while True:
            try:
                logging.info("[BOT] Starting Telegram bot polling...")
                await bot.delete_webhook(drop_pending_updates=True)
                await dp.start_polling(bot)
            except Exception as e:
                logging.error(f"[BOT] Polling failed: {e}")
                logging.info(f"[BOT] Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                retry_delay = min(retry_delay * 2, max_delay)
    finally:
        await api_client.close()
        await bot.session.close()
