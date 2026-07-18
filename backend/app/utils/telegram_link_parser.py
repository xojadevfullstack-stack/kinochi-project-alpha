import re
from urllib.parse import urlparse, parse_qs

def parse_telegram_link(url: str) -> dict[str, int | str | None]:
    """
    Parses a Telegram web link and extracts chat_id, message_id, and topic_id.
    Converts chat_id to supergroup ID by prepending -100 if it's numeric.
    
    Also accepts raw IDs (e.g. 1990123456 or -1001990123456).
    """
    input_str = url.strip()
    
    # Handle raw ID
    if input_str.startswith("-100") and input_str[4:].isdigit():
        return {"chat_id": int(input_str), "message_id": 0, "topic_id": None}
    elif input_str.isdigit():
        return {"chat_id": int(f"-100{input_str}"), "message_id": 0, "topic_id": None}
        
    parsed_url = urlparse(input_str)
    
    # Check domain
    if parsed_url.netloc not in ("t.me", "telegram.me"):
        raise ValueError("Noto'g'ri Telegram link formati: link yoki kanal ID bo'lishi kerak.")
        
    path = parsed_url.path.strip("/")
    query = parse_qs(parsed_url.query)
    
    parts = path.split("/")
    
    chat_id_str = None
    topic_id_str = None
    message_id_str = None
    
    if path.startswith("c/"):
        # Format: c/<chat_id>/<topic_id>/<message_id>
        if len(parts) == 4:
            _, chat_id_str, topic_id_str, message_id_str = parts
        # Format: c/<chat_id>/<message_id>
        elif len(parts) == 3:
            _, chat_id_str, message_id_str = parts
        # Format: c/<chat_id>
        elif len(parts) == 2:
            _, chat_id_str = parts
            message_id_str = "0"
        else:
            raise ValueError("Noto'g'ri Telegram link formati: noto'g'ri URL segmentlari.")
            
        if not chat_id_str.isdigit():
            raise ValueError("Noto'g'ri Telegram link formati: chat_id raqam bo'lishi kerak.")
    else:
        if len(parts) == 3:
            # Format: <username>/<topic_id>/<message_id>
            chat_id_str, topic_id_str, message_id_str = parts
        elif len(parts) == 2:
            # Format: <username>/<message_id>
            chat_id_str, message_id_str = parts
        else:
            raise ValueError("Noto'g'ri Telegram link formati: link '/c/' bilan boshlanishi kerak yoki ID kiriting.")
            
    # Parse thread parameter if it exists
    if "thread" in query:
        topic_id_str = query["thread"][0]
        
    if chat_id_str and chat_id_str.isdigit():
        chat_id = int(f"-100{chat_id_str}")
    else:
        chat_id = chat_id_str # Keep username as string
        
    message_id = int(message_id_str) if message_id_str and message_id_str.isdigit() else 0
    if topic_id_str and not topic_id_str.isdigit():
        raise ValueError("Noto'g'ri Telegram link formati: topic_id raqam bo'lishi kerak.")
    topic_id = int(topic_id_str) if topic_id_str else None
    
    if not message_id and len(parts) > 2:
         raise ValueError("Noto'g'ri Telegram link formati: message_id raqam bo'lishi kerak.")
         
    return {
        "chat_id": chat_id,
        "message_id": message_id,
        "topic_id": topic_id
    }
