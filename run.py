import asyncio
import logging
import os
import sys
import uvicorn
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, "backend", ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, "bot", ".env"))

# Ensure python path includes backend and bot directories
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))
sys.path.append(os.path.join(PROJECT_ROOT, "bot"))

# ── Logging Configuration ──────────────────────────────────────────
def setup_global_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ── Uvicorn API Runner ───────────────────────────────────────────
async def run_api():
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
        timeout_keep_alive=65
    )
    server = uvicorn.Server(config)
    
    logging.info(f"[API] Starting Uvicorn server on {host}:{port}")
    await server.serve()

# ── Main Entrypoint ──────────────────────────────────────────────
async def main():
    setup_global_logging()
    
    # Lazy import to avoid import errors before sys.path is set
    from bot.main import run_bot
    
    # Run both concurrently
    # return_exceptions=True prevents one crashing from killing the other
    results = await asyncio.gather(
        run_api(),
        run_bot(),
        return_exceptions=True
    )
    
    # Handle results in case they return (which they shouldn't unless crashed)
    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Process crashed: {result}", exc_info=result)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down cleanly...")
