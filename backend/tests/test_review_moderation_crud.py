import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.api.v1.reviews import remove_review, get_admin_reviews


@pytest.mark.asyncio
async def test_admin_remove_review_success():
    """Admin deletes a review."""
    with patch("app.api.v1.reviews.delete_review", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = True

        await remove_review(
            review_id=42,
            admin={"id": 1, "role": "admin"}
        )
        mock_delete.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_admin_remove_review_not_found():
    """When review is not found, raises 404."""
    with patch("app.api.v1.reviews.delete_review", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await remove_review(
                review_id=999,
                admin={"id": 1, "role": "admin"}
            )
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_get_reviews_feed():
    """Admin gets paginated review feed."""
    with patch("app.api.v1.reviews.list_admin_reviews", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {
            "items": [{"id": 1, "comment": "Ajoyib kino", "rating": 10}],
            "total": 1
        }

        result = await get_admin_reviews(
            search="Ajoyib",
            limit=20,
            offset=0,
            admin={"id": 1, "role": "admin"}
        )
        assert result["total"] == 1
        assert len(result["items"]) == 1
        mock_list.assert_called_once_with(search="Ajoyib", limit=20, offset=0)
