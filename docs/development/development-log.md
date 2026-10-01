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

## 2026-10-01 — M1 processing layer

- Implemented the tool registry, job results/progress/cancellation, collision-safe temporary output commits, PDF structural operations/rendering, image PDF export, conversion, resize, and HEIC decode.
- Preserved originals and completed outputs on partial batch failures or cancellation; normalized image orientation and JPEG transparency.
- Added bounded render/resize sizes and encrypted/corrupt input errors.
- 38 Cloud tests passed, covering real PDFs and a licensed HEIC fixture, page order/rotation/reopen, dimensions/formats/EXIF, batches, invalid options, partial failures, cancellation, Unicode names and concurrent output collisions.
- Corrected a PDFium page lifetime API mismatch observed in the first rendering probe. Windows runtime remains pending.

## 2026-10-01 — Shared M1 desktop app and packaging

- Connected all 14 tools to one Qt workspace with categories/cards, drop/picker, ordered files/pages, preview/options, background processing, progress/cancellation, results and local file/folder opening.
- Added host-native onedir packaging, explicit Windows HEIC DLL inclusion, license collection, executable smoke checks, and Windows/Linux CI instructions.
- 59 Cloud tests passed (38 processing, 20 GUI, 1 packaging notice). All 14 tools executed through GUI jobs.
- Built the 192 MB Linux bundle and passed frozen image/PDF/HEIC/Qt smoke. Downloaded all pinned Windows x64 runtime wheels; no Windows binaries were run.
- Reviewed screenshots of home/workspace; corrected hidden option parsing and raw metadata notice collection after observed failures.
- Updated product requirements, architecture, status, verification and Windows setup instructions. Actual Windows GUI, DLL/package behavior and public release compliance remain pending.

## 2026-10-01 — M2 processing and shared workflow

- M1 gate: read requested documentation/skills, confirmed clean main matched GitHub, reran all 59 baseline tests successfully. Pending Windows/release checks do not block source development; no M1 stack change or M3 work.
- Added crop, watermark, numbers, AES-256 protection/correct-password removal, signature images, secure source-free raster redaction, visual comparison and standard AcroForm inspect/fill/flatten. ReportLab/cryptography licenses reviewed from installed publisher metadata.
- Reused registry/options/Context/Result/output layer and one Qt workspace; added point-coordinate region preview, password handling, field editor and relevant controls.
- Corrected writer context reset and radio flattening appearance collisions using observed failures; cloned inside context and rasterized filled appearances for flattening.
- Full suite: 101 passed (29 M2 processor + 13 M2 GUI + 59 baseline/notice). Validated source-content removal, actual pixels, AES passwords, form limits, cancellation/cleanup, batch safety and stale redaction prevention.
- Linux onedir/frozen M1/M2 smoke passed; Windows x64 additions downloaded but not executed. Actual Windows runtime and public distribution compliance remain pending; exact next task is Windows M1/M2 source/packaged validation.

- Final geometry review preserved original rotation/annotation coordinates for crop/overlays; rotated form crop and signature tests verify unchanged form pixels outside the edited region.
