# Test-Driven Development (TDD) Workflow

## Purpose
Ensure every bug fix and feature has a verified automated test before any implementation code is written. Eliminate half-baked code and untested assumptions.

## Execution Steps
1. **Understand Requirement:** Read the specification (`docs/specs/<name>.md`) and identify the exact expected behavior and boundary conditions.
2. **Write Failing Test First (RED):**
   - Create or locate test file in `backend/tests/` or corresponding test directory.
   - Write an integration or unit test asserting the expected behavior.
   - Run the test using pytest:
     ```bash
     backend/.venv/Scripts/pytest.exe <path/to/test.py> -k "<test_name>"
     ```
   - **MANDATORY:** Verify that the test explicitly FAILS for the expected reason (RED). Never write implementation code until RED is proven.
3. **Write Minimal Implementation (GREEN):**
   - Write the simplest, cleanest code to make the failing test pass.
   - Do NOT add unrequested features or speculative optimizations.
   - Re-run the test to verify it PASSES (GREEN).
4. **Refactor & Cleanup:**
   - Clean up code formatting, eliminate duplication, and verify docstrings.
   - Keep diff under 200 lines.
5. **Quality Gate Verification:**
   - Run `make check` to ensure no regressions across the entire test suite.
