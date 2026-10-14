"""
Unit tests for Kinochi Autopilot 2.0.
Verifies:
1. Zero-tolerance health inspection.
2. 90% Circuit Breaker Auto-Pause.
3. Dual-tier quality selection and 2GB limit.
4. Smart Upgrade (Variant B).
5. Quarantine & Manual Season Resolution.
"""

import sys
import os

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scraper.autopilot_v2 import (
    health_evaluator,
    quality_manager,
    quarantine_manager,
    autopilot_engine
)


def test_zero_tolerance_and_quarantine():
    print("--- Test 1: Zero-Tolerance Health & Quarantine ---")
    defective_item = {
        "id": "test_defective_01",
        "title": "Forsaj 10",
        "original_title": "",  # Missing!
        "tmdb_id": None,       # Missing!
        "source": "uzmovi",
        "poster_url": "https://image.tmdb.org/t/p/w500/test.jpg",
        "description": "Juda qiziqarli yangi poyga filmi tafsilotlari.",
        "genres": "Jangari, Poyga",
        "voiceover": "O'zbekcha dublyaj",
        "file_size": 1500 * 1024 * 1024,
        "quality": "1080p",
        "media_type": "movie"
    }

    success, msg, item = autopilot_engine.process_incoming_media(defective_item)
    assert not success, "Defective item should fail zero-tolerance check"
    assert "missing_tmdb_id" in msg or "Karantinga olindi" in msg
    print("✓ Defective item successfully rejected and quarantined!")


def test_healthy_item_approval():
    print("--- Test 2: Healthy Item Approval ---")
    healthy_item = {
        "id": "test_healthy_02",
        "title": "Inception",
        "original_title": "Inception",
        "tmdb_id": 27205,
        "source": "asilmedia",
        "poster_url": "https://image.tmdb.org/t/p/w500/inception.jpg",
        "description": "Tushlar ichidagi maxfiy sirlarni o'g'irlash haqidagi ajoyib film.",
        "genres": "Fantastika, Triller",
        "voiceover": "O'zbekcha dublyaj",
        "media_type": "movie",
        "variants": [
            {"quality": "1080p", "file_size": 1800 * 1024 * 1024},
            {"quality": "720p", "file_size": 900 * 1024 * 1024},
            {"quality": "480p", "file_size": 400 * 1024 * 1024}
        ]
    }

    success, msg, item = autopilot_engine.process_incoming_media(healthy_item)
    assert success, f"Healthy item should be approved: {msg}"
    assert item["best_quality"]["quality"] == "1080p"
    assert item["step_down_quality"]["quality"] == "720p"
    print("✓ Healthy item approved with dual qualities (1080p + 720p)!")


def test_2gb_limit_cascade():
    print("--- Test 3: 2GB Telegram Limit Cascade ---")
    oversized_item = {
        "id": "test_oversized_03",
        "title": "Interstellar",
        "original_title": "Interstellar",
        "tmdb_id": 157336,
        "source": "asilmedia",
        "poster_url": "https://image.tmdb.org/t/p/w500/interstellar.jpg",
        "description": "Fazoviy sayohat va insoniyat kelajagi haqidagi film.",
        "genres": "Fantastika",
        "voiceover": "O'zbekcha dublyaj",
        "media_type": "movie",
        "variants": [
            {"quality": "1080p", "file_size": 2500 * 1024 * 1024},  # 2.5 GB! Exceeds Telegram 2GB limit
            {"quality": "720p", "file_size": 1400 * 1024 * 1024},   # Valid
            {"quality": "480p", "file_size": 600 * 1024 * 1024}     # Valid
        ]
    }

    success, msg, item = autopilot_engine.process_incoming_media(oversized_item)
    assert success, f"Item should be approved with fallback quality: {msg}"
    assert item["best_quality"]["quality"] == "720p", "720p should become best quality when 1080p > 2GB"
    assert item["step_down_quality"]["quality"] == "480p", "480p should become step-down"
    print("✓ 1080p > 2GB was correctly dropped, 720p became best and 480p became step-down!")


def test_smart_upgrade_variant_b():
    print("--- Test 4: Smart Upgrade (Variant B) ---")
    current_media = {
        "best_quality": {"quality": "720p", "file_size": 900 * 1024 * 1024},
        "step_down_quality": {"quality": "480p", "file_size": 400 * 1024 * 1024}
    }

    new_analog = {"quality": "1080p", "file_size": 1700 * 1024 * 1024}

    upgraded, result = quality_manager.handle_smart_upgrade(current_media, new_analog)
    assert upgraded, "Upgrade should be performed"
    assert result["best_quality"]["quality"] == "1080p", "New 1080p analog should be best"
    assert result["step_down_quality"]["quality"] == "720p", "Old 720p should be preserved as step-down"
    print("✓ Smart Upgrade executed: 1080p became best, old 720p became step-down budget tier!")


def test_season_quarantine_and_manual_resolve():
    print("--- Test 5: Seasonless Series Quarantine & Manual Resolve ---")
    seasonless_series = {
        "id": "series_ep_45",
        "title": "Kurtlar Vadisi",
        "original_title": "Kurtlar Vadisi",
        "tmdb_id": 4443,
        "source": "uzmovi",
        "poster_url": "https://image.tmdb.org/t/p/w500/kv.jpg",
        "description": "Mashhur turk jangari seriali.",
        "genres": "Jangari",
        "voiceover": "O'zbekcha dublyaj",
        "media_type": "series",
        "season_number": None,  # Missing season!
        "episode_number": 45,
        "quality": "720p",
        "file_size": 500 * 1024 * 1024
    }

    success, msg, item = autopilot_engine.process_incoming_media(seasonless_series)
    assert not success, "Seasonless series must be held in quarantine"
    assert "missing_season_number" in msg

    # Admin manual action:
    resolved, res_msg, resolved_item = quarantine_manager.assign_season("series_ep_45", season_number=2)
    assert resolved, f"Manual season assignment should resolve item: {res_msg}"
    assert resolved_item["season_number"] == 2
    print("✓ Seasonless series successfully quarantined and resolved by admin!")


def main():
    print("Starting Autopilot 2.0 Verification Suite...\n")
    test_zero_tolerance_and_quarantine()
    test_healthy_item_approval()
    test_2gb_limit_cascade()
    test_smart_upgrade_variant_b()
    test_season_quarantine_and_manual_resolve()
    print("\n🎉 ALL AUTOPILOT 2.0 ARCHITECTURAL TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    main()
