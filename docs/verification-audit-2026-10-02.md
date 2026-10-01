# Requirements and defect audit — 2026-10-02

Date uses Asia/Seoul; Cloud commands ran on 2026-10-01 UTC. Audited baseline: main at `1eb47f4e5833aa5e5c799a24954877b47cc7cf1b`, initially clean and matching origin/main.

## Verdict

All 28 authorized M1/M2/M3 tools are implemented within the explicit boundaries in [product-spec.md](product-spec.md), using the existing shared workflow. Initial milestone tests passed, but independent boundary probes found five defective behaviors. They were reproduced, fixed and covered by eight additional regression cases. Final Linux Cloud suite: **151 passed, 0 failures/errors/skips**, with real independent PDF/A validation enabled. Fresh source and frozen Linux smoke passed.

This is verified Cloud implementation, not completion of Windows runtime or public release readiness. Actual Windows execution and distribution-license work remain incomplete. Passing samples cannot prove every possible PDF is handled without defects.

## Requirement coverage

The following evidence was executed in this audit through the full suite. GUI cases exercise all 28 tools with real shared background jobs; processor cases inspect actual outputs rather than only successful return values.

| Requirement | Observed Cloud evidence | Scope boundary |
|---|---|---|
| M1 merge/split/reorder/delete/import/rotate | Reopened page count/order/rotation, selected ranges, unchanged originals | Split creates individual selected-page files; arbitrary document-level structure preservation is not promised |
| M1 PDF/image conversion and resize | JPEG/PNG dimensions/content, real HEIC fixture, batches, custom sizes/percentages, EXIF, filled-form exports | Primary 8-bit HEIC image; bounded buffers; M1 rejects encrypted PDFs |
| M2 crop | Visible rotated/cropped geometry, form pixels and unchanged input | Crop retains hidden source content |
| M2 watermark/numbers/signature | Extracted added text and rendered pixels; selected-page placement and rotation | Signature is an inserted image; optional Unicode font must contain the glyphs |
| M2 passwords | AES-256 dictionary, correct/wrong user/owner passwords, decrypted reopen, Unicode password round-trip | No recovery/cracking; transient passwords |
| M2 secure redaction | Fresh source-free objects, absent original secrets/forms/attachments/metadata, marked black pixels, fractional/rotated edge footprints | All pages rasterized; only user-marked visible areas are erased |
| M2 comparison | Identical/changed/missing-page JSON and highlighted PNGs | Visual comparison by page index |
| M2 practical forms | Text/check/radio/single-choice values and appearances, flattening, unsupported/edit-limit errors | ASCII text edits; no XFA/multi-select/certificate signing |
| M3 compression | Stream reduction, text/forms, optional photo reduction, masks, CMYK pixels, hidden layer and ICC preservation | Optional JPEG is lossy; calibrated/ICC images are left unchanged; size reduction is not guaranteed |
| M3 OCR | Actual installed Tesseract 5.5.0/English searchable scan with retained visible dimensions/pixels; prerequisite, timeout and child-cancel errors | Engine/data/font must be installed locally; recognition requires review. Earlier English/Korean sample remains historical evidence, not a new Korean OCR run |
| M3 repair | Broken startxref recovery, strict reopen and native render; unreadable input cleanup | Cannot recover missing source bytes |
| M3 PDF/A | Four text/form/rotated-cropped/encrypted specimens accepted by real Apache PDFBox Preflight 3.0.6 | Raster PDF/A-1b; text/vector/interactivity lost; no 1a/2/3 claim |
| M3 HTML | Basic text/table/local image/multiple pages; script inert, remote/outside-folder resources rejected | UTF-8 Qt rich text, A4; no browser/JavaScript/modern CSS |
| Shared application/output | GUI jobs, preview/region controls, masked passwords, form editor, progress/errors/retry/cancel, collision/Unicode/partial-result safety | Offscreen Linux GUI cannot verify Windows dialogs, Explorer, DPI or DLL behavior |

Sources/tests: [processing.py](../src/local_pdf_editor/processing.py), [m2.py](../src/local_pdf_editor/m2.py), [m3.py](../src/local_pdf_editor/m3.py), [processor tests](../tests/test_processing.py), [M2 tests](../tests/test_m2.py), [M3 tests](../tests/test_m3.py), [GUI tests](../tests/test_gui.py), [M2 GUI tests](../tests/test_m2_gui.py), [M3 GUI tests](../tests/test_m3_gui.py).

## Reproduced defects and corrections

| Defect | Before the fix | Correction and regression evidence |
|---|---|---|
| Redaction edge pixels on fractional page sizes | Nominal DPI mapping differed from the rounded bitmap stretched onto the page. A 100.01 × 80.01 point page at 36 DPI, marked rectangle `1:98,10,1,20`, retained a red pixel at `(50,8)` whose physical footprint overlaps the mark | Use actual bitmap/page scales per axis and outward rounding. Three cases at 36/144 DPI and 0/90° inspect every intersecting embedded-pixel footprint, retain unmarked content and preserve input |
| Filled fields missing from PDF → image | M1 export opened PDFium without its form environment, omitting text/check widget appearances | Initialize forms before rendering annotations. PNG and JPEG cases compare native filled-form reference pixels |
| CMYK color shift in optional image compression | Every eligible image was converted to RGB before JPEG replacement; native rendered colors changed substantially | Retain the source color model. CMYK image mode, native visual difference and reduced size checked |
| Hidden image exposed by optional compression | Replacement discarded the image's `/OC` reference; a hidden-layer image became visible | Preserve optional-content and rendering/document attributes after re-encoding. Hidden group reference and native page pixels checked |
| ICC color profile lost in optional compression | Replacement changed ICCBased color space to DeviceRGB and removed its interpretation | Leave calibrated/ICC images unchanged. Embedded profile, decoded pixels and native page rendering checked |

The new cases failed against the previous affected implementations before the fixes. These changes reuse the existing engines, job/output contracts and pinned dependencies; no architecture or license boundary was expanded.

**Existing redacted outputs:** before this fix, fractional page sizes could leave edge pixels inside marked areas. Source structures were still excluded, but the marked-pixel guarantee was incomplete. Regenerate affected outputs from originals with the corrected revision and inspect boundaries before sharing sensitive files. Optional compression outputs containing CMYK/profiled/hidden-layer images should also be regenerated or checked against their originals for the above appearance changes.

## Final executed checks

Environment: Linux x64, Python 3.12.14, Qt 6.11.2, Tesseract 5.5.0 with installed English data. Runtime pins unchanged. Independent Preflight jar and ICC checksums match ADR-0003.

```bash
export XDG_CACHE_HOME=/workspace/local-pdf-editor/.cache
export PDF_PREFLIGHT_JAR=/workspace/local-pdf-editor/.cache/tools/preflight-app-3.0.6.jar
.venv/bin/python -m pytest -q --junitxml=.cache/audit-2026-10-02-pytest.xml
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src scripts
QT_QPA_PLATFORM=offscreen .venv/bin/python -m local_pdf_editor --smoke-test --heic-fixture tests/fixtures/sample.heic --ocr-smoke
.venv/bin/python scripts/package_app.py --cloud-smoke
QT_QPA_PLATFORM=offscreen strace -f -e trace=network -o .cache/audit-2026-10-02-network.trace dist/LocalPdfUtilities-CloudSmoke/LocalPdfUtilities-CloudSmoke --smoke-test --heic-fixture tests/fixtures/sample.heic --ocr-smoke
git diff --check
```

| Check | Result |
|---|---|
| Final automated suite | 151 passed in 20.99 s; JUnit confirms 0 errors/failures/skips |
| Suite composition | 40 M1 processing, 20 M1 GUI, 32 M2 processing, 13 M2 GUI, 38 M3 processing, 7 M3 GUI, 1 notice-packaging case |
| Independent PDF/A | Four real Preflight acceptances; the earlier ordinary-PDF rejection is recorded in verification.md |
| Dependencies / compile / whitespace | No broken requirements; compile and diff checks passed. No repository lint/type-check command is configured |
| Fresh Linux onedir | Build passed; current frozen smoke passed including real HEIC, AES/forms, fractional redaction, filled-form export, PDF/A, HTML and installed OCR |
| Packaged resources | ICC SHA-256 matches the licensed source; profile notice, LGPL text and local-engine guide included |
| Frozen sample network trace | No printer-service port 631 calls or AF_INET/AF_INET6 sendto/sendmsg. Native engine performs local netlink and port-0 interface/address queries. This sample is not a Windows/offline-network capture |
| Remote CI visibility | GitHub Actions API access returned Forbidden; no Windows CI result is claimed |

The Qt offscreen `propagateSizeHints` message did not fail smoke. PyInstaller's module-analysis file lists platform/optional imports; successful frozen execution verifies the exercised paths, not every optional library feature. Generated packages, traces, caches and JUnit output are ignored and not committed.

## Remaining verification and limitations

- Windows x64 source suite, real desktop GUI, 100%/150% DPI, Explorer/drop/dialogs, native DLLs and frozen execution have not been observed. Next task: install local Tesseract 5/English/Korean, run source/full-suite/frozen `--ocr-smoke`, then clean-machine offline M1/M2/M3 checks from [verification.md](verification.md), recording results and fixing failures.
- Public distribution remains pending: Qt LGPL source/replacement/notice rights, exact bundled HEIC component/source obligations, HEVC review, crypto notices and the application's own license. Existing source development does not resolve release compliance. No new engine was adopted in this audit.
- Practical forms, visual comparison, raster security/PDF/A, repair, OCR and basic HTML retain their documented limitations above. The OCR package is not self-contained; Tesseract binaries/models are not redistributed.
- No M4/excluded feature, app installer/signing, or Cloud-environment publication was performed.

Commit identity is supplied by the Git history containing this report; release and Windows status stay pending until observed evidence changes them.
