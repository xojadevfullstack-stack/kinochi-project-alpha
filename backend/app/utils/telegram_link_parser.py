import re
from urllib.parse import urlparse, parse_qs

def parse_telegram_link(url: str) -> dict[str, int | None]:
    """
    Parses a Telegram web link and extracts chat_id, message_id, and topic_id.
    Converts chat_id to supergroup ID by prepending -100.
    
    Supported formats:
    - https://t.me/c/1234567890/123 -> chat: -1001234567890, msg: 123, topic: None
    - https://t.me/c/1234567890/123?thread=45 -> chat: -1001234567890, topic: 45, msg: 123
    - https://t.me/c/1990123456/152/155 -> chat: -1001990123456, topic: 152, msg: 155
    
    Raises:
        ValueError: If the link is not a valid Telegram supergroup link.
    """
    parsed_url = urlparse(url)
    
    # Check domain
    if parsed_url.netloc not in ("t.me", "telegram.me"):
        raise ValueError("Noto'g'ri Telegram link formati: domain 't.me' emas.")
        
    path = parsed_url.path.strip("/")
    
    # Needs to start with c/ for private groups/supergroups
    if not path.startswith("c/"):
        raise ValueError("Noto'g'ri Telegram link formati: link '/c/' bilan boshlanishi kerak.")
        
    parts = path.split("/")
    
    # Base extraction variables
    chat_id_str = None
    topic_id_str = None
    message_id_str = None
    
    # Format: c/<chat_id>/<topic_id>/<message_id>
    if len(parts) == 4:
        _, chat_id_str, topic_id_str, message_id_str = parts
    # Format: c/<chat_id>/<message_id>
    elif len(parts) == 3:
        _, chat_id_str, message_id_str = parts
        # Check query string for thread
        query = parse_qs(parsed_url.query)
        if "thread" in query:
            topic_id_str = query["thread"][0]
    else:
        raise ValueError("Noto'g'ri Telegram link formati: noto'g'ri URL segmentlari.")
        
    if not chat_id_str.isdigit():
        raise ValueError("Noto'g'ri Telegram link formati: chat_id raqam bo'lishi kerak.")
    if not message_id_str.isdigit():
        raise ValueError("Noto'g'ri Telegram link formati: message_id raqam bo'lishi kerak.")
    if topic_id_str is not None and not topic_id_str.isdigit():
        raise ValueError("Noto'g'ri Telegram link formati: topic_id raqam bo'lishi kerak.")
        
    chat_id = int(f"-100{chat_id_str}")
    message_id = int(message_id_str)
    topic_id = int(topic_id_str) if topic_id_str else None
    
    return {
        "chat_id": chat_id,
        "message_id": message_id,
        "topic_id": topic_id
    }
