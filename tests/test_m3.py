import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from threading import Event, Timer

import pypdfium2 as pdfium
import pytest
from PIL import Image, ImageChops, ImageStat
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject, TextStringObject
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from local_pdf_editor.m2 import render
from local_pdf_editor.m3 import run_engine
from local_pdf_editor.processing import Cancelled, Context, Result, run_job
from local_pdf_editor.tools import Options
from test_gui import app
from test_m2 import document, form


def job(tool, files, root, options=Options()):
    result = run_job(tool, files, root / 'out', options)
    assert not result.errors and not result.cancelled, result
    assert len(result.outputs) == len(files)
    return result.outputs[0]


def pixels(path, page=0):
    with pdfium.PdfDocument(str(path)) as doc:
        doc.init_forms()
        return render(doc, page, 72)[0]


def test_lossless_compression_retains_text_forms_and_pixels(tmp_path):
    source = form(tmp_path / 'source.pdf')
    original = source.read_bytes()
    output = job('pdf_compress', [source], tmp_path)
    a, b = PdfReader(source), PdfReader(output)
    assert a.pages[0].extract_text() == b.pages[0].extract_text()
    assert a.get_fields()['name']['/V'] == b.get_fields()['name']['/V']
    with pixels(source) as left, pixels(output) as right:
        assert ImageChops.difference(left, right).getbbox() is None
    assert source.read_bytes() == original


def test_compression_reduces_uncompressed_streams(tmp_path):
    source = tmp_path / 'large.pdf'
    canvas = Canvas(str(source), pageCompression=0)
    for n in range(1000): canvas.drawString(10, n % 800, 'REPEATED STREAM TEXT')
    canvas.showPage(); canvas.save()
    output = job('pdf_compress', [source], tmp_path)
    assert output.stat().st_size < source.stat().st_size / 2
    assert PdfReader(output).pages[0].extract_text().count('REPEATED STREAM TEXT') == 1000


def test_lossy_compression_downsamples_photo_and_keeps_text(tmp_path):
    source = tmp_path / 'photo.pdf'
    with Image.effect_noise((1200, 800), 60).convert('RGB') as image:
        canvas = Canvas(str(source), pagesize=(400, 300))
        canvas.drawImage(ImageReader(image), 0, 0, width=400, height=260)
        canvas.drawString(20, 280, 'TEXT RETAINED'); canvas.showPage(); canvas.save()
    output = job('pdf_compress', [source], tmp_path, Options(compress_images=True, quality=60, image_max_dimension=400))
    page = PdfReader(output).pages[0]
    assert 'TEXT RETAINED' in page.extract_text()
    assert page.images[0].image.width <= 400
    assert output.stat().st_size < source.stat().st_size / 3


def test_lossy_compression_preserves_transparency(tmp_path):
    source = tmp_path / 'alpha.pdf'
    with Image.new('RGBA', (80, 60), (240, 0, 0, 100)) as image:
        canvas = Canvas(str(source), pagesize=(160, 120))
        canvas.drawImage(ImageReader(image), 0, 0, width=160, height=120, mask='auto')
        canvas.showPage(); canvas.save()
    output = job('pdf_compress', [source], tmp_path, Options(compress_images=True))
    with pixels(source) as left, pixels(output) as right:
        assert ImageChops.difference(left, right).getbbox() is None


def test_lossy_compression_preserves_cmyk_color_space(tmp_path):
    source = tmp_path / 'cmyk.pdf'
    with Image.effect_noise((800, 600), 60).convert('CMYK') as image:
        canvas = Canvas(str(source), pagesize=(400, 300))
        canvas.drawImage(ImageReader(image), 0, 0, width=400, height=300)
        canvas.showPage(); canvas.save()
    output = job('pdf_compress', [source], tmp_path, Options(compress_images=True, quality=90, image_max_dimension=0))
    assert PdfReader(output).pages[0].images[0].image.mode == 'CMYK'
    with pixels(source) as left, pixels(output) as right, ImageChops.difference(left, right) as difference:
        assert sum(ImageStat.Stat(difference).mean) / 3 < 3
    assert output.stat().st_size < source.stat().st_size


@pytest.mark.parametrize('protected', ['hidden-layer', 'icc-profile'])
def test_image_compression_preserves_layers_and_color_profiles(tmp_path, protected):
    base = tmp_path / 'base.pdf'
    with Image.effect_noise((800, 600), 60).convert('RGB') as image:
        canvas = Canvas(str(base), pagesize=(400, 300))
        canvas.drawImage(ImageReader(image), 0, 0, width=400, height=300)
        canvas.showPage(); canvas.save()
    source = tmp_path / 'protected-image.pdf'
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(base))
        obj = writer.pages[0].images[0].indirect_reference.get_object()
        if protected == 'hidden-layer':
            group = writer._add_object(DictionaryObject({NameObject('/Type'): NameObject('/OCG'),
                                                         NameObject('/Name'): TextStringObject('Hidden photo')}))
            obj[NameObject('/OC')] = group
            writer.root_object[NameObject('/OCProperties')] = DictionaryObject({
                NameObject('/OCGs'): ArrayObject([group]), NameObject('/D'): DictionaryObject({
                    NameObject('/BaseState'): NameObject('/OFF'), NameObject('/OFF'): ArrayObject([group])})})
        else:
            from local_pdf_editor import m3
            profile = DecodedStreamObject()
            profile.set_data((Path(m3.__file__).parent / 'assets' / 'sRGB.icc').read_bytes())
            profile[NameObject('/N')] = NumberObject(3)
            obj[NameObject('/ColorSpace')] = ArrayObject([NameObject('/ICCBased'), writer._add_object(profile)])
        writer.write(source)
    output = job('pdf_compress', [source], tmp_path, Options(compress_images=True, quality=90, image_max_dimension=0))
    old = PdfReader(source).pages[0].images[0].indirect_reference.get_object()
    new = PdfReader(output).pages[0].images[0].indirect_reference.get_object()
    if protected == 'hidden-layer':
        assert new['/OC']['/Name'] == 'Hidden photo'
        with pixels(source) as left, pixels(output) as right:
            assert ImageChops.difference(left, right).getbbox() is None
    else:
        assert new['/ColorSpace'][0] == '/ICCBased'
        assert new['/ColorSpace'][1].get_data() == old['/ColorSpace'][1].get_data()
        assert new.get_data() == old.get_data()
        with pixels(source) as left, pixels(output) as right:
            assert ImageChops.difference(left, right).getbbox() is None


def test_compression_rejects_oversized_image_before_decode(tmp_path):
    source = tmp_path / 'large.pdf'
    with PdfWriter() as writer:
        page = writer.add_blank_page(100, 100)
        image = DecodedStreamObject();image.set_data(b'\0\0\0')
        image.update({NameObject('/Subtype'): NameObject('/Image'), NameObject('/Width'): NumberObject(8000),
                      NameObject('/Height'): NumberObject(8000), NameObject('/BitsPerComponent'): NumberObject(8),
                      NameObject('/ColorSpace'): NameObject('/DeviceRGB')})
        objects = DictionaryObject({NameObject('/Im1'): writer._add_object(image)})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/XObject'): writer._add_object(objects)})
        writer.write(source)
    result = run_job('pdf_compress', [source], tmp_path / 'out', Options(compress_images=True))
    assert not result.outputs and '40 megapixel' in result.errors[0]


def broken_xref(path):
    source = document(path)
    import re
    data = source.read_bytes()
    data = re.sub(rb'startxref\s+\d+', b'startxref\n1', data)
    source.write_bytes(data)
    return source


def test_repair_broken_xref_reopens_and_keeps_pages(tmp_path):
    source = broken_xref(tmp_path / 'broken.pdf')
    original = source.read_bytes()
    with pytest.raises(Exception): PdfReader(source, strict=True)
    output = job('pdf_repair', [source], tmp_path)
    reader = PdfReader(output, strict=True)
    assert len(reader.pages) == 2 and 'SECRET' in reader.pages[0].extract_text()
    with pixels(output) as image: assert image.width == 240
    assert source.read_bytes() == original


@pytest.mark.parametrize('payload', [b'not a pdf', b'%PDF-1.4\n%%EOF', b''])
def test_unrecoverable_pdf_leaves_no_output(tmp_path, payload):
    source = tmp_path / 'broken.pdf'; source.write_bytes(payload)
    result = run_job('pdf_repair', [source], tmp_path / 'out')
    assert result.errors and not result.outputs
    assert not list((tmp_path / 'out').glob('*'))


@pytest.mark.parametrize('variant', ['text', 'form', 'rotated', 'encrypted'])
def test_pdfa_fresh_raster_output_and_independent_preflight(tmp_path, variant):
    source = form(tmp_path / 'source.pdf') if variant == 'form' else document(tmp_path / 'source.pdf')
    options = Options(dpi=72)
    if variant == 'rotated':
        with PdfWriter() as writer:
            writer.clone_document_from_reader(PdfReader(source))
            writer.pages[0].rotate(90)
            writer.pages[0].cropbox.lower_left = (10, 20)
            writer.add_metadata({'/Title': 'SOURCE SECRET'})
            writer.add_attachment('secret.txt', b'SOURCE SECRET')
            with source.open('wb') as stream: writer.write(stream)
    if variant == 'encrypted':
        source = job('pdf_protect', [source], tmp_path, Options(new_password='supplied'))
        options = Options(dpi=72, password='supplied')
    output = job('pdf_pdfa', [source], tmp_path, options)
    reader = PdfReader(output, strict=True)
    assert not reader.is_encrypted and not reader.get_fields() and not reader.attachments
    assert reader.pdf_header == '%PDF-1.4'
    assert reader.xmp_metadata.pdfaid_part == '1' and reader.xmp_metadata.pdfaid_conformance == 'B'
    assert reader.root_object['/OutputIntents'][0]['/DestOutputProfile']['/N'] == 3
    assert 'SOURCE SECRET' not in str(reader.metadata)
    for page in reader.pages:
        assert not page.extract_text().strip() and '/Font' not in page['/Resources']
        assert page.images
    if variant != 'encrypted':
        with pixels(source) as left, pixels(output) as right:
            assert left.size == right.size and ImageChops.difference(left, right).getbbox() is None
    # Configure the independent validator explicitly for the conformance run.
    if os.environ.get('PDF_PREFLIGHT_JAR'):
        result = subprocess.run(['java', '-Duser.home=' + str(tmp_path), '-jar', os.environ['PDF_PREFLIGHT_JAR'], str(output)], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0 and 'is a valid PDF/A-1b file' in result.stdout, result.stdout + result.stderr


def test_icc_profile_provenance():
    from local_pdf_editor import m3
    profile = Path(m3.__file__).parent / 'assets' / 'sRGB.icc'
    assert hashlib.sha256(profile.read_bytes()).hexdigest() == '2a92d4bae450b76d8b0aa42193df974d75f62738ecebf74f01c5e75b12a95796'


def scanned_pdf(path):
    from local_pdf_editor.m2 import font_for
    from reportlab.pdfbase import pdfmetrics
    font = font_for('LOCAL OCR TEST', '')
    vector = path.with_name('vector.pdf')
    canvas = Canvas(str(vector), pagesize=(400, 240))
    canvas.setFont(font, 26); canvas.drawString(30, 170, 'LOCAL OCR TEST')
    canvas.showPage(); canvas.save()
    result = run_job('pdf_pdfa', [vector], path.parent, Options(dpi=144))
    assert not result.errors
    shutil.copyfile(result.outputs[0], path)
    assert not PdfReader(path).pages[0].extract_text().strip()
    return path


def test_real_tesseract_creates_searchable_pdf_and_preserves_visible_pixels(tmp_path):
    source = scanned_pdf(tmp_path / 'scan.pdf')
    output = job('pdf_ocr', [source], tmp_path, Options(dpi=144, ocr_psm=6))
    page = PdfReader(output).pages[0]
    assert 'LOCAL OCR TEST' in page.extract_text()
    assert float(page.mediabox.width) == 400 and float(page.mediabox.height) == 240
    with pixels(source) as left, pixels(output) as right:
        diff = ImageChops.difference(left, right)
        assert sum(ImageStat.Stat(diff).mean) / 3 < 1


@pytest.mark.parametrize('options,fragment', [
    (Options(tesseract_path='/missing/engine'), 'Install local'),
    (Options(ocr_language='../../eng'), 'language codes'),
    (Options(ocr_language='missing_language'), 'Missing local'),
    (Options(tessdata_path='/missing/data'), 'tessdata folder'),
    (Options(ocr_psm=2), 'segmentation'),
    (Options(dpi=36), 'OCR raster DPI'),
])
def test_ocr_prerequisite_errors_are_actionable(tmp_path, options, fragment):
    source = document(tmp_path / 'source.pdf')
    result = run_job('pdf_ocr', [source], tmp_path / 'out', options)
    assert not result.outputs and fragment in result.errors[0]


@pytest.mark.parametrize('version,accepted', [
    ('tesseract 5.5.0', True), ('tesseract v5.5.0.20241111', True),
    ('tesseract 4.1.1', False), ('unrecognized version', False),
])
def test_tesseract_version_formats(tmp_path, monkeypatch, version, accepted):
    from local_pdf_editor import m3
    engine = tmp_path / 'tesseract.exe'
    engine.touch()
    monkeypatch.setattr(m3, 'run_engine', lambda command, *_args, **_kwargs:
                        version if '--version' in command else 'List of available languages:\neng\n')
    options = Options(tesseract_path=str(engine))
    context = Context(Event(), lambda *_: None, Result())
    if accepted:
        assert m3.tesseract_command(options, context) == [str(engine.resolve())]
    else:
        with pytest.raises(ValueError, match='Tesseract 5 is required'):
            m3.tesseract_command(options, context)


def test_ocr_child_cancellation_and_timeout_cleanup():
    ctx = Context(Event(), lambda *_: None, Result())
    timer = Timer(.2, ctx.cancel.set); timer.start()
    try:
        with pytest.raises(Cancelled): run_engine([sys.executable, '-c', 'import time;time.sleep(30)'], ctx)
    finally: timer.cancel()
    ctx.cancel.clear()
    with pytest.raises(ValueError, match='timed out'):
        run_engine([sys.executable, '-c', 'import time;time.sleep(30)'], ctx, timeout=.1)


def test_local_html_text_table_image_and_multipage(tmp_path, app):
    with Image.new('RGB', (30, 20), 'red') as image: image.save(tmp_path / 'image.png')
    source = tmp_path / 'local.html'
    source.write_text('<h1>LOCAL HTML</h1><table border="1"><tr><td>Cell value</td></tr></table><img src="image.png">' + '<p>Many local paragraphs</p>' * 150)
    output = job('html_pdf', [source], tmp_path)
    reader = PdfReader(output)
    assert len(reader.pages) > 1
    text = ' '.join(reader.pages[0].extract_text().split())
    assert 'LOCAL HTML' in text and 'Cell value' in text, {
        'fonts': str(reader.pages[0]['/Resources'].get('/Font'))[:1200],
        'content': reader.pages[0].get_contents().get_data()[:1800],
    }
    assert reader.pages[0].images
    with pixels(output) as image:
        assert any(r > 200 and g < 50 and b < 50 for r, g, b in image.get_flattened_data())


@pytest.mark.parametrize('resource', ['https://example.invalid/image.png', '../outside.png', 'file:///etc/passwd'])
def test_html_resource_boundary_fails_without_output(tmp_path, app, resource):
    source = tmp_path / 'input.html';source.write_text(f'<img src="{resource}">')
    result = run_job('html_pdf', [source], tmp_path / 'out')
    assert result.errors and not result.outputs
    assert not list((tmp_path / 'out').glob('*'))


def test_html_script_is_not_executed(tmp_path, app):
    source = tmp_path / 'input.html'
    source.write_text('<h1>VISIBLE</h1><script>document.write("EXECUTED")</script>')
    output = job('html_pdf', [source], tmp_path)
    text = PdfReader(output).pages[0].extract_text()
    assert 'VISIBLE' in text and 'EXECUTED' not in text, {
        'fonts': str(PdfReader(output).pages[0]['/Resources'].get('/Font'))[:1200],
        'content': PdfReader(output).pages[0].get_contents().get_data()[:1800],
    }


@pytest.mark.parametrize('tool', ['pdf_compress', 'pdf_repair', 'pdf_pdfa', 'pdf_ocr'])
def test_m3_password_batch_and_collision(tmp_path, tool):
    source = document(tmp_path / 'source.pdf')
    protected = job('pdf_protect', [source], tmp_path, Options(new_password='correct'))
    original = protected.read_bytes()
    wrong = run_job(tool, [protected], tmp_path / 'bad', Options(password='wrong'))
    assert wrong.errors and not wrong.outputs and 'wrong' not in '\n'.join(wrong.errors)
    good = job(tool, [protected], tmp_path, Options(password='correct', dpi=72))
    duplicate = job(tool, [protected], tmp_path, Options(password='correct', dpi=72))
    assert good != duplicate and not PdfReader(good).is_encrypted
    assert protected.read_bytes() == original
    bad = tmp_path / 'bad.pdf';bad.write_bytes(b'not a pdf')
    partial = run_job(tool, [bad, protected], tmp_path / 'partial', Options(password='correct', dpi=72))
    assert len(partial.errors) == 1 and len(partial.outputs) == 1


@pytest.mark.parametrize('tool', ['pdf_compress', 'pdf_repair', 'pdf_pdfa', 'pdf_ocr'])
def test_m3_cancel_before_output_is_committed(tmp_path, tool):
    source = document(tmp_path / 'source.pdf')
    cancel = Event()
    result = run_job(tool, [source], tmp_path / 'out', Options(dpi=72), cancel,
                     lambda n, message: cancel.set() if 0 < n < 100 else None)
    assert result.cancelled and not result.outputs and not result.errors
    assert not list((tmp_path / 'out').glob('*'))
