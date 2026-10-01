# Development Log

## 2026-10-01 — Cloud-compatible development baseline

### Changes
- Copied search-first and verification-loop from the supplied baseline ZIP into repository-local skill directories without modifying their contents.
- Adapted the supplied project instructions to use repository-local skills and the existing Cloud checkout.
- Added project state, architecture, and decision documentation; updated the project README.
- Did not install extra tools or implement PDF functionality.

### Verification
- Compared both installed SKILL.md files byte for byte with their ZIP sources.
- Checked required files, local skill references, the preserved status model, and Git whitespace errors.
- No application build or tests exist, so none were run.

### Next
Define the PDF editor MVP and target platform before selecting dependencies.

## 2026-10-01 — M1 foundation

- Recorded the full M1 scope and excluded features in product-spec.md.
- Selected Python/Qt Widgets, pypdf/PDFium, Pillow, decoder-only pi-heif, pytest and PyInstaller in ADR-0001.
- Installed pinned wheels and the editable project; checked dependency consistency and offscreen Qt startup.
- Official documentation websites returned proxy 403; research used publisher wheel metadata, license files and runtime probes.
- Windows runtime remains unverified. Next: processors and shared UI.

## 2026-10-01 — M1 processing layer

- Implemented the tool registry, job results/progress/cancellation, collision-safe temporary output commits, PDF structural operations/rendering, image PDF export, conversion, resize, and HEIC decode.
- Preserved originals and completed outputs on partial batch failures or cancellation; normalized image orientation and JPEG transparency.
- Added bounded render/resize sizes and encrypted/corrupt input errors.
- 38 Cloud tests passed, covering real PDFs and a licensed HEIC fixture, page order/rotation/reopen, dimensions/formats/EXIF, batches, invalid options, partial failures, cancellation, Unicode names and concurrent output collisions.
- Corrected a PDFium page lifetime API mismatch observed in the first rendering probe. Windows runtime remains pending.

## 2026-10-01 — Shared M1 desktop app and packaging

- Connected all 14 tools to one Qt workspace with categories/cards, drop/picker, ordered files/pages, preview/options, background processing, progress/cancellation, results and local file/folder opening.
- Added host-native onedir packaging, explicit Windows HEIC DLL inclusion, license collection, executable smoke checks, and Windows/Linux CI instructions.
- 59 Cloud tests passed (38 processing, 20 GUI, 1 packaging notice). All 14 tools executed through GUI jobs.
- Built the 192 MB Linux bundle and passed frozen image/PDF/HEIC/Qt smoke. Downloaded all pinned Windows x64 runtime wheels; no Windows binaries were run.
- Reviewed screenshots of home/workspace; corrected hidden option parsing and raw metadata notice collection after observed failures.
- Updated product requirements, architecture, status, verification and Windows setup instructions. Actual Windows GUI, DLL/package behavior and public release compliance remain pending.

## 2026-10-01 — M2 processing and shared workflow

- M1 gate: read requested documentation/skills, confirmed clean main matched GitHub, reran all 59 baseline tests successfully. Pending Windows/release checks do not block source development; no M1 stack change or M3 work.
- Added crop, watermark, numbers, AES-256 protection/correct-password removal, signature images, secure source-free raster redaction, visual comparison and standard AcroForm inspect/fill/flatten. ReportLab/cryptography licenses reviewed from installed publisher metadata.
- Reused registry/options/Context/Result/output layer and one Qt workspace; added point-coordinate region preview, password handling, field editor and relevant controls.
- Corrected writer context reset and radio flattening appearance collisions using observed failures; cloned inside context and rasterized filled appearances for flattening.
- Full suite: 101 passed (29 M2 processor + 13 M2 GUI + 59 baseline/notice). Validated source-content removal, actual pixels, AES passwords, form limits, cancellation/cleanup, batch safety and stale redaction prevention.
- Linux onedir/frozen M1/M2 smoke passed; Windows x64 additions downloaded but not executed. Actual Windows runtime and public distribution compliance remain pending; exact next task is Windows M1/M2 source/packaged validation.

- Final geometry review preserved original rotation/annotation coordinates for crop/overlays; rotated form crop and signature tests verify unchanged form pixels outside the edited region.
- Re-executed the retained Cloud install script successfully with M2 pins; saved updated start instructions in the environment draft. Updated README usage/limits and CI naming for M1/M2; no Windows CI result or environment publication is claimed.

## 2026-10-01 — M3 local engines and shared workflow

- Read repository-owned context/skills and gated on clean coherent M2, 101 passing regressions and dependency consistency. Windows/public-release checks remained pending without changing settled M1/M2 decisions.
- Search-first: reused existing pypdf/PDFium/Pillow/ReportLab/Qt Gui; reviewed engine/source/model/profile licenses, redistribution, Windows support, offline use and packaging in ADR-0003. No Python runtime dependency added. External Tesseract 5 is user-installed, with no redistributed OCR binary/DLL/model/font.
- Implemented stream/object compression with optional bounded opaque-image JPEG/downsample; forgiving-parser repair with strict reopen/render; searchable raster OCR with cancellable timed child; fresh raster PDF/A-1b with licensed ICC v2/output intent/XMP; basic local HTML via Qt Gui PDF writing.
- Reused cards/registry/options/QThread/Context/Result/collision-safe output and added scoped controls. Encrypted M3 input requires a correct password and outputs unencrypted copies; user hints/documentation state this.
- Verification: 143 passed (35 M3 processors + 7 M3 GUI + 101 previous). Four independent Preflight PDF/A specimens accepted; ordinary source rejected as expected. Tested actual pixels/text/forms/sizes, wrong passwords, partial batches, cancellation/temp cleanup, remote/outside HTML resource rejection and all 28 GUI tools.
- Real English OCR scan passed; separate installed `eng+kor` model probe in a Unicode data folder recognized Korean/English sample text. Models stayed outside the repository. Wheel/native Linux package built and frozen M1/M2/M3 smoke including real installed OCR passed.
- Corrected HTML extraction test to normalize Qt's whitespace mapping while retaining text/image checks. Removed empty ReportLab font/text resources in fresh PDF/A output. Native tracing found QPrinter CUPS probes; switched to direct QPdfWriter, reran verification and confirmed no printer-service/remote traffic in observed source/frozen samples.
- Updated scope/status/architecture/plan/README/license/engine/Windows verification context, CI prerequisite instructions, package data/notices/guide and reusable Cloud configuration. No actual Windows runtime/CI result or environment publication is claimed.
- Cloud tool preparation retained the previously HTTPS-downloaded, SHA-256-verified Preflight jar in ignored cache; later fresh Maven requests returned HTTP 429. Installer validates/reuses the cache and verifies any new download without disabling TLS/checksums. Fresh validator download remains subject to Maven availability; the current conformance workflow is verified.
- Exact next incomplete task: Windows x64 source/full-suite and frozen offline M1/M2/M3 validation with local Tesseract English/Korean data, then record results/fix Windows-specific failures. Public binary release compliance remains separate; no later milestone authorized.

## 2026-10-02 (Asia/Seoul) — Requirements and defect audit

- Read repository context and both local skills; initial main was clean and matched origin at `1eb47f4`. Audited authorized M1/M2/M3 coverage without starting another milestone. Existing 143 tests passed before new boundary probes.
- Reproduced five defects: redaction's nominal DPI missed overlapping edge pixels on fractional page sizes; PDF image export lacked filled form appearances; optional compression converted CMYK to RGB, discarded hidden-layer references and lost ICC interpretation.
- Reused existing raster/PDFium/pypdf/Pillow workflows: actual per-axis bitmap/page scales with outward rounding; initialized forms in M1 export; retained image color models/layer/rendering attributes and skipped calibrated/ICC re-encoding. No new dependencies or architecture.
- Added eight meaningful regressions that failed against the affected old code: three fractional/rotated redaction, two form image-export and three compression color/layer/profile cases. Extended source/frozen smoke with the security/form regressions.
- Final full suite 151 passed in 20.99 s, 0 errors/failures/skips; four independent Preflight specimens enabled. Dependency consistency, compile/whitespace, fresh Linux onedir and source/frozen real HEIC/AES/forms/PDF-A/HTML/installed English OCR passed. Bundled ICC checksum/notices/guide verified; frozen network sample had no CUPS/remote document sends, retaining native local interface queries.
- Updated README, product scope, current architecture, M3 behavior clarification, status and verification; added `docs/verification-audit-2026-10-02.md` with requirement coverage, reproduced defects, existing-output guidance and remaining work. Historical evidence preserved.
- No actual Windows or Korean OCR rerun is claimed; GitHub Actions inspection returned Forbidden. Exact next incomplete task remains Windows source/full-suite/frozen and clean-machine offline M1/M2/M3 validation with local English/Korean OCR prerequisites. Public distribution compliance remains pending.

## 2026-10-02 (Asia/Seoul) — Windows CI diagnosis and package delivery

- User authorized Windows verification and executable preparation. Native Git access works; API requests are denied by the Cloud egress proxy. Public GitHub web access is available and exposed failed source-suite results on both Windows and Ubuntu in run 36889443508 for ab917cb. Detailed logs require login; no passing Windows result is inferred.
- Search-first: extended the existing Actions workflow/package helper and composed standard-library XML reporting. Added explicit failure annotations/summary and retained JUnit evidence so actual failing tests can be diagnosed through the permitted web route. Added a checksummed Windows onedir ZIP artifact gated on passing source/frozen smoke; this is a development package, not a public release.
- Locally verified reporting against actual retained 151-case evidence and synthetic pass/failure/collection-error/empty/malformed reports, with meaningful exit statuses; parsed workflow YAML and checked artifact success gates/whitespace. Actionlint is not installed (the host's `go` command is not the Go language toolchain); no actionlint or Windows execution result is claimed at this checkpoint.

- Diagnostic run 36914991351 produced real hosted failures: Linux collection cannot load libEGL.so.1; Windows OCR rejected version identification, and basic HTML tests extracted empty text. Added libegl1/libopengl0, accepted optional `v` in Tesseract 5 identification with four positive/negative regression cases, and registered the existing licensed Vera font as HTML's default.
- Final local suite at this corrective checkpoint: 155 passed with four independent Preflight cases enabled; dependency consistency/compile/whitespace and successful/failing smoke JSON exits checked. Windows execution remains pending the new run, not inferred from Linux.
- Added a native Windows frozen verification script: Unicode relocation, no Python on PATH, temporary outbound firewall rules for the executable/engine, native Qt at 100%/150%, and real English/Korean OCR. CI prepares the upstream Apache-licensed Korean model pinned to commit 87416418657359cb625c412a48b6e1d6d41c29bd with SHA-256 6b85e11d9bbf07863b97b3523b1b112844c43e713df8b66418a081fd1060b3b2. Model/Windows font are used locally for synthetic checks, not shipped. A hosted runner still contains installed Python and does not establish physical clean-machine behavior.

- Observed run 36917030277 for 22d7a9a: source/build and both native frozen Windows checks passed; public annotations confirm scales 1/1.5, relocation/no Python PATH/outbound blocking and English/Korean OCR. Actual Windows engine reports v5.5.3.20260724. Windows development ZIP artifact generated (58.5 MB) with JUnit/JSON evidence retained. Local rebuilt frozen Linux smoke/report also passed.
- Enabled pinned independent Preflight/Java in both hosted platforms and public notices for actual case counts/conformance; that stronger run is pending at this checkpoint. Added Korean Windows package-use guide/README links and separated successful hosted evidence from remaining physical/manual/public-release checks. No application/runtime dependency was added.

- Final observed run 36919001214 for 578a042 passed: Windows/Linux each publicly reported 155 cases, 0 failures/errors/skips and four independent Preflight specimen acceptances. Windows native frozen 100%/150% relocated/no-Python-PATH/outbound-blocked English/Korean OCR checks passed again. Package artifact retained (58.5 MB); inner ZIP SHA-256 c63b872c00ad760bc659c8407e1df94288fb688dc77e1b92c45e5ebd282d6a51. JUnit/JSON evidence is downloadable in the same run.
- Updated current status/plan/architecture/engine guide and verification with observed hosted Windows evidence, and linked the actual package in the Korean use guide. Physical personal-PC Explorer/dialogs/display/real-document/clean-machine behavior and public-release compliance remain unverified; those are the exact next incomplete tasks. Deprecation warnings in Actions were nonblocking; no app/test failures or skips in the final run.
