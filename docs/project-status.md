# Project Status

Last updated: 2026-10-01

## Current Goal

M1 implementation is complete for the offline Windows-first PDF/image utility in [product-spec.md](product-spec.md). Cloud processing/offscreen validation is complete. Actual Windows runtime validation remains pending.

## Status Model

`PROPOSAL / DECISION / PLANNED / IMPLEMENTED / VERIFIED / BLOCKED / DEFERRED / SUPERSEDED`

`DECISION != IMPLEMENTED` and `IMPLEMENTED != VERIFIED`.

## Feature Matrix

VERIFIED below means observed Linux Cloud results only; Windows runtime remains PLANNED.

| Feature | Implementation | Cloud | Windows runtime |
|---|---|---|---|
| PDF merge | IMPLEMENTED | VERIFIED | PLANNED |
| PDF split (individual selected pages) | IMPLEMENTED | VERIFIED | PLANNED |
| Page reorder/delete/import/rotation | IMPLEMENTED | VERIFIED | PLANNED |
| PDF → JPEG/PNG | IMPLEMENTED | VERIFIED | PLANNED |
| JPEG/PNG → PDF | IMPLEMENTED | VERIFIED | PLANNED |
| HEIC → JPEG/PNG | IMPLEMENTED | VERIFIED | PLANNED |
| JPEG ↔ PNG | IMPLEMENTED | VERIFIED | PLANNED |
| Batch resize: presets/arbitrary %, dimensions/aspect | IMPLEMENTED | VERIFIED | PLANNED |
| EXIF orientation | IMPLEMENTED | VERIFIED | PLANNED |
| Cards/categories/shared workspace | IMPLEMENTED | VERIFIED | PLANNED |
| Drop/selection/remove/reorder/preview/results | IMPLEMENTED | VERIFIED | PLANNED |
| Output safety/errors/progress/cancellation | IMPLEMENTED | VERIFIED | PLANNED |
| Host-native package/notice collection | IMPLEMENTED | VERIFIED | PLANNED |
| Windows package smoke | IMPLEMENTED | PLANNED | PLANNED |
| Public binary distribution compliance | PLANNED | PLANNED | PLANNED |
| Additional agent tools | DEFERRED | DEFERRED | DEFERRED |

## Evidence and Decisions

- Original baseline skills preserved; repository-local paths checked.
- 59 tests passed: 38 processors, 20 offscreen GUI, 1 package notice collection. All 14 tools exercised through the GUI.
- Linux onedir build and bundled PDF/image/HEIC/Qt smoke passed.
- Windows x64 Python 3.12 dependency wheels downloaded, not executed.
- [ADR-0001](decisions/ADR-0001-m1-stack.md): Python 3.12, Qt Widgets, pypdf/PDFium, Pillow, decoder-only pi-heif, pytest, PyInstaller onedir.
- [verification.md](verification.md) contains commands and pending Windows checks.

## Known Limitations

- Actual Windows GUI and frozen executable have not been run in Cloud.
- pi-heif is discontinued; support/security and redistribution source/notice material need review before public release.
- Primary 8-bit HEIC output, cooperative cancellation, bounded large buffers; see product-spec.md.
- Linux bundle and Windows wheel availability do not prove Windows runtime compatibility.
- Git push and Cloud environment publication are separate.

## Next Incomplete Task

Run the Windows source/packaged app checks in verification.md, record observed results, and fix any Windows-specific failures. Mark Windows runtime VERIFIED only with observed results.
