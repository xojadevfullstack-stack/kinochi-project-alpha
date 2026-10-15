import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request
from fastapi import HTTPException
from app.api.v1.collections import get_collection, get_movie_franchise_context
from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
from app.infrastructure.db.models.movie import MovieModel


@pytest.mark.asyncio
async def test_f007_get_collection_filters_unpublished_items(monkeypatch):
    """F-007 regression: get_collection must omit items with publish_status != 'published'."""
    # Bypass redis cache
    monkeypatch.setattr("app.api.v1.collections.get_cache", AsyncMock(return_value=None))
    monkeypatch.setattr("app.api.v1.collections.set_cache", AsyncMock(return_value=None))

    mock_db = AsyncMock()

    # Mock collection
    mock_collection = CollectionModel(
        id=1,
        name="Marvel Cinematic Universe",
        slug="mcu",
        description="All MCU movies",
        is_active=True,
        is_franchise=True,
        sort_order=1
    )

    # Item 1: published movie
    pub_movie = MovieModel(
        id=10,
        title="Iron Man",
        code="MCU01",
        release_year=2008,
        publish_status="published"
    )
    item_pub = CollectionItemModel(
        id=101,
        collection_id=1,
        movie_id=10,
        chronological_order=1,
        release_order=1,
        is_locked=False,
    )
    item_pub.movie = pub_movie
    item_pub.series = None

    # Item 2: pending movie (unreleased or awaiting approval)
    pending_movie = MovieModel(
        id=20,
        title="Iron Man 2 (Unpublished)",
        code="MCU02",
        release_year=2010,
        publish_status="pending"
    )
    item_pending = CollectionItemModel(
        id=102,
        collection_id=1,
        movie_id=20,
        chronological_order=2,
        release_order=2,
        is_locked=False,
    )
    item_pending.movie = pending_movie
    item_pending.series = None

    # DB mocks
    exec_collection_res = MagicMock()
    exec_collection_res.scalar_one_or_none.return_value = mock_collection

    exec_items_res = MagicMock()
    exec_items_res.scalars.return_value.all.return_value = [item_pub, item_pending]

    mock_db.execute.side_effect = [exec_collection_res, exec_items_res]

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/collections/mcu",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    req = Request(scope)

    result = await get_collection(request=req, slug_or_id="mcu", sort="chronological", db=mock_db)

    # Must only include published items
    assert result.items_count == 1
    assert len(result.items) == 1
    assert result.items[0].movie_id == 10


@pytest.mark.asyncio
async def test_f007_get_movie_franchise_context_blocks_pending_movie(monkeypatch):
    """F-007 regression: get_movie_franchise_context must 404 on pending movie."""
    monkeypatch.setattr("app.api.v1.collections.get_cache", AsyncMock(return_value=None))

    mock_db = AsyncMock()

    # Query for movie returns None because publish_status='published' filter was applied
    movie_res = MagicMock()
    movie_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = movie_res

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/collections/movie-context/MCU02",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    req = Request(scope)

    with pytest.raises(HTTPException) as exc_info:
        await get_movie_franchise_context(request=req, movie_code="MCU02", db=mock_db)

    assert exc_info.value.status_code == 404
