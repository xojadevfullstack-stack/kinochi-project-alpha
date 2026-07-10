import pytest
from unittest.mock import AsyncMock

from app.domain.categories.entities import Category
from app.application.categories.service import CategoryService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return CategoryService(mock_repo)


@pytest.mark.asyncio
async def test_create_category(service, mock_repo):
    expected_category = Category(id=1, name="Action", slug="action")
    mock_repo.create.return_value = expected_category

    result = await service.create_category(name="Action", slug="action")
    
    assert result == expected_category
    mock_repo.create.assert_called_once()
    args, _ = mock_repo.create.call_args
    assert args[0].name == "Action"
    assert args[0].slug == "action"


@pytest.mark.asyncio
async def test_get_category(service, mock_repo):
    expected_category = Category(id=1, name="Action", slug="action")
    mock_repo.get_by_id.return_value = expected_category

    result = await service.get_category(1)
    
    assert result == expected_category
    mock_repo.get_by_id.assert_called_once_with(1)
