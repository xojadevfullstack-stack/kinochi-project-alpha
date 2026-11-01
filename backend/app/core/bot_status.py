_bot_alive: bool = False
_bot_status: str = "stopped"  # "alive", "degraded", "stopped"


def set_bot_alive(alive: bool) -> None:
    """Sets the current health/alive status of the Telegram bot."""
    global _bot_alive, _bot_status
    _bot_alive = bool(alive)
    if alive:
        _bot_status = "alive"
    elif _bot_status != "degraded":
        _bot_status = "stopped"


def set_bot_status(status_str: str) -> None:
    """Sets the explicit bot status string (e.g. 'alive', 'degraded', 'stopped')."""
    global _bot_status, _bot_alive
    _bot_status = str(status_str)
    if _bot_status == "alive":
        _bot_alive = True
    else:
        _bot_alive = False


def get_bot_status() -> str:
    """Returns the current bot status string."""
    return _bot_status


def is_bot_alive() -> bool:
    """Returns True if the bot is currently alive and polling."""
    return _bot_alive
