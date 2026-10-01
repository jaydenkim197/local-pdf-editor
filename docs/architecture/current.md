# Current Architecture

## Implemented Components

| Source | Responsibility |
|---|---|
| src/local_pdf_editor/app.py | Qt shell, cards/categories, one shared workspace, file/page selection/order, preview, options, results, local output opening |
| src/local_pdf_editor/tools.py | Immutable tool registry and options; 14 M1 tools |
| src/local_pdf_editor/processing.py | PDF/image processors, job result/progress/cancellation, validation, bounded buffers |
| src/local_pdf_editor/output.py | Windows-safe Unicode names, exclusive collision reservation, temporary writes and completed-output commits |
| src/local_pdf_editor/smoke.py | Native dependency and Qt smoke check for frozen builds |
| scripts/package_app.py | Host-native onedir packaging and notice collection; Windows builds require Windows |

## Runtime / Data Flow

1. Category selection filters tool cards. A selected tool configures the single workspace.
2. Files are selected/dropped locally; list order is preserved. PDF page lists expose selections and explicit order controls. Preview shows the current image or first PDF page.
3. Immutable options and ordered paths go to JobThread. One background QThread runs processing; editing/previews are disabled during jobs so PDFium is not used concurrently.
4. Processors open originals read-only, validate input/options, normalize images, and check a cancellation Event between file/page steps. Qt signals update progress/results on the UI thread.
5. Output names are exclusively reserved. Data is written to temporary files in the output folder and replaces only those reservations after completion. Failed writes remove incomplete output/temp files. Originals/prior outputs are not overwritten.
6. Completed outputs, per-file errors, and cancellation status are returned together. Paths open through the OS. No application network API is used.

No server, database, account, telemetry, upload, or plugin system exists. The default output folder is Documents/Local PDF Outputs and can be changed. GUI/job processes must restart in new environments.

## Constraints

- Stack: [ADR-0001](../decisions/ADR-0001-m1-stack.md). Scope: [product-spec.md](../product-spec.md).
- Cancellation cannot interrupt a native call. Render/resize buffers are bounded to 40 megapixels; images-to-PDF batches to 120 megapixels.
- Preview decoding is synchronous and bounded, so a slow input can briefly delay selection feedback; jobs run in the background.
- Structural operations preserve page content; full document-level attachment/bookmark/form/tag preservation and signature validity are not promised by M1.
- Cloud GUI tests are offscreen. Windows runtime and public distribution compliance are separate pending checks.
