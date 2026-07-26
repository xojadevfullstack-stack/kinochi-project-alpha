import pytest
from unittest.mock import AsyncMock

from app.domain.series.entities import EpisodeCreate, EpisodeUpdate, Episode, Season
from app.application.series.series_service import SeriesService


@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def mock_telegram_client():
    return AsyncMock()

@pytest.fixture
def service(mock_repo, mock_telegram_client):
    return SeriesService(mock_repo, mock_telegram_client)


@pytest.mark.asyncio
async def test_create_episode_success(service, mock_repo):
    # Setup
    episode_data = EpisodeCreate(
        season_id=1,
        episode_number=1,
        title="First Episode"
    )
    
    import datetime
    mock_season = Season(
        id=1, series_id=1, season_number=2, description="Test", created_at=datetime.datetime.utcnow(), episodes=[]
    )
    mock_repo.get_season_by_id.return_value = mock_season
    
    # Kutilayotgan db javobi
    mock_db_episode = AsyncMock()
    mock_db_episode.id = 10
    mock_db_episode.season_id = 1
    mock_db_episode.episode_number = 1
    mock_db_episode.title = "First Episode"
    mock_db_episode.code = "random-code"
    mock_db_episode.display_code = "S2-CH1"
    
    mock_repo.create_episode.return_value = mock_db_episode
    
    # Action
    result = await service.create_episode(episode_data)
    
    # Assert
    assert result.id == 10
    assert result.display_code == "S2-CH1"
    mock_repo.create_episode.assert_called_once()
    
    # Check if display_code was correctly set before creating
    create_call_args = mock_repo.create_episode.call_args[0][0]
    assert create_call_args["display_code"] == "S2-CH1"


@pytest.mark.asyncio
async def test_create_episode_season_not_found(service, mock_repo):
    # Setup
    episode_data = EpisodeCreate(
        season_id=999,
        episode_number=1,
        title="First Episode"
    )
    mock_repo.get_season_by_id.return_value = None
    
    # Action & Assert
    with pytest.raises(ValueError, match="Season with ID 999 not found"):
        await service.create_episode(episode_data)
    
    mock_repo.create_episode.assert_not_called()


@pytest.mark.asyncio
async def test_update_episode_display_code_changes(service, mock_repo):
    # Setup
    update_data = EpisodeUpdate(episode_number=5, title="Updated Episode")
    
    mock_db_episode = AsyncMock()
    mock_db_episode.id = 10
    mock_db_episode.season_id = 1
    mock_db_episode.episode_number = 4
    
    mock_repo.get_episode_by_id.return_value = mock_db_episode
    
    import datetime
    mock_season = Season(
        id=1, series_id=1, season_number=2, description="", created_at=datetime.datetime.utcnow(), episodes=[]
    )
    mock_repo.get_season_by_id.return_value = mock_season
    
    class MockEpisodeModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
                
    import datetime
    updated_db_episode = MockEpisodeModel(
        id=10,
        season_id=1,
        episode_number=5,
        title="Updated Episode",
        code="random-code",
        display_code="S2-CH5",
        created_at=datetime.datetime.utcnow(),
        duration=None
    )
    mock_repo.update_episode.return_value = updated_db_episode
    
    # Action
    result = await service.update_episode(10, update_data)
    
    # Assert
    assert result is not None
    assert result.display_code == "S2-CH5"
    
    update_call_args = mock_repo.update_episode.call_args[0][1]
    assert update_call_args["display_code"] == "S2-CH5"


@pytest.mark.asyncio
async def test_update_episode_not_found(service, mock_repo):
    # Setup
    update_data = EpisodeUpdate(episode_number=5)
    mock_repo.get_episode_by_id.return_value = None
    
    # Action
    result = await service.update_episode(999, update_data)
    
    # Assert
    assert result is None
    mock_repo.update_episode.assert_not_called()


@pytest.mark.asyncio
async def test_link_episode_video_with_telegram_file_id(service, mock_repo, mock_telegram_client):
    class MockEpisode:
        def __init__(self, id, season_id):
            self.id = id
            self.season_id = season_id

    mock_ep = MockEpisode(id=1, season_id=1)
    mock_repo.get_episode_by_id.return_value = mock_ep
    
    class MockUpdatedEpisode:
        def __init__(self):
            import datetime
            self.id = 1
            self.season_id = 1
            self.episode_number = 1
            self.title = "test"
            self.code = "code"
            self.display_code = "dcode"
            self.duration = 0
            self.created_at = datetime.datetime.now(datetime.timezone.utc)
    
    mock_repo.add_episode_translation.return_value = MockUpdatedEpisode()

    result = await service.link_episode_video_from_message(
        episode_id=1, 
        message_id=99999, 
        telegram_file_id="mock_series_file_id_123"
    )
    
    assert result is not None
    mock_repo.add_episode_translation.assert_called_once_with(
        episode_id=1, 
        language="Asosiy", 
        telegram_file_id="mock_series_file_id_123", 
        storage_channel_message_id=99999
    )
    mock_telegram_client.get_video_file_id_from_message.assert_not_called()
