# Offline M3 setup and boundaries

Compression, repair, PDF/A-1b and basic HTML printing use the application's existing dependencies. No network service, account or credential is required. HTML input is UTF-8; images must be JPEG/PNG inside its folder. External stylesheets, JavaScript and modern browser CSS layout are unsupported.

## Tesseract OCR prerequisite

Install **Tesseract 5** once on Windows, including your required languages and the PDF font `pdf.ttf`. Follow [upstream installation guidance](https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md) or build from the [Apache-licensed upstream source](https://github.com/tesseract-ocr/tesseract). Windows third-party distributions include other native components: inspect their notices before redistributing them. This app does not ship, download or update an engine/model.

In OCR PDF choose `tesseract.exe` and, if needed, the installed `tessdata` folder. Blank engine auto-detects PATH, then on Windows an `engines/tesseract/tesseract.exe` directory beside the application, then `C:\Program Files\Tesseract-OCR\tesseract.exe`. Blank data uses the engine installation's normal lookup, or its adjacent tessdata directory when present. Explicit data must contain `pdf.ttf` and selected language `.traineddata` files. Moving an executable alone does not move required DLLs and data.

Use `eng`, `kor` or `eng+kor` **only when those languages are installed**. Automatic layout, single-block and sparse-text modes are available. Start with 200–300 DPI for scans, within the 40 megapixel/page and 120 megapixel/document limits. Language data is [Apache-2.0](https://github.com/tesseract-ocr/tessdata_fast/blob/main/LICENSE); install it before going offline. Recognition accuracy, handwriting and complex layouts are not guaranteed; review the searchable text before relying on it.

From a terminal, verify the same executable/data before using the UI:

```powershell
& 'C:\Program Files\Tesseract-OCR\tesseract.exe' --version
& 'C:\Program Files\Tesseract-OCR\tesseract.exe' --list-langs
```

OCR runs a child process without a shell or network request. Cancel terminates an active engine and cleans temporary page files. A page has a 180-second engine timeout. Output is a fresh image PDF plus recognized hidden text, with original page dimensions; original text/forms/links/attachments/metadata are discarded. Supplying a PDF password decrypts the input locally; the result is unencrypted.

## Packaging and verification

The normal onedir package includes Qt Gui PDF writing and the licensed ICC profile/notices. Tesseract is an external installation prerequisite; a clean machine can use the other tools without it and receives an actionable OCR error when it is absent. Do not claim a fully self-contained OCR distribution.

Source/frozen `--smoke-test` exercises compression, repair, PDF/A and HTML. Add `--ocr-smoke` to require and exercise installed Tesseract; absence is a failure when this flag is supplied. Run the complete pytest suite only after installing Tesseract 5 with English data. CI installs that prerequisite explicitly. No OCR tests are silently skipped.

For independent PDF/A conformance verification, download Apache PDFBox Preflight 3.0.6 (developer-only, Java required) using HTTPS and compare SHA-256 with ADR-0003. Set `PDF_PREFLIGHT_JAR` to the local jar, then run `python -m pytest -q tests/test_m3.py`; four PDF/A specimen cases run the real independent validator. Without that variable, tests still check raster fidelity, structures, output intent and XMP but do not run external conformance validation. Inspect real PDF/A outputs independently for important archiving workflows.

Lossless compression may produce a larger file. Optional image compression is lossy; text/forms are retained but eligible pictures may lose detail. Direct RGB/gray/CMYK color models and optional-layer visibility are preserved; calibrated/ICC-profiled images are not JPEG-reencoded to avoid changing color interpretation. Repair rewrites objects readable by the forgiving parser; missing bytes/content cannot be recovered. PDF/A conversion creates raster **PDF/A-1b**, losing search, vectors and interactivity, and is not PDF/A-1a/2/3 conversion. Actual Windows runtime, font/DLL behavior and independent viewer checks remain pending until observed.

See [ADR-0003](decisions/ADR-0003-m3-local-engines.md) for license/redistribution/platform/packaging research, and [verification.md](verification.md) for observed results.
