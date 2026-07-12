from typing import Sequence
from fastapi import BackgroundTasks
from app.domain.broadcasts.entities import Broadcast, BroadcastStatus
from app.domain.broadcasts.repository import IBroadcastRepository
from app.domain.users.repository import IUserRepository
from app.application.broadcasts.sender import process_broadcast

class BroadcastService:
    def __init__(self, broadcast_repo: IBroadcastRepository, user_repo: IUserRepository):
        self.broadcast_repo = broadcast_repo
        self.user_repo = user_repo

    async def create_broadcast(self, message_text: str) -> Broadcast:
        # Get total active recipients initially
        _, total_recipients = await self.user_repo.list_users(limit=1, is_banned=False)
        
        broadcast = Broadcast(
            message_text=message_text,
            status=BroadcastStatus.DRAFT,
            total_recipients=total_recipients
        )
        return await self.broadcast_repo.create(broadcast)

    async def get_broadcast(self, id: int) -> Broadcast | None:
        return await self.broadcast_repo.get_by_id(id)

    async def list_broadcasts(self, skip: int = 0, limit: int = 20) -> tuple[Sequence[Broadcast], int]:
        return await self.broadcast_repo.list_broadcasts(skip, limit)

    async def start_broadcast(self, id: int, background_tasks: BackgroundTasks) -> Broadcast | None:
        broadcast = await self.broadcast_repo.get_by_id(id)
        if not broadcast or broadcast.status != BroadcastStatus.DRAFT:
            return None

        # process_broadcast o'z session'ini yaratadi — repo'larni berish shart emas
        background_tasks.add_task(
            process_broadcast,
            broadcast_id=id,
            message_text=broadcast.message_text,
        )

        # Mark as sending initially
        return await self.broadcast_repo.update_status(id, BroadcastStatus.SENDING)
