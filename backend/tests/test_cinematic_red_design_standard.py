import os
import re
import pytest

WEBSITE_APP_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "website", "app")
)

PAGES_TO_AUDIT = [
    os.path.join(WEBSITE_APP_DIR, "achievements", "page.tsx"),
    os.path.join(WEBSITE_APP_DIR, "catalog", "page.tsx"),
    os.path.join(WEBSITE_APP_DIR, "notifications", "page.tsx"),
    os.path.join(WEBSITE_APP_DIR, "profile", "page.tsx"),
    os.path.join(WEBSITE_APP_DIR, "subscriptions", "page.tsx"),
]

# Disallowed color tokens outside IMDb/Kinopoisk rating contexts
NON_RATING_GOLD_AMBER_REGEX = re.compile(
    r"(amber-\d+|text-rating-gold|bg-rating-gold|border-rating-gold|yellow-\d+)"
)


def test_cinematic_red_design_standard_enforcement():
    """
    BUG-009 Regression Test:
    Cinematic Red Design Standard Law:
    Amber, yellow, and rating-gold classes are strictly forbidden for cards,
    badges, icons, banners, and buttons in website pages.
    All active and accent states must use Primary Red (#E50914 / primary / red).
    """
    violations = []

    for page_path in PAGES_TO_AUDIT:
        assert os.path.exists(page_path), f"Page file does not exist: {page_path}"
        with open(page_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line_no, line in enumerate(lines, 1):
            matches = NON_RATING_GOLD_AMBER_REGEX.findall(line)
            if matches:
                # Disallow amber, yellow, or rating-gold unless explicitly on imdb/kinopoisk rating score
                is_imdb_kinopoisk_score = any(
                    k in line.lower() for k in ["imdb", "kinopoisk", "rating_score", "star_rating"]
                )
                if not is_imdb_kinopoisk_score:
                    violations.append(
                        f"{os.path.basename(os.path.dirname(page_path))}/page.tsx:{line_no} -> {matches} in: {line.strip()}"
                    )

    assert len(violations) == 0, (
        f"Found {len(violations)} Cinematic Red Design Standard violations:\n"
        + "\n".join(violations[:15])
    )
