import logging
import uuid
from aiogram import Router, F, Bot
from aiogram.types import Message
from config import settings
from services.api_client import api_client

router = Router()
logger = logging.getLogger(__name__)

async def process_video(message: Message, bot: Bot):
    chat_id = message.chat.id
    topic_id = message.message_thread_id
    
    # 1. Look up Series by source
    try:
        url = f"/series/by-source?chat_id={chat_id}"
        if topic_id:
            url += f"&topic_id={topic_id}"
        resp = await api_client.client.get(url)
        if resp.status_code == 404:
            return
        resp.raise_for_status()
        series = resp.json()
    except Exception as e:
        # Not a registered source, ignore
        return

    # 2. Get or create Season
    seasons = series.get("seasons", [])
    if not seasons:
        try:
            resp = await api_client.client.post(f"/series/{series['id']}/seasons", json={
                "series_id": series['id'],
                "season_number": 1,
                "title": "Mavsum 1"
            })
            resp.raise_for_status()
            season = resp.json()
            seasons = [season]
        except Exception as e:
            logger.error(f"Error creating season: {e}")
            return
    
    # Use the last season (assuming sequential uploads)
    season = seasons[-1]

    # 3. Get Episode number
    try:
        resp = await api_client.client.get(f"/series/seasons/{season['id']}/episodes")
        resp.raise_for_status()
        episodes = resp.json()
        ep_num = len(episodes) + 1
    except Exception as e:
        logger.error(f"Error fetching episodes: {e}")
        return

    storage_channel_id = settings.STORAGE_CHANNEL_ID
    if not storage_channel_id:
        logger.warning("STORAGE_CHANNEL_ID is not set. Cannot index.")
        return

    # 4. Check if it's the first episode
    is_first_series_ep = (len(seasons) == 1 and ep_num == 1)
    is_first_season_ep = (ep_num == 1)

    try:
        if is_first_series_ep:
            title_str = series.get('title') or "Noma'lum"
            caption = f"🎬 *{title_str}*\n\n"
            if series.get('description'):
                caption += f"{series.get('description')}\n"
            
            poster_url = series.get('poster_url')
            if poster_url:
                await bot.send_photo(storage_channel_id, photo=poster_url, caption=caption, parse_mode="Markdown")
            else:
                await bot.send_message(storage_channel_id, text=caption, parse_mode="Markdown")
        elif is_first_season_ep:
            season_title = season.get('title') or f"{season.get('season_number', 1)}-mavsum"
            await bot.send_message(storage_channel_id, text=f"📺 *{season_title}*", parse_mode="Markdown")
            
        # 5. Copy video to storage
        msg = await bot.copy_message(storage_channel_id, from_chat_id=chat_id, message_id=message.message_id)
        storage_msg_id = msg.message_id
        
        # 6. Create Episode
        code = str(uuid.uuid4())[:8]
        resp = await api_client.client.post(f"/series/seasons/{season['id']}/episodes", json={
            "season_id": season['id'],
            "episode_number": ep_num,
            "title": f"{ep_num}-qism",
            "code": code
        })
        resp.raise_for_status()
        episode = resp.json()

        # 7. Link video
        resp = await api_client.client.post(f"/series/episodes/{episode['id']}/link-video", json={
            "message_id": storage_msg_id,
            "language": "Asosiy"
        })
        resp.raise_for_status()
        
        # Optionally, reply to the admin in the source chat
        await message.reply(f"✅ {ep_num}-qism saqlandi va indekslandi. Kod: `{code}`", parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in auto_index process: {e}")
        await message.reply(f"❌ Xatolik yuz berdi: {e}")

@router.message(F.video)
async def auto_index_message(message: Message, bot: Bot):
    await process_video(message, bot)

@router.channel_post(F.video)
async def auto_index_channel(message: Message, bot: Bot):
    await process_video(message, bot)
