---
description: Conditional rules for modifying TypeScript, Vite, components, and state management in fast-framework UI.
globs: fast-framework/packages/**/*.ts,fast-framework/packages/**/*.json
---

# TypeScript & Frontend Workspace Rules

- Maintain valid JSON syntax across all `package.json` manifests. Never leave trailing commas or duplicated object keys.
- Search for existing components or services before creating new files (e.g., check `components/` and `departments/` to prevent duplicate implementations).
- Adhere to the single source of truth for UI state in `state/store.ts`.
- When modifying chart components, verify types against `@zuari` design tokens and `lightweight-charts`.
- Verify build or test integrity via `pnpm -C fast-framework run test` before finishing work.
