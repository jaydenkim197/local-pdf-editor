import json
from io import BytesIO
from pathlib import Path
from threading import Event

import pytest
import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject, RectangleObject, TextStringObject
from reportlab.pdfgen.canvas import Canvas

from local_pdf_editor.m2 import inspect_forms, parse_redactions
from local_pdf_editor.processing import run_job
from local_pdf_editor.tools import Options


def document(path, text='SECRET-ONLY-IN-SOURCE', pages=2):
    canvas = Canvas(str(path), pagesize=(240, 180))
    canvas.setTitle('PRIVATE-METADATA')
    for index in range(pages):
        canvas.setFillColorRGB(0, 0, 1)
        canvas.rect(20, 50, 80, 25, fill=1, stroke=0)
        canvas.setFillColorRGB(0, 0, 0)
        canvas.drawString(20, 140, text)
        canvas.drawString(20, 20, f'VISIBLE PAGE {index + 1}')
        canvas.showPage()
    canvas.save()
    return path


def form(path):
    canvas = Canvas(str(path), pagesize=(300, 300))
    canvas.acroForm.textfield(name='name', x=20, y=240, width=150, height=20)
    canvas.acroForm.checkbox(name='agree', x=20, y=190)
    canvas.acroForm.choice(name='color', x=20, y=140, width=100, height=20, options=['Red', 'Blue'], value='Red')
    canvas.acroForm.radio(name='choice', value='A', x=20, y=80, selected=True)
    canvas.acroForm.radio(name='choice', value='B', x=80, y=80)
    canvas.showPage(); canvas.save()
    return path


def result(tool, files, root, opt=Options()):
    value = run_job(tool, files, root / 'out', opt)
    assert not value.errors, value.errors
    assert not value.cancelled
    assert value.outputs
    return value.outputs


def rendered(path, password='', index=0):
    with pdfium.PdfDocument(str(path), password=password) as doc:
        doc.init_forms()
        page = doc[index]
        try:
            bitmap = page.render(scale=1, draw_annots=True)
            try:
                return bitmap.to_pil().convert('RGB')
            finally:
                bitmap.close()
        finally:
            page.close()


def test_crop_selected_rotated_and_offset_pages(tmp_path):
    source = document(tmp_path / 'source.pdf')
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(source))
        writer.pages[0].rotate(90)
        writer.pages[1].cropbox = RectangleObject((10, 10, 230, 170))
        writer.write(tmp_path / 'rotated.pdf')
    output = result('pdf_crop', [tmp_path / 'rotated.pdf'], tmp_path, Options(pages='1', margins=(10, 20, 30, 40)))[0]
    reader = PdfReader(output)
    assert reader.pages[0].rotation == 90
    with rendered(output) as image:
        assert image.size == (140, 180)
    assert tuple(reader.pages[1].cropbox) == (10, 10, 230, 170)
    assert 'SECRET-ONLY-IN-SOURCE' in reader.pages[0].extract_text()  # crop is not redaction


def test_watermark_and_number_visibility_and_selection(tmp_path):
    source = document(tmp_path / 'source.pdf')
    watermark = result('pdf_watermark', [source], tmp_path, Options(pages='2', text='REVIEW', font_size=28))[0]
    reader = PdfReader(watermark)
    assert 'REVIEW' not in reader.pages[0].extract_text()
    assert 'REVIEW' in reader.pages[1].extract_text()
    with rendered(source, index=1) as a, rendered(watermark, index=1) as b:
        assert a.tobytes() != b.tobytes()
    numbered = result('pdf_numbers', [source], tmp_path, Options(start_number=7))[0]
    assert [p.extract_text().splitlines()[-1] for p in PdfReader(numbered).pages] == ['7', '8']


def test_signature_image_really_renders(tmp_path):
    source = document(tmp_path / 'source.pdf')
    signature = tmp_path / 'signature.png'
    Image.new('RGBA', (80, 20), (250, 0, 0, 255)).save(signature)
    output = result('pdf_signature', [source], tmp_path, Options(signature_path=str(signature), rect=(120, 70, 80, 20)))[0]
    with rendered(output) as image:
        r, g, b = image.getpixel((150, 80))
        assert r > 200 and g < 30 and b < 30
    assert 'SECRET-ONLY-IN-SOURCE' in PdfReader(output).pages[0].extract_text()


def test_aes256_protection_correct_password_removal_and_no_password_leak(tmp_path):
    source = document(tmp_path / 'source.pdf')
    password = '여권-Password-123'
    protected = result('pdf_protect', [source], tmp_path, Options(new_password=password))[0]
    reader = PdfReader(protected)
    assert reader.is_encrypted
    assert reader.trailer['/Encrypt']['/V'] == 5
    assert reader.trailer['/Encrypt']['/Length'] == 256
    assert not reader.decrypt('wrong')
    assert reader.decrypt(password)
    assert len(reader.pages) == 2
    assert password.encode() not in protected.read_bytes()
    incorrect = run_job('pdf_unlock', [protected], tmp_path / 'bad', Options(password='wrong'))
    assert incorrect.errors and not incorrect.outputs
    assert 'wrong' not in '\n'.join(incorrect.errors)
    unlocked = result('pdf_unlock', [protected], tmp_path, Options(password=password))[0]
    reopened = PdfReader(unlocked)
    assert not reopened.is_encrypted
    assert 'SECRET-ONLY-IN-SOURCE' in reopened.pages[0].extract_text()
    assert password not in repr(Options(password=password, new_password=password))
    with rendered(protected, password) as a, rendered(unlocked) as b:
        assert a.tobytes() == b.tobytes()


def test_secure_redaction_discards_text_metadata_attachments_forms_and_hidden_content(tmp_path):
    source = document(tmp_path / 'source.pdf')
    enriched = tmp_path / 'enriched.pdf'
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(source))
        writer.add_attachment('secret.txt', b'ATTACHMENT-SECRET')
        writer.add_metadata({'/Subject': 'PRIVATE-SUBJECT'})
        writer.write(enriched)
    output = result('pdf_redact', [enriched], tmp_path, Options(dpi=72, redactions=((1, 10, 20, 220, 35),)))[0]
    reader = PdfReader(output)
    assert len(reader.pages) == 2
    assert not reader.get_fields()
    assert not reader.attachments
    assert not reader.root_object.get('/Names')
    assert not reader.root_object.get('/OCProperties')
    assert not reader.root_object.get('/Metadata')
    assert all(not p.extract_text().strip() and not p.get('/Annots') for p in reader.pages)
    for marker in [b'SECRET-ONLY-IN-SOURCE', b'PRIVATE-METADATA', b'PRIVATE-SUBJECT', b'ATTACHMENT-SECRET']:
        assert marker not in output.read_bytes()
    # Inspect actual embedded pixels, not only the final viewer image.
    embedded = reader.pages[0].images[0].image.convert('RGB')
    assert embedded.getpixel((25, 40)) == (0, 0, 0)
    assert embedded.getpixel((30, 110))[2] > 200  # visible non-redacted blue box preserved
    with rendered(output) as image:
        assert image.getpixel((25, 40)) == (0, 0, 0)
    form_source = form(tmp_path / 'form.pdf')
    filled = result('pdf_forms', [form_source], tmp_path, Options(form_values=(('name', 'TOP-SECRET'),)))[0]
    redacted_form = result('pdf_redact', [filled], tmp_path, Options(dpi=72, redactions=((1, 15, 30, 180, 40),)))[0]
    assert not PdfReader(redacted_form).get_fields()
    assert b'TOP-SECRET' not in redacted_form.read_bytes()


def test_redaction_rotated_cropped_and_fractional_rectangles(tmp_path):
    source = document(tmp_path / 'source.pdf', pages=1)
    rotated = tmp_path / 'rotated.pdf'
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(source))
        writer.pages[0].cropbox = RectangleObject((10, 10, 230, 170))
        writer.pages[0].rotate(90)
        writer.write(rotated)
    output = result('pdf_redact', [rotated], tmp_path, Options(dpi=72, redactions=((1, 5.2, 7.3, 20.2, 30.2),)))[0]
    with rendered(output) as image:
        assert image.size == (160, 220)
        assert image.getpixel((5, 7)) == (0, 0, 0)
        assert image.getpixel((25, 37)) == (0, 0, 0)


def test_compare_identical_changed_size_and_missing_pages(tmp_path):
    a = document(tmp_path / 'a.pdf')
    b = document(tmp_path / 'b.pdf', text='DIFFERENT')
    identical = result('pdf_compare', [a, a], tmp_path, Options(dpi=72))
    assert len(identical) == 1
    assert json.loads(identical[0].read_text())['identical_visuals']
    different = result('pdf_compare', [a, b], tmp_path, Options(dpi=72))
    report = json.loads(different[-1].read_text())
    assert not report['identical_visuals']
    assert report['pages'][0]['changed_pixels'] > 0
    assert all((different[-1].parent / p['diff_file']).exists() for p in report['pages'])
    short = document(tmp_path / 'short.pdf', pages=1)
    report = json.loads(result('pdf_compare', [a, short], tmp_path, Options(dpi=72))[-1].read_text())
    assert report['page_counts'] == [2, 1]
    assert report['pages'][1]['missing_page']
    resized = tmp_path / 'resized.pdf'
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(a))
        writer.pages[0].mediabox = RectangleObject((0, 0, 280, 180))
        writer.write(resized)
    report = json.loads(result('pdf_compare', [a, resized], tmp_path, Options(dpi=72))[-1].read_text())
    assert report['pages'][0]['size_changed'] and not report['identical_visuals']


def test_form_inspect_fill_text_checkbox_choice_radio_and_flatten(tmp_path):
    source = form(tmp_path / 'form.pdf')
    schema = {f['name']: f for f in inspect_forms(source)}
    assert set(schema) == {'name', 'agree', 'color', 'choice'}
    values = (('name', 'Alice'), ('agree', '/Yes'), ('color', 'Blue'), ('choice', '/B'))
    filled = result('pdf_forms', [source], tmp_path, Options(form_values=values))[0]
    assert {k: str(f['/V']) for k, f in PdfReader(filled).get_fields().items()} == dict(values)
    with rendered(source) as a, rendered(filled) as b:
        assert a.tobytes() != b.tobytes()
    flattened = result('pdf_forms', [source], tmp_path, Options(form_values=values, flatten_forms=True, dpi=72))[0]
    assert not PdfReader(flattened).get_fields()
    assert all(not p.get('/Annots') for p in PdfReader(flattened).pages)
    with rendered(filled) as a, rendered(flattened) as b:
        assert a.tobytes() == b.tobytes()
    rotated = tmp_path / 'rotated-form.pdf'
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(filled))
        writer.pages[0].rotate(90)
        writer.write(rotated)
    cropped = result('pdf_crop', [rotated], tmp_path, Options(margins=(10, 10, 10, 10)))[0]
    with rendered(rotated) as a, rendered(cropped) as b:
        assert a.crop((10, 10, 290, 290)).tobytes() == b.tobytes()
    signed_image = tmp_path / 'red-signature.png'
    Image.new('RGB', (20, 10), 'red').save(signed_image)
    signed = result('pdf_signature', [rotated], tmp_path, Options(signature_path=str(signed_image), rect=(250, 10, 20, 10)))[0]
    with rendered(rotated) as a, rendered(signed) as b:
        assert a.crop((0, 30, 300, 300)).tobytes() == b.crop((0, 30, 300, 300)).tobytes()
        assert b.getpixel((260, 15))[0] > 200 and b.getpixel((260, 15))[1] < 30


@pytest.mark.parametrize('tool,opt', [
    ('pdf_crop', Options(margins=(200, 0, 200, 0))),
    ('pdf_crop', Options(margins=(float('nan'), 0, 0, 0))),
    ('pdf_watermark', Options(text='')),
    ('pdf_watermark', Options(text='한글')),
    ('pdf_signature', Options(signature_path='missing.png')),
    ('pdf_protect', Options(new_password='')),
    ('pdf_unlock', Options(password='anything')),
    ('pdf_redact', Options(redactions=())),
    ('pdf_redact', Options(redactions=((99, 0, 0, 10, 10),))),
    ('pdf_redact', Options(redactions=((1, 230, 0, 20, 10),))),
    ('pdf_redact', Options(redactions=((1, 0, 0, -10, 10),))),
])
def test_invalid_operations_leave_no_partial_pdf(tmp_path, tool, opt):
    source = document(tmp_path / 'input.pdf')
    value = run_job(tool, [source], tmp_path / 'out', opt)
    assert value.errors and not value.outputs
    assert not list((tmp_path / 'out').glob('*')) if (tmp_path / 'out').exists() else True


@pytest.mark.parametrize('values', [ (('missing', 'value'),), (('agree', 'invalid'),), (('name', '한글'),), (('color', 'Green'),) ])
def test_invalid_form_values(tmp_path, values):
    source = form(tmp_path / 'form.pdf')
    value = run_job('pdf_forms', [source], tmp_path / 'out', Options(form_values=values))
    assert value.errors and not value.outputs


def test_redaction_cancellation_does_not_commit_partial_output(tmp_path):
    source = document(tmp_path / 'input.pdf', pages=4)
    event = Event()
    progress = []

    def update(n, _):
        progress.append(n)
        if n > 0:
            event.set()

    value = run_job('pdf_redact', [source], tmp_path / 'out', Options(dpi=72, redactions=((1, 0, 0, 20, 20),)), event, update)
    assert value.cancelled and not value.errors and not value.outputs
    assert not list((tmp_path / 'out').iterdir())
    assert progress == sorted(progress)


def test_invalid_redaction_syntax():
    assert parse_redactions('1:10,20,30,40\n2:1,2,3,4') == ((1, 10, 20, 30, 40), (2, 1, 2, 3, 4))
    for bad in ['', 'bad', '0:1,2,3,4', '1:1,2,3', '1:nan,1,2,3']:
        with pytest.raises(ValueError):
            parse_redactions(bad)


def test_form_readonly_maxlength_and_xfa_are_enforced(tmp_path):
    source = form(tmp_path / 'form.pdf')
    readonly = tmp_path / 'readonly.pdf'
    limited = tmp_path / 'limited.pdf'
    xfa = tmp_path / 'xfa.pdf'
    for target, key, value in [(readonly, '/Ff', NumberObject(1)), (limited, '/MaxLen', NumberObject(3))]:
        with PdfWriter() as writer:
            writer.clone_document_from_reader(PdfReader(source))
            writer.root_object['/AcroForm']['/Fields'][0].get_object()[NameObject(key)] = value
            writer.write(target)
        failed = run_job('pdf_forms', [target], tmp_path / 'out', Options(form_values=(('name', 'Too long'),)))
        assert failed.errors and not failed.outputs
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(source))
        writer.root_object['/AcroForm'][NameObject('/XFA')] = TextStringObject('unsupported XFA')
        writer.write(xfa)
    with pytest.raises(ValueError, match='XFA'):
        inspect_forms(xfa)


def test_encrypted_redaction_and_owner_password_removal(tmp_path):
    source = document(tmp_path / 'source.pdf')
    protected = tmp_path / 'protected.pdf'
    with PdfWriter() as writer:
        writer.clone_document_from_reader(PdfReader(source))
        writer.encrypt('user-password', owner_password='owner-password', algorithm='AES-256')
        writer.write(protected)
    unlocked = result('pdf_unlock', [protected], tmp_path, Options(password='owner-password'))[0]
    assert not PdfReader(unlocked).is_encrypted
    redacted = result('pdf_redact', [protected], tmp_path, Options(password='user-password', dpi=72, redactions=((1, 10, 20, 220, 35),)))[0]
    assert not PdfReader(redacted).is_encrypted
    assert all(not page.extract_text().strip() for page in PdfReader(redacted).pages)


def test_m2_batch_errors_preserve_completed_outputs_and_no_overwrite(tmp_path):
    source = document(tmp_path / 'source.pdf')
    corrupt = tmp_path / 'corrupt.pdf'
    corrupt.write_bytes(b'not a pdf')
    value = run_job('pdf_numbers', [source, corrupt, source], tmp_path / 'out')
    assert len(value.outputs) == 2 and len(value.errors) == 1
    assert value.outputs[0] != value.outputs[1]
    assert all(len(PdfReader(p).pages) == 2 for p in value.outputs)
    assert 'SECRET-ONLY-IN-SOURCE' in PdfReader(source).pages[0].extract_text()


def test_redaction_rejects_oversized_render_before_allocation(tmp_path):
    source = tmp_path / 'large.pdf'
    with PdfWriter() as writer:
        writer.add_blank_page(100000, 100000)
        writer.write(source)
    value = run_job('pdf_redact', [source], tmp_path / 'out', Options(redactions=((1, 0, 0, 10, 10),)))
    assert value.errors and not value.outputs
    assert not list((tmp_path / 'out').iterdir())
