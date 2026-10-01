# Verification Evidence

## Requirements Audit — 2026-10-02 (Asia/Seoul)

Full report: [verification-audit-2026-10-02.md](verification-audit-2026-10-02.md). Starting main was clean and matched origin. All 143 earlier cases passed, but additional probes reproduced five defects: fractional-page redaction edge pixels, missing filled-form image exports, and optional compression changing CMYK colors, hidden-layer visibility and ICC color interpretation. Fixed all five with eight added regression cases using existing dependencies.

Final observed checks: **151 passed, 0 errors/failures/skips** with all four independent Preflight specimens enabled; dependency consistency, compilation, whitespace, fresh Linux build and source/frozen HEIC/AES/form/redaction/PDF-A/HTML/OCR smoke passed. Frozen trace showed no printer-service or remote document traffic in the tested sample. Actual Windows execution/CI results and public-release compliance remain unverified. Earlier redacted outputs on fractional page sizes need regeneration and boundary inspection; see the report. Historical milestone counts below are retained as evidence of those checkpoints.

## Executed in Linux Cloud — 2026-10-01

| Check | Observed result |
|---|---|
| Python 3.12 editable install / pip check | Passed; no broken requirements |
| `.venv/bin/python -m pytest -q` | 59 passed, no skipped/disabled tests |
| 38 processor cases | PDF count/order/rotation/reopen, multiple files, render formats/sizes/content, images-to-PDF, real HEIC, JPEG/PNG, resize presets/custom %, dimensions/aspect, EXIF, invalid/encrypted input, output collisions/Unicode/cleanup, cancellation/partial results |
| 20 offscreen Qt cases | Cards/categories, drop/remove/file/page order, previews, all 14 tools with real jobs, results/local-open routing, errors/retry, close/cancel/thread cleanup |
| Package notice test | Native notices, versions and LGPL text copied |
| `python scripts/package_app.py --cloud-smoke` | Linux onedir built; approximately 192 MB on this host |
| Bundled executable `--smoke-test --heic-fixture tests/fixtures/sample.heic` | Passed: image → PDF → PDFium render → reopened image, real HEIC decode, Qt workspace/preview |
| Windows x64 / CPython 3.12 binary-wheel download | Runtime dependency wheels downloaded; not run |
| Git whitespace / documentation links | Checked before commits |

Cloud is not Windows runtime verification. Offscreen tests do not verify desktop display, Explorer integration, OS dialogs, DPI scaling, display drivers, or native Windows DLL loading.

## Required Windows Validation — Pending

Clone main on Windows x64 with Python 3.12; follow README installation commands. Install Tesseract 5 with English data first for the current full suite, as described in [m3-engines.md](m3-engines.md).

1. Run `.venv\Scripts\python.exe -m pytest -q`; record platform, versions, count/results.
2. Run `.venv\Scripts\python.exe -m local_pdf_editor`. Confirm startup, cards at 100%/150% scaling, keyboard navigation, dialogs and Explorer drop with Unicode paths.
3. Use real multi-page PDFs: merge reversed inputs, split selected pages, reorder all pages, delete, import a range and rotate. Reopen in an independent Windows viewer; confirm count/order/rotation and unchanged originals.
4. Export JPEG/PNG and import images to PDF; check dimensions/visual content, including filled text/check/radio form appearances. Corrupt/encrypted inputs must show useful errors without incomplete output.
5. Convert an iPhone HEIC and fixture; convert JPEG/PNG; resize batches at all presets/custom %, aspect-preserving box and stretched dimensions. Check dimensions and EXIF-rotated photo orientation.
6. Re-run into a populated folder; confirm no overwrite. Cancel/close during jobs; completed outputs remain and incomplete output/temp files are cleaned after normal cancellation. Confirm output folder choice and Open output/folder work.
7. Build `.venv\Scripts\python.exe scripts\package_app.py`; run `dist\LocalPdfUtilities\LocalPdfUtilities.exe --smoke-test --heic-fixture tests\fixtures\sample.heic`. Copy the entire onedir folder to a clean Windows machine without Python and repeat PDF rendering/HEIC conversion offline. Verify Qt plugin and codec DLL discovery.
8. Record evidence here and update Windows status only for observed checks; resolve failures before claiming Windows readiness.

## Not Executed / Not Claimed

- Actual Windows GUI, Explorer dialogs/drop, Windows frozen executable and clean-machine offline startup.
- GitHub Actions results (workflow provided; run status not inspected).
- Public binary compliance, signing, installer and HEVC patent review.
- Linux package size is not a Windows measurement.

## Diagnosed and Corrected

- PDFium pages required explicit close rather than page context managers; render tests then passed.
- Raw wheel METADATA copying replaced email metadata serialization rejected by PySide's description. Notice test and package build passed afterward.
- Hidden resize fields were parsed for unrelated tools; restricted parsing and added a regression test.

## M2 Cloud Evidence — 2026-10-01

M1 gate passed: coherent/clean main and 59 baseline tests re-executed successfully. After M2, the full suite executed **101 tests, all passed**, with no skipped/disabled cases (59 M1/notice + 29 M2 processing + 13 M2 GUI).

| Check | Observed result |
|---|---|
| Crop geometry | Rotated/cropped/offset selected pages correctly bounded; underlying text remains, as expected for crop |
| Watermark/numbers/signature | Added text extracted and pixels changed; selected pages respected; signature image rendered at chosen bounds |
| AES-256 | Encryption dictionary V=5/256 bits; wrong password rejected; correct user/owner password accepted; decrypted output reopened; Unicode password round-trip; passwords excluded from repr/errors |
| Secure redaction | Rebuilt all pages; no original selectable text/annotations/forms/attachments/layers/metadata; synthetic secrets absent; embedded pixels and rendered rectangle black; unmarked visual content retained |
| Redaction edge cases | Rotated/cropped/fractional coordinates, encrypted input, invalid bounds/page numbers, huge render rejection and cancelled-write cleanup |
| Visual comparison | Identical/different PDFs and missing pages produced matching reports and highlighted PNGs |
| Forms | Text/check/radio/choice values reopened and appearances changed; image flattening retained visual appearance and removed fields; read-only/MaxLen/XFA/invalid values rejected |
| Shared GUI | All 9 M2 tools ran real jobs; preview region selection mapped to selected page; input replacement cleared stale redaction marks; passwords masked/cleared, mismatches/incorrect passwords rejected; form edits/flatten and M1 regression passed |
| Native bundle | Linux onedir plus frozen M1/M2 smoke passed; approximately 214 MB on this host; fonts/crypto/native codecs included |
| Windows additions | ReportLab/cryptography and transitive Windows x64 wheels downloaded, not executed |

The redaction guarantee applies to marked visible pixels and source structures excluded by rebuilding; it does not identify sensitive information automatically or prove a user's regions are complete. Raster output cannot preserve vector resolution, accessibility or search.

M2 diagnostics corrected during verification: pypdf's writer context entry reset pre-cloned content, so cloning now occurs inside the context; direct radio-widget flattening collided on appearance resources, so flattening renders the filled document into a fresh lossless PDF. Tests validate both corrected outputs.

## Additional Windows M2 Checks — Pending

1. Re-run the full suite on Windows, then source GUI and packaged smoke with all M2 additions. Verify bundled Vera font, optional Korean TTF, AES provider and PDFium/Qt DLL loading.
2. Exercise crop/overlays on landscape, rotated and previously cropped PDFs. Independently confirm crop bounds, watermark opacity, sequential numbers and visible signature placement.
3. Protect with an explicit password and reopen in an independent Windows viewer. Wrong password must fail; removing protection with the correct user/owner password must yield an unencrypted readable copy. Originals must remain unchanged.
4. Mark redaction regions across pages, including text/images and form content. Inspect outputs visually and with an independent text/object extraction tool: removed text must be unselectable, metadata/attachments/forms absent, and selected pixels erased. Check fractional page sizes/region edges at low/high DPI, rotated pages and input replacement before sharing real sensitive files. Include the audit's 100.01 × 80.01 point edge specimen; recreate affected outputs made before the audit fix.
5. Compare identical/changed/differently sized/missing-page PDFs and inspect report/highlights. Fill representative standard AcroForms, reopen editable values and flattened appearances in an independent viewer. Record unsupported XFA/Unicode/multi-select limits accurately.

These checks and actual Windows CI results have not been observed in this Cloud machine. At the M2 checkpoint no M3 verification had been performed; the later M3 evidence follows.

## M3 Cloud Evidence — 2026-10-01

M2 gate passed: coherent clean main, 101 regression tests and dependency consistency re-executed. Final suite: **143 passed, no skipped/disabled tests** (101 previous + 35 M3 processor + 7 M3 GUI). Independent PDF/A validation enabled for four specimen cases.

```bash
export XDG_CACHE_HOME=/workspace/local-pdf-editor/.cache
export PDF_PREFLIGHT_JAR=/workspace/local-pdf-editor/.cache/tools/preflight-app-3.0.6.jar
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
QT_QPA_PLATFORM=offscreen .venv/bin/python -m local_pdf_editor --smoke-test --heic-fixture tests/fixtures/sample.heic --ocr-smoke
.venv/bin/python scripts/package_app.py --cloud-smoke
QT_QPA_PLATFORM=offscreen dist/LocalPdfUtilities-CloudSmoke/LocalPdfUtilities-CloudSmoke --smoke-test --heic-fixture tests/fixtures/sample.heic --ocr-smoke
```

| Check | Observed result |
|---|---|
| Compression | Uncompressed stream fixture reduced by more than half with retained text; photo reduced by more than two-thirds with text/downsampled image; default forms/pixels and transparency retained; oversized images rejected before decode |
| Repair | Broken startxref rejected by strict input parser, repaired and strict-reopened with intact pages/text/render; unreadable/missing content failed cleanly |
| OCR | Actual Tesseract 5.5.0/English created searchable text from an image-only scan, preserved dimensions/near-identical pixels; missing engine/language/data/invalid settings failed; active child cancelled/timed out and reaped |
| English/Korean manual sample | HTML → raster scan → actual `eng+kor` OCR with explicit Unicode tessdata folder yielded `한글 문서` and `LOCAL OCR TEST`; official Apache-licensed data used locally, not shipped |
| PDF/A-1b | Text/form/rotated-cropped/encrypted specimens rebuilt without original text/forms/attachments/metadata; dimensions/pixels retained; four independently accepted by Apache PDFBox Preflight 3.0.6 |
| Validator negative control | Ordinary source PDF correctly rejected for missing profile/XMP/unembedded fonts; expected nonconforming input, not a failed app check |
| HTML | Headings/table/text/local image/multiple pages yielded readable PDFs; script did not execute; network/outside-folder image requests failed without incomplete outputs |
| Shared workflow | Five M3 tools ran real GUI background jobs; scoped options, missing-engine error/retry; passwords, batches, collisions/original preservation and cancellation cleanup tested |
| Packaging | Wheel and Linux onedir built; ICC included; profile notice/ADRs copied; frozen M1/M2/M3 smoke including installed OCR passed |
| Platform research | Publisher licenses/source reviewed; Windows Essentials artifacts inspected, chosen Qt Gui writer available; actual Windows execution remains unrun |

Syscall tracing found QPrinter queried CUPS while initializing. Replaced it with Qt Gui QPdfWriter and reran tests/smoke. Final source/frozen traces show no printer-service or remote traffic; native Tesseract performs local OS interface/address inspection (netlink/local port-0 socket queries) without sending document data. This is observed Linux sample behavior, not a Windows network trace claim.

Preflight is developer-only Java tooling, not an app dependency or packaged runtime. Pinned jar/checksum and ICC provenance are in ADR-0003. No veraPDF result is claimed. Public binary license obligations from earlier milestones remain pending.

Cloud setup retains the independently checksum-verified Preflight jar in ignored `.cache/tools`. Re-executed installation and cached-tool checks passed. Later fresh Maven requests returned HTTP 429; a new download depends on repository availability and must still pass the pinned checksum. This does not affect installed conformance validation or application runtime. Updated installer/start instructions are saved as a configuration draft, not a published environment.

## Additional Windows M3 Checks — Pending

1. Install Tesseract 5/English/Korean/pdf.ttf, check executable/`--list-langs`, run full pytest/source/frozen `--ocr-smoke`. Inspect DLL/data discovery with spaces/Unicode paths and explicit tessdata. Without an engine, other tools must work and OCR must show an actionable error.
2. Copy the package to a clean machine without Python and disconnect networking. With local OCR prerequisites, process English/Korean scans, review text accuracy, dimensions/multipage output, progress, child cancel and timeout.
3. Compress text/form/photo/transparent/CMYK/ICC/hidden-layer PDFs, compare sizes/text/forms/colors/layer visibility and unchanged originals in an independent viewer. ICC/calibrated images must retain their original interpretation. Already optimized files need not shrink. Repair real broken cross-references; missing content is not recoverable.
4. Convert rotated/cropped/form/encrypted/color documents to PDF/A-1b, inspect visuals and run independent Preflight/another validator. Confirm bundled ICC, unencrypted output and removed source interactive structures. No PDF/A-1a/2/3/accessibility claim.
5. Print local UTF-8 Korean/English HTML with images/tables/multiple pages. Confirm fonts/A4/margins, no printer-service/network request, blocked-resource errors and native Qt behavior. Modern web/CSS/JS fidelity is outside scope.
6. Inspect Windows CI results when available; CI commands are provided but no run result was observed. Complete earlier LGPL/HEIC/crypto/app-license public release review before distributing binaries; this package does not bundle Tesseract native binaries/models.
