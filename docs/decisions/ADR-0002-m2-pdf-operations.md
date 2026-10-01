# ADR-0002: M2 PDF Operations and Security Boundaries

## Status
DECISION

## Date
2026-10-01

## M1 Gate
Read instructions, status, implementation plan, verification and development log. Clean main matched the remote; all 59 M1 tests passed again. Shared registry/workspace/job/output architecture is coherent. Windows runtime and public-release LGPL/HEVC compliance remain pending; neither establishes a failed M1 development capability or requires changing the selected stack. No M3 work is authorized.

## Search and Decision
Reuse pypdf, PDFium, Pillow and the job/output layer. Add ReportLab 5.0.1 for overlays/lossless raster PDF output, and cryptography 50.0.2 for pypdf AES-256. Installed publisher metadata/licenses identify ReportLab's BSD license and cryptography's Apache-2.0/BSD choice. ReportLab's bundled Vera font license is retained by packaging. No AGPL engine or replacement desktop framework is added.

## Behavior
- Crop changes page CropBox, keeping underlying source content. It is not a security operation.
- Watermarks/page numbers and signature images add content using a viewport-to-page transform that preserves original rotation and annotations. Signature insertion is a visible image, not certificate-based signing. Rectangle coordinates use visible page points from the top-left; crop uses left/top/right/bottom margins.
- AES-256 protection uses an explicit new password. Removal attempts only the supplied user/owner password through pypdf's decrypt API. Passwords stay transient, masked and excluded from repr/logs/configuration.
- Secure redaction rebuilds **every** page from a rendered, losslessly encoded image. Marked rectangles are filled before encoding, rounding outward to pixel boundaries. No original text streams, annotations, forms, attachments, scripts, layers, metadata or incremental history are copied. All selectable/searchable text, vectors and interactive fields are lost. The output is resolution-limited; users must inspect selected regions and the resulting file before sharing. It is not a black overlay over a retained source PDF.
- Comparison is page-by-page visual comparison at a chosen DPI/threshold, producing highlighted PNGs and a JSON report. Page insertion/deletion is reported by index; semantic matching and metadata comparison are not promised.
- Practical forms means inspection and filling standard AcroForm text, check/radio and single-choice fields. Text edits are ASCII-only; untouched existing values are preserved. XFA, pushbuttons, certificate signature fields, multi-select and unsupported/read-only edits are rejected. Optional flattening rasterizes all pages with lossless pixels and removes interactivity/text search. This avoids an observed pypdf radio-group appearance resource collision when flattening widgets directly.

## Guardrails and Consequences
Use shared output collision/cancellation semantics. Reject invalid rectangles, non-finite coordinates, excessive buffers and unsupported geometry rather than guessing. Raster redaction deliberately sacrifices document structure for a verifiable removal boundary. Public binary distribution compliance remains a separate release prerequisite from source development. Actual Windows GUI/DLL/package checks remain pending until observed.
