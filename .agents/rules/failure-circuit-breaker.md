---
description: Circuit breaker and recovery rules for repeated failures and tool error fingerprints.
globs: **/*
---

# Failure Recovery & Circuit Breaker Policy

- **Classify before retrying**: Identify error fingerprint (`MODEL_INVALID_OUTPUT`, `JSON_PARSE_ERROR`, `PNPM_WORKSPACE_ERROR`, `TEST_ASSERTION_FAILURE`, `FILE_NOT_FOUND`, `BUILD_TIMEOUT`).
- **Two-Failure Rule**: If an operation fails once, diagnose the root cause and try an alternative approach with new evidence. If the exact same operation fails a second time, stop execution immediately.
- **Never blindly repeat**: Rerunning the identical failed command without a file edit or configuration change is strictly forbidden.
- **Record evidence**: Log the real error output and report the blocker rather than claiming a false positive.
