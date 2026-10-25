import asyncio
import logging
import os
import sys

# Ensure backend and bot directories are in sys.path
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BOT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from aiogram import Bot, Dispatcher
from config import settings
from handlers.start import router as start_router
from handlers.check_sub import router as check_sub_router
from handlers.search import router as search_router
from middlewares.subscription_check import SubscriptionMiddleware
from middlewares.throttling import ThrottlingMiddleware
from services.api_client import api_client

async def run_bot():
    logging.info("CHECKPOINT 10: run_bot() funksiyasiga kirildi")
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
    
    from handlers.reviews import router as reviews_router
    dp.include_router(reviews_router)

    dp.include_router(search_router)
    
    from handlers.browsing import router as browsing_router
    dp.include_router(browsing_router)
    
    # Apply rate limiting globally to messages, callbacks, and inline queries
    throttler = ThrottlingMiddleware()
    dp.message.middleware(throttler)
    dp.callback_query.middleware(throttler)
    dp.inline_query.middleware(throttler)
    

    
    from handlers.episode import router as episode_router
    dp.include_router(episode_router)
    
    from handlers.translation_callback import router as translation_router
    dp.include_router(translation_router)
    
    from handlers.auto_index import router as auto_index_router
    dp.include_router(auto_index_router)
    
    from handlers.trailer import router as trailer_router
    dp.include_router(trailer_router)
    
    from handlers.history import router as history_router
    dp.include_router(history_router)
    
    from handlers.recommendation import router as recommendation_router
    dp.include_router(recommendation_router)
    
    from handlers.profile import router as profile_router
    dp.include_router(profile_router)

    from handlers.reports import router as reports_router
    dp.include_router(reports_router)
    

    try:
        # Set up the menu button for WebApp
        from aiogram.types import MenuButtonWebApp, WebAppInfo
        web_app_url = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app/").rstrip("/") + "/"
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="🌐 Sayt", web_app=WebAppInfo(url=web_app_url))
            )
        except Exception as e:
            logging.warning(f"[BOT] Could not set chat menu button: {e}")
        
        # Log pending update count at startup
        try:
            webhook_info = await bot.get_webhook_info()
            pending_count = getattr(webhook_info, "pending_update_count", 0)
            logging.info(f"[BOT] Startup pending update count: {pending_count}")
        except Exception as e:
            logging.warning(f"[BOT] Could not fetch pending update count: {e}")

        # Configurable drop_pending_updates (default False)
        env_val = os.environ.get("BOT_DROP_PENDING_UPDATES")
        if env_val is not None:
            drop_pending = env_val.lower() in ("true", "1", "yes")
        else:
            drop_pending = getattr(settings, "BOT_DROP_PENDING_UPDATES", False)
        logging.info(f"CHECKPOINT 11: bot.delete_webhook(drop_pending_updates={drop_pending}) chaqirilmoqda")
        await bot.delete_webhook(drop_pending_updates=drop_pending)

        logging.info("CHECKPOINT 12: dp.start_polling(bot) chaqirilmoqda")
        try:
            from app.core.bot_status import set_bot_alive
            set_bot_alive(True)
        except Exception:
            pass

        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        logging.info("CHECKPOINT 13: dp.start_polling(bot) tugadi")
    finally:
        try:
            from app.core.bot_status import set_bot_alive
            set_bot_alive(False)
        except Exception:
            pass
        await api_client.close()
        await bot.session.close()

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")

