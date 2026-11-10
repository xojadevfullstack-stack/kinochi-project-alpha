"""
TDD Tests for Admission Gate Quality Guards:
1. Runtime mismatch with +/- 10% tolerance
2. Episode filename / caption vs episode number consistency
3. Episode number exceeding TMDb season episode count
4. Duplicate file_unique_id
5. file_id liveness check
"""
from app.core.admission_gate import final_check

def test_final_check_runtime_tolerance_10_percent():
    # Movie 100 min runtime, 112 min video -> 12% difference -> FAIL (>10% and >5 min)
    media = {
        "telegram_file_id": "file_123",
        "storage_channel_message_id": 100,
        "duration": 112 * 60,
        "language": "O'zbekcha",
        "tmdb_runtime": 100,
    }
    ok, defects = final_check("movie", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "runtime_mismatch" in codes

    # Movie 100 min runtime, 108 min video -> 8% difference -> PASS (<= 10%)
    media_pass = {
        "telegram_file_id": "file_123",
        "storage_channel_message_id": 100,
        "duration": 108 * 60,
        "language": "O'zbekcha",
        "tmdb_runtime": 100,
    }
    ok_p, defects_p = final_check("movie", media_pass)
    assert ok_p
    assert len(defects_p) == 0

def test_final_check_episode_filename_and_caption_consistency():
    # Episode 5, but filename is S01E06 -> FAIL
    media = {
        "telegram_file_id": "file_ep_1",
        "storage_channel_message_id": 101,
        "duration": 24 * 60,
        "language": "O'zbekcha",
        "season_number": 1,
        "episode_number": 5,
        "filename": "Kaiju.No.8.S01E06.1080p.mkv",
        "caption": "Kaiju 1-mavsum 5-qism",
    }
    ok, defects = final_check("episode", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "season_episode_conflict" in codes

def test_final_check_episode_count_exceeds_tmdb_season():
    # Season has 12 episodes according to TMDb, but uploading episode 13 -> FAIL
    media = {
        "telegram_file_id": "file_ep_13",
        "storage_channel_message_id": 113,
        "duration": 24 * 60,
        "language": "O'zbekcha",
        "season_number": 1,
        "episode_number": 13,
        "tmdb_season_episode_count": 12,
        "filename": "Kaiju.No.8.S01E13.1080p.mkv",
    }
    ok, defects = final_check("episode", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "episode_count_exceeds_tmdb" in codes

def test_final_check_duplicate_file_unique_id():
    media = {
        "telegram_file_id": "file_dup",
        "file_unique_id": "unique_abc_123",
        "duplicate_file_unique_id": True,
        "storage_channel_message_id": 100,
        "duration": 90 * 60,
        "language": "O'zbekcha",
    }
    ok, defects = final_check("movie", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "duplicate_file_unique_id" in codes

def test_final_check_file_id_liveness():
    media = {
        "telegram_file_id": "file_dead",
        "file_id_alive": False,
        "storage_channel_message_id": 100,
        "duration": 90 * 60,
        "language": "O'zbekcha",
    }
    ok, defects = final_check("movie", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "file_id_dead" in codes
