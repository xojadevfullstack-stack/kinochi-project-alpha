import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from app.api.v1.movies import update_movie_translation, UpdateMovieTranslationRequest


@pytest.mark.asyncio
async def test_update_movie_translation_success():
    """Admin updates language of a movie translation."""
    mock_service = AsyncMock()
    mock_service.update_movie_translation.return_value = True

    payload = UpdateMovieTranslationRequest(language="Ruscha (Dublyaj)")
    result = await update_movie_translation(
        translation_id=12,
        request=payload,
        service=mock_service,
        admin={"id": 1, "role": "admin"},
    )

    assert result == {"message": "Success"}
    mock_service.update_movie_translation.assert_called_once_with(12, "Ruscha (Dublyaj)")


@pytest.mark.asyncio
async def test_update_movie_translation_not_found():
    """When translation is not found, raises 404."""
    mock_service = AsyncMock()
    mock_service.update_movie_translation.return_value = False

    payload = UpdateMovieTranslationRequest(language="Ruscha")
    with pytest.raises(HTTPException) as exc_info:
        await update_movie_translation(
            translation_id=999,
            request=payload,
            service=mock_service,
            admin={"id": 1, "role": "admin"},
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Translation not found"
