# Product Specification — M1

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
PDF to Word/PowerPoint/Excel, Word/PowerPoint/Excel to PDF, direct editing of existing PDF text/images/shapes, AI summarization, AI translation, PDF to Markdown. No M2/M3 implementations or plans.

## M1 Boundaries
- Encrypted PDFs are rejected with a clear message; no password/security tool is included.
- HEIC uses the primary image, normalizes orientation, and converts HDR to 8-bit output. Multi-image HEIC sequences and color-managed HDR fidelity are outside M1.
- Images to PDF uses 72 points/inch (one pixel per PDF point). PDF export defaults to 144 DPI, with user control.
- Resize aspect preservation fits within a requested width/height box. Percentage resize rounds to the nearest pixel, minimum one pixel.
- Cancellation is cooperative between files/pages. A native decode or single PDF write cannot be interrupted mid-call.
- Inputs requiring extremely large rendered buffers are rejected. Image decompression-bomb warnings become errors. Jobs run off the UI thread.
- Signed PDFs may lose signature validity after structural changes; this is shown to users of PDF manipulation tools.

## Verification
Cloud processing tests and offscreen Qt interaction tests are separate from Windows desktop runtime and packaged executable validation. See [verification.md](verification.md).
