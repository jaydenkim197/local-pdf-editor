# Project Status

Last updated: 2026-10-02 (Asia/Seoul)

## Current Goal

M1, M2 and M3 implementation is complete for the offline Windows-first PDF/image utility in [product-spec.md](product-spec.md). Cloud processing/offscreen/native package validation is complete; actual Windows runtime validation remains pending. OCR integrates installed local Tesseract 5; PDF/A is image-based PDF/A-1b and HTML is basic local rich text.

Hosted Windows source and native frozen verification passed in [run 36917030277](https://github.com/jaydenkim197/local-pdf-editor/actions/runs/36917030277) for 22d7a9a. Its development ZIP is available (58.5 MB Actions artifact); see [Windows use](windows-use.md). The executable passed Unicode relocation, Python-free PATH, outbound blocking, native Windows Qt at 100%/150% and actual English/Korean OCR with Tesseract v5.5.3.20260724. Windows independent Preflight is being enabled; physical clean-machine/manual desktop and public-release checks remain pending.

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

## M3 Feature Matrix

| Feature | Implementation | Cloud | Windows runtime |
|---|---|---|---|
| Lossless structural / optional lossy image compression | IMPLEMENTED | VERIFIED | PLANNED |
| Local Tesseract OCR integration / searchable image PDF | IMPLEMENTED | VERIFIED | PLANNED |
| Readable damaged-PDF repair / strict reopen / render | IMPLEMENTED | VERIFIED | PLANNED |
| Raster PDF/A-1b / independent Preflight conformance | IMPLEMENTED | VERIFIED | PLANNED |
| Basic local HTML / images / direct Qt PDF writing | IMPLEMENTED | VERIFIED | PLANNED |
| Shared M3 controls / jobs / errors / cancellation | IMPLEMENTED | VERIFIED | PLANNED |

## Evidence and Decisions

- Original baseline skills preserved; repository-local paths checked.
- 155 Cloud tests passed: the 143 milestone cases, 8 audit regressions and 4 version-format cases. All 28 tools exercised through the shared GUI. Four PDF/A specimens passed real Apache PDFBox Preflight 3.0.6 validation. The earlier ordinary-source negative control was correctly rejected.
- Linux onedir build and bundled M1/M2/M3 PDF/image/HEIC/AES/form/HTML/ICC/Qt smoke including real installed Tesseract OCR passed.
- [2026-10-02 requirements audit](verification-audit-2026-10-02.md) reproduced and corrected fractional-page redaction edge pixels, missing form appearances in PDF image exports, and optional compression's CMYK/color-profile/layer changes. Fresh source/frozen smoke includes the redaction and form-export regressions.
- English/Korean `eng+kor` OCR sample passed with explicit Unicode data folder and official locally installed data; sample evidence, not a general accuracy guarantee.
- Hosted Windows source tests and the native executable now passed after fixing OCR version identification and default HTML font loading; independent Windows conformance and physical/manual checks remain separate.
- [ADR-0001](decisions/ADR-0001-m1-stack.md): Python 3.12, Qt Widgets, pypdf/PDFium, Pillow, decoder-only pi-heif, pytest, PyInstaller onedir.
- [ADR-0002](decisions/ADR-0002-m2-pdf-operations.md): retain M1 stack; add BSD ReportLab and Apache/BSD cryptography, with lossless raster redaction/flattening.
- [ADR-0003](decisions/ADR-0003-m3-local-engines.md): existing dependencies, direct Qt Gui PDF writer, external local Tesseract 5, licensed ICC v2 and independent developer-only Preflight. No new Python runtime packages or OCR binaries/models redistributed.
- [verification.md](verification.md) contains commands and pending Windows checks.

## Known Limitations

- Native Windows GUI-backend/frozen smoke passed on a hosted Windows runner; physical user-PC display/Explorer/dialogs and clean-machine execution remain unverified.
- pi-heif is discontinued; support/security and redistribution source/notice material need review before public release.
- Primary 8-bit HEIC output, cooperative cancellation, bounded large buffers; see product-spec.md.
- Linux bundle and Windows wheel availability do not prove Windows runtime compatibility.
- Secure redaction and form flattening discard all text search/vector/interactivity; only explicitly marked visible regions are erased. Crop is not security deletion; signatures are image insertion, not certificate signing.
- Redactions made before the audit fix can retain edge pixels on fractional page sizes. Regenerate affected outputs from originals with this revision and inspect marked boundaries before sharing.
- Forms support standard text (ASCII edits), check/radio and single-choice fields, not XFA or all possible PDF form behavior. Comparison is visual by page index, not semantic matching.
- Git push and Cloud environment publication are separate.
- OCR needs installed engine/languages/pdf.ttf and recognition review; the package is not self-contained for OCR. Repair cannot recover missing bytes. Compression may increase size; optional image compression is lossy. PDF/A rasterizes to PDF/A-1b and loses text/vector/interactivity. HTML supports basic Qt rich text, not JavaScript/external CSS/browser fidelity.

## Next Incomplete Task

On Windows x64/Python 3.12, install local Tesseract 5 with English/Korean data, run the full suite and frozen `--ocr-smoke`, then offline clean-machine M1/M2/M3 checks in verification.md. Record actual results and fix Windows failures; mark Windows runtime VERIFIED only with observed evidence. Public release compliance remains separate.
