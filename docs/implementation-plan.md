# Implementation Plan — M1, M2 and M3

1. Record the product scope and minimum stack decision; commit the foundation.
2. Implement the tool registry, job result/cancellation/progress contract, collision-safe output handling, PDF and image processors; verify real output files.
3. Implement one Qt tool workspace, cards/categories, input ordering, page controls, previews, background jobs, results, and local file/folder opening.
4. Add Windows onedir packaging and license collection; verify Cloud code, UI, build, and Windows wheel availability.
5. Update evidence and status, create logical commits, push to main.

M1 implementation and Cloud validation completed. Windows runtime/package validation remains pending until observed on Windows.

## Authorized M2

1. Gate on coherent M1 and passing regression tests; record minimum additions/security boundaries in ADR-0002.
2. Reuse the registry/job/output contract for crop, watermark, numbering, protection/removal, signature images, secure raster redaction, visual comparison and practical AcroForm support.
3. Verify page geometry/visible outputs, AES passwords, source-content removal, form values/appearances and cancellation/invalid inputs.
4. Connect shared options, password controls, form editors and page-region selection; run M1/M2 GUI regression tests.
5. Verify host-native package smoke, update documentation/environment instructions, commit and push.

M2 implementation/Cloud validation completed. Windows M1/M2 runtime and distribution-compliance checks remain separate incomplete tasks.

## Authorized M3

1. Gate on coherent M2 and passing regressions; apply search-first and verify engine licenses, redistribution, Windows support, offline operation and packaging before adoption.
2. Reuse existing pypdf/PDFium/Pillow/ReportLab/Qt Gui; integrate a user-installed local Tesseract 5, without adding Python dependencies, models or binaries to the package.
3. Implement compression, OCR, repair, raster PDF/A-1b and basic local HTML printing through the existing registry/workspace/job/output contract.
4. Verify real text/images/forms, compression sizes, broken cross-reference recovery, OCR searchable text, independent PDF/A conformance, local HTML resource boundaries, errors/cancellation/batches/collisions, all shared GUI jobs and native package smoke.
5. Update context/license/setup/verification documents and Cloud instructions, create logical commits, push main.

M3 implementation/Cloud validation completed. Next incomplete work: actual Windows M1/M2/M3 source and packaged validation, including Tesseract/data discovery and offline clean-machine behavior. Public redistribution compliance remains a release prerequisite. No further milestone is authorized.
