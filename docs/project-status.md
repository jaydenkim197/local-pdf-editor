# Project Status

Last updated: 2026-10-02 (Asia/Seoul)

## Current Goal

M1, M2 and M3 implementation is complete for the offline Windows-first PDF/image utility in [product-spec.md](product-spec.md). Cloud and hosted Windows automated processing/GUI/native package validation passed. Physical clean-machine/manual desktop and public-release checks remain pending. OCR integrates installed local Tesseract 5; PDF/A is image-based PDF/A-1b and HTML is basic local rich text.

Hosted Windows source, independent Preflight and native frozen verification passed in [run 36919001214](https://github.com/jaydenkim197/local-pdf-editor/actions/runs/36919001214) for 578a042. Both Windows and Linux reported 155 cases, 0 failures/errors/skips and four independently validated PDF/A specimens. Its Windows development ZIP is available (58.5 MB Actions artifact); see [Windows use](windows-use.md). The executable passed Unicode relocation, Python-free PATH, outbound blocking, native Windows Qt at 100%/150% and actual English/Korean OCR with Tesseract v5.5.3.20260724.

## Status Model

`PROPOSAL / DECISION / PLANNED / IMPLEMENTED / VERIFIED / BLOCKED / DEFERRED / SUPERSEDED`

`DECISION != IMPLEMENTED` and `IMPLEMENTED != VERIFIED`.

## Feature Matrix

VERIFIED denotes observed automated checks on the named platform. Windows covers hosted source processing/offscreen GUI and representative frozen native-backend smoke; physical/manual desktop and clean-machine checks remain PLANNED. The scope is detailed in verification.md.

| Feature | Implementation | Cloud | Windows automated |
|---|---|---|---|
| PDF merge | IMPLEMENTED | VERIFIED | VERIFIED |
| PDF split (individual selected pages) | IMPLEMENTED | VERIFIED | VERIFIED |
| Page reorder/delete/import/rotation | IMPLEMENTED | VERIFIED | VERIFIED |
| PDF → JPEG/PNG | IMPLEMENTED | VERIFIED | VERIFIED |
| JPEG/PNG → PDF | IMPLEMENTED | VERIFIED | VERIFIED |
| HEIC → JPEG/PNG | IMPLEMENTED | VERIFIED | VERIFIED |
| JPEG ↔ PNG | IMPLEMENTED | VERIFIED | VERIFIED |
| Batch resize: presets/arbitrary %, dimensions/aspect | IMPLEMENTED | VERIFIED | VERIFIED |
| EXIF orientation | IMPLEMENTED | VERIFIED | VERIFIED |
| Cards/categories/shared workspace | IMPLEMENTED | VERIFIED | VERIFIED |
| Drop/selection/remove/reorder/preview/results | IMPLEMENTED | VERIFIED | VERIFIED |
| Output safety/errors/progress/cancellation | IMPLEMENTED | VERIFIED | VERIFIED |
| Host-native package/notice collection | IMPLEMENTED | VERIFIED | VERIFIED |
| Windows package smoke | IMPLEMENTED | DEFERRED | VERIFIED |
| Public binary distribution compliance | PLANNED | PLANNED | PLANNED |
| Additional agent tools | DEFERRED | DEFERRED | DEFERRED |

## M2 Feature Matrix

| Feature | Implementation | Cloud | Windows automated |
|---|---|---|---|
| PDF crop | IMPLEMENTED | VERIFIED | VERIFIED |
| Watermark / page numbers | IMPLEMENTED | VERIFIED | VERIFIED |
| AES-256 protection / correct-password removal | IMPLEMENTED | VERIFIED | VERIFIED |
| Signature image insertion | IMPLEMENTED | VERIFIED | VERIFIED |
| Secure raster redaction | IMPLEMENTED | VERIFIED | VERIFIED |
| Visual PDF comparison | IMPLEMENTED | VERIFIED | VERIFIED |
| Basic AcroForm inspection/fill | IMPLEMENTED | VERIFIED | VERIFIED |
| Image-based form flattening | IMPLEMENTED | VERIFIED | VERIFIED |
| Shared region selection / masked transient passwords / field editor | IMPLEMENTED | VERIFIED | VERIFIED |

## M3 Feature Matrix

| Feature | Implementation | Cloud | Windows automated |
|---|---|---|---|
| Lossless structural / optional lossy image compression | IMPLEMENTED | VERIFIED | VERIFIED |
| Local Tesseract OCR integration / searchable image PDF | IMPLEMENTED | VERIFIED | VERIFIED |
| Readable damaged-PDF repair / strict reopen / render | IMPLEMENTED | VERIFIED | VERIFIED |
| Raster PDF/A-1b / independent Preflight conformance | IMPLEMENTED | VERIFIED | VERIFIED |
| Basic local HTML / images / direct Qt PDF writing | IMPLEMENTED | VERIFIED | VERIFIED |
| Shared M3 controls / jobs / errors / cancellation | IMPLEMENTED | VERIFIED | VERIFIED |

## Evidence and Decisions

- Original baseline skills preserved; repository-local paths checked.
- 155 Cloud tests passed: the 143 milestone cases, 8 audit regressions and 4 version-format cases. All 28 tools exercised through the shared GUI. Four PDF/A specimens passed real Apache PDFBox Preflight 3.0.6 validation. The earlier ordinary-source negative control was correctly rejected.
- Linux onedir build and bundled M1/M2/M3 PDF/image/HEIC/AES/form/HTML/ICC/Qt smoke including real installed Tesseract OCR passed.
- [2026-10-02 requirements audit](verification-audit-2026-10-02.md) reproduced and corrected fractional-page redaction edge pixels, missing form appearances in PDF image exports, and optional compression's CMYK/color-profile/layer changes. Fresh source/frozen smoke includes the redaction and form-export regressions.
- English/Korean `eng+kor` OCR sample passed with explicit Unicode data folder and official locally installed data; sample evidence, not a general accuracy guarantee.
- Hosted Windows 155-case source suite, four independent Preflight acceptances and the native executable passed after fixing OCR version identification and default HTML font loading; physical/manual checks remain separate.
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

On a personal Windows x64 machine without Python, download the verified development ZIP and confirm actual desktop/Explorer/dialogs/DPI/real-document/offline behavior from verification.md. Install local Tesseract 5 with English/Korean data for OCR, record results and fix target-PC failures. Hosted automation does not establish this physical clean-machine evidence. Public release compliance remains separate.
