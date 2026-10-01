# Architecture / Technical Decisions

Use ADR-style files for decisions future sessions need to understand.

## ADR Status
Use one of:
- `PROPOSAL`
- `DECISION`
- `SUPERSEDED`

Implementation status belongs in `docs/project-status.md`.

This keeps:
`DECISION != IMPLEMENTED`
`IMPLEMENTED != VERIFIED`

## Filename
`ADR-0001-short-decision-title.md`

## Template

```md
# ADR-0001: Decision Title

## Status
PROPOSAL | DECISION | SUPERSEDED

## Date
YYYY-MM-DD

## Context
What problem or constraint required a decision?

## Decision
What was chosen?

## Alternatives Considered
What realistic alternatives were considered?

## Rationale
Why was this option chosen?

## Consequences
What trade-offs, constraints, or follow-up work result?

## Implementation Tracking
Link to the relevant item in `docs/project-status.md` if applicable.

## Supersedes / Superseded By
Optional links to related ADRs.
```
