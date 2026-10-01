# Verification Evidence

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

Clone main on Windows x64 with Python 3.12; follow README installation commands.

1. Run `.venv\Scripts\python.exe -m pytest -q`; record platform, versions, count/results.
2. Run `.venv\Scripts\python.exe -m local_pdf_editor`. Confirm startup, cards at 100%/150% scaling, keyboard navigation, dialogs and Explorer drop with Unicode paths.
3. Use real multi-page PDFs: merge reversed inputs, split selected pages, reorder all pages, delete, import a range and rotate. Reopen in an independent Windows viewer; confirm count/order/rotation and unchanged originals.
4. Export JPEG/PNG and import images to PDF; check dimensions/visual content. Corrupt/encrypted inputs must show useful errors without incomplete output.
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
4. Mark redaction regions across pages, including text/images and form content. Inspect outputs visually and with an independent text/object extraction tool: removed text must be unselectable, metadata/attachments/forms absent, and selected pixels erased. Check fractional edges, DPI and input replacement before sharing real sensitive files.
5. Compare identical/changed/differently sized/missing-page PDFs and inspect report/highlights. Fill representative standard AcroForms, reopen editable values and flattened appearances in an independent viewer. Record unsupported XFA/Unicode/multi-select limits accurately.

These checks and actual Windows CI results have not been observed in this Cloud machine. No M3 verification is claimed.
