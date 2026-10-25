---
name: smkd-verify-change
description: Deterministic verification procedure. Runs builds, tests, schema checks, and diff analysis to guarantee changes meet the Definition of Done.
---

# SMKD Verify Change Procedure

Execute this procedure before marking any task as complete or updating its status to `DONE`.

## Inputs
- Task ID / Task directory in `.runtime/tasks/<task-id>/`
- Target modified files
- Expected test commands

## Verification Sequence

1. **Working Tree Scope Check**:
   - Run `git status --porcelain`.
   - Ensure only files within the task's `allowed_paths` were modified.
   - If unrelated files were touched, revert or isolate them before proceeding.

2. **Run Focused Tests**:
   - For backend changes: run pytest on affected test modules (`stock-signal-bot/backend/app/tests/`).
   - For frontend changes: run vitest on affected unit/integration tests (`pnpm -C fast-framework run test`).
   - Capture exact exit code, stdout, and stderr.

3. **Check Build Integrity**:
   - Run workspace typecheck/build if interfaces or exports changed.
   - Ensure zero TypeScript or bundling errors.

4. **Verify Diff & Evidence**:
   - Save the finalized diff to `.runtime/tasks/<task-id>/diff-after.patch`.
   - Record test outputs into `.runtime/tasks/<task-id>/verification.json`.

5. **Stop Condition**:
   - Never claim success if a test failed or was skipped due to an unresolved error.
   - If tests pass, record status as `DONE`.
