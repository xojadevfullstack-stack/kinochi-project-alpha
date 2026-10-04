import pytest
from app.domain.movies.entities import Movie
from app.domain.series.entities import Series, SeriesCreate, SeriesUpdate
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel


def test_movie_entity_tmdb_id():
    m = Movie(title="Avatar", code="1234", tmdb_id=19995)
    assert m.tmdb_id == 19995
    dumped = m.model_dump()
    assert dumped["tmdb_id"] == 19995


def test_series_entity_tmdb_id():
    s = SeriesCreate(title="Breaking Bad", tmdb_id=1396)
    assert s.tmdb_id == 1396
    
    u = SeriesUpdate(tmdb_id=1396)
    assert u.tmdb_id == 1396


def test_orm_models_tmdb_id():
    m_model = MovieModel(title="Inception", code="5678", tmdb_id=27205)
    assert m_model.tmdb_id == 27205
    
    s_model = SeriesModel(title="Dark", tmdb_id=70523)
    assert s_model.tmdb_id == 70523
