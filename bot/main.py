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
    
    from handlers.catalog import router as catalog_router
    dp.include_router(catalog_router)
    
    dp.include_router(search_router)
    
    from handlers.browsing import router as browsing_router
    dp.include_router(browsing_router)
    

    
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
                
                # Set up the menu button for WebApp
                from aiogram.types import MenuButtonWebApp, WebAppInfo
                web_app_url = settings.WEBSITE_URL
                if not web_app_url.startswith("https://"):
                    web_app_url = "https://kinochi-project-alpha.vercel.app/"
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text="🌐 Sayt", web_app=WebAppInfo(url=web_app_url))
                )
                
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
