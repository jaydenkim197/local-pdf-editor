# Project Instructions for Codex

## 1. Source of Truth
Use this order:
1. Current source code and configuration
2. `docs/architecture/`
3. `docs/decisions/`
4. `docs/project-status.md`
5. `docs/development/`
6. `README.md`

Do not treat old plans, stale comments, historical docs, or generated artifacts as current implementation unless confirmed.

## 2. Project Status Model
Use only:
- `PROPOSAL` — under consideration
- `DECISION` — selected, not necessarily implemented
- `PLANNED` — approved/scheduled work
- `IMPLEMENTED` — exists in code/config/hardware integration
- `VERIFIED` — passed defined validation criteria
- `BLOCKED` — cannot proceed due to unresolved dependency/constraint
- `DEFERRED` — intentionally postponed
- `SUPERSEDED` — replaced by a newer decision/design/implementation

Important:
`DECISION != IMPLEMENTED`
`IMPLEMENTED != VERIFIED`

Do not promote status without evidence.

## 3. Development Philosophy
Prefer the smallest correct change.

Before creating new code:
1. Reuse existing project code.
2. Prefer built-in or standard-library capabilities.
3. Prefer already-installed dependencies.
4. Add a dependency only for clear reliability/maintenance benefit.
5. Create abstractions only when current concrete requirements justify them.

Avoid unrelated refactoring, speculative abstractions, duplicate implementations, unnecessary wrappers/dependencies, broad architecture changes for local problems, and style-only rewrites.

Use the repository-local `search-first` skill at `.agents/skills/search-first/SKILL.md` for substantial new functionality, integrations, dependencies, helpers, wrappers, or abstractions.

## 4. Before Editing
For non-trivial work:
1. Locate the current implementation.
2. Read relevant surrounding code.
3. Identify callers, dependencies, tests, and config.
4. Check relevant architecture/decision docs.
5. Determine the smallest safe implementation.
6. If architecture changes, state the impact before implementing.

## 5. Verification
Use the repository-local `verification-loop` skill at `.agents/skills/verification-loop/SKILL.md` after meaningful changes and before reporting completion.

Never claim a check passed unless it was actually run and observed.

Keep these states distinct:
- implemented
- statically checked
- automated-tested
- integration-verified
- hardware-verified
- not verified

Do not build a large testing framework only because tests are absent.

## 6. Hardware / AI / Embedded Work
When hardware, edge AI, robotics, IoT, sensors, cameras, GPU acceleration, firmware, or external devices are involved:
- separate software correctness from target-device verification
- define measurable pass/fail criteria before experiments when practical
- preserve reproducible configuration and benchmark conditions
- do not claim target-device performance from desktop/simulated results
- record hardware-specific limitations
- prefer MVP validation before optional optimization

## 7. Documentation
Update:
- `docs/project-status.md` for current state
- `docs/architecture/` for implemented structure and runtime/data flow
- `docs/decisions/` for important decisions
- `docs/development/` for useful chronological records

When a decision is replaced, mark the old record `SUPERSEDED` and link to the replacement when practical.

Do not describe `PLANNED` work as implemented or `IMPLEMENTED` work as verified without evidence.

## 8. Git Policy
Codex may autonomously:
- create/switch branches
- stage files
- commit
- push normal branches
- inspect history/diffs
- create logical checkpoint commits when useful

Before committing:
1. Review the diff.
2. Run relevant verification.
3. Exclude temporary/debug/generated files that should not be versioned.
4. Use a concise commit message describing the actual change.

Destructive history changes require explicit user instruction:
- force push / force-with-lease
- reset --hard
- rewriting/deleting shared history
- deleting active remote branches

Never commit secrets or credentials.

## 9. Scope Control
Complete the requested task, not adjacent improvements.

If an unrelated issue is found:
- fix it only if required for correctness/safety
- otherwise report it without expanding scope

## 10. Completion
For substantial work, report:
- what changed
- what was verified
- what remains unverified
- docs updated
- branch/commit/push status
- blockers or known limitations

## 11. Cloud and Local Development

Repository-local skills are canonical for this project. Optional personal/global installations may be used for other local projects; Cloud tasks rely on the copies committed here.

Cloud tasks already have an isolated workspace. Use the existing checkout; do not create a Git worktree unless the user explicitly requests one.

## 12. Product Scope and Verification

Read `docs/product-spec.md` and `docs/implementation-plan.md` before application changes. This is a Windows-first, fully local PDF/image utility. Preserve explicit excluded features and the authorized M1/M2/M3 scope; do not create future feature placeholders. GitHub owns project history and repository documentation preserves context.

Use the stack in `docs/decisions/ADR-0001-m1-stack.md` and M2 boundaries in `docs/decisions/ADR-0002-m2-pdf-operations.md`; revisit settled decisions only with new evidence. Features reuse the registry, shared workspace, processor job contract, and output layer. Secure redaction must never retain original source content behind visual masks; inspect actual output objects and rendered pixels. Crop and signature images have different purposes from redaction and certificate signing.

M3 uses `docs/decisions/ADR-0003-m3-local-engines.md` and `docs/m3-engines.md`. OCR requires an installed Tesseract 5 and local language data, never runtime downloads. PDF/A is image-based PDF/A-1b; verify conformance with a real independent validator when modifying that conversion. HTML is basic local rich text via Qt Gui QPdfWriter, without browser/JavaScript/network resources. Preserve explicit limitations and external-engine distribution boundaries.

Run relevant tests before coherent checkpoints. Update project status, current architecture, development log and verification evidence when behavior changes. Cloud/offscreen checks are not Windows GUI or packaged executable checks. Do not mark Windows runtime VERIFIED without observed Windows results.
