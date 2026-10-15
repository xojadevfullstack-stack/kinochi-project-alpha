import subprocess
import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_f009_migrate_18plus_requires_flag():
    """F-009 regression: scripts/migrate_18plus_and_reports.py must require --i-know-this-bypasses-gate."""
    script_path = os.path.join(REPO_ROOT, "scripts", "migrate_18plus_and_reports.py")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    assert result.returncode != 0
    assert "i-know-this-bypasses-gate" in (result.stdout + result.stderr)


def test_f009_fix_anime_posters_requires_flag():
    """F-009 regression: scripts/fix_anime_posters_db.py must require --i-know-this-bypasses-gate."""
    script_path = os.path.join(REPO_ROOT, "scripts", "fix_anime_posters_db.py")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    assert result.returncode != 0
    assert "i-know-this-bypasses-gate" in (result.stdout + result.stderr)


def test_f009_inspect_and_fix_adult_requires_flag_on_apply():
    """F-009 regression: backend/scripts/inspect_and_fix_adult.py with --apply must require --i-know-this-bypasses-gate."""
    script_path = os.path.join(REPO_ROOT, "backend", "scripts", "inspect_and_fix_adult.py")
    result = subprocess.run([sys.executable, script_path, "--apply"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "i-know-this-bypasses-gate" in (result.stdout + result.stderr)
