# Dependency Notices and Distribution Review

The packaging helper copies installed wheel metadata, license/notice files, dependency version information and LGPLv3/GPLv3 texts into THIRD_PARTY_NOTICES beside the executable. LGPL-3.0.txt and GPL-3.0.txt are the unmodified standard texts from the build host's /usr/share/common-licenses.

The selected Qt Core/Gui/Widgets and HEIC native libraries are dynamically loaded; onedir packaging retains shared libraries. This is a development build, not a completed public distribution compliance review.

Before a public binary release:
- Verify all shipped Qt plugins and native components and include their copyright notices/licenses.
- Provide corresponding source/source-offer information for the actual LGPL library builds, including upstream changes, build material, and instructions sufficient for library replacement. The HEIC wheel's bundled source links list older versions than the runtime library reports; resolve this discrepancy rather than relying on those links.
- Preserve the rights required by LGPLv3, including replacement/relinking and reverse engineering to debug modifications. Avoid a restrictive end-user license that conflicts with them.
- Confirm HEVC patent obligations for the intended distribution and jurisdiction.
- Review pi-heif support/security because 1.4.0 is its final release.
- Choose the application's own license explicitly when release requirements are known.

See [ADR-0001](../decisions/ADR-0001-m1-stack.md). Creating a package or collecting these files does not certify legal compliance.
