# Current Architecture

## Implemented Components

| Source | Responsibility |
|---|---|
| src/local_pdf_editor/app.py | Qt shell, one shared workspace, file/page selection/order, region preview, masked passwords, form editor, options/results/local output opening |
| src/local_pdf_editor/tools.py | Immutable registry/options; 14 M1 and 9 M2 tools; passwords/form values excluded from repr |
| src/local_pdf_editor/processing.py | PDF/image processors, job result/progress/cancellation, validation, bounded buffers |
| src/local_pdf_editor/m2.py | Crop/overlays, AES protection/removal, source-free raster redaction/flattening, visual comparison and basic AcroForms |
| src/local_pdf_editor/output.py | Windows-safe Unicode names, exclusive collision reservation, temporary writes and completed-output commits |
| src/local_pdf_editor/smoke.py | Native dependency and Qt smoke check for frozen builds |
| scripts/package_app.py | Host-native onedir packaging and notice collection; Windows builds require Windows |

## Runtime / Data Flow

1. Category selection filters tool cards. A selected tool configures the single workspace.
2. Files are selected/dropped locally; list order is preserved. Page lists expose selections/order controls. M2 preview shows the selected page and maps drag rectangles into visible point coordinates. Redaction regions are cleared when the input is replaced.
3. Immutable options and ordered paths go to JobThread. One background QThread runs processing; editing/previews are disabled during jobs so PDFium is not used concurrently.
4. Processors open originals read-only, validate input/options, normalize images, and check cancellation between file/page steps. M2 optionally decrypts only with a supplied password. Password controls clear at job start and the thread releases its option snapshot at completion. Qt signals update progress/results on the UI thread.
5. Output names are exclusively reserved. Data is written to temporary files in the output folder and replaces only those reservations after completion. Failed writes remove incomplete output/temp files. Originals/prior outputs are not overwritten.
6. Completed outputs, per-file errors, and cancellation status are returned together. Paths open through the OS. No application network API is used.

No server, database, account, telemetry, upload, or plugin system exists. The default output folder is Documents/Local PDF Outputs and can be changed. GUI/job processes must restart in new environments.

## Constraints

- Stack: [ADR-0001](../decisions/ADR-0001-m1-stack.md). Scope: [product-spec.md](../product-spec.md).
- Cancellation cannot interrupt a native call. Render/resize buffers are bounded to 40 megapixels; images-to-PDF batches to 120 megapixels.
- Preview decoding is synchronous and bounded, so a slow input can briefly delay selection feedback; jobs run in the background.
- Structural operations preserve page content; full document-level attachment/bookmark/form/tag preservation and signature validity are not promised by M1.
- Cloud GUI tests are offscreen. Windows runtime and public distribution compliance are separate pending checks.

## M2 Security and Forms

M2 processors share the existing Context/Result and collision-safe output layer; no alternate service, shell or plugin architecture was introduced. ReportLab supplies text/image overlays, standard fonts and fresh lossless raster PDFs. pypdf uses cryptography for AES-256.

Secure redaction renders **every** visible page, erases chosen pixels with outward rounding, then writes only those images into a new PDF. Source dictionaries/streams/metadata are not cloned. Form flattening first fills an in-memory copy, renders appearances including check/radio widgets, then uses the same source-free image writer. Both lose original selectable text, vectors and interactive structure and obey the render/aggregate bounds.

Editable forms use an inspected field schema, inherited flags/limits and pypdf appearance updates. Unsupported/read-only edits fail. Text edits are bounded to ASCII to avoid silently missing glyphs in existing form fonts. Comparison emits page-index PNG highlights plus a JSON summary, sharing partial-result/cancellation behavior.

See [ADR-0002](../decisions/ADR-0002-m2-pdf-operations.md); these additions leave M1 decisions intact.
