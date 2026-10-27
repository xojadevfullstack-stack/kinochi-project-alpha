import subprocess
import sys
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _run_script(args: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": f"{REPO_ROOT}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"}
    return subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT, env=env)


def test_f009_migrate_18plus_requires_flag():
    """F-009 regression: scripts/migrate_18plus_and_reports.py must require --i-know-this-bypasses-gate."""
    script_path = os.path.join(REPO_ROOT, "scripts", "migrate_18plus_and_reports.py")
    result = _run_script([sys.executable, script_path])
    assert result.returncode != 0
    assert "i-know-this-bypasses-gate" in (result.stdout + result.stderr)


def test_f009_fix_anime_posters_requires_flag():
    """F-009 regression: scripts/fix_anime_posters_db.py must require --i-know-this-bypasses-gate."""
    script_path = os.path.join(REPO_ROOT, "scripts", "fix_anime_posters_db.py")
    result = _run_script([sys.executable, script_path])
    assert result.returncode != 0
    assert "i-know-this-bypasses-gate" in (result.stdout + result.stderr)


def test_f009_inspect_and_fix_adult_requires_flag_on_apply():
    """F-009 regression: backend/scripts/inspect_and_fix_adult.py with --apply must require --i-know-this-bypasses-gate."""
    script_path = os.path.join(REPO_ROOT, "backend", "scripts", "inspect_and_fix_adult.py")
    result = _run_script([sys.executable, script_path, "--apply"])
    assert result.returncode != 0
    assert "i-know-this-bypasses-gate" in (result.stdout + result.stderr)
