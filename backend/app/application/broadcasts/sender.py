import asyncio
import logging
from app.domain.broadcasts.repository import IBroadcastRepository
from app.domain.broadcasts.entities import BroadcastStatus
from app.domain.users.repository import IUserRepository
from app.infrastructure.telegram.telegram_client import telegram_client

logger = logging.getLogger(__name__)

async def process_broadcast(
    broadcast_id: int, 
    message_text: str, 
    broadcast_repo: IBroadcastRepository, 
    user_repo: IUserRepository
):
    """
    Background task to send a broadcast message to all active users.
    Implements rate limiting (20 msg/sec max, safe pauses).
    """
    logger.info(f"Starting broadcast {broadcast_id}")
    await broadcast_repo.update_status(broadcast_id, BroadcastStatus.SENDING)
    
    skip = 0
    limit = 100
    sent_count = 0
    failed_count = 0
    total_processed = 0

    try:
        while True:
            # Fetch active users (is_banned=False)
            users, _ = await user_repo.list_users(skip=skip, limit=limit, is_banned=False)
            
            if not users:
                break
                
            for user in users:
                # Send message via Telegram Bot API directly
                success = await telegram_client.send_message(chat_id=user.telegram_id, text=message_text)
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
                total_processed += 1
                
                # Update DB every 20 messages to keep UI somewhat live, without overloading DB
                if total_processed % 20 == 0:
                    await broadcast_repo.increment_counts(broadcast_id, sent=sent_count, failed=failed_count)
                    sent_count = 0
                    failed_count = 0
                
                # Safe sleep to avoid exceeding 30 msg/sec (0.05 = 20 msg/sec)
                await asyncio.sleep(0.05)
                
                # Extra pause every 500 messages
                if total_processed % 500 == 0:
                    logger.info(f"Broadcast {broadcast_id}: Sent {total_processed} messages, pausing for 1 second.")
                    await asyncio.sleep(1.0)
                    
            skip += limit
            
        # Final update for remaining counts
        if sent_count > 0 or failed_count > 0:
            await broadcast_repo.increment_counts(broadcast_id, sent=sent_count, failed=failed_count)
            
        await broadcast_repo.update_status(broadcast_id, BroadcastStatus.COMPLETED)
        logger.info(f"Broadcast {broadcast_id} completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during broadcast {broadcast_id}: {str(e)}", exc_info=True)
        await broadcast_repo.update_status(broadcast_id, BroadcastStatus.FAILED)
