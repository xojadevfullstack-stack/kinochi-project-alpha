import asyncio
import logging
import os
import sys
import uvicorn
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, "backend", ".env"), override=False)
load_dotenv(os.path.join(PROJECT_ROOT, "bot", ".env"), override=False)

# Ensure python path includes project root, backend, and bot directories
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))
sys.path.append(os.path.join(PROJECT_ROOT, "bot"))

# ── Logging Configuration ──────────────────────────────────────────
def setup_global_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ── Uvicorn API Runner ───────────────────────────────────────────
async def run_api():
    try:
        logging.info("CHECKPOINT 3: run_api() funksiyasiga kirildi")
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        # Custom log config for uvicorn
        log_config = uvicorn.config.LOGGING_CONFIG.copy()
        for formatter in log_config["formatters"].values():
            if "fmt" in formatter:
                formatter["fmt"] = f"[API] {formatter['fmt']}"
        
        config = uvicorn.Config(
            "app.main:app", # The backend directory is in sys.path, so app.main:app should work
            host=host, 
            port=port, 
            log_config=log_config,
            workers=1, # Very important: 1 worker to save memory
            timeout_keep_alive=65,
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        
        logging.info("CHECKPOINT 4: Uvicorn Server.serve() chaqirilmoqda")
        logging.info(f"CHECKPOINT 4b: PORT env = {os.environ.get('PORT')}, kodda ishlatilayotgan port = {port}")
        logging.info(f"CHECKPOINT 4c: Uvicorn log_config berilgan: ha, log_level={config.log_level}")
        logging.info(f"[API] Starting Uvicorn server on {host}:{port}")
        await server.serve()
        logging.info("CHECKPOINT 9: Uvicorn Server.serve() tugadi")
    except Exception:
        logging.error("run_api() ICHIDA XATO:", exc_info=True)
        raise

# ── Bot Supervisor ───────────────────────────────────────────────
MAX_BOT_RESTARTS = int(os.environ.get("MAX_BOT_RESTARTS", "5"))
BOT_RESTART_BASE_DELAY = float(os.environ.get("BOT_RESTART_BASE_DELAY", "2.0"))
BOT_RESTART_MAX_DELAY = float(os.environ.get("BOT_RESTART_MAX_DELAY", "60.0"))

async def supervised_run_bot():
    """
    Supervises run_bot():
    On an exception, logs the traceback and restarts it with exponential backoff
    (limited attempts up to MAX_BOT_RESTARTS). If all attempts are exhausted,
    exits with non-zero exit code so Render restarts the service.
    """
    from bot.main import run_bot
    try:
        from app.core.bot_status import set_bot_alive
    except Exception:
        def set_bot_alive(v): pass

    max_attempts = int(os.environ.get("MAX_BOT_RESTARTS", "5"))
    base_delay = float(os.environ.get("BOT_RESTART_BASE_DELAY", "2.0"))
    max_delay = float(os.environ.get("BOT_RESTART_MAX_DELAY", "60.0"))

    attempts = 0
    delay = base_delay

    while attempts < max_attempts:
        try:
            logging.info(f"[SUPERVISOR] Starting run_bot() (attempt {attempts + 1}/{max_attempts})...")
            set_bot_alive(True)
            await run_bot()
            set_bot_alive(False)
            logging.info("[SUPERVISOR] run_bot() completed normally.")
            return
        except (KeyboardInterrupt, asyncio.CancelledError):
            set_bot_alive(False)
            raise
        except Exception:
            set_bot_alive(False)
            attempts += 1
            logging.error(f"[SUPERVISOR] run_bot() crashed with exception (attempt {attempts}/{max_attempts}):", exc_info=True)
            if attempts >= max_attempts:
                logging.critical(f"[SUPERVISOR] run_bot() failed after {max_attempts} attempts. Exiting non-zero so Render restarts service.")
                sys.exit(1)
                return
            logging.info(f"[SUPERVISOR] Restarting bot in {delay:.1f}s...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)
    sys.exit(1)

# ── Main Entrypoint ──────────────────────────────────────────────
async def main():
    setup_global_logging()
    logging.info("CHECKPOINT 1: run.py main() boshlandi")
    
    # Patch BACKEND_API_URL to use the correct port dynamically if running locally/on Render
    port = os.environ.get("PORT", "8000")
    backend_url = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000/api/v1")
    if "localhost" in backend_url or "127.0.0.1" in backend_url:
        os.environ["BACKEND_API_URL"] = f"http://127.0.0.1:{port}/api/v1"
    
    # Run both concurrently without masking exceptions
    logging.info("CHECKPOINT 2: asyncio.gather(run_api(), supervised_run_bot()) chaqirilmoqda (no return_exceptions masking)")
    await asyncio.gather(
        run_api(),
        supervised_run_bot(),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down cleanly...")
