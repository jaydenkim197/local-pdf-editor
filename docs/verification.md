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
