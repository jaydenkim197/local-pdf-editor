# ADR-0003 — Local M3 engines

Date: 2026-10-01. Status: DECISION. Scope: the user's authorized M3 request.

M2 gate: clean main, coherent architecture/status/log, 101 tests passed and `pip check` passed. Existing Windows execution and public redistribution reviews remain release prerequisites, not a failed M2 verification or a source-development blocker. Retain ADR-0001/0002.

## Search-first outcome

Searched registry, Context/Result/run_job, output commits, raster/form rendering, packaging, installed Qt modules, publisher source/license files and host tools. No additional Python runtime dependency is necessary. REUSE pypdf/PDFium/Pillow/ReportLab, COMPOSE existing raster workflow, COMPOSE Qt Gui PDF writing, INTEGRATE a local Tesseract executable. No new job/plugin/service architecture.

| Component | License / redistribution | Windows and offline | Packaging decision |
|---|---|---|---|
| Existing pypdf 6.19.0 | BSD-3-Clause; preserve notices | Pure Python; pinned Windows-compatible dependency; no network | Reuse structural stream optimization, image replacement and forgiving parser |
| Existing PDFium 5.13.0 wrappers / engine | Existing BSD/Apache/component notices, ADR-0001 obligations | Windows wheel previously inspected; local native renderer | Reuse rasterization and repaired-output checks |
| Existing ReportLab 5.0.1 / Pillow 12.3.0 | BSD / MIT-CMU with component notices | Existing Windows wheels; offline | Fresh raster PDF/A pages; keep existing dynamic/native components |
| Existing Qt Gui 6.11.2 | LGPL-3.0 / commercial; QPdfWriter license header checked, preserve source/replacement/notice rights from ADR-0001 | Essentials Windows wheel contains Qt Gui; native local PDF writing | Reuse Gui directly; no PrintSupport, Qt WebEngine, browser or network module |
| Tesseract 5 CLI | Apache-2.0; permits source/binary redistribution with license/notices, mark modifications. Leptonica BSD-2-Clause; other actual native components have separate obligations | Upstream Windows build/NSIS scripts and CLI documented; image + installed traineddata + pdf.ttf suffice offline; observed host 5.5.0 | User-installed engine integration, **no Tesseract executable/DLLs/models shipped by this repository**. PATH, explicit executable/data folder, adjacent engines/tesseract or normal Windows installation discovery |
| Official tessdata_fast models | Apache-2.0, explicitly applies to all data in upstream README; preserve notices if redistributed | Tesseract 4/5 LSTM, portable traineddata; no inference network | User-installed languages; no automatic downloads or redistributed models |
| sRGB.icc | Unmodified zlib-licensed profile in icc-profiles-free; permits commercial use/redistribution with notice | Platform-independent embedded ICC v2.3 | Include 6,922-byte profile as package data, plus original copyright notice |
| Apache PDFBox Preflight 3.0.6 | Apache-2.0, Java dependency notices; developer-only validator | Java CLI supports Windows/Linux, validation offline | Independent PDF/A-1b verification tool, never included or invoked by application |

Windows **support evidence is not observed Windows execution**. Tests, DLL discovery and clean-machine packaging remain pending until run on Windows.

## Behavior and alternatives

- Compression preserves source document structures and text; compress content streams/deduplicate objects, optionally downsample and JPEG-encode eligible opaque RGB/gray/CMYK images. Skip masks/transparency/palette/bitonal/inline images; retain original image object if re-encoding is larger. Overall file size may increase for already optimized documents.
- Repair rebuilds readable objects with `strict=False`, then checks a strict reopen/page count and renders every output page. It cannot reconstruct missing bytes/content or guarantee every damaged document's fidelity.
- OCR renders all visible pages, runs cancellable Tesseract 5 with installed languages and an invisible text layer, combines fresh searchable pages and preserves visible page dimensions. No password recovery, remote OCR or runtime downloads. Readable scans are required; user must review recognized text. Raster output loses original vectors/interactivity.
- PDF/A is **image-based PDF/A-1b**, not lossless structural conversion or tagged PDF/A-1a. Compose the existing opaque RGB raster writer, discard source objects and unused text/font resources, embed the licensed ICC v2 output intent, add required XMP/identifiers and use PDF 1.4. Independently validate representative outputs with Preflight; merely setting PDF/A metadata is insufficient. No searchable original text/forms/links/attachments/layers/history survives. All pages must be inspected for visual fidelity; 36–300 DPI and existing raster limits apply.
- HTML means local UTF-8 **basic Qt rich-text HTML**: headings, paragraphs, tables, inline styles and JPEG/PNG inside the input folder. A4 with 15 mm margins. Reject requested network/outside-folder images, including symlink escapes. JavaScript never executes; external CSS/modern browser layout are unsupported. Existing Gui/QPdfWriter avoids Chromium/native Pango packaging and extra licenses. QPrinter was considered, but a syscall trace showed CUPS printer-service probes on construction; direct QPdfWriter removes that unnecessary service access.
- All encrypted PDF inputs require the correct supplied password. M3 produces unencrypted copies; the shared UI states this. Originals/output collisions/cancellation remain governed by the existing output layer.

Considered Ghostscript: AGPL/commercial distribution introduces a material license decision absent an application license; not adopted or packaged. Considered qpdf/pikepdf for compression/repair: useful but adds a native Windows engine where current bounded behavior is already available. Considered OCRmyPDF: brings additional engines and platform/packaging work unnecessary for the current OCR pipeline. Considered WeasyPrint/Qt WebEngine: stronger browser/CSS behavior but heavier Windows runtime/component redistribution; defer until new product evidence requires browser fidelity. This does not reopen M1/M2 decisions.

## Research evidence

- [pypdf source](https://github.com/py-pdf/pypdf), installed publisher metadata/API: compress_content_streams, compress_identical_objects, ImageFile.replace and strict=False. Existing pinned license evidence in ADR-0001.
- [Qt QPdfWriter source/license](https://github.com/qt/qtbase/blob/e3eb91196c823b77835f28e3cb8320575c372975/src/gui/painting/qpdfwriter.cpp), Essentials runtime probe and Windows wheel inspection. Header is LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only OR LicenseRef-Qt-Commercial. The PrintSupport wheel artifacts were also checked before choosing Gui-only PDF writing.
- [Tesseract source](https://github.com/tesseract-ocr/tesseract/tree/db20f322d03664d1e878e2fbf6e904f5da755594): LICENSE, README license/dependencies/CLI, nsis/build.sh Windows cross-build and dependency collection. Read-only clone used for research; host version/languages probed.
- [tessdata_fast README/license](https://github.com/tesseract-ocr/tessdata_fast/tree/87416418657359cb625c412a48b6e1d6d41c29bd): cloned publisher repository, all-data Apache-2.0 statement checked.
- Host `/usr/share/color/icc/sRGB.icc` from `icc-profiles-free`; original notice copied to docs/licenses/sRGB-NOTICE.txt. SHA-256 `2a92d4bae450b76d8b0aa42193df974d75f62738ecebf74f01c5e75b12a95796`; not a Ghostscript binary/profile dependency. Debian packaging scripts' separate license does not apply to the selected profile.
- [Apache PDFBox Preflight artifact](https://repo.maven.apache.org/maven2/org/apache/pdfbox/preflight-app/3.0.6/preflight-app-3.0.6.jar), downloaded over verified HTTPS; jar notices inspected. SHA-256 `99d1a0bb97b2f6dc92ec04a2788b21b5af135c36efb58f994f7b0a28238b7c9c`. Not tracked/shipped. Maven veraPDF paths were rate-limited; use actual Preflight rather than claim veraPDF results.

No publisher Windows binary is adopted just because its engine source is permissive. If a future release bundles Tesseract, inspect the specific binary's dependencies/notices/source obligations first and provide the actual languages/font data and their licenses. Current source integration avoids redistributing an unreviewed Windows OCR binary.

## Audit clarification — 2026-10-02

Actual image-output probes found CMYK-to-RGB color shifts and pypdf replacement dropping optional-layer and ICC color-space information. Keep the existing engine decision: copy eligible direct DeviceRGB/DeviceGray/DeviceCMYK images without changing their color model, preserve image layer/rendering/document attributes after replacement, and leave calibrated/ICC color spaces unchanged. This narrows optional JPEG eligibility to a verified path; it adds no dependency or architecture. Three regression cases inspect native pixels, CMYK mode, hidden-layer visibility and embedded ICC objects. See [the audit](../verification-audit-2026-10-02.md).
