"""Exercise actual native dependencies inside a built executable."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

from PIL import Image
from PySide6.QtWidgets import QApplication

from .processing import run_job
from .tools import Options


def smoke_test():
    from .app import Window

    with TemporaryDirectory() as directory:
        root = Path(directory)
        image = root / 'smoke.png'
        Image.new('RGB', (32, 24), 'red').save(image)
        created = run_job('image_pdf', [image], root)
        if created.errors or len(created.outputs) != 1:
            raise RuntimeError(str(created))
        rendered = run_job('pdf_png', created.outputs, root, Options(dpi=72))
        if rendered.errors or len(rendered.outputs) != 1:
            raise RuntimeError(str(rendered))
        with Image.open(rendered.outputs[0]) as reopened:
            if reopened.size != (32, 24):
                raise RuntimeError('Unexpected rendered output size')
        if '--heic-fixture' in sys.argv:
            fixture = Path(sys.argv[sys.argv.index('--heic-fixture') + 1])
            decoded = run_job('heic_png', [fixture], root)
            if decoded.errors or len(decoded.outputs) != 1:
                raise RuntimeError(str(decoded))
            with Image.open(decoded.outputs[0]) as reopened:
                reopened.load()
        app = QApplication.instance() or QApplication([])
        window = Window()
        window.select_tool('image_resize')
        window.add_files([image])
        window.show()
        app.processEvents()
        if window.files.count() != 1 or window.preview.pixmap().isNull():
            raise RuntimeError('Qt preview did not load')
        window.close()
    print('SMOKE PASS: image → PDF → rendered image, codecs imported, Qt workspace and preview')
    return 0
