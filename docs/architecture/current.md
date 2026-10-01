# Current Architecture

## Implemented Components

| Source | Responsibility |
|---|---|
| src/local_pdf_editor/app.py | Qt shell, one shared workspace, file/page selection/order, region preview, masked passwords, form editor, options/results/local output opening |
| src/local_pdf_editor/tools.py | Immutable registry/options; 14 M1, 9 M2 and 5 M3 tools; passwords/form values excluded from repr |
| src/local_pdf_editor/processing.py | PDF/image processors, job result/progress/cancellation, validation, bounded buffers |
| src/local_pdf_editor/m2.py | Crop/overlays, AES protection/removal, source-free raster redaction/flattening, visual comparison and basic AcroForms |
| src/local_pdf_editor/m3.py | pypdf compression/repair, fresh raster PDF/A-1b, local Tesseract child execution, Qt Gui basic HTML PDF writing |
| src/local_pdf_editor/assets/sRGB.icc | Licensed, embedded ICC v2 profile for PDF/A output intent |
| src/local_pdf_editor/output.py | Windows-safe Unicode names, exclusive collision reservation, temporary writes and completed-output commits |
| src/local_pdf_editor/smoke.py | Native dependency and Qt smoke check for frozen builds |
| scripts/package_app.py | Host-native onedir packaging and notice collection; Windows builds require Windows |

## Runtime / Data Flow

1. Category selection filters tool cards. A selected tool configures the single workspace.
2. Files are selected/dropped locally; list order is preserved. Page lists expose selections/order controls. M2 preview shows the selected page and maps drag rectangles into visible point coordinates. Redaction regions are cleared when the input is replaced.
3. Immutable options and ordered paths go to JobThread. One background QThread runs processing; editing/previews are disabled during jobs so PDFium is not used concurrently.
4. Processors open originals read-only, validate input/options, normalize images, and check cancellation between file/page steps. M2/M3 optionally decrypt only with a supplied password. Password controls clear at job start and the thread releases its option snapshot at completion. Qt signals update progress/results on the UI thread.
5. Output names are exclusively reserved. Data is written to temporary files in the output folder and replaces only those reservations after completion. Failed writes remove incomplete output/temp files. Originals/prior outputs are not overwritten.
6. Completed outputs, per-file errors, and cancellation status are returned together. Paths open through the OS. No application network API is used.

No server, database, account, telemetry, upload, or plugin system exists. The default output folder is Documents/Local PDF Outputs and can be changed. GUI/job processes must restart in new environments.

## Constraints

- Stack: [ADR-0001](../decisions/ADR-0001-m1-stack.md). Scope: [product-spec.md](../product-spec.md).
- Cancellation cannot interrupt an in-process native call; the M3 OCR child can be terminated. Render/resize buffers are bounded to 40 megapixels; images-to-PDF/raster documents to 120 megapixels.
- Preview decoding is synchronous and bounded, so a slow input can briefly delay selection feedback; jobs run in the background.
- Structural operations preserve page content; full document-level attachment/bookmark/form/tag preservation and signature validity are not promised by M1.
- Cloud GUI tests are offscreen. Windows runtime and public distribution compliance are separate pending checks.

## M2 Security and Forms

M2 processors share the existing Context/Result and collision-safe output layer; no alternate service, shell or plugin architecture was introduced. ReportLab supplies text/image overlays, standard fonts and fresh lossless raster PDFs. pypdf uses cryptography for AES-256.

Secure redaction renders **every** visible page, maps regions using the actual bitmap width/height divided by the visible page dimensions, erases touching pixels with outward rounding, then writes only those images into a new PDF. Independent axis scales account for fractional page sizes and rounded render dimensions. Source dictionaries/streams/metadata are not cloned. Form flattening first fills an in-memory copy, renders appearances including check/radio widgets, then uses the same source-free image writer. M1 PDF image exports also initialize the PDFium form environment before rendering. Both raster document operations lose original selectable text, vectors and interactive structure and obey the render/aggregate bounds.

Editable forms use an inspected field schema, inherited flags/limits and pypdf appearance updates. Unsupported/read-only edits fail. Text edits are bounded to ASCII to avoid silently missing glyphs in existing form fonts. Comparison emits page-index PNG highlights plus a JSON summary, sharing partial-result/cancellation behavior.

See [ADR-0002](../decisions/ADR-0002-m2-pdf-operations.md); these additions leave M1 decisions intact.

## M3 Local Engines

M3 keeps Context/Result and per-file batch progress/errors. Compression clones document structures, compresses streams and deduplicates objects, optionally replaces eligible direct DeviceRGB/DeviceGray/DeviceCMYK images after pre-decode size checks. Replacements keep the original color model and layer visibility/rendering/document attributes; calibrated/ICC/palette color spaces and masks/transparency are left unchanged. Repair uses pypdf's forgiving parser, then strict-reopens and renders every generated page before committing output.

PDF/A composes the existing source-free raster writer with a new PDF 1.4 writer: strips empty ReportLab text blocks/unused fonts, embeds the licensed ICC v2 profile and output intent, writes XMP/identifiers. Only fresh opaque image pages enter this step. Independent Preflight validates representative PDF/A-1b specimens; native rendering alone is not conformance evidence.

OCR writes visible pages into a private temporary directory, executes local Tesseract 5 with fixed argv and no shell, checks installed data, waits with cancellation/timeout, combines its fresh image/text pages, and cleans intermediate files. Tesseract/model/native DLLs are user-installed external prerequisites, not redistributed by packaging. No downloads occur in the app.

HTML uses a QTextDocument subclass with resource access limited to JPEG/PNG within the input directory and prints directly into Qt Gui QPdfWriter on the shared worker. GUI is initialized by the application; HTML registers the already bundled, embeddable Vera TrueType font as its default, avoiding missing text when headless Windows Qt has no default face. Local system fonts still supply other requested glyphs/families. This avoids QPrinter's service queries; no browser/JS/network renderer exists. Package data includes the ICC profile and notices/engine instructions.

See [ADR-0003](../decisions/ADR-0003-m3-local-engines.md) and [m3-engines.md](../m3-engines.md). Windows behavior remains unverified until observed.

## Windows verification and development artifacts

Actions runs existing source tests and executable smoke. Standard-library JUnit reporting exposes actual failures as annotations/summary and retains result files. The Windows package check relocates the whole onedir bundle into a Unicode temporary directory, removes Python/Qt developer environment paths, enables temporary per-executable outbound firewall blocking and runs the native Windows backend at scale 1/1.5. It restores the host's environment/firewall configuration afterwards. This isolates runtime dependencies but is not a physical clean-machine or manual Explorer/display validation.

The frozen entrypoint can record `--smoke-report` JSON and exit nonzero on smoke errors without a windowed crash dialog. CI retains those results and a SHA-256 Windows ZIP only after checks pass. OCR/model preparation occurs on the runner; Tesseract and Korean data remain external and are not included in the ZIP.
