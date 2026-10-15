import pytest
import inspect
from fastapi import Form
from app.api.v1.movies import upload_movie_video, LinkVideoRequest
from app.api.v1.series import upload_episode_video, LinkVideoRequest as SeriesLinkVideoRequest
from app.application.movies.service import MovieService
from app.application.series.series_service import SeriesService
from app.core.admission_gate import final_check


def test_f005_default_languages_are_not_asosiy():
    """F-005 regression test: language defaults must not be 'Asosiy' across APIs and services."""
    # 1. Movie API endpoints
    sig_movie_upload = inspect.signature(upload_movie_video)
    lang_param = sig_movie_upload.parameters.get("language")
    assert lang_param is not None
    assert lang_param.default != "Asosiy"
    if isinstance(lang_param.default, type(Form(...))):
        assert lang_param.default.default != "Asosiy"
        assert lang_param.default.default in ("O'zbekcha", "O'zbek tilida", "uz")

    link_movie_req = LinkVideoRequest(message_id=123)
    assert link_movie_req.language != "Asosiy"
    assert link_movie_req.language in ("O'zbekcha", "O'zbek tilida", "uz")

    # 2. Series API endpoints
    sig_series_upload = inspect.signature(upload_episode_video)
    s_lang_param = sig_series_upload.parameters.get("language")
    assert s_lang_param is not None
    assert s_lang_param.default != "Asosiy"
    if isinstance(s_lang_param.default, type(Form(...))):
        assert s_lang_param.default.default != "Asosiy"
        assert s_lang_param.default.default in ("O'zbekcha", "O'zbek tilida", "uz")

    link_ep_req = SeriesLinkVideoRequest(message_id=123)
    assert link_ep_req.language != "Asosiy"
    assert link_ep_req.language in ("O'zbekcha", "O'zbek tilida", "uz")

    # 3. Application Services
    sig_movie_link = inspect.signature(MovieService.link_movie_video_from_message)
    m_svc_lang = sig_movie_link.parameters.get("language").default
    assert m_svc_lang != "Asosiy"

    sig_series_link = inspect.signature(SeriesService.link_episode_video_from_message)
    s_svc_lang = sig_series_link.parameters.get("language").default
    assert s_svc_lang != "Asosiy"

    # 4. Final check passes with the new default
    is_valid, defects = final_check("movie", {
        "telegram_file_id": "file_123",
        "storage_channel_message_id": 999,
        "language": link_movie_req.language
    })
    assert is_valid, f"final_check rejected default language: {defects}"
