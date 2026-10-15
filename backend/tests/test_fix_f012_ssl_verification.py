import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_f012_no_hardcoded_ssl_false_in_scraper():
    """F-012 regression: scraper files must not hardcode ssl=False."""
    scraper_dir = os.path.join(REPO_ROOT, "scraper")
    violating_lines = []

    for root, _, files in os.walk(scraper_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        # Match ssl=False without env flag
                        if "ssl=False" in line and not line.strip().startswith("#"):
                            violating_lines.append(f"{file}:{line_num}: {line.strip()}")

    assert not violating_lines, f"Found hardcoded ssl=False in scraper:\n" + "\n".join(violating_lines)
