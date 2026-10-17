import sys
import re
import ast
import os
import pytest
from unittest.mock import MagicMock

# Ensure mocks for backend modules not available in bot venv
sys.modules.setdefault("app", MagicMock())
sys.modules.setdefault("app.core", MagicMock())
sys.modules.setdefault("app.core.reviews", MagicMock())
sys.modules.setdefault("app.core.watch_history", MagicMock())

from aiogram.types import CallbackQuery, User, Chat, Message
from handlers.start import router as start_router
from handlers.check_sub import router as check_sub_router
from handlers.catalog import router as catalog_router
from handlers.reviews import router as reviews_router
from handlers.search import router as search_router
from handlers.browsing import router as browsing_router
from handlers.episode import router as episode_router
from handlers.translation_callback import router as translation_router
from handlers.trailer import router as trailer_router
from handlers.history import router as history_router
from handlers.recommendation import router as recommendation_router
from handlers.profile import router as profile_router
from handlers.reports import router as reports_router

ALL_ROUTERS = [
    start_router,
    check_sub_router,
    catalog_router,
    reviews_router,
    search_router,
    browsing_router,
    episode_router,
    translation_router,
    trailer_router,
    history_router,
    recommendation_router,
    profile_router,
    reports_router,
]

def extract_callback_data_from_code(code_str: str) -> list[str]:
    """Extracts raw string literals or format templates passed to callback_data."""
    results = []
    # Match callback_data="literal" or callback_data='literal'
    for m in re.finditer(r'callback_data\s*=\s*["\']([^"\']+)["\']', code_str):
        results.append(m.group(1))
    # Match callback_data=f"..." or callback_data=f'...'
    for m in re.finditer(r'callback_data\s*=\s*f["\']([^"\']+)["\']', code_str):
        results.append(m.group(1))
    return results

def get_all_produced_callback_data() -> set[str]:
    """Scans bot/keyboards and bot/handlers for all produced callback_data."""
    bot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    scan_dirs = [
        os.path.join(bot_dir, "keyboards"),
        os.path.join(bot_dir, "handlers"),
        os.path.join(bot_dir, "utils"),
        os.path.join(bot_dir, "middlewares"),
    ]
    
    collected_templates = set()
    for sdir in scan_dirs:
        if not os.path.exists(sdir):
            continue
        for fname in os.listdir(sdir):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(sdir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            for cb in extract_callback_data_from_code(content):
                collected_templates.add(cb)
    return collected_templates

def instantiate_callback_template(template: str) -> str:
    """Replaces format expressions in templates with realistic sample data."""
    # Replace common dynamic placeholders with valid sample values
    s = template
    s = re.sub(r'\{item_type\}', 'M', s)
    s = re.sub(r'\{item_code\}', '1001', s)
    s = re.sub(r'\{t\[[\'"]id[\'"]\]\}', '1', s)
    s = re.sub(r'\{code\}', '1001', s)
    s = re.sub(r'\{series_id\}', '2002', s)
    s = re.sub(r'\{sid\}', '2002', s)
    s = re.sub(r'\{item\.get\([\'"]id[\'"]\)\}', '10', s)
    s = re.sub(r'\{item_id\}', '10', s)
    s = re.sub(r'\{page_id\}', '5', s)
    s = re.sub(r'\{page[+-]1\}', '2', s)
    s = re.sub(r'\{page\}', '1', s)
    s = re.sub(r'\{total_pages\}', '5', s)
    s = re.sub(r'\{total\}', '50', s)
    s = re.sub(r'\{prefix\}', 'cat_movies', s)
    s = re.sub(r'\{pid\}', '3', s)
    s = re.sub(r'\{cat_type\}', 'movie', s)
    s = re.sub(r'\{skip[\s\+\d]*\}', '1', s)
    s = re.sub(r'\{itype\}', 'video_xato', s)
    s = re.sub(r'\{ep_id\}', '3003', s)
    s = re.sub(r'\{target_type\}', 'm', s)
    s = re.sub(r'\{target_id\}', '1001', s)
    s = re.sub(r'\{i\}', '8', s)
    s = re.sub(r'\{score\}', '9', s)
    s = re.sub(r'\{prev_code\}', 'e_prev', s)
    s = re.sub(r'\{next_code\}', 'e_next', s)
    s = re.sub(r'\{s_id\}', '1', s)
    s = re.sub(r'\{e_code\}', 'e_101', s)
    return s

@pytest.mark.asyncio
async def test_every_produced_callback_data_has_matching_handler():
    """Barcha ishlab chiqarilgan callback_data uchun mos handler filtri mavjudligini tekshirish."""
    templates = get_all_produced_callback_data()
    assert len(templates) > 15, f"Expected many callback_data templates, found {len(templates)}"

    for template in sorted(templates):
        concrete_data = instantiate_callback_template(template)
        cb = CallbackQuery(
            id="test_query",
            from_user=User(id=123, is_bot=False, first_name="Tester"),
            chat_instance="test_chat",
            data=concrete_data,
        )

        matched_handler = None
        for router in ALL_ROUTERS:
            for handler in router.callback_query.handlers:
                res, _ = await handler.check(cb)
                if res:
                    matched_handler = handler
                    break
            if matched_handler:
                break

        assert matched_handler is not None, (
            f"callback_data template '{template}' (resolved to '{concrete_data}') "
            f"has NO matching handler filter in any registered router!"
        )

def test_no_mismatched_action_names():
    """Unifikatsiya qilingan nomlar tekshiruvi: main_menu, back_to_catalog kabi eski nomlar qolmagan."""
    templates = get_all_produced_callback_data()
    
    # Hech qaysi klaviatura yoki handler main_menu yoki back_to_catalog ishlab chiqarmasligi shart
    assert "main_menu" not in templates, "Mismatched callback_data 'main_menu' found! Must be unified to 'menu_main'."
    assert "back_to_catalog" not in templates, "Mismatched callback_data 'back_to_catalog' found! Must be unified to 'menu_catalog'."
    assert "menu_movies" not in templates, "Obsolete 'menu_movies' found! Must be 'catalog_all_movies'."
    assert "menu_series" not in templates, "Obsolete 'menu_series' found! Must be 'catalog_all_series'."

    # Kanonik nomlar mavjudligi
    assert "menu_main" in templates, "'menu_main' canonical callback_data must be present."
    assert "menu_catalog" in templates, "'menu_catalog' canonical callback_data must be present."
