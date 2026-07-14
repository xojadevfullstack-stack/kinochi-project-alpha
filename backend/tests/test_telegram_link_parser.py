import pytest
from app.utils.telegram_link_parser import parse_telegram_link

def test_parse_telegram_link_standard():
    url = "https://t.me/c/1234567890/123"
    result = parse_telegram_link(url)
    assert result == {
        "chat_id": -1001234567890,
        "message_id": 123,
        "topic_id": None
    }

def test_parse_telegram_link_with_thread_query():
    url = "https://t.me/c/1234567890/123?thread=45"
    result = parse_telegram_link(url)
    assert result == {
        "chat_id": -1001234567890,
        "message_id": 123,
        "topic_id": 45
    }

def test_parse_telegram_link_forum_topic_real():
    # Haqiqiy forum topic xabarining havolasi
    url = "https://t.me/c/1990123456/152/155"
    result = parse_telegram_link(url)
    assert result == {
        "chat_id": -1001990123456,
        "topic_id": 152,
        "message_id": 155
    }

def test_parse_telegram_link_public_forum():
    # User provided public group link
    url = "https://telegram.me/kinochi_mvp/1/22"
    result = parse_telegram_link(url)
    assert result["topic_id"] == 1
    assert result["message_id"] == 22
    # chat_id for kinochi_mvp will be tested based on how the parser handles it

def test_parse_telegram_link_invalid_domain():
    with pytest.raises(ValueError, match="domain 't.me' emas"):
        parse_telegram_link("https://google.com/c/123/456")

def test_parse_telegram_link_no_c_prefix():
    with pytest.raises(ValueError, match="link '/c/' bilan boshlanishi kerak"):
        parse_telegram_link("https://t.me/kinochi_bot")

def test_parse_telegram_link_invalid_segments():
    with pytest.raises(ValueError, match="noto'g'ri URL segmentlari"):
        parse_telegram_link("https://t.me/c/123")
        
    with pytest.raises(ValueError, match="noto'g'ri URL segmentlari"):
        parse_telegram_link("https://t.me/c/123/45/67/89")

def test_parse_telegram_link_non_numeric():
    with pytest.raises(ValueError, match="chat_id raqam bo'lishi kerak"):
        parse_telegram_link("https://t.me/c/abc/123")
        
    with pytest.raises(ValueError, match="message_id raqam bo'lishi kerak"):
        parse_telegram_link("https://t.me/c/123/abc")
        
    with pytest.raises(ValueError, match="topic_id raqam bo'lishi kerak"):
        parse_telegram_link("https://t.me/c/123/abc/123")
