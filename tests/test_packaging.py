import importlib.util
from pathlib import Path


def test_packaging_collects_real_native_notices(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'scripts/package_app.py'
    spec = importlib.util.spec_from_file_location('package_app', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.collect_notices(tmp_path)
    assert (tmp_path / 'versions.json').is_file()
    assert (tmp_path / 'LGPL-3.0.txt').is_file()
    assert list((tmp_path / 'pypdfium2').rglob('pdfium.txt'))
    assert list((tmp_path / 'pi-heif').rglob('LICENSES_bundled.txt'))
    assert list((tmp_path / 'reportlab').rglob('bitstream-vera-license.txt'))
    assert list((tmp_path / 'cryptography').rglob('LICENSE.APACHE'))
