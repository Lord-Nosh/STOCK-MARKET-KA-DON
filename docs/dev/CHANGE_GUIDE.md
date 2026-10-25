# SMKD — Change Impact & Implementation Guide

This guide establishes the mandatory procedure for proposing, assessing, and implementing changes in SMKD.

---

## 1. The Change-Impact Plan Template

Before modifying code that touches public interfaces, database models, or shared components, fill out this brief plan:

```markdown
TASK: SMKD-XXXX (or DEV-XXXX)

OBJECTIVE:
Why is this change required? What feature or bug does it address?

ROOT_CAUSE / EVIDENCE:
What exact log, test failure, or requirement proves the need?

FILES_TO_EDIT:
1. path/to/file.ext — Reason for change
2. path/to/second_file.ext — Reason for change

DEPENDENCIES & CONSUMERS:
- Callers / APIs:
- Downstream UI components:
- External packages:

EXPECTED BEHAVIOR:
What will the system do after this patch that it does not do now?

REGRESSION RISKS:
What existing workflows, tests, or contracts could be broken?

VERIFICATION COMMANDS:
1. Exact command (e.g., pnpm -C fast-framework test)
2. Exact command (e.g., python -m unittest discover -s ...)

DOCUMENTATION AFFECTED:
Which documents in docs/ must be updated?
```

---

## 2. Risk Sizing & Autonomy Boundaries

- **Low-Risk (Bug fix in isolated helper, style tweak, documentation typo)**:
  - Proceed autonomously (`AUTO`). Plan can be a 3-bullet mental checklist.
- **Medium-Risk (API endpoint addition, package dependency change, component refactor)**:
  - Proceed autonomously under `AUTO + REPORT`. Add dependency, update matching lockfile, document change in task checkpoint.
- **High-Risk (Modifying real SQLite databases, deleting user data, Git reset, public secrets)**:
  - Halt and request explicit approval (`ASK FIRST`).
