from scraper.site_parser import (
    _extract_asilmedia_items_from_html,
    _extract_uzmovi_items_from_html,
)

def test_extract_asilmedia_items_with_default_media_type_anime():
    sample_html = """
    <html>
      <body>
        <div class="card">
          <a href="/15372-zodiak-ritsarlari-uzbek-tilida-hd.html" title="Zodiak ritsarlari">
            <span class="title">Zodiak ritsarlari (2023)</span>
          </a>
        </div>
      </body>
    </html>
    """
    items_default = _extract_asilmedia_items_from_html(sample_html)
    assert len(items_default) == 1
    assert items_default[0].media_type == "movie"

    items_anime = _extract_asilmedia_items_from_html(sample_html, default_media_type="anime")
    assert len(items_anime) == 1
    assert items_anime[0].media_type == "anime"


def test_extract_uzmovi_items_with_default_media_type_anime():
    sample_html = """
    <html>
      <body>
        <div class="shortstory">
          <a href="/7267-suzume.html" title="Suzume 2022">
            <span>Suzume (2022)</span>
          </a>
        </div>
      </body>
    </html>
    """
    items_default = _extract_uzmovi_items_from_html(sample_html)
    assert len(items_default) == 1
    assert items_default[0].media_type == "movie"

    items_anime = _extract_uzmovi_items_from_html(sample_html, default_media_type="anime")
    assert len(items_anime) == 1
    assert items_anime[0].media_type == "anime"


def test_asilmedia_anime_urls_generation():
    urls = []
    for page in range(1, 4):
        if page <= 2:
            urls.append(f"https://asilmedia.org/kolleksiya/anime-ozbek-tilida/page/{page}/" if page > 1 else "https://asilmedia.org/kolleksiya/anime-ozbek-tilida/")
        urls.append(f"https://asilmedia.org/index.php?do=search&subaction=search&story=anime&search_start={page}")

    assert len(urls) == 5
    assert "https://asilmedia.org/kolleksiya/anime-ozbek-tilida/" in urls
    assert "https://asilmedia.org/kolleksiya/anime-ozbek-tilida/page/2/" in urls
    assert "https://asilmedia.org/index.php?do=search&subaction=search&story=anime&search_start=1" in urls
    assert "https://asilmedia.org/index.php?do=search&subaction=search&story=anime&search_start=2" in urls
    assert "https://asilmedia.org/index.php?do=search&subaction=search&story=anime&search_start=3" in urls
