"""M3 operations composed from existing engines and an offline Tesseract CLI."""
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile

import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject, DecodedStreamObject, DictionaryObject, NameObject,
    NumberObject, TextStringObject,
)

from .m2 import render, write_raster_document
from .processing import MAX_PIXELS, Cancelled, Context, open_image, read_pdf, rgb


def check_image_dimensions(resources):
    pending = [resources]
    seen = set()
    while pending:
        xobjects = pending.pop().get('/XObject')
        if not xobjects:
            continue
        for reference in xobjects.get_object().values():
            obj = reference.get_object()
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            if obj.get('/Subtype') == '/Image':
                images = [obj]
                for key in ('/SMask', '/Mask'):
                    if key in obj and isinstance(obj[key], DictionaryObject): images.append(obj[key])
                if any(int(image.get('/Width', 0)) * int(image.get('/Height', 0)) > MAX_PIXELS for image in images):
                    raise ValueError('Image exceeds the 40 megapixel limit.')
            elif obj.get('/Subtype') == '/Form' and '/Resources' in obj:
                pending.append(obj['/Resources'])


def compress_pdf(path, folder, opt, ctx):
    if not 0 <= opt.image_max_dimension <= 40000:
        raise ValueError('Maximum image dimension must be 0–40000 pixels (0 preserves dimensions).')
    with ExitStack() as stack:
        reader = read_pdf(stack, path, opt.password)
        with PdfWriter() as writer:
            writer.clone_document_from_reader(reader)
            seen = set()
            for index, page in enumerate(writer.pages):
                ctx.check()
                if opt.compress_images:
                    check_image_dimensions(page['/Resources'])
                    for item in page.images:
                        original_image = item.image
                        try:
                            ctx.check()
                            ref = item.indirect_reference
                            if ref is None or ref.idnum in seen:
                                continue
                            seen.add(ref.idnum)
                            obj = ref.get_object()
                            # Re-encoding masks, palette/bitonal images can alter transparency or line art.
                            if '/SMask' in obj or '/Mask' in obj or item.image.mode not in ('RGB', 'L', 'CMYK'):
                                continue
                            with rgb(item.image) as replacement:
                                if opt.image_max_dimension:
                                    replacement.thumbnail((opt.image_max_dimension,) * 2, Image.Resampling.LANCZOS)
                                item.replace(replacement, quality=opt.quality)
                                if len(ref.get_object()._data) >= len(obj._data):
                                    writer._objects[ref.idnum - 1] = obj
                        finally:
                            original_image.close()
                            if item.image is not original_image: item.image.close()
                page.compress_content_streams(level=9)
                ctx.progress(round(90 * (index + 1) / len(writer.pages)), f'Compressing page {index + 1}')
            writer.compress_identical_objects()
            ctx.save(folder, path.stem + '_compressed', '.pdf', lambda output: writer.write(str(output)))


def repair_pdf(path, folder, opt, ctx):
    with ExitStack() as stack:
        reader = PdfReader(stack.enter_context(path.open('rb')), strict=False)
        if reader.is_encrypted and not reader.decrypt(opt.password):
            raise ValueError('The supplied password is incorrect.')
        if not reader.pages:
            raise ValueError('No recoverable pages found.')
        with PdfWriter() as writer:
            writer.clone_document_from_reader(reader)
            def write(output):
                ctx.check()
                writer.write(str(output))
                reopened = PdfReader(str(output), strict=True)
                if len(reopened.pages) != len(reader.pages):
                    raise ValueError('Repaired page count did not match.')
                with pdfium.PdfDocument(str(output)) as document:
                    document.init_forms()
                    for index in range(len(document)):
                        ctx.check()
                        image, _ = render(document, index, 36)
                        image.close()
                        ctx.progress(round(90 * (index + 1) / len(document)), f'Checking repaired page {index + 1}')
            ctx.save(folder, path.stem + '_repaired', '.pdf', write)


def add_pdfa_metadata(raster, output):
    """Only fresh opaque RGB raster pages are accepted here, never source objects."""
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(raster))
        writer.pdf_header = '%PDF-1.4'
        writer.metadata = None
        for page in writer.pages:
            # ReportLab adds an initial empty text block and Helvetica even on raster-only pages.
            contents = page.get_contents()
            operations = []
            in_text = False
            for operands, operator in contents.operations:
                if operator == b'BT':
                    in_text = True
                elif operator == b'ET':
                    in_text = False
                elif not in_text:
                    operations.append((operands, operator))
            contents.operations = operations
            page.replace_contents(contents)
            page['/Resources'].pop('/Font', None)
        profile = DecodedStreamObject()
        profile.set_data((Path(__file__).parent / 'assets' / 'sRGB.icc').read_bytes())
        profile.update({NameObject('/N'): NumberObject(3)})
        intent = DictionaryObject({
            NameObject('/Type'): NameObject('/OutputIntent'),
            NameObject('/S'): NameObject('/GTS_PDFA1'),
            NameObject('/OutputConditionIdentifier'): TextStringObject('sRGB'),
            NameObject('/Info'): TextStringObject('sRGB IEC61966-2.1'),
            NameObject('/DestOutputProfile'): writer._add_object(profile),
        })
        writer.root_object[NameObject('/OutputIntents')] = ArrayObject([writer._add_object(intent)])
        metadata = DecodedStreamObject()
        metadata.set_data(('<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>'
            '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">'
            '<pdfaid:part>1</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance>'
            '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>').encode('utf-8'))
        metadata.update({NameObject('/Type'): NameObject('/Metadata'), NameObject('/Subtype'): NameObject('/XML')})
        writer.root_object[NameObject('/Metadata')] = writer._add_object(metadata)
        writer.generate_file_identifiers()
        writer.compress_identical_objects()
        writer.write(str(output))


def pdfa_pdf(path, folder, opt, ctx):
    if not 36 <= opt.dpi <= 300:
        raise ValueError('PDF/A raster DPI must be 36–300.')
    with ExitStack() as stack:
        read_pdf(stack, path, opt.password)
        document = stack.enter_context(pdfium.PdfDocument(str(path), password=opt.password))
        document.init_forms()
        def write(output):
            with TemporaryDirectory(prefix='local-pdf-pdfa-') as temp:
                raster = Path(temp) / 'raster.pdf'
                write_raster_document(document, raster, opt.dpi, {}, ctx, action='Converting PDF/A')
                ctx.check()
                add_pdfa_metadata(str(raster), output)
        ctx.save(folder, path.stem + '_pdfa1b', '.pdf', write)


def run_engine(command, ctx, timeout=180):
    """No shell; cancellable child; bounded diagnostics; no pipe-buffer deadlock."""
    with TemporaryFile() as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        started = time.monotonic()
        try:
            while process.poll() is None:
                ctx.check()
                if time.monotonic() - started > timeout:
                    raise ValueError('OCR engine timed out. Use a smaller page or simpler segmentation.')
                ctx.cancel.wait(.1)
            ctx.check()
            log.seek(0)
            diagnostic = log.read(8000).decode('utf-8', errors='replace')
            if process.returncode:
                raise ValueError('Tesseract failed. Check installed language data and pdf.ttf. ' + diagnostic[-1000:])
            return diagnostic
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def tesseract_command(opt, ctx):
    if not re.fullmatch(r'[A-Za-z0-9_]+(?:\+[A-Za-z0-9_]+)*', opt.ocr_language):
        raise ValueError('Use installed language codes, e.g. eng or eng+kor.')
    if opt.ocr_psm not in (3, 6, 11):
        raise ValueError('OCR segmentation must be automatic (3), block (6) or sparse (11).')
    executable = opt.tesseract_path or shutil.which('tesseract')
    if not executable and sys.platform == 'win32':
        roots = [Path(sys.executable).parent / 'engines' / 'tesseract',
                 Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Tesseract-OCR']
        executable = next((str(root / 'tesseract.exe') for root in roots if (root / 'tesseract.exe').is_file()), None)
    if not executable or not Path(executable).is_file():
        raise ValueError('Install local Tesseract 5, or choose its executable. No engine or data is downloaded by this app.')
    executable = str(Path(executable).resolve())
    version = run_engine([executable, '--version'], ctx, timeout=15)
    if not re.search(r'tesseract 5\.', version):
        raise ValueError('Tesseract 5 is required.')
    command = [executable]
    data = Path(opt.tessdata_path).expanduser().resolve() if opt.tessdata_path else Path(executable).parent / 'tessdata'
    if opt.tessdata_path or data.is_dir():
        if not data.is_dir() or not (data / 'pdf.ttf').is_file():
            raise ValueError('Choose a tessdata folder containing language .traineddata files and pdf.ttf.')
        command += ['--tessdata-dir', str(data)]
    listing = run_engine(command + ['--list-langs'], ctx, timeout=15)
    installed = set(listing.splitlines())
    missing = [language for language in opt.ocr_language.split('+') if language not in installed]
    if missing:
        raise ValueError('Missing local OCR language data: ' + ', '.join(missing))
    return command


def ocr_pdf(path, folder, opt, ctx):
    if not 72 <= opt.dpi <= 300:
        raise ValueError('OCR raster DPI must be 72–300.')
    command = tesseract_command(opt, ctx)
    with ExitStack() as stack:
        read_pdf(stack, path, opt.password)
        document = stack.enter_context(pdfium.PdfDocument(str(path), password=opt.password))
        document.init_forms()
        with TemporaryDirectory(prefix='local-pdf-ocr-') as temp, PdfWriter() as writer:
            root = Path(temp)
            total = 0
            for index in range(len(document)):
                ctx.check()
                image, (width, height) = render(document, index, opt.dpi)
                try:
                    total += image.width * image.height
                    if total > 120_000_000:
                        raise ValueError('OCR batch exceeds 120 megapixels. Lower DPI or split the document.')
                    source = root / 'page.png'
                    image.save(source, dpi=(opt.dpi, opt.dpi))
                finally:
                    image.close()
                run_engine(command + [str(source), str(root / 'recognized'), '-l', opt.ocr_language,
                                      '--oem', '1', '--psm', str(opt.ocr_psm), '--dpi', str(opt.dpi),
                                      '-c', 'tessedit_create_pdf=1'], ctx)
                reader = PdfReader(str(root / 'recognized.pdf'), strict=True)
                if len(reader.pages) != 1:
                    raise ValueError('OCR engine did not produce one readable page.')
                page = writer.add_page(reader.pages[0])
                page.scale_to(width, height)
                ctx.progress(round(90 * (index + 1) / len(document)), f'Recognizing page {index + 1}')
            ctx.save(folder, path.stem + '_ocr', '.pdf', lambda output: writer.write(str(output)))


def html_pdf(path, folder, opt, ctx):
    from PySide6.QtCore import QMarginsF, QSizeF, QUrl
    from PySide6.QtGui import QGuiApplication, QImage, QPageLayout, QPageSize, QPdfWriter, QTextDocument

    if QGuiApplication.instance() is None:
        raise ValueError('HTML printing requires the application GUI to be initialized.')
    if path.stat().st_size > 10_000_000:
        raise ValueError('HTML exceeds the 10 MB input limit.')
    class LocalDocument(QTextDocument):
        def __init__(self):
            super().__init__()
            self.blocked = []

        def loadResource(self, kind, url):
            resolved = self.baseUrl().resolved(url)
            source = Path(resolved.toLocalFile()).resolve() if resolved.isLocalFile() else None
            if (kind != QTextDocument.ResourceType.ImageResource or not source or
                    not source.is_relative_to(path.parent) or source.suffix.lower() not in ('.png', '.jpg', '.jpeg')):
                self.blocked.append('Only JPEG/PNG images inside the HTML folder are supported; network/outside resources are blocked.')
                return None
            try:
                with open_image(source) as image, image.convert('RGBA') as rgba:
                    return QImage(rgba.tobytes(), rgba.width, rgba.height, rgba.width * 4, QImage.Format.Format_RGBA8888).copy()
            except Exception:
                self.blocked.append('A local HTML image could not be loaded: ' + source.name)
                return None

    document = LocalDocument()
    document.setBaseUrl(QUrl.fromLocalFile(str(path.parent) + '/'))
    document.setHtml(path.read_text(encoding='utf-8-sig'))
    def write(output):
        ctx.check()
        writer = QPdfWriter(str(output))
        writer.setResolution(72)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageMargins(QMarginsF(15, 15, 15, 15), QPageLayout.Unit.Millimeter)
        document.setPageSize(QSizeF(writer.pageLayout().paintRectPoints().size()))
        if document.pageCount() > 1000:
            raise ValueError('HTML exceeds the 1000 page limit.')
        if document.blocked:
            raise ValueError(document.blocked[0])
        ctx.progress(30, 'Printing local HTML…')
        document.print_(writer)
        del writer
        if document.blocked:
            raise ValueError(document.blocked[0])
        if not output.is_file() or not PdfReader(str(output), strict=True).pages:
            raise ValueError('HTML printing produced no readable pages.')
        ctx.progress(90, 'Checking printed PDF…')
    ctx.save(folder, path.stem + '_html', '.pdf', write)


def process_m3(tool, files, folder, opt, ctx):
    processor = {'pdf_compress': compress_pdf, 'pdf_repair': repair_pdf, 'pdf_pdfa': pdfa_pdf,
                 'pdf_ocr': ocr_pdf, 'html_pdf': html_pdf}[tool]
    for index, path in enumerate(files):
        ctx.check()
        batch = Context(ctx.cancel, lambda n, message: ctx.progress(round((index + n / 100) * 100 / len(files)), message), ctx.result)
        try:
            processor(path, folder, opt, batch)
        except Cancelled:
            raise
        except Exception as error:
            message = str(error)
            if opt.password:
                message = message.replace(opt.password, '[password]')
            ctx.result.errors.append(f'{path.name}: {message}')
        ctx.progress(round(100 * (index + 1) / len(files)), path.name)
