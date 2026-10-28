# Bugfix Workflow
1. Write an automated test that reproduces the reported bug and fails.
2. State a clear hypothesis explaining the root cause based on code and logs.
3. Apply the minimal necessary fix without introducing unrelated refactoring.
4. Add a regression test to permanently guard against recurrence.
5. Execute `make check` to verify the fix and ensure no existing tests broke.
6. If 3 fix attempts fail: stop immediately, list hypotheses with evidence, revert to the plan, and ask the user.
