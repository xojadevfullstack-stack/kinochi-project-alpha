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
from middlewares.ban_check import BanCheckMiddleware
from middlewares.subscription_check import SubscriptionMiddleware
from middlewares.throttling import ThrottlingMiddleware
from services.api_client import api_client

DEFAULT_BOT_LOCK_FILE = os.path.join(BOT_DIR, ".bot.lock")
DEFAULT_BOT_PID_FILE = os.path.join(BOT_DIR, ".bot.pid")

class BotAlreadyRunningError(RuntimeError):
    pass

class BotInstanceLock:
    """Ensures only a single bot polling instance runs at any given time using atomic OS flags."""
    def __init__(self, lock_file: str | None = None, pid_file: str | None = None):
        self.lock_file = lock_file or DEFAULT_BOT_LOCK_FILE
        self.pid_file = pid_file or DEFAULT_BOT_PID_FILE
        self._fd: int | None = None
        self._is_locked = False

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            if sys.platform == "win32":
                import ctypes
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                STILL_ACTIVE = 259
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if not handle:
                    return False
                exit_code = ctypes.c_ulong()
                ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                ctypes.windll.kernel32.CloseHandle(handle)
                return exit_code.value == STILL_ACTIVE
            else:
                os.kill(pid, 0)
                return True
        except Exception:
            return False

    def acquire(self) -> bool:
        # Check for stale lock
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content.isdigit():
                    pid = int(content)
                    if not self._is_pid_alive(pid):
                        try:
                            os.remove(self.lock_file)
                        except Exception:
                            pass
            except Exception:
                pass

        try:
            fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            self._fd = fd
            self._is_locked = True
            current_pid = str(os.getpid())
            os.write(fd, current_pid.encode("utf-8"))
            try:
                with open(self.pid_file, "w", encoding="utf-8") as pf:
                    pf.write(current_pid)
            except Exception:
                pass
            return True
        except (FileExistsError, OSError):
            existing_pid = None
            if os.path.exists(self.lock_file):
                try:
                    with open(self.lock_file, "r", encoding="utf-8") as f:
                        existing_pid = f.read().strip()
                except Exception:
                    pass
            pid_info = f" (PID: {existing_pid})" if existing_pid else ""
            raise BotAlreadyRunningError(
                f"Telegram bot boshqa jarayonda allaqachon ishlayapti{pid_info}. "
                "Ikkita bot bir vaqtda polling qila olmaydi (TelegramConflictError)."
            )

    def release(self):
        if self._is_locked:
            if self._fd is not None:
                try:
                    os.close(self._fd)
                except Exception:
                    pass
                self._fd = None
            self._is_locked = False
            if os.path.exists(self.lock_file):
                try:
                    os.remove(self.lock_file)
                except Exception:
                    pass
            if os.path.exists(self.pid_file):
                try:
                    os.remove(self.pid_file)
                except Exception:
                    pass

async def run_bot():
    logging.info("CHECKPOINT 10: run_bot() funksiyasiga kirildi")
    bot_lock = BotInstanceLock()
    bot_lock.acquire()
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Register Middlewares (Ban check runs first, before subscription and handlers)
    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.inline_query.middleware(BanCheckMiddleware())
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
        bot_lock.release()
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

