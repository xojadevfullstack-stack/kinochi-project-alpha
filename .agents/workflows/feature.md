# Feature Workflow
1. Read the approved feature specification in `docs/specs/<name>.md` and existing architecture rules.
2. Plan atomic slices where each slice takes 1-2 hours with a git diff <= 200 lines.
3. For each slice: write a failing test first, run test to verify failure.
4. Implement minimal code to make the test pass, following existing project patterns.
5. Execute `make check` and verify zero new regressions.
6. Commit the slice with conventional commit format, update `STATE.md`, and write the progress report.
7. Stop and wait for user approval before moving to the next slice.
