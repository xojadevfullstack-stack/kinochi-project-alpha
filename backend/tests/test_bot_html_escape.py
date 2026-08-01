import pytest
import sys
import os
import html

# Add bot to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../bot')))

import utils.movie_sender
import utils.episode_sender

@pytest.mark.asyncio
async def test_movie_sender_html_escape():
    movie = {
        "title": "Bad <script> title & stuff",
        "description": "More bad <things> & \"quotes\"",
        "translations": [{"telegram_file_id": "123"}],
        "code": "M1"
    }
    
    class MockBot:
        async def send_video(self, *args, **kwargs):
            # Because python's html.escape defaults to quote=True, " is converted to &quot;
            assert "Bad &lt;script&gt; title &amp; stuff" in kwargs['caption']
            assert "More bad &lt;things&gt; &amp; &quot;quotes&quot;" in kwargs['caption']
            assert kwargs.get('parse_mode') == "HTML"
            
        async def send_message(self, *args, **kwargs):
            assert "Bad &lt;script&gt; title &amp; stuff" in kwargs['text']
            assert kwargs.get('parse_mode') == "HTML"
            
    bot = MockBot()
    await utils.movie_sender.send_movie_to_user(bot, 123, movie)

def test_episode_caption_html_escape():
    episode = {
        "series_title": "Bad <series>",
        "display_code": "S1-E1",
        "season_description": "Bad <desc>"
    }
    
    caption = utils.episode_sender.format_episode_caption(episode)
    assert "Bad &lt;series&gt;" in caption
    assert "Bad &lt;desc&gt;" in caption
    assert "<series>" not in caption
    assert "<desc>" not in caption
