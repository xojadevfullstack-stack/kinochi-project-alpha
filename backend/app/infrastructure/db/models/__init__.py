"""
Infrastructure — DB models.

Import all ORM models here so Alembic can discover them via Base.metadata.
"""
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.movie import MovieModel, movie_category_table
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.models.channel import MandatoryChannelModel
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.db.models.broadcast import BroadcastModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel, series_category_table

__all__ = ["CategoryModel", "MovieModel", "movie_category_table", "UserModel", "MandatoryChannelModel", "AdminUserModel", "BroadcastModel", "SeriesModel", "SeasonModel", "EpisodeModel", "series_category_table"]
