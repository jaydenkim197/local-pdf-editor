# Project Status

Last updated: 2026-10-01

## Current Goal

M1 and M2 implementation is complete for the offline Windows-first PDF/image utility in [product-spec.md](product-spec.md). Cloud processing/offscreen validation is complete; actual Windows runtime validation remains pending. M3 is not implemented or planned.

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

## M2 Feature Matrix

| Feature | Implementation | Cloud | Windows runtime |
|---|---|---|---|
| PDF crop | IMPLEMENTED | VERIFIED | PLANNED |
| Watermark / page numbers | IMPLEMENTED | VERIFIED | PLANNED |
| AES-256 protection / correct-password removal | IMPLEMENTED | VERIFIED | PLANNED |
| Signature image insertion | IMPLEMENTED | VERIFIED | PLANNED |
| Secure raster redaction | IMPLEMENTED | VERIFIED | PLANNED |
| Visual PDF comparison | IMPLEMENTED | VERIFIED | PLANNED |
| Basic AcroForm inspection/fill | IMPLEMENTED | VERIFIED | PLANNED |
| Image-based form flattening | IMPLEMENTED | VERIFIED | PLANNED |
| Shared region selection / masked transient passwords / field editor | IMPLEMENTED | VERIFIED | PLANNED |

## Evidence and Decisions

- Original baseline skills preserved; repository-local paths checked.
- 101 tests passed: 38 M1 processors, 29 M2 processors, 20 M1 GUI/regression, 13 M2 GUI, 1 package notice collection. All 23 tools exercised through the shared GUI.
- Linux onedir build and bundled M1/M2 PDF/image/HEIC/AES/form/Qt smoke passed.
- Windows x64 Python 3.12 dependency wheels, including M2 additions, downloaded but not executed.
- [ADR-0001](decisions/ADR-0001-m1-stack.md): Python 3.12, Qt Widgets, pypdf/PDFium, Pillow, decoder-only pi-heif, pytest, PyInstaller onedir.
- [ADR-0002](decisions/ADR-0002-m2-pdf-operations.md): retain M1 stack; add BSD ReportLab and Apache/BSD cryptography, with lossless raster redaction/flattening.
- [verification.md](verification.md) contains commands and pending Windows checks.

## Known Limitations

- Actual Windows GUI and frozen executable have not been run in Cloud.
- pi-heif is discontinued; support/security and redistribution source/notice material need review before public release.
- Primary 8-bit HEIC output, cooperative cancellation, bounded large buffers; see product-spec.md.
- Linux bundle and Windows wheel availability do not prove Windows runtime compatibility.
- Secure redaction and form flattening discard all text search/vector/interactivity; only explicitly marked visible regions are erased. Crop is not security deletion; signatures are image insertion, not certificate signing.
- Forms support standard text (ASCII edits), check/radio and single-choice fields, not XFA or all possible PDF form behavior. Comparison is visual by page index, not semantic matching.
- Git push and Cloud environment publication are separate.

## Next Incomplete Task

Run the Windows source/packaged app checks in verification.md, record observed results, and fix any Windows-specific failures. Mark Windows runtime VERIFIED only with observed results.
