"""M1 processors shared by the GUI and functional tests; no Qt dependency."""
import math
import warnings
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Callable

import pi_heif
import pypdfium2 as pdfium
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter

from .output import write_output
from .tools import M2_IDS, M3_IDS, Options, TOOL_BY_ID

pi_heif.register_heif_opener()
MAX_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class Cancelled(Exception):
    pass


@dataclass
class Result:
    outputs: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    cancelled: bool = False


@dataclass
class Context:
    cancel: Event
    progress: Callable[[int, str], None]
    result: Result

    def check(self):
        if self.cancel.is_set():
            raise Cancelled()

    def save(self, folder, stem, extension, callback):
        self.check()

        def guarded(path):
            callback(path)
            self.check()

        path = write_output(folder, stem, extension, guarded)
        self.result.outputs.append(path)


def parse_pages(text: str, count: int) -> list[int]:
    if not text.strip():
        return list(range(count))
    pages = []
    try:
        for part in text.split(","):
            bounds = part.strip().split("-")
            if len(bounds) == 1:
                start = end = int(bounds[0])
            elif len(bounds) == 2:
                start, end = map(int, bounds)
            else:
                raise ValueError()
            if not 1 <= start <= end <= count:
                raise ValueError()
            pages.extend(range(start - 1, end))
        if not pages or len(set(pages)) != len(pages):
            raise ValueError()
    except ValueError:
        raise ValueError(f"Use unique page numbers/ranges within 1–{count}, e.g. 1,3-5.") from None
    return pages


def read_pdf(stack: ExitStack, path: Path, password: str | None = None) -> PdfReader:
    stream = stack.enter_context(path.open("rb"))
    reader = PdfReader(stream, strict=True)
    if reader.is_encrypted:
        if password is None:
            raise ValueError("Encrypted PDFs are not supported in M1.")
        if not reader.decrypt(password):
            raise ValueError("Incorrect PDF password.")
    if not reader.pages:
        raise ValueError("The PDF has no pages.")
    return reader


@contextmanager
def open_image(path: Path):
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as original:
            if original.width * original.height > MAX_PIXELS:
                raise ValueError("Image exceeds the 40 megapixel limit.")
            image = ImageOps.exif_transpose(original)
            try:
                image.load()
                yield image
            finally:
                image.close()


def rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        base = Image.new("RGB", image.size, "white")
        base.paste(rgba, mask=rgba.getchannel("A"))
        rgba.close()
        return base
    return image.convert("RGB")


def resize_dimensions(size: tuple[int, int], options: Options) -> tuple[int, int]:
    w, h = size
    if options.width < 0 or options.height < 0:
        raise ValueError("Dimensions cannot be negative.")
    if options.width or options.height:
        if options.keep_aspect:
            ratios = []
            if options.width:
                ratios.append(options.width / w)
            if options.height:
                ratios.append(options.height / h)
            ratio = min(ratios)
            out = (max(1, round(w * ratio)), max(1, round(h * ratio)))
        else:
            if not options.width or not options.height:
                raise ValueError("Specify both width and height when aspect preservation is off.")
            out = (options.width, options.height)
    else:
        if not math.isfinite(options.percent) or not 0 < options.percent <= 1000:
            raise ValueError("Percentage must be greater than 0 and at most 1000.")
        out = (max(1, round(w * options.percent / 100)), max(1, round(h * options.percent / 100)))
    if out[0] * out[1] > MAX_PIXELS:
        raise ValueError("Resized image exceeds the 40 megapixel limit.")
    return out


def process_pdf(tool: str, files: list[Path], folder: Path, opt: Options, ctx: Context):
    with ExitStack() as stack:
        readers = [read_pdf(stack, path) for path in files]
        writer = PdfWriter()
        if tool == "pdf_merge":
            for reader in readers:
                for page in reader.pages:
                    ctx.check()
                    writer.add_page(page)
        elif tool == "pdf_import":
            destination, source = readers
            if not 0 <= opt.insert_after <= len(destination.pages):
                raise ValueError("Insertion position must be between 0 and the destination page count.")
            imported = [source.pages[i] for i in parse_pages(opt.pages, len(source.pages))]
            sequence = list(destination.pages[:opt.insert_after]) + imported + list(destination.pages[opt.insert_after:])
            for page in sequence:
                ctx.check()
                writer.add_page(page)
        else:
            reader = readers[0]
            selected = parse_pages(opt.pages, len(reader.pages))
            if tool == "pdf_reorder":
                if len(selected) != len(reader.pages):
                    raise ValueError("Reorder must include every page exactly once.")
                order = selected
            elif tool == "pdf_delete":
                if not opt.pages.strip():
                    raise ValueError("Specify pages to delete.")
                order = [i for i in range(len(reader.pages)) if i not in selected]
                if not order:
                    raise ValueError("Deleting all pages would create an empty PDF.")
            else:
                order = list(range(len(reader.pages)))
            if tool == "pdf_rotate" and opt.rotation not in (90, 180, 270):
                raise ValueError("Rotation must be 90, 180 or 270 degrees.")
            for i in order:
                ctx.check()
                page = writer.add_page(reader.pages[i])
                if tool == "pdf_rotate" and i in selected:
                    page.rotate(opt.rotation)
        try:
            ctx.save(folder, files[0].stem + "_" + tool.removeprefix("pdf_"), ".pdf", writer.write)
        finally:
            writer.close()


def split_pdf(path: Path, folder: Path, opt: Options, ctx: Context):
    with ExitStack() as stack:
        reader = read_pdf(stack, path)
        selected = parse_pages(opt.pages, len(reader.pages))
        for index, page_number in enumerate(selected):
            with PdfWriter() as writer:
                writer.add_page(reader.pages[page_number])
                ctx.save(folder, f"{path.stem}_page_{page_number + 1}", ".pdf", writer.write)
            ctx.progress(round(100 * (index + 1) / len(selected)), f"{path.name}: page {page_number + 1}")


def render_pdf(path: Path, folder: Path, opt: Options, ctx: Context, format: str):
    if not 36 <= opt.dpi <= 600:
        raise ValueError("DPI must be between 36 and 600.")
    # Validate encryption/corruption through the same path as structural operations.
    with ExitStack() as stack:
        reader = read_pdf(stack, path)
        selected = parse_pages(opt.pages, len(reader.pages))
    with pdfium.PdfDocument(str(path)) as document:
        for index, number in enumerate(selected):
            ctx.check()
            page = document[number]
            try:
                w, h = page.get_size()
                if math.ceil(w * opt.dpi / 72) * math.ceil(h * opt.dpi / 72) > MAX_PIXELS:
                    raise ValueError("Rendered page exceeds the 40 megapixel limit. Lower the DPI.")
                bitmap = page.render(scale=opt.dpi / 72)
                try:
                    image = bitmap.to_pil()
                    converted = rgb(image)
                    try:
                        ctx.save(folder, f"{path.stem}_page_{number + 1}", ".jpg" if format == "JPEG" else ".png",
                                 lambda p: converted.save(p, format=format, quality=opt.quality))
                    finally:
                        converted.close()
                        image.close()
                finally:
                    bitmap.close()
            finally:
                page.close()
            ctx.progress(round(100 * (index + 1) / len(selected)), f"{path.name}: page {number + 1}")


def images_pdf(files: list[Path], folder: Path, ctx: Context):
    images = []
    try:
        total = 0
        for path in files:
            ctx.check()
            with open_image(path) as image:
                total += image.width * image.height
                if total > 120_000_000:
                    raise ValueError("Combined images exceed 120 megapixels; use a smaller batch.")
                images.append(rgb(image))
        ctx.save(folder, files[0].stem + "_images", ".pdf",
                 lambda p: images[0].save(p, format="PDF", save_all=True, append_images=images[1:], resolution=72))
    finally:
        for image in images:
            image.close()


def convert_image(tool: str, path: Path, folder: Path, opt: Options, ctx: Context):
    format = opt.image_format if tool == "image_resize" else ("JPEG" if tool.endswith("jpeg") else "PNG")
    if format not in ("JPEG", "PNG"):
        raise ValueError("Output format must be JPEG or PNG.")
    with open_image(path) as image:
        resized = image.resize(resize_dimensions(image.size, opt), Image.Resampling.LANCZOS) if tool == "image_resize" else image.copy()
        converted = rgb(resized) if format == "JPEG" else resized.convert("RGBA" if "A" in resized.mode or "transparency" in resized.info else "RGB")
        try:
            ctx.save(folder, path.stem + "_" + tool, ".jpg" if format == "JPEG" else ".png",
                     lambda p: converted.save(p, format=format, quality=opt.quality))
        finally:
            converted.close()
            resized.close()


def run_job(tool_id: str, files: list[Path], folder: Path, options: Options = Options(),
            cancel: Event | None = None, progress: Callable[[int, str], None] | None = None) -> Result:
    result = Result()
    ctx = Context(cancel if cancel is not None else Event(), progress or (lambda *_: None), result)
    try:
        tool = TOOL_BY_ID[tool_id]
        if len(files) < tool.minimum or (tool.maximum is not None and len(files) > tool.maximum):
            raise ValueError(f"{tool.title}: select {tool.minimum}–{tool.maximum or 'many'} files.")
        if not 1 <= options.quality <= 100:
            raise ValueError("JPEG quality must be between 1 and 100.")
        files = [Path(p).resolve() for p in files]
        for path in files:
            ctx.check()
            if not path.is_file():
                raise ValueError(f"File not found: {path.name}")
            if path.suffix.lower() not in tool.extensions:
                raise ValueError(f"Unsupported file type: {path.name}")
        ctx.progress(0, "Processing locally…")
        if tool_id in M3_IDS:
            from .m3 import process_m3
            process_m3(tool_id, files, folder, options, ctx)
        elif tool_id in M2_IDS:
            from .m2 import process_m2
            process_m2(tool_id, files, folder, options, ctx)
        elif tool_id in ("pdf_merge", "pdf_import", "pdf_reorder", "pdf_delete"):
            process_pdf(tool_id, files, folder, options, ctx)
        elif tool_id == "image_pdf":
            images_pdf(files, folder, ctx)
        else:
            for index, path in enumerate(files):
                ctx.check()
                # Page-level progress is mapped into the entire batch.
                batch_ctx = Context(ctx.cancel, lambda n, message: ctx.progress(round((index + n / 100) * 100 / len(files)), message), result)
                try:
                    if tool_id == "pdf_split":
                        split_pdf(path, folder, options, batch_ctx)
                    elif tool_id == "pdf_rotate":
                        process_pdf(tool_id, [path], folder, options, batch_ctx)
                    elif tool_id in ("pdf_jpeg", "pdf_png"):
                        render_pdf(path, folder, options, batch_ctx, "JPEG" if tool_id == "pdf_jpeg" else "PNG")
                    else:
                        convert_image(tool_id, path, folder, options, batch_ctx)
                except Cancelled:
                    raise
                except Exception as e:
                    result.errors.append(f"{path.name}: {e}")
                ctx.progress(round(100 * (index + 1) / len(files)), path.name)
        ctx.check()
        ctx.progress(100, "Finished" if not result.errors else "Finished with errors")
    except Cancelled:
        result.cancelled = True
    except Exception as e:
        result.errors.append(str(e))
    return result
