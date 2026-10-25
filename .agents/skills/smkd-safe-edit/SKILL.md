---
name: smkd-safe-edit
description: Use whenever modifying existing SMKD code, fixing a bug, changing an API contract, editing dependencies, or resuming an interrupted implementation. Preserves existing changes and avoids unrelated modifications.
---

# SMKD Safe Edit Procedure

Use this procedure for autonomous, bounded modifications within the SMKD repository.

## Inputs
- Task ID / Objective
- Target modules / files
- Acceptance criteria & verification command

## Procedure

1. **Baseline Inspection**:
   - Run `git status` to observe uncommitted work.
   - Never overwrite or discard existing uncommitted changes.
2. **Search Existing Implementations**:
   - Check if the function, class, or endpoint already exists before authoring a new one.
3. **Localized Patch**:
   - Apply the smallest clean modification.
   - If a dependency is needed for the task (e.g. library package), add it and update the lockfile (`AUTO + REPORT`).
4. **Immediate Diff Inspection**:
   - Run `git diff <file>` to verify only intended edits were made.
5. **Focused Verification**:
   - Run the specific test or build script for the modified module.
   - Capture real command exit codes and output.
6. **Two-Failure Rule**:
   - If an edit or command fails, inspect the error.
   - If the exact same operation fails twice, pause, preserve evidence, and try an alternative approach or report the blocker.

## Completion Criteria
- Intended files modified cleanly.
- Tests or builds executed with output verified.
- Summary reported back with changed files and verification evidence.
