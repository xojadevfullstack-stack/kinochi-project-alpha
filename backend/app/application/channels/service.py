"""MandatoryChannel application service."""
from typing import Sequence
from app.domain.channels.entities import MandatoryChannel
from app.domain.channels.repository import IMandatoryChannelRepository

class ChannelService:
    def __init__(self, channel_repo: IMandatoryChannelRepository):
        self.channel_repo = channel_repo

    async def create_channel(
        self,
        channel_id: int,
        channel_username: str | None = None,
        channel_title: str | None = None,
        is_active: bool = True
    ) -> MandatoryChannel:
        channel = MandatoryChannel(
            channel_id=channel_id,
            channel_username=channel_username,
            channel_title=channel_title,
            is_active=is_active
        )
        return await self.channel_repo.create(channel)

    async def get_channel(self, id: int) -> MandatoryChannel | None:
        return await self.channel_repo.get_by_id(id)

    async def update_channel(
        self,
        id: int,
        channel_username: str | None = None,
        channel_title: str | None = None,
        is_active: bool | None = None
    ) -> MandatoryChannel | None:
        channel = await self.channel_repo.get_by_id(id)
        if not channel:
            return None
        if channel_username is not None: channel.channel_username = channel_username
        if channel_title is not None: channel.channel_title = channel_title
        if is_active is not None: channel.is_active = is_active
        return await self.channel_repo.update(channel)

    async def delete_channel(self, id: int) -> bool:
        return await self.channel_repo.delete(id)

    async def list_active(self) -> Sequence[MandatoryChannel]:
        return await self.channel_repo.list_active()

    async def list_all(self, skip: int = 0, limit: int = 20) -> tuple[Sequence[MandatoryChannel], int]:
        return await self.channel_repo.list_all(skip=skip, limit=limit)
