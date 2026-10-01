# Development Log

## 2026-10-01 — Cloud-compatible development baseline

### Changes
- Copied search-first and verification-loop from the supplied baseline ZIP into repository-local skill directories without modifying their contents.
- Adapted the supplied project instructions to use repository-local skills and the existing Cloud checkout.
- Added project state, architecture, and decision documentation; updated the project README.
- Did not install extra tools or implement PDF functionality.

### Verification
- Compared both installed SKILL.md files byte for byte with their ZIP sources.
- Checked required files, local skill references, the preserved status model, and Git whitespace errors.
- No application build or tests exist, so none were run.

### Next
Define the PDF editor MVP and target platform before selecting dependencies.

## 2026-10-01 — M1 foundation

- Recorded the full M1 scope and excluded features in product-spec.md.
- Selected Python/Qt Widgets, pypdf/PDFium, Pillow, decoder-only pi-heif, pytest and PyInstaller in ADR-0001.
- Installed pinned wheels and the editable project; checked dependency consistency and offscreen Qt startup.
- Official documentation websites returned proxy 403; research used publisher wheel metadata, license files and runtime probes.
- Windows runtime remains unverified. Next: processors and shared UI.
