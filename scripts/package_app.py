"""Build an onedir bundle on Windows, or an explicitly requested Cloud smoke bundle."""
import argparse
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('PySide6-Essentials', 'shiboken6', 'pypdf', 'pypdfium2', 'Pillow', 'pi-heif',
            'reportlab', 'cryptography', 'cffi', 'charset-normalizer', 'pycparser', 'pyinstaller')


def collect_notices(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    versions = {}
    for name in PACKAGES:
        dist = metadata.distribution(name)
        versions[name] = dist.version
        package_folder = folder / name
        package_folder.mkdir(exist_ok=True)
        (package_folder / 'METADATA.txt').write_text(dist.read_text('METADATA') or '', encoding='utf-8')
        for file in dist.files or ():
            if any(part in str(file).lower() for part in ('license', 'copying', 'notice')):
                source = dist.locate_file(file)
                if source.is_file():
                    # Preserve paths to avoid collisions among native component notices.
                    parts = [p for p in Path(str(file)).parts if p not in ('..', '.')]
                    destination = package_folder.joinpath(*parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, destination)
    for source in (ROOT / 'docs' / 'licenses').iterdir():
        if source.is_file():
            shutil.copyfile(source, folder / source.name)
    shutil.copyfile(ROOT / 'docs' / 'decisions' / 'ADR-0001-m1-stack.md', folder / 'DEPENDENCY-DECISION.md')
    for source in (ROOT / 'docs' / 'decisions').glob('ADR-*.md'):
        shutil.copyfile(source, folder / source.name)
    (folder / 'versions.json').write_text(json.dumps(versions, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cloud-smoke', action='store_true', help='Allow a non-Windows build for host-only smoke validation')
    args = parser.parse_args()
    if sys.platform != 'win32' and not args.cloud_smoke:
        parser.error('Windows executables must be built on Windows. Use --cloud-smoke only for host-only validation.')
    name = 'LocalPdfUtilities' if sys.platform == 'win32' else 'LocalPdfUtilities-CloudSmoke'
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
               '--name', name, '--paths', str(ROOT / 'src'),
               '--specpath', str(ROOT / 'build'), '--distpath', str(ROOT / 'dist'),
               '--workpath', str(ROOT / 'build' / 'pyinstaller'),
               '--collect-all', 'pi_heif', '--collect-all', 'pypdfium2', '--collect-data', 'reportlab',
               '--collect-data', 'local_pdf_editor',
               '--exclude-module', 'pytest', '--exclude-module', 'PySide6.QtNetwork']
    if sys.platform == 'win32':
        command.append('--windowed')
        # pi-heif Windows wheels keep decoder DLLs at site-packages root.
        # Copy them explicitly; collecting the Python package alone misses them.
        for file in metadata.distribution('pi-heif').files or ():
            if str(file).lower().endswith('.dll'):
                source = metadata.distribution('pi-heif').locate_file(file)
                command.extend(['--add-binary', f'{source}:.'])
    command.append(str(ROOT / 'scripts' / 'entrypoint.py'))
    subprocess.run(command, cwd=ROOT, check=True)
    collect_notices(ROOT / 'dist' / name / 'THIRD_PARTY_NOTICES')
    guide = (ROOT / 'docs' / 'm3-engines.md').read_text(encoding='utf-8')
    guide = guide.replace('](decisions/', '](THIRD_PARTY_NOTICES/').replace('](verification.md)',
                          '](https://github.com/jaydenkim197/local-pdf-editor/blob/main/docs/verification.md)')
    (ROOT / 'dist' / name / 'LOCAL-ENGINES.md').write_text(guide, encoding='utf-8')
    print(f'Built {ROOT / "dist" / name}. Distribution compliance and Windows runtime checks are still required.')


if __name__ == '__main__':
    main()
