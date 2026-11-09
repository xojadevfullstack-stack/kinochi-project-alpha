import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("scraper"))
import config
from telethon_moderator_pipeline import create_telethon_client

async def main():
    client = create_telethon_client()
    await client.connect()
    msg_ids = [2654, 2655, 2656, 2657, 2658, 2659]
    msgs = await client.get_messages(config.STORAGE_CHANNEL_ID, ids=msg_ids)
    for m in msgs:
        if m:
            fname = getattr(getattr(m, "file", None), "name", None)
            size_mb = (getattr(getattr(m, "file", None), "size", 0) or 0) / (1024*1024)
            dur = 0
            if getattr(m, "document", None) and hasattr(m.document, "attributes"):
                for a in m.document.attributes:
                    if hasattr(a, "duration"):
                        dur = int(a.duration)
            cap = (m.text or "").replace("\n", " ")[:60]
            print(f"Msg {m.id}: file='{fname}' | dur={dur//60}:{dur%60:02d} | size={size_mb:.1f}MB | text='{cap}'")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
