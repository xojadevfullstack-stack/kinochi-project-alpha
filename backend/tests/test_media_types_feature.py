import os
import sys
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.queue_manager import QueueManager, QueueItem, matches_media_type
from scraper.site_parser import _extract_uzmovi_items_from_html, _extract_asilmedia_items_from_html
from scraper.telethon_moderator_pipeline import resolve_page_ids
from backend.app.api.v1.scraper import MEDIA_TYPES, ParseRequest, DownloadRequest, AutopilotRequest
from scraper.process_manager import ProcessManager


def test_matches_media_type():
    # 1. Exact media_type matches
    assert matches_media_type({"media_type": "dorama"}, "dorama") is True
    assert matches_media_type({"media_type": "anime"}, "anime") is True
    assert matches_media_type({"media_type": "multfilm"}, "multfilm") is True
    assert matches_media_type({"media_type": "movie"}, "movie") is True
    assert matches_media_type({"media_type": "series"}, "series") is True
    assert matches_media_type({"media_type": "series"}, "all") is True

    # 2. Anime heuristics (source or title/url)
    assert matches_media_type({"source": "anitoob", "title": "Naruto"}, "anime") is True
    assert matches_media_type({"source": "animeelar", "title": "Attack on Titan"}, "anime") is True
    assert matches_media_type({"source": "uzmovi", "title": "Solo Leveling anime", "media_type": "series"}, "anime") is True
    assert matches_media_type({"source": "uzmovi", "url": "https://uzmovi.tv/anime/123", "media_type": "series"}, "anime") is True

    # 3. Dorama heuristics
    assert matches_media_type({"title": "Mening sevgilim (Koreya serial)", "media_type": "series"}, "dorama") is True
    assert matches_media_type({"url": "https://uzmovi.tv/drama/123.html", "media_type": "series"}, "dorama") is True

    # 4. Multfilm heuristics
    assert matches_media_type({"title": "Muzlik davri multfilm", "media_type": "movie"}, "multfilm") is True
    assert matches_media_type({"url": "https://uzmovi.tv/multfilmlari/456.html"}, "multfilm") is True

    # 5. Non-matching checks
    assert matches_media_type({"title": "Oddiy Film", "media_type": "movie"}, "anime") is False
    assert matches_media_type({"title": "Oddiy Serial", "media_type": "series"}, "multfilm") is False


def test_queue_manager_filtering(setup_test_db):
    qm = QueueManager()
    qm.clear_all()

    item1 = QueueItem(id="uzmovi_1", source="uzmovi", source_id="1", title="Qasoskorlar", media_type="movie", url="http://1", status="queued")
    item2 = QueueItem(id="uzmovi_2", source="uzmovi", source_id="2", title="Qish ertagi (Koreya serial)", media_type="dorama", url="http://2", status="queued")
    item3 = QueueItem(id="anitoob_3", source="anitoob", source_id="3", title="Bleach", media_type="anime", url="http://3", status="queued")
    item4 = QueueItem(id="uzmovi_4", source="uzmovi", source_id="4", title="Shrek", media_type="multfilm", url="http://4", status="queued")
    item5 = QueueItem(id="uzmovi_5", source="uzmovi", source_id="5", title="Taxtlar o'yini", media_type="series", url="http://5", status="queued")

    for it in [item1, item2, item3, item4, item5]:
        qm.add(it)

    # get_pending with media_type
    doramas = qm.get_pending(limit=10, media_type="dorama")
    assert len(doramas) == 1
    assert doramas[0].id == "uzmovi_2"

    animes = qm.get_pending(limit=10, media_type="anime")
    assert len(animes) == 1
    assert animes[0].id == "anitoob_3"

    cartoons = qm.get_pending(limit=10, media_type="multfilm")
    assert len(cartoons) == 1
    assert cartoons[0].id == "uzmovi_4"

    movies = qm.get_pending(limit=10, media_type="movie")
    assert len(movies) == 1
    assert movies[0].id == "uzmovi_1"

    all_items = qm.get_pending(limit=10, media_type="all")
    assert len(all_items) == 5

    # get_filtered with media_type
    filtered_dorama, total_d = qm.get_filtered(media_type="dorama")
    assert total_d == 1
    assert filtered_dorama[0].id == "uzmovi_2"
    qm.clear_all()


def test_resolve_page_ids():
    # Anime should map to page id=1
    anime_item = QueueItem(id="10", source="anitoob", title="Naruto", media_type="anime", url="http://a")
    pages_anime = resolve_page_ids(anime_item, {"category_ids": [2]})
    assert 1 in pages_anime

    # Dorama should map to page id=5
    dorama_item = QueueItem(id="11", source="asilmedia", title="Koreya dorama", media_type="dorama", url="http://d")
    pages_dorama = resolve_page_ids(dorama_item, {"genres": ["Drama"]})
    assert 5 in pages_dorama

    # Multfilm should map to page id=8
    mult_item = QueueItem(id="12", source="uzmovi", title="Muzlik davri", media_type="multfilm", url="http://m")
    pages_mult = resolve_page_ids(mult_item, {"category_ids": [22]})
    assert 8 in pages_mult


def test_media_types_api_validation():
    assert "dorama" in MEDIA_TYPES
    assert "anime" in MEDIA_TYPES
    assert "multfilm" in MEDIA_TYPES

    p_req = ParseRequest(source="uzmovi", media_type="dorama")
    assert p_req.media_type == "dorama"

    d_req = DownloadRequest(target="uzmovi", media_type="anime")
    assert d_req.media_type == "anime"

    a_req = AutopilotRequest(source="all", media_type="multfilm")
    assert a_req.media_type == "multfilm"


def test_process_manager_validation():
    pm = ProcessManager()
    
    # Invalid media types should fail validation
    res = pm.start_download(target="uzmovi", media_type="invalid_type")
    assert res["success"] is False
    assert "Noma'lum media turi" in res["message"]

    res2 = pm.start_autopilot(source="uzmovi", media_type="invalid_type")
    assert res2["success"] is False
    assert "Noma'lum media turi" in res2["message"]

    res3 = pm.start_parse(source="uzmovi", media_type="invalid_type")
    assert res3["success"] is False
    assert "Noma'lum media turi" in res3["message"]
