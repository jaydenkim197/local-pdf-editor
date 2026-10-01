# Current Architecture

## Implemented Structure

| Component | Responsibility | Status |
|---|---|---|
| AGENTS.md | Project instructions and status model | IMPLEMENTED |
| .agents/skills/search-first/ | Search and reuse workflow | IMPLEMENTED |
| .agents/skills/verification-loop/ | Evidence-based verification workflow | IMPLEMENTED |
| docs/ | Repository-owned state, decisions, and development history | IMPLEMENTED |

## Runtime and Data Flow
No PDF application runtime or data flow exists yet. The PDF engine, GUI framework, storage model, and runtime dependencies are not selected.

## Constraints
- Repository-local skills must work without a Windows personal/global skill directory.
- Cloud tasks use their existing isolated checkout; no additional worktree is needed.
- Source code and configuration take precedence over plans and generated diagrams.
- Additional agent tools are deferred until concrete project needs justify them.
