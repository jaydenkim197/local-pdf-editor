# ADR-0001: Offline M1 Desktop Stack

## Status
DECISION

## Date
2026-10-01

## Context and Search
The repository contains only the baseline; no existing app or framework can be reused. M1 requires local PDF structural operations, rendering, image/HEIC conversion, shared Windows UI, and meaningful processing tests in Linux Cloud.

Official documentation sites were blocked by the environment proxy (403). Research used publisher-provided PyPI wheel metadata, bundled license files, package APIs, and executable Cloud probes. Links below identify upstream sources; live website access was not verified.

## Options Compared

| Option | Fit and tradeoff |
|---|---|
| .NET/WPF | Excellent native Windows UI; WPF runtime/UI tests require Windows, and PDF/HEIC require additional native integrations |
| Electron + JS PDF libraries | Shared web UI; Chromium adds size, HEIC still needs native/WASM integration |
| Tauri + Rust/web UI | Smaller shell; WebView2 and Rust/native codec integration add toolchains and platform boundaries |
| Python + Qt Widgets | One runtime with mature cross-platform PDF/image wheels, shared UI and offscreen Cloud tests; larger packaged footprint than a minimal native app |
| MuPDF/PyMuPDF | Strong combined PDF engine; AGPL/commercial licensing adds a distribution decision unnecessary for M1 |
| qpdf/PDFBox | Structural operations available, but separate renderer and executable/JVM/runtime integration would add moving parts |

## Decision
- Python 3.12, PySide6-Essentials 6.11.2 (Qt Core/Gui/Widgets only).
- pypdf 6.19.0 for structure, pypdfium2 5.13.0/PDFium for rendering and previews.
- Pillow 12.3.0 for images and PDF creation; pi-heif 1.4.0 for HEIC decoding only.
- pytest for processors and offscreen Qt integration; PyInstaller 6.22.3 for Windows onedir packaging built on Windows.
- No network dependency at runtime, plugin system, server, or optional agent tools.

## Licensing and Redistribution
- pypdf: BSD-3-Clause; pypdfium2: BSD/Apache plus PDFium component notices; Pillow: MIT-CMU.
- Qt/PySide: use LGPLv3 path with dynamically loaded libraries; include notices and corresponding upstream source information, preserve replacement of shared libraries and user reverse-engineering rights for debugging modifications. Do not use GPL-only Qt modules.
- pi-heif wrapper is BSD; bundled libheif/libde265 are LGPLv3. Its wheel has no x265 encoder. The current pillow-heif wheel includes an x265 encoder; it was not retained because encoding HEIC is not needed and introduces GPL distribution considerations.
- pi-heif is discontinued at 1.4.0. It is pinned for this bounded decoder use; review security/support before release. Installed bundled notice source version references differ from runtime version reports; do not treat those links alone as a complete corresponding-source offer. Verify Windows wheel source versions before distribution.
- PyInstaller has a GPL exception permitting bundled applications under their own licenses; this does not waive dependency obligations.
- No application license is selected by this decision. Before public binary release, finish the source/notice compliance review and evaluate HEVC patent obligations for the intended distribution jurisdiction.

## Evidence / Sources
- [Qt for Python](https://doc.qt.io/qtforpython-6/licenses.html)
- [pypdf](https://github.com/py-pdf/pypdf)
- [pypdfium2](https://github.com/pypdfium2-team/pypdfium2)
- [Pillow](https://github.com/python-pillow/Pillow)
- [pi-heif](https://pypi.org/project/pi-heif/1.4.0/) and [HEIF bindings](https://github.com/bigcat88/pillow_heif)
- [PyInstaller license](https://pyinstaller.org/en/stable/license.html)

Installed wheels imported successfully; Qt Widgets started offscreen. Dependency pins are in pyproject.toml and requirements-dev.txt. The product behavior is in [product-spec.md](../product-spec.md); implementation evidence belongs in [project-status.md](../project-status.md).
