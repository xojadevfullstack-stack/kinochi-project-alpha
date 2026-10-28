#!/usr/bin/env bash
# Git pre-commit hook for Kinochi project.
# Ensures 'make check' passes and STATE.md is staged in every commit.

set -e

echo "=== [PRE-COMMIT HOOK] Verifying commit requirements ==="

# 1. Verify STATE.md is staged in this commit
if ! git diff --cached --name-only | grep -E '^STATE\.md$' > /dev/null 2>&1; then
    echo "ERROR: STATE.md has not been staged for this commit!"
    echo "Every slice and commit must update STATE.md to reflect current progress."
    echo "Please update STATE.md, stage it ('git add STATE.md'), and try again."
    exit 1
fi

echo "✓ STATE.md is staged."

# 2. Run make check (lint, typecheck, test, build)
echo "=== Running 'make check' ==="
if command -v make > /dev/null 2>&1; then
    make check
elif [ -f "./Makefile" ]; then
    echo "Notice: 'make' binary not found on PATH. Executing check steps directly..."
    if [ -f "./backend/.venv/Scripts/python.exe" ]; then
        ./backend/.venv/Scripts/python.exe -m pytest backend/tests/
        ./backend/.venv/Scripts/python.exe -m pytest bot/tests/
    else
        python -m pytest backend/tests/
        python -m pytest bot/tests/
    fi
else
    echo "ERROR: Makefile not found!"
    exit 1
fi

echo "=== [PRE-COMMIT HOOK] All checks passed successfully ==="
exit 0
