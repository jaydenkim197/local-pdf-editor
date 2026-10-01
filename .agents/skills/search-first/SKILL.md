---
name: search-first
description: Use before adding new functionality, dependencies, helpers, wrappers, abstractions, integrations, or significant new code. Prefer reuse and the smallest suitable solution.
metadata:
  origin: adapted-from-ECC
---

# Search First

## Purpose
Avoid unnecessary code, dependencies, abstractions, and duplicated functionality.

## Decision Order
1. Reuse an existing implementation in the repository.
2. Use the language/platform standard library or built-in capability.
3. Use an already-installed dependency.
4. Use a small, well-maintained external dependency when it clearly reduces risk or maintenance.
5. Extend or compose an existing solution with a thin adapter.
6. Write custom code only when the options above are unsuitable.

## Workflow
1. Define the required behavior and constraints.
2. Search the repository first: source, tests, config, utilities, dependencies, and relevant docs.
3. Evaluate existing options for fit, maintenance, compatibility, license, dependency cost, and operational complexity.
4. Choose explicitly: REUSE / BUILT-IN / ADOPT / EXTEND / COMPOSE / BUILD.
5. Implement the smallest correct change.

## Guardrails
Do not:
- perform unrelated refactoring
- create abstractions for hypothetical future use
- duplicate existing functionality
- add a dependency without concrete benefit
- create one-use wrappers or modules without justification
- introduce a new architecture layer for a local problem
- claim nothing exists if relevant search channels were unavailable

For substantial additions, briefly record what was checked, what was chosen, and why.
For trivial changes, do not add ceremony.
