import re
from pathlib import Path

def test_backend_issue_001_no_bare_swallowed_exceptions():
    r"""BACKEND-ISSUE-001: Backend code in reports.py, scraper.py, main.py, and cache.py
    must NOT have bare `except Exception:\s*pass` without logging.
    """
    root = Path(__file__).resolve().parent.parent.parent
    backend_app = root / "backend" / "app"

    target_files = [
        backend_app / "api" / "v1" / "reports.py",
        backend_app / "api" / "v1" / "scraper.py",
        backend_app / "main.py",
        backend_app / "core" / "cache.py",
    ]

    bare_pattern = re.compile(r"except\s+(Exception|BaseException)\s*:\s*\n\s*pass\b")

    violations = []
    for f in target_files:
        assert f.exists(), f"Target file does not exist: {f}"
        content = f.read_text(encoding="utf-8")
        matches = list(bare_pattern.finditer(content))
        if matches:
            violations.append(f"{f.name} has {len(matches)} bare `except Exception: pass` blocks")

    assert not violations, f"Violations of zero-swallowed-exceptions rule found: {violations}"
