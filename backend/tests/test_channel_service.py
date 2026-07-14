import pytest
from app.domain.channels.entities import MandatoryChannel
from app.application.channels.service import ChannelService

class FakeChannelRepository:
    def __init__(self):
        self.channels = {}
        self.counter = 1

    async def create(self, channel: MandatoryChannel) -> MandatoryChannel:
        channel.id = self.counter
        self.counter += 1
        self.channels[channel.id] = channel
        return channel

    async def get_by_id(self, id: int) -> MandatoryChannel | None:
        return self.channels.get(id)

    async def update(self, channel: MandatoryChannel) -> MandatoryChannel | None:
        if channel.id in self.channels:
            self.channels[channel.id] = channel
            return channel
        return None

    async def delete(self, id: int) -> bool:
        if id in self.channels:
            del self.channels[id]
            return True
        return False

    async def list_active(self) -> list[MandatoryChannel]:
        return [c for c in self.channels.values() if c.is_active]

    async def list_all(self, skip: int = 0, limit: int = 20) -> tuple[list[MandatoryChannel], int]:
        channels = list(self.channels.values())[skip:skip+limit]
        return channels, len(self.channels)

    async def verify_subscription(self, channel_id: int, user_id: int) -> bool:
        channel = self.channels.get(channel_id)
        if not channel:
            return False
        if not hasattr(self, 'verified'):
            self.verified = set()
        if (channel_id, user_id) in self.verified:
            return False
        self.verified.add((channel_id, user_id))
        
        channel.current_subscriber_count += 1
        if channel.subscriber_limit is not None and channel.current_subscriber_count >= channel.subscriber_limit:
            channel.is_active = False
            
        return True

@pytest.fixture
def channel_service():
    repo = FakeChannelRepository()
    return ChannelService(repo)

@pytest.mark.asyncio
async def test_create_channel(channel_service: ChannelService):
    channel = await channel_service.create_channel(
        channel_id=-100123, channel_username="testchannel", channel_title="Test"
    )
    assert channel.id is not None
    assert channel.channel_id == -100123
    assert channel.is_active is True

@pytest.mark.asyncio
async def test_update_channel(channel_service: ChannelService):
    channel = await channel_service.create_channel(channel_id=-1001)
    updated = await channel_service.update_channel(
        id=channel.id, is_active=False
    )
    assert updated.is_active is False

@pytest.mark.asyncio
async def test_delete_channel(channel_service: ChannelService):
    channel = await channel_service.create_channel(channel_id=-1001)
    assert await channel_service.delete_channel(channel.id) is True
    assert await channel_service.get_channel(channel.id) is None

@pytest.mark.asyncio
async def test_list_active_channels(channel_service: ChannelService):
    await channel_service.create_channel(channel_id=-1)
    c2 = await channel_service.create_channel(channel_id=-2)
    await channel_service.update_channel(c2.id, is_active=False)

    active = await channel_service.list_active()
    assert len(active) == 1
    assert active[0].channel_id == -1

@pytest.mark.asyncio
async def test_list_all_channels(channel_service: ChannelService):
    await channel_service.create_channel(channel_id=-1)
    await channel_service.create_channel(channel_id=-2)
    channels, total = await channel_service.list_all()
    assert total == 2

@pytest.mark.asyncio
async def test_verify_subscription_happy_path(channel_service: ChannelService):
    channel = await channel_service.create_channel(channel_id=-10)
    
    # Birinchi marta tasdiqlanganda True qaytadi va count oshadi
    res1 = await channel_service.verify_subscription(channel.id, user_id=111)
    assert res1 is True
    
    # Xuddi shu user yana tasdiqlashga urinsa False qaytadi va count oshmaydi
    res2 = await channel_service.verify_subscription(channel.id, user_id=111)
    assert res2 is False
    
    ch = await channel_service.get_channel(channel.id)
    assert ch.current_subscriber_count == 1
    assert ch.is_active is True

@pytest.mark.asyncio
async def test_verify_subscription_limit_reached(channel_service: ChannelService):
    channel = await channel_service.create_channel(channel_id=-20)
    # Qo'lda limit o'rnatamiz, chunki create_channel da limit parametr yo'q edi, yoki obyektdan o'zgartiramiz
    ch_update = await channel_service.get_channel(channel.id)
    ch_update.subscriber_limit = 2
    await channel_service.channel_repo.update(ch_update)
    
    await channel_service.verify_subscription(channel.id, user_id=101)
    
    ch_check = await channel_service.get_channel(channel.id)
    assert ch_check.current_subscriber_count == 1
    assert ch_check.is_active is True
    
    await channel_service.verify_subscription(channel.id, user_id=102)
    
    ch_final = await channel_service.get_channel(channel.id)
    assert ch_final.current_subscriber_count == 2
    assert ch_final.is_active is False  # Limit 2 edi, yetib bordi, False bo'lishi kerak
