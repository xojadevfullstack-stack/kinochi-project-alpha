_bot_alive: bool = False

def set_bot_alive(alive: bool) -> None:
    """Sets the current health/alive status of the Telegram bot."""
    global _bot_alive
    _bot_alive = bool(alive)

def is_bot_alive() -> bool:
    """Returns True if the bot is currently alive and polling."""
    return _bot_alive
