import re
import pytest
from pathlib import Path

CRITICAL_FILES = [
    "backend/app/api/v1/movies.py",
    "backend/app/api/v1/series.py",
    "backend/app/api/v1/content_lookup.py",
    "backend/app/infrastructure/db/repositories/movie_repo.py",
    "backend/app/infrastructure/external/tmdb_client.py",
    "backend/app/infrastructure/telegram/telegram_client.py",
    "bot/handlers/auto_index.py",
]

def test_no_swallowed_exceptions_in_critical_modules():
    """F-013: Tekshirilgan muhim modullarda 'except ...: pass' yashirin xatoliklar qolmagan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    violations = []

    pattern = re.compile(r'^\s*pass\s*$')

    for rel_path in CRITICAL_FILES:
        file_path = root_dir / rel_path
        assert file_path.exists(), f"Fayl topilmadi: {rel_path}"
        lines = file_path.read_text(encoding="utf-8").splitlines()

        for idx, line in enumerate(lines):
            if re.match(r'^\s*except(\s+[^:]*)?:', line):
                # Check next non-empty line
                next_idx = idx + 1
                while next_idx < len(lines) and not lines[next_idx].strip():
                    next_idx += 1
                if next_idx < len(lines) and pattern.match(lines[next_idx]):
                    violations.append(f"{rel_path}:{idx+1} -> {lines[next_idx].strip()}")

    assert not violations, f"Quyidagi joylarda xatoliklar yashirilgan (bare pass topildi):\n" + "\n".join(violations)
