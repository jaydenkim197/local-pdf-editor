# Product Specification — M1 and M2

## Goal
Windows-first, fully local PDF and image utilities. Files stay on the user's machine. GitHub owns development history; the application has no accounts, telemetry, network calls, or remote processing.

## Included
- PDF merge, split into individual pages, reorder, delete selected pages, import pages from another PDF, rotate, export JPEG/PNG, and JPEG/PNG to PDF.
- HEIC to JPEG/PNG, JPEG to PNG, PNG to JPEG.
- Batch image resize: 25/50/75/100%, arbitrary percentage, explicit width/height, optional aspect preservation, EXIF orientation normalization.
- Shared tool cards → selection/drop → ordered file list → useful preview → options → process/progress/cancel → results → open file/output folder.
- Page selections use 1-based numbers and ranges. Reorder requires every page exactly once. Import uses a selected source-page range and a destination insertion position.
- Output filenames are sanitized for Windows and preserve Unicode. Existing files and original inputs are never overwritten. Each output is committed from a temporary file after completion; completed outputs survive cancellation or a later batch error and are listed to the user.

## Navigation
All, Workflow, PDF Organization, PDF Optimization, PDF Conversion, PDF Editing, PDF Security, PDF Analysis, Image. Empty categories explain that no M1 tools are available; they do not contain future feature placeholders.

## Explicitly Out of Scope
PDF to Word/PowerPoint/Excel, Word/PowerPoint/Excel to PDF, direct editing of existing PDF text/images/shapes, AI summarization, AI translation, PDF to Markdown. No M3 implementations or plans.

## M1 Boundaries
- M1 tools reject encrypted PDFs. M2 tools accept a supplied password; no password recovery/cracking or bypass is included.
- HEIC uses the primary image, normalizes orientation, and converts HDR to 8-bit output. Multi-image HEIC sequences and color-managed HDR fidelity are outside M1.
- Images to PDF uses 72 points/inch (one pixel per PDF point). PDF export defaults to 144 DPI, with user control.
- Resize aspect preservation fits within a requested width/height box. Percentage resize rounds to the nearest pixel, minimum one pixel.
- Cancellation is cooperative between files/pages. A native decode or single PDF write cannot be interrupted mid-call.
- Inputs requiring extremely large rendered buffers are rejected. Image decompression-bomb warnings become errors. Jobs run off the UI thread.
- Signed PDFs may lose signature validity after structural changes; this is shown to users of PDF manipulation tools.

## Verification
Cloud processing tests and offscreen Qt interaction tests are separate from Windows desktop runtime and packaged executable validation. See [verification.md](verification.md).

## M2 Scope and Behavior

- Crop selected pages by left/top/right/bottom visible margins in points. Cropping keeps hidden original content; use secure redaction for removal.
- Add text watermarks (font, size, angle, opacity) and sequential numbers to selected pages. Use bundled Vera when it contains the requested glyphs; otherwise choose an appropriate .ttf, including for Korean. Font embedding permissions depend on the selected font.
- Protect with AES-256 or remove protection with the correct supplied password. Passwords are masked, transient, absent from logs/configuration and cleared from controls when jobs start.
- Insert a JPEG/PNG signature image in a visible rectangle; this is visual signing, not a cryptographic digital signature.
- Secure redaction: select a page and drag regions or enter `page:left,top,width,height` per line. Coordinates use the rendered visible page's top-left in points. Every page is rebuilt as a lossless raster image after burning out marked pixels with outward rounding. Original text, metadata, form values, layers, annotations, attachments and document history are not copied. All text search, vector quality and interactivity are lost; results are resolution-limited (36–300 DPI). Users must mark every region needing removal and inspect outputs before sharing. Unmarked visible sensitive content remains visible.
- Visual PDF comparison: exactly two PDFs, compared by page index at 36–300 DPI and threshold 0–255 (default 8 per channel). Changed pages yield highlighted PNGs and a JSON report with dimensions/counts/missing pages. Semantic page matching, metadata equality and cryptographic equivalence are not included. The same input password is used for a batch/comparison.
- Practical forms: inspect standard AcroForm text, checkboxes, radio groups and single-choice lists, edit permitted values, save an editable copy or flatten all pages to images. Form text filling is ASCII-only to avoid unsupported existing-font appearances. Existing Unicode values are preserved when untouched. XFA, pushbuttons, certificate fields, read-only fields and multi-select edits are unsupported. Flattening loses all selectable text/interactivity and uses the same raster limits as redaction.
- Geometry-aware tools map visible coordinates while preserving page rotation and annotations; overlay/crop pages with UserUnit other than 1 are rejected. Invalid bounds, passwords, fonts, values and excessive render buffers fail without incomplete PDF outputs. Comparison may preserve earlier diff PNGs if later work fails/cancels.
