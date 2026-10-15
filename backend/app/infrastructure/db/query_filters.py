"""Markazlashtirilgan SQL filtrlash yordamchilari (A3)."""
from typing import Any
from sqlalchemy import Select
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel


def published_only(stmt: Select[Any], model: Any = None) -> Select[Any]:
    """
    Ommaviy o'qish yo'llari uchun faqat 'published' holatdagi media va ularning
    bog'liq qismlarini (seasons, episodes) filtrlaydi.
    
    Qoidalar:
    - MovieModel: MovieModel.publish_status == 'published'
    - SeriesModel: SeriesModel.publish_status == 'published'
    - SeasonModel: tegishli ota SeriesModel.publish_status == 'published'
    - EpisodeModel: tegishli ota SeriesModel.publish_status == 'published'
    """
    if model is MovieModel:
        return stmt.where(MovieModel.publish_status == "published")
    elif model is SeriesModel:
        return stmt.where(SeriesModel.publish_status == "published")
    elif model is SeasonModel:
        return stmt.join(SeriesModel, SeasonModel.series_id == SeriesModel.id).where(
            SeriesModel.publish_status == "published"
        )
    elif model is EpisodeModel:
        return (
            stmt.join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)
            .join(SeriesModel, SeasonModel.series_id == SeriesModel.id)
            .where(SeriesModel.publish_status == "published")
        )
    elif model is not None and hasattr(model, "publish_status"):
        return stmt.where(model.publish_status == "published")

    return stmt
