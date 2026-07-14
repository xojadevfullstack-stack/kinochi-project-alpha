import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.enums import ContentType, ChatMemberStatus

from services.api_client import api_client

logger = logging.getLogger(__name__)

router = Router(name="auto_index")

@router.message(F.chat.type.in_({"supergroup", "group"}), F.content_type.in_({ContentType.VIDEO, ContentType.DOCUMENT}))
async def auto_index_video(message: Message, bot: Bot):
    # 1. Check if the user is an admin
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            return  # Ignore silently
    except Exception as e:
        logger.error(f"Error checking chat member status: {e}")
        return

    topic_id = message.message_thread_id

    # 2. Find Series by source
    series = await api_client.get_series_by_source(chat_id=chat_id, topic_id=topic_id)
    if not series:
        return  # No series linked to this topic

    # 3. Determine the season to add the episode to.
    # Usually, we add to the last season, or the first season if only 1 exists.
    seasons = series.get("seasons", [])
    if not seasons:
        logger.warning(f"Series {series['id']} has no seasons. Cannot auto-index.")
        await message.reply("⚠️ Bu serialga hali mavsum qo'shilmagan, avval admin panelda mavsum yarating.")
        return
        
    import asyncio
    max_retries = 3
    new_episode = None
    new_episode_num = 0

    for attempt in range(max_retries):
        if attempt > 0:
            # Re-fetch series to get the latest episodes list in case another video was inserted
            fresh_series = await api_client.get_series_by_source(chat_id=chat_id, topic_id=topic_id)
            if not fresh_series:
                break
            seasons = fresh_series.get("seasons", [])
            if not seasons:
                break
            latest_season = sorted(seasons, key=lambda s: s["season_number"])[-1]
            season_id = latest_season["id"]
            episodes = latest_season.get("episodes", [])
        
        # 4. Find the last episode number
        if episodes:
            last_episode_num = max(ep.get("episode_number", 0) for ep in episodes)
        else:
            last_episode_num = 0
            
        new_episode_num = last_episode_num + 1

        # 5. Create new episode using client.post directly to inspect status code
        try:
            response = await api_client.client.post(
                f"/series/seasons/{season_id}/episodes",
                json={
                    "season_id": season_id,
                    "episode_number": new_episode_num,
                    "title": message.caption or f"{new_episode_num}-qism"
                }
            )
            
            if response.status_code in (200, 201):
                new_episode = response.json()
                break
            
            # Check if error is due to UNIQUE constraint (IntegrityError -> 500, or 409 Conflict)
            error_text = response.text.lower()
            is_unique_error = response.status_code in (409, 500) or "unique" in error_text or "integrity" in error_text
            
            if is_unique_error:
                logger.warning(f"Duplicate/UNIQUE error for episode {new_episode_num}. Retrying ({attempt+1}/{max_retries})...")
                await asyncio.sleep(1)
                continue
            else:
                logger.error(f"Failed to create episode: {response.status_code} - {response.text}")
                break
                
        except Exception as e:
            logger.error(f"Error making request to create episode: {e}")
            break
    
    if new_episode:
        logger.info(f"Auto-indexed new episode {new_episode_num} for series {series['id']}")
        
        # Link the video to the newly created episode.
        try:
            await api_client.client.post(
                f"/series/episodes/{new_episode['id']}/link-video",
                json={"message_id": message.message_id, "language": "Asosiy"}
            )
            logger.info(f"Linked video {message.message_id} to episode {new_episode['id']}")
            
        except Exception as e:
            logger.error(f"Error linking video to auto-created episode: {e}")
    else:
        logger.error(f"Failed to auto-index episode after {max_retries} retries for series {series['id']}")
        await message.reply("⚠️ Bu video avtomatik indekslanmadi, qo'lda tekshiring.")
