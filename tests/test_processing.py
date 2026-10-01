from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

from local_pdf_editor.output import safe_stem, write_output
from local_pdf_editor.processing import parse_pages, run_job
from local_pdf_editor.tools import Options


def pdf(path, widths=(100, 200, 300)):
    with PdfWriter() as writer:
        for width in widths:
            writer.add_blank_page(width=width, height=100)
        writer.write(path)
    return path


def widths(path):
    with path.open('rb') as stream:
        return [int(p.mediabox.width) for p in PdfReader(stream).pages]


def run(tool, files, tmp_path, options=Options()):
    result = run_job(tool, files, tmp_path / '결과', options)
    assert not result.errors, result.errors
    assert not result.cancelled
    assert result.outputs
    return result.outputs


def test_pdf_merge_and_import_order(tmp_path):
    a = pdf(tmp_path / '문서.pdf')
    b = pdf(tmp_path / '추가.pdf', (400, 500))
    assert widths(run('pdf_merge', [b, a], tmp_path)[0]) == [400, 500, 100, 200, 300]
    imported = run('pdf_import', [a, b], tmp_path, Options(pages='2', insert_after=1))[0]
    assert widths(imported) == [100, 500, 200, 300]
    assert widths(a) == [100, 200, 300]


def test_pdf_split_reorder_delete_rotate(tmp_path):
    source = pdf(tmp_path / 'original.pdf')
    assert [widths(p) for p in run('pdf_split', [source], tmp_path, Options(pages='3,1'))] == [[300], [100]]
    assert widths(run('pdf_reorder', [source], tmp_path, Options(pages='3,1,2'))[0]) == [300, 100, 200]
    assert widths(run('pdf_delete', [source], tmp_path, Options(pages='2'))[0]) == [100, 300]
    rotated = run('pdf_rotate', [source], tmp_path, Options(pages='1,3', rotation=270))[0]
    reader = PdfReader(rotated)
    assert [p.rotation for p in reader.pages] == [270, 0, 270]
    assert [p.rotation for p in PdfReader(source).pages] == [0, 0, 0]


@pytest.mark.parametrize('tool,format', [('pdf_jpeg', 'JPEG'), ('pdf_png', 'PNG')])
def test_pdf_render_and_multiple_inputs(tmp_path, tool, format):
    a = pdf(tmp_path / 'a.pdf', (72, 144))
    b = pdf(tmp_path / 'b.pdf', (216,))
    outputs = run(tool, [a, b], tmp_path, Options(dpi=72))
    assert len(outputs) == 3
    for path, size in zip(outputs, [(72, 100), (144, 100), (216, 100)]):
        with Image.open(path) as image:
            assert image.format == format
            assert image.size == size
            image.load()


@pytest.mark.parametrize('tool', ['pdf_png', 'pdf_jpeg'])
def test_pdf_image_export_includes_filled_form_appearances(tmp_path, tool):
    from reportlab.pdfgen.canvas import Canvas
    from PIL import ImageChops, ImageStat
    import pypdfium2 as pdfium

    source = tmp_path / 'form.pdf'
    canvas = Canvas(str(source), pagesize=(300, 180))
    canvas.acroForm.textfield(name='name', value='VISIBLE FIELD', x=20, y=100, width=160, height=30)
    canvas.acroForm.checkbox(name='checked', checked=True, x=20, y=50)
    canvas.showPage(); canvas.save()
    output = run(tool, [source], tmp_path, Options(dpi=72, quality=100))[0]
    with pdfium.PdfDocument(str(source)) as document:
        document.init_forms()
        page = document[0]
        try:
            bitmap = page.render(scale=1, draw_annots=True)
            try:
                expected = bitmap.to_pil().convert('RGB')
            finally:
                bitmap.close()
        finally:
            page.close()
    try:
        with Image.open(output).convert('RGB') as actual, ImageChops.difference(actual, expected) as difference:
            assert sum(ImageStat.Stat(difference).mean) / 3 < 1
    finally:
        expected.close()


def test_images_pdf_order_and_content(tmp_path):
    paths = []
    for i, (size, color) in enumerate([((32, 24), 'red'), ((48, 36), 'blue')]):
        path = tmp_path / f'{i}.png'
        Image.new('RGB', size, color).save(path)
        paths.append(path)
    output = run('image_pdf', paths, tmp_path)[0]
    assert widths(output) == [32, 48]
    rendered = run('pdf_png', [output], tmp_path, Options(dpi=72))
    with Image.open(rendered[0]) as first, Image.open(rendered[1]) as second:
        assert first.getpixel((10, 10))[0] > 200
        assert second.getpixel((10, 10))[2] > 200


@pytest.mark.parametrize('percent,size', [(25, (20, 10)), (50, (40, 20)), (75, (60, 30)), (100, (80, 40)), (37.5, (30, 15))])
def test_percentage_resize(tmp_path, percent, size):
    path = tmp_path / '사진.png'
    Image.new('RGBA', (80, 40), (255, 0, 0, 100)).save(path)
    output = run('image_resize', [path], tmp_path, Options(percent=percent))[0]
    with Image.open(output) as image:
        assert image.size == size
        assert image.format == 'PNG'
        assert image.getpixel((0, 0))[3] == 100


@pytest.mark.parametrize('options,size', [
    (Options(width=30, height=30), (30, 15)),
    (Options(width=30), (30, 15)),
    (Options(height=30), (60, 30)),
    (Options(width=30, height=30, keep_aspect=False), (30, 30)),
])
def test_explicit_resize(tmp_path, options, size):
    path = tmp_path / 'x.png'
    Image.new('RGB', (80, 40)).save(path)
    with Image.open(run('image_resize', [path], tmp_path, options)[0]) as image:
        assert image.size == size


def test_orientation_conversion_batch_and_jpeg_background(tmp_path):
    jpeg = tmp_path / 'rotated.jpg'
    exif = Image.Exif()
    exif[274] = 6
    Image.new('RGB', (30, 20), 'green').save(jpeg, exif=exif)
    outputs = run('jpeg_png', [jpeg, jpeg], tmp_path)
    assert len(set(outputs)) == 2
    for path in outputs:
        with Image.open(path) as image:
            assert image.size == (20, 30)
            assert image.getexif().get(274, 1) == 1
    png = tmp_path / 'transparent.png'
    Image.new('RGBA', (20, 20), (0, 0, 0, 0)).save(png)
    with Image.open(run('png_jpeg', [png], tmp_path)[0]) as image:
        assert image.format == 'JPEG'
        assert min(image.getpixel((0, 0))) > 250


@pytest.mark.parametrize('tool,format', [('heic_jpeg', 'JPEG'), ('heic_png', 'PNG')])
def test_real_heic_decode(tmp_path, tool, format):
    source = Path(__file__).parent / 'fixtures/sample.heic'
    for path in run(tool, [source, source], tmp_path):
        with Image.open(path) as image:
            assert image.format == format
            assert image.size == (29, 100)
            image.load()


@pytest.mark.parametrize('tool,options', [
    ('pdf_delete', Options(pages='1-3')), ('pdf_delete', Options()),
    ('pdf_reorder', Options(pages='1,2')), ('pdf_rotate', Options(rotation=45)),
    ('pdf_split', Options(pages='4')), ('pdf_png', Options(dpi=1000)),
])
def test_invalid_pdf_options(tmp_path, tool, options):
    source = pdf(tmp_path / 'x.pdf')
    result = run_job(tool, [source], tmp_path / 'out', options)
    assert result.errors and not result.outputs


def test_corrupt_input_encryption_and_partial_batch(tmp_path):
    bad = tmp_path / 'bad.pdf'
    bad.write_bytes(b'not a pdf')
    good = pdf(tmp_path / 'good.pdf', (100,))
    result = run_job('pdf_split', [bad, good], tmp_path / 'out')
    assert len(result.errors) == 1 and len(result.outputs) == 1
    encrypted = tmp_path / 'encrypted.pdf'
    with PdfWriter() as writer:
        writer.add_blank_page(100, 100)
        writer.encrypt('secret')
        writer.write(encrypted)
    result = run_job('pdf_png', [encrypted], tmp_path / 'out')
    assert 'Encrypted' in result.errors[0] and not result.outputs
    bad_image = tmp_path / 'bad.png'
    bad_image.write_bytes(b'bad')
    assert run_job('png_jpeg', [bad_image], tmp_path / 'out').errors


def test_cancellation_preserves_completed_outputs(tmp_path):
    source = pdf(tmp_path / 'x.pdf')
    event = Event()
    history = []

    def progress(value, message):
        history.append(value)
        if value > 0:
            event.set()

    result = run_job('pdf_split', [source], tmp_path / 'out', cancel=event, progress=progress)
    assert result.cancelled and len(result.outputs) == 1 and not result.errors
    assert widths(result.outputs[0]) == [100]
    assert history == sorted(history)
    assert not list((tmp_path / 'out').glob('.local-pdf-*'))
    event.set()
    assert not run_job('pdf_split', [source], tmp_path / 'out', cancel=event).outputs


def test_output_collision_cleanup_and_unicode(tmp_path):
    existing = tmp_path / '결과.png'
    existing.write_bytes(b'original')

    def save(p):
        p.write_bytes(b'new')

    with ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(lambda _: write_output(tmp_path, '결과', '.png', save), range(4)))
    assert len(set(paths)) == 4
    assert existing.read_bytes() == b'original'
    assert all(p.read_bytes() == b'new' for p in paths)

    def fail(p):
        p.write_bytes(b'partial')
        raise OSError('disk error')

    with pytest.raises(OSError):
        write_output(tmp_path, 'failure', '.png', fail)
    assert not (tmp_path / 'failure.png').exists()
    assert not list(tmp_path.glob('.local-pdf-*'))
    assert safe_stem('CON') == '_CON'
    assert safe_stem('a:b?. ') == 'a_b_'


@pytest.mark.parametrize('text', ['0', '4', '2-1', '1,1', 'a', '1-2-3', '1,'])
def test_bad_page_selection(text):
    with pytest.raises(ValueError):
        parse_pages(text, 3)


@pytest.mark.parametrize('options', [Options(percent=0), Options(percent=float('nan')), Options(width=-1), Options(width=50, keep_aspect=False), Options(width=100000, height=100000)])
def test_invalid_resize(tmp_path, options):
    source = tmp_path / 'x.png'
    Image.new('RGB', (20, 20)).save(source)
    result = run_job('image_resize', [source], tmp_path / 'out', options)
    assert result.errors and not result.outputs
