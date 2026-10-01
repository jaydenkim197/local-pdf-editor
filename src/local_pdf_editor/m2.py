"""M2 PDF operations using the existing job/output contract."""
import hashlib
import json
import math
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path

import pypdfium2 as pdfium
import reportlab
from PIL import Image, ImageChops, ImageDraw, ImageOps
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from .processing import MAX_PIXELS, Cancelled, open_image, parse_pages, read_pdf, rgb


def finite(values):
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Coordinates and sizes must be finite numbers.")


def rectangle(rect, width, height):
    finite((*rect, width, height))
    left, top, w, h = rect
    if left < 0 or top < 0 or w <= 0 or h <= 0 or left + w > width or top + h > height:
        raise ValueError("Rectangle must fit inside the visible page, with positive width/height.")
    return left, top, w, h


def parse_redactions(text):
    """One 1-based page:left,top,width,height rectangle per line."""
    result = []
    try:
        for line in text.splitlines():
            if not line.strip():
                continue
            page, coordinates = line.split(':')
            rect = tuple(map(float, coordinates.split(',')))
            if len(rect) != 4 or int(page) < 1:
                raise ValueError()
            finite(rect)
            result.append((int(page), *rect))
    except ValueError:
        raise ValueError("Use one page:left,top,width,height per line, e.g. 1:20,30,100,40.") from None
    if not result:
        raise ValueError("Mark at least one redaction rectangle.")
    return tuple(result)


def font_for(text, path):
    source = Path(path) if path else Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf'
    name = 'Local_' + hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(source)))
    font = pdfmetrics.getFont(name)
    if any(ord(char) not in font.face.charToGlyph for char in text):
        raise ValueError("The font lacks a required character. Choose a TrueType font covering your text.")
    return name


def page_geometry(page):
    if float(page.get('/UserUnit', 1)) != 1:
        raise ValueError("Page geometry with UserUnit other than 1 is unsupported for overlays/crop.")
    box = page.cropbox
    width, height = float(box.width), float(box.height)
    finite((width, height))
    if width <= 0 or height <= 0:
        raise ValueError("Invalid visible page dimensions.")
    rotation = page.rotation % 360
    left, bottom, right, top = map(float, (box.left, box.bottom, box.right, box.top))
    transforms = {
        0: (1, 0, 0, 1, left, bottom),
        90: (0, 1, -1, 0, right, bottom),
        180: (-1, 0, 0, -1, right, top),
        270: (0, -1, 1, 0, left, top),
    }
    if rotation not in transforms:
        raise ValueError('Page rotation must be a multiple of 90 degrees.')
    return (height, width, Transformation(transforms[rotation])) if rotation in (90, 270) else (width, height, Transformation(transforms[rotation]))


def overlay_page(page, tool, opt, label=None):
    width, height, transform = page_geometry(page)
    if not 1 <= opt.font_size <= 200 or not 0 < opt.opacity <= 1:
        raise ValueError("Font size must be 1–200 points and opacity greater than 0, at most 1.")
    finite((opt.font_size, opt.opacity, opt.angle))
    data = BytesIO()
    canvas = Canvas(data, pagesize=(width, height))
    if tool == 'pdf_signature':
        left, top, w, h = rectangle(opt.rect, width, height)
        if not opt.signature_path or Path(opt.signature_path).suffix.lower() not in ('.png', '.jpg', '.jpeg'):
            raise ValueError("Choose a JPEG/PNG signature image.")
        with open_image(Path(opt.signature_path)) as image:
            canvas.drawImage(ImageReader(image), left, height - top - h, w, h, mask='auto', preserveAspectRatio=True, anchor='c')
    else:
        text = opt.text if tool == 'pdf_watermark' else label
        if not text or len(text) > 500 or any(ord(c) < 32 for c in text):
            raise ValueError("Use 1–500 text characters on a single line.")
        font = font_for(text, opt.font_path)
        canvas.setFont(font, opt.font_size)
        canvas.setFillColorRGB(0, 0, 0)
        if tool == 'pdf_watermark':
            canvas.setFillAlpha(opt.opacity)
            canvas.translate(width / 2, height / 2)
            canvas.rotate(opt.angle)
            canvas.drawCentredString(0, 0, text)
        else:
            if opt.font_size + 20 >= height or pdfmetrics.stringWidth(text, font, opt.font_size) >= width:
                raise ValueError("Page number does not fit the visible page.")
            canvas.drawCentredString(width / 2, 16, text)
    canvas.showPage()
    canvas.save()
    overlay = PdfReader(data).pages[0]
    page.merge_transformed_page(overlay, transform)


def standard_pdf(tool, path, folder, opt, ctx):
    with ExitStack() as stack:
        reader = read_pdf(stack, path, opt.password)
        if tool == 'pdf_unlock' and not reader.is_encrypted:
            raise ValueError("This PDF is not password protected.")
        with PdfWriter() as writer:
            writer.clone_document_from_reader(reader)
            if tool == 'pdf_protect':
                if not opt.new_password or len(opt.new_password.encode('utf-8')) > 127:
                    raise ValueError("A new password of 1–127 UTF-8 bytes is required.")
                writer.encrypt(opt.new_password, algorithm='AES-256')
            elif tool not in ('pdf_unlock',):
                selected = sorted(parse_pages(opt.pages, len(writer.pages)))
                if tool == 'pdf_numbers' and not 1 <= opt.start_number <= 1_000_000:
                    raise ValueError("Starting page number must be 1–1000000.")
                for index, number in enumerate(selected):
                    ctx.check()
                    page = writer.pages[number]
                    if tool == 'pdf_crop':
                        width, height, transform = page_geometry(page)
                        finite(opt.margins)
                        left, top, right, bottom = opt.margins
                        if min(opt.margins) < 0 or left + right >= width or top + bottom >= height:
                            raise ValueError("Crop margins must leave a positive visible page area.")
                        a = transform.apply_on((left, bottom))
                        b = transform.apply_on((width - right, height - top))
                        page.cropbox = RectangleObject((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
                    else:
                        overlay_page(page, tool, opt, str(opt.start_number + index))
                    ctx.progress(round(90 * (index + 1) / len(selected)), f"{path.name}: page {number + 1}")
            ctx.save(folder, path.stem + '_' + tool.removeprefix('pdf_'), '.pdf', writer.write)


def render(document, index, dpi):
    page = document[index]
    try:
        w, h = page.get_size()
        finite((w, h))
        if w <= 0 or h <= 0 or math.ceil(w * dpi / 72) * math.ceil(h * dpi / 72) > MAX_PIXELS:
            raise ValueError("Rendered page exceeds the 40 megapixel limit or has invalid dimensions.")
        bitmap = page.render(scale=dpi / 72, draw_annots=True)
        try:
            image = rgb(bitmap.to_pil())
        finally:
            bitmap.close()
        return image, (w, h)
    finally:
        page.close()


def raster_redact(path, folder, opt, ctx):
    if not 36 <= opt.dpi <= 300:
        raise ValueError("Redaction DPI must be 36–300.")
    if not opt.redactions:
        raise ValueError("Mark at least one redaction rectangle.")
    with ExitStack() as stack:
        read_pdf(stack, path, opt.password)
    with pdfium.PdfDocument(str(path), password=opt.password) as document:
        document.init_forms()
        by_page = {}
        for page_number, *rect in opt.redactions:
            if not isinstance(page_number, int) or not 1 <= page_number <= len(document):
                raise ValueError("Redaction page number is outside the document.")
            page = document[page_number - 1]
            try:
                rectangle(rect, *page.get_size())
            finally:
                page.close()
            by_page.setdefault(page_number - 1, []).append(rect)

        ctx.save(folder, path.stem + '_redacted', '.pdf',
                 lambda output: write_raster_document(document, output, opt.dpi, by_page, ctx))


def write_raster_document(document, output, dpi, by_page, ctx, action='Redacting'):
    canvas = Canvas(str(output), pageCompression=1)
    # Only new pixels go into this PDF. No reader/writer source cloning occurs.
    total = 0
    for index in range(len(document)):
        ctx.check()
        image, (w, h) = render(document, index, dpi)
        try:
            total += image.width * image.height
            if total > 120_000_000:
                raise ValueError("Redaction batch exceeds 120 megapixels. Lower DPI or split the document first.")
            draw = ImageDraw.Draw(image)
            x_scale, y_scale = image.width / w, image.height / h
            for left, top, width, height in by_page.get(index, []):
                # Rounded bitmap dimensions determine the pixels' actual page footprints.
                # Round outward independently on each axis, including fractional page sizes.
                x0, y0 = math.floor(left * x_scale), math.floor(top * y_scale)
                x1, y1 = math.ceil((left + width) * x_scale), math.ceil((top + height) * y_scale)
                draw.rectangle((x0, y0, min(x1, image.width) - 1, min(y1, image.height) - 1), fill='black')
            canvas.setPageSize((w, h))
            canvas.drawImage(ImageReader(image), 0, 0, width=w, height=h)
            canvas.showPage()
        finally:
            image.close()
        ctx.progress(round(90 * (index + 1) / len(document)), f"{action} page {index + 1}")
    ctx.check()
    canvas.save()


def compare_pdf(files, folder, opt, ctx):
    if not 36 <= opt.dpi <= 300 or not 0 <= opt.compare_threshold <= 255:
        raise ValueError("Comparison DPI must be 36–300 and threshold 0–255.")
    with ExitStack() as stack:
        for path in files:
            read_pdf(stack, path, opt.password)
        first = stack.enter_context(pdfium.PdfDocument(str(files[0]), password=opt.password))
        second = stack.enter_context(pdfium.PdfDocument(str(files[1]), password=opt.password))
        first.init_forms()
        second.init_forms()
        count = max(len(first), len(second))
        report = {'mode': 'visual-by-page-index', 'dpi': opt.dpi, 'threshold': opt.compare_threshold,
                  'page_counts': [len(first), len(second)], 'pages': []}
        for index in range(count):
            ctx.check()
            a, a_size = render(first, index, opt.dpi) if index < len(first) else (None, None)
            b, b_size = render(second, index, opt.dpi) if index < len(second) else (None, None)
            try:
                size = (max(image.width for image in (a, b) if image), max(image.height for image in (a, b) if image))
                if size[0] * size[1] > MAX_PIXELS:
                    raise ValueError("Comparison canvas exceeds the 40 megapixel limit.")
                with ExitStack() as images:
                    left = images.enter_context(Image.new('RGB', size, 'white'))
                    right = images.enter_context(Image.new('RGB', size, 'white'))
                    if a is not None: left.paste(a, (0, 0))
                    if b is not None: right.paste(b, (0, 0))
                    diff = images.enter_context(ImageChops.difference(left, right))
                    r, g, blue = diff.split()
                    try:
                        strength = images.enter_context(ImageChops.lighter(ImageChops.lighter(r, g), blue))
                    finally:
                        r.close(); g.close(); blue.close()
                    mask = images.enter_context(strength.point(lambda p: 255 if p > opt.compare_threshold else 0))
                    missing = a is None or b is None
                    if missing: mask.paste(255, (0, 0, *size))
                    changed = sum(mask.histogram()[1:])
                    entry = {'page': index + 1, 'changed_pixels': changed, 'missing_page': missing,
                             'size_changed': a_size != b_size, 'first_size_points': a_size, 'second_size_points': b_size}
                    if changed or a_size != b_size:
                        highlighted = images.enter_context(ImageOps.grayscale(right).convert('RGB'))
                        highlighted.paste((240, 50, 70), mask=mask)
                        before = len(ctx.result.outputs)
                        ctx.save(folder, files[0].stem + f'_diff_page_{index + 1}', '.png',
                                 lambda p: highlighted.save(p, format='PNG'))
                        entry['diff_file'] = ctx.result.outputs[before].name
                    report['pages'].append(entry)
            finally:
                if a is not None: a.close()
                if b is not None: b.close()
            ctx.progress(round(90 * (index + 1) / count), f"Comparing page {index + 1}")
        report['identical_visuals'] = all(not p['changed_pixels'] and not p['size_changed'] for p in report['pages'])
        ctx.save(folder, files[0].stem + '_comparison', '.json',
                 lambda p: p.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8'))


def field_schema(reader):
    acro = reader.root_object.get('/AcroForm')
    if acro and '/XFA' in acro.get_object():
        raise ValueError("XFA forms are unsupported; use a standard AcroForm PDF.")
    fields = reader.get_fields() or {}
    if not fields:
        raise ValueError("No AcroForm fields found.")
    raw_fields = {}
    visited = set()
    def walk(nodes, prefix='', inherited=None):
        for node in nodes:
            field = node.get_object()
            identity = id(field)
            if identity in visited: continue
            visited.add(identity)
            if len(visited) > 10000:
                raise ValueError('Form field tree is too large.')
            name = str(field.get('/T', ''))
            full_name = '.'.join(part for part in (prefix, name) if part)
            properties = dict(inherited or {})
            for key in ('/FT', '/Ff', '/MaxLen'):
                if key in field: properties[key] = field[key]
            if full_name: raw_fields[full_name] = properties
            walk(field.get('/Kids', []), full_name, properties)
    walk(acro.get_object().get('/Fields', []) if acro else [])
    schema = []
    for name, field in fields.items():
        raw = raw_fields.get(name, field)
        kind, flags = str(raw.get('/FT', '')), int(raw.get('/Ff', 0))
        readonly = bool(flags & 1)
        supported = kind in ('/Tx', '/Btn', '/Ch') and not (kind == '/Btn' and flags & (1 << 16)) and not (kind == '/Ch' and flags & (1 << 21))
        choices = []
        if kind == '/Ch':
            for value in field.get('/Opt', []):
                choices.append(str(value[0]) if isinstance(value, list) else str(value))
        elif kind == '/Btn':
            choices = [str(value) for value in field.get('/_States_', [])]
        schema.append({'name': name, 'type': kind, 'value': str(field.get('/V', '')),
                       'choices': choices, 'readonly': readonly, 'supported': supported,
                       'max_length': int(raw.get('/MaxLen', 0)), 'multiline': bool(flags & (1 << 12))})
    return schema


def inspect_forms(path, password=''):
    with ExitStack() as stack:
        return field_schema(read_pdf(stack, Path(path), password))


def fill_forms(path, folder, opt, ctx):
    with ExitStack() as stack:
        reader = read_pdf(stack, path, opt.password)
        schema = {field['name']: field for field in field_schema(reader)}
        values = dict(opt.form_values)
        if len(values) != len(opt.form_values):
            raise ValueError("Duplicate form field names.")
        for name, value in values.items():
            if name not in schema:
                raise ValueError("Unknown form field name.")
            field = schema[name]
            if not field['supported'] or field['readonly']:
                raise ValueError(f"Field {name} is unsupported or read-only.")
            if field['type'] == '/Tx':
                if any(ord(c) > 126 or (ord(c) < 32 and c not in '\n\r\t') for c in value):
                    raise ValueError("M2 form text uses printable ASCII; Unicode form font appearances are unsupported.")
                if not field['multiline'] and any(c in value for c in '\n\r'):
                    raise ValueError(f"Field {name} is single-line.")
                if field['max_length'] and len(value) > field['max_length']:
                    raise ValueError(f"Field {name} exceeds its maximum length.")
            elif value not in field['choices']:
                raise ValueError(f"Field {name} requires one of its listed choices.")
        with PdfWriter() as writer:
            writer.clone_document_from_reader(reader)
            for index, page in enumerate(writer.pages):
                ctx.check()
                if page.get('/Annots'):
                    writer.update_page_form_field_values(page, values, auto_regenerate=False, flatten=False)
                ctx.progress(round((45 if opt.flatten_forms else 90) * (index + 1) / len(writer.pages)), f"Form page {index + 1}")
            if opt.flatten_forms:
                if not 36 <= opt.dpi <= 300:
                    raise ValueError('Flatten DPI must be 36–300.')
                data = BytesIO()
                writer.write(data)
                with pdfium.PdfDocument(data.getvalue()) as document:
                    document.init_forms()
                    from .processing import Context
                    raster_ctx = Context(ctx.cancel, lambda n, msg: ctx.progress(45 + round(n/2), msg), ctx.result)
                    ctx.save(folder, path.stem + '_flattened', '.pdf',
                             lambda output: write_raster_document(document, output, opt.dpi, {}, raster_ctx))
            else:
                ctx.save(folder, path.stem + '_filled', '.pdf', writer.write)


def process_m2(tool, files, folder, opt, ctx):
    if tool == 'pdf_compare':
        compare_pdf(files, folder, opt, ctx)
        return
    for index, path in enumerate(files):
        ctx.check()
        # Reuse the existing whole-batch progress/result contract.
        from .processing import Context
        batch = Context(ctx.cancel, lambda n, message: ctx.progress(round((index + n / 100) * 100 / len(files)), message), ctx.result)
        try:
            if tool == 'pdf_redact':
                raster_redact(path, folder, opt, batch)
            elif tool == 'pdf_forms':
                fill_forms(path, folder, opt, batch)
            else:
                standard_pdf(tool, path, folder, opt, batch)
        except Cancelled:
            raise
        except Exception as e:
            # Do not include supplied passwords or form values in diagnostics.
            message = str(e)
            for secret in (opt.password, opt.new_password, *(value for _, value in opt.form_values)):
                if secret:
                    message = message.replace(secret, '[hidden]')
            ctx.result.errors.append(f"{path.name}: {message}")
        ctx.progress(round(100 * (index + 1) / len(files)), path.name)
