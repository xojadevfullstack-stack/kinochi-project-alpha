import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.requests import Request
from app.api.v1.search import live_search
from app.infrastructure.db.models.series import SeriesModel


@pytest.mark.asyncio
async def test_live_search_punctuation_tolerance():
    """
    Asserts that typing 'aka uka' or 'spider man' with spaces
    matches hypenated titles like 'Aka-uka Grimm ertaklari' in live search.
    """
    mock_db = AsyncMock()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/search/live",
        "headers": [],
        "query_string": b"q=aka+uka",
        "client": ("127.0.0.1", 12345),
    }
    mock_request = Request(scope)

    series = SeriesModel(
        id=1016,
        title="Aka-uka Grimm ertaklari",
        release_year=1987,
        poster_url="https://image.tmdb.org/t/p/w500/test.jpg",
        imdb_rating=6.0,
        publish_status="published",
    )

    executed_statements = []

    def mock_execute(stmt):
        executed_statements.append(stmt)
        mock_result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from series" in stmt_str or "series.title" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [series]
        else:
            mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        return mock_result

    mock_db.execute = AsyncMock(side_effect=mock_execute)

    with patch("app.api.v1.search.get_cache", return_value=None), \
         patch("app.api.v1.search.set_cache", return_value=None):
        resp = await live_search(request=mock_request, q="aka uka", limit=5, db=mock_db)

    # Assert that one of the SQL queries compiled has wildcard pattern matching %aka%uka%
    compiled_sqls = [str(s.compile(compile_kwargs={"literal_binds": True})).lower() for s in executed_statements]
    assert any("%aka%uka%" in sql for sql in compiled_sqls), f"Compiled SQLs did not contain %aka%uka%: {compiled_sqls}"
    assert resp.total >= 1
    assert resp.results[0].id == 1016


@pytest.mark.asyncio
async def test_bot_code_resolver_series_prefixed_link():
    """
    Asserts that clicking the website button 'start=s_1016' or typing 's_1016'
    in Telegram bot successfully resolves and sends the series card.
    """
    import sys
    sys.path.insert(0, "bot")
    from bot.utils.code_resolver import resolve_and_send_content

    mock_bot = AsyncMock()
    series_data = {
        "id": 1016,
        "title": "Aka-uka Grimm ertaklari",
        "release_year": 1987,
        "seasons": [],
        "poster_url": "https://example.com/p.jpg",
    }

    with patch("bot.utils.code_resolver.api_client.get_series_by_id", return_value=series_data), \
         patch("bot.utils.code_resolver.send_series_info", return_value=True) as mock_send_series:
        found = await resolve_and_send_content(mock_bot, 123456, "s_1016")

    assert found is True
    mock_send_series.assert_called_once()
