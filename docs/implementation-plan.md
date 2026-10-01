# Implementation Plan — M1 and M2

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

Do not implement M3. Windows M1/M2 runtime and distribution-compliance checks remain separate incomplete tasks.
