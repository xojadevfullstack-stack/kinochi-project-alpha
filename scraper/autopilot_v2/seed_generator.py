"""
Seed Generator & Priority Queue Ingestor for Kinochi Autopilot 2.0.

Core Features:
1. Implements Variant C (TMDB Top-Rated & Popular + Uzbek platforms' Most-Viewed TOP).
2. Generates initial High-Priority Seeds when starting from a clean 0 database:
   - TMDB Top Movies & Series (All-time Masterpieces).
   - Asilmedia & Uzmovi TOP Views (Uzbekistan's most-loved cinema).
   - Anitoob / Animeelar Top Anime.
3. Automatically queues them with Priority=100 so Autopilot fills the database
   with gold-standard popular content first!
"""

import logging
from typing import List, Dict, Any
import httpx
from app.infrastructure.external.tmdb_client import tmdb_client

logger = logging.getLogger(__name__)


class SeedGenerator:
    @staticmethod
    async def fetch_tmdb_popular_seeds(limit: int = 100) -> List[Dict[str, Any]]:
        """Fetches worldwide top-rated & popular movies and series from TMDB."""
        seeds = []
        try:
            # 1. TMDB Popular Movies
            data = await tmdb_client.get_popular_movies(page=1)
            results = data.get("results") or []
            for item in results[:limit // 2]:
                seeds.append({
                    "title": item.get("title"),
                    "original_title": item.get("original_title"),
                    "year": int(item.get("release_date", "2000")[:4]) if item.get("release_date") else None,
                    "tmdb_id": item.get("id"),
                    "media_type": "movie",
                    "priority": 100,
                    "seed_type": "tmdb_popular"
                })

            # 2. TMDB Top Rated Series
            tv_data = await tmdb_client.get_popular_tv(page=1)
            tv_results = tv_data.get("results") or []
            for item in tv_results[:limit // 2]:
                seeds.append({
                    "title": item.get("name"),
                    "original_title": item.get("original_name"),
                    "year": int(item.get("first_air_date", "2000")[:4]) if item.get("first_air_date") else None,
                    "tmdb_id": item.get("id"),
                    "media_type": "series",
                    "priority": 100,
                    "seed_type": "tmdb_popular_series"
                })
        except Exception as e:
            logger.warning(f"TMDB popular seeds fetch warning: {e}")
        return seeds

    @staticmethod
    def get_uzbek_top_priority_seeds() -> List[Dict[str, Any]]:
        """
        Hard-coded gold seeds of Uzbekistan's most-watched movies, series and anime
        (Asilmedia / Uzmovi / Anitoob top viewed list).
        """
        top_list = [
            # Legendary Blockbusters
            {"title": "Qasoskorlar: Intiho", "original_title": "Avengers: Endgame", "year": 2019, "media_type": "movie"},
            {"title": "Forsaj 10", "original_title": "Fast X", "year": 2023, "media_type": "movie"},
            {"title": "Avatar 2: Suv yo'li", "original_title": "Avatar: The Way of Water", "year": 2022, "media_type": "movie"},
            {"title": "Muqaddima", "original_title": "Inception", "year": 2010, "media_type": "movie"},
            {"title": "Interstellar", "original_title": "Interstellar", "year": 2014, "media_type": "movie"},
            {"title": "Qora pantera 2", "original_title": "Black Panther: Wakanda Forever", "year": 2022, "media_type": "movie"},
            {"title": "Jon Uik 4", "original_title": "John Wick: Chapter 4", "year": 2023, "media_type": "movie"},
            {"title": "Gladiator", "original_title": "Gladiator", "year": 2000, "media_type": "movie"},
            {"title": "Cho'qintirgan ota", "original_title": "The Godfather", "year": 1972, "media_type": "movie"},
            {"title": "Garri Potter va hikmatlar toshi", "original_title": "Harry Potter and the Philosopher's Stone", "year": 2001, "media_type": "movie"},

            # Top Series
            {"title": "Taxtlar o'yini", "original_title": "Game of Thrones", "year": 2011, "media_type": "series"},
            {"title": "Qashqirlar makoni pistirma", "original_title": "Kurtlar Vadisi Pusu", "year": 2007, "media_type": "series"},
            {"title": "Chuqur", "original_title": "Çukur", "year": 2017, "media_type": "series"},
            {"title": "Boshpanasizlar", "original_title": "Shameless", "year": 2011, "media_type": "series"},
            {"title": "Venzdey", "original_title": "Wednesday", "year": 2022, "media_type": "series"},
            {"title": "Kalmar o'yini", "original_title": "Squid Game", "year": 2021, "media_type": "series"},

            # Top Anime
            {"title": "Naruto Shippuden", "original_title": "Naruto: Shippuuden", "year": 2007, "media_type": "anime"},
            {"title": "Iblislar qotili", "original_title": "Kimetsu no Yaiba", "year": 2019, "media_type": "anime"},
            {"title": "Titanlar hujumi", "original_title": "Shingeki no Kyojin", "year": 2013, "media_type": "anime"},
            {"title": "O'lim kundaligi", "original_title": "Death Note", "year": 2006, "media_type": "anime"},
            {"title": "Yolg'izlikda daraja ko'tarish", "original_title": "Solo Leveling", "year": 2024, "media_type": "anime"}
        ]

        seeds = []
        for item in top_list:
            seeds.append({
                **item,
                "priority": 100,
                "seed_type": "uzbek_top_chart"
            })
        return seeds


seed_generator = SeedGenerator()
