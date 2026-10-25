---
name: smkd-debug-failure
description: Diagnoses and resolves test failures, compiler/bundler errors, and tool errors. Prevents permission loops and infinite retry cycles.
---

# SMKD Debug Failure Procedure

Use this procedure when a test fails, a build breaks, or a tool returns an error.

## Failure Classification

1. **Tool / CLI Invocation Error**:
   - Inspect tool argument syntax and shell differences (Windows pwsh vs bash).
   - Check file existence and directory paths with forward slashes or escaped backslashes.
   - Do not repeat the identical invalid command.

2. **Package / Manifest Serialization Error**:
   - Inspect JSON/YAML syntax directly around the reported line.
   - Look for copy-paste duplicates or unescaped characters.
   - Verify package version availability against registry.

3. **Code / Test Regression**:
   - Read exact stack trace and line numbers.
   - Isolate whether it is a contract mismatch (e.g. backend route vs frontend model) or business logic assertion.
   - Fix at the single authoritative source of truth.

## The Two-Failure Rule
- Attempt 1: Diagnose specific cause from error output, apply targeted fix, rerun check.
- Attempt 2: If the same check fails with the same error, do not repeat blindly.
- Action on 2nd Failure:
  - Stop the failing loop.
  - Record the actual command output and state.
  - Formulate an alternative path or request user input with exact diagnostic logs.
