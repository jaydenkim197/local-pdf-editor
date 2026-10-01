"""Exercise actual native dependencies inside a built executable."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

from PIL import Image
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from .processing import run_job
from .tools import Options


def smoke_test():
    from .app import Window

    with TemporaryDirectory() as directory:
        root = Path(directory)
        app = QApplication.instance() or QApplication([])
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
        source = root / 'm2.pdf'
        canvas = Canvas(str(source), pagesize=(240, 180))
        canvas.drawString(20, 140, 'SMOKE SECRET')
        canvas.acroForm.textfield(name='name', x=20, y=70, width=150, height=20)
        canvas.showPage(); canvas.save()
        def check(tool, files, options):
            result = run_job(tool, files, root, options)
            if result.errors or not result.outputs:
                raise RuntimeError(f'{tool}: {result.errors}')
            return result.outputs
        protected = check('pdf_protect', [source], Options(new_password='smoke-test-password'))
        unlocked = check('pdf_unlock', protected, Options(password='smoke-test-password'))
        if PdfReader(unlocked[0]).is_encrypted:
            raise RuntimeError('Password removal failed')
        check('pdf_crop', [source], Options())
        check('pdf_watermark', [source], Options(text='SMOKE'))
        numbered = check('pdf_numbers', [source], Options())
        check('pdf_signature', [source], Options(signature_path=str(image), rect=(20, 20, 40, 30)))
        redacted = check('pdf_redact', [source], Options(dpi=72, redactions=((1, 10, 20, 220, 40),)))
        if PdfReader(redacted[0]).pages[0].extract_text().strip() or PdfReader(redacted[0]).get_fields():
            raise RuntimeError('Redaction retained source structure')
        check('pdf_compare', [source, numbered[0]], Options(dpi=72))
        check('pdf_forms', [source], Options(form_values=(('name', 'Smoke'),), flatten_forms=True, dpi=72))
        check('pdf_compress', [source], Options())
        check('pdf_repair', [source], Options())
        archival = check('pdf_pdfa', [source], Options(dpi=144))
        reader = PdfReader(archival[0])
        if reader.xmp_metadata.pdfaid_part != '1' or not reader.root_object.get('/OutputIntents'):
            raise RuntimeError('PDF/A metadata/profile missing')
        html = root / 'local.html'
        html.write_text('<h1>LOCAL HTML</h1><p>Offline printing</p><img src="smoke.png">', encoding='utf-8')
        printed = check('html_pdf', [html], Options())
        if 'LOCAL' not in PdfReader(printed[0]).pages[0].extract_text():
            raise RuntimeError('HTML content missing')
        if '--ocr-smoke' in sys.argv:
            recognized = check('pdf_ocr', archival, Options(dpi=144))
            if 'SMOKE' not in PdfReader(recognized[0]).pages[0].extract_text():
                raise RuntimeError('OCR searchable text missing')
        window = Window()
        window.select_tool('image_resize')
        window.add_files([image])
        window.show()
        app.processEvents()
        if window.files.count() != 1 or window.preview.pixmap().isNull():
            raise RuntimeError('Qt preview did not load')
        window.close()
    print('SMOKE PASS: M1/M2, M3 compression/repair/PDF-A/HTML, Qt workspace/preview' +
          (', installed Tesseract OCR' if '--ocr-smoke' in sys.argv else '; OCR engine not requested'))
    return 0
