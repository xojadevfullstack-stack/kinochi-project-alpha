"""Markazlashtirilgan SQL filtrlash yordamchilari (A3)."""
from typing import Any
from sqlalchemy import Select, and_, func, or_
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel


ADULT_KEYWORDS = ("18+", "18-plus", "kattalar", "adult", "erotika", "erotik", "ecchi", "hentai")


def non_adult_condition(model: Any):
    """18+ flag, kategoriya yoki janrga ega bo'lmagan xavfsiz media sharti."""
    cat_adult_filters = []
    for kw in ADULT_KEYWORDS:
        cat_adult_filters.append(func.lower(CategoryModel.name).contains(kw))
        cat_adult_filters.append(func.lower(CategoryModel.slug).contains(kw))

    clauses = [
        model.is_18_plus.is_(False),
        ~model.categories.any(or_(*cat_adult_filters)),
    ]
    if hasattr(model, "genres"):
        clauses.append(
            or_(
                model.genres.is_(None),
                and_(*(~func.lower(model.genres).contains(kw) for kw in ADULT_KEYWORDS)),
            )
        )
    return and_(*clauses)


def exclude_adult_media(stmt: Select[Any], model: Any) -> Select[Any]:
    """18+ mediayani SQL darajasida chiqarib tashlaydi."""
    return stmt.where(non_adult_condition(model))


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
