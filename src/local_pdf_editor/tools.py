from dataclasses import dataclass, field

CATEGORIES = (
    "All", "Workflow", "PDF Organization", "PDF Optimization", "PDF Conversion",
    "PDF Editing", "PDF Security", "PDF Analysis", "Image",
)


@dataclass(frozen=True)
class Tool:
    id: str
    title: str
    category: str
    extensions: tuple[str, ...]
    hint: str
    minimum: int = 1
    maximum: int | None = None


M1_TOOLS = (
    Tool("pdf_merge", "Merge PDFs", "PDF Organization", (".pdf",), "Combine files in the selected order.", 2),
    Tool("pdf_split", "Split PDF", "PDF Organization", (".pdf",), "Save each selected page as a separate PDF."),
    Tool("pdf_reorder", "Reorder pages", "PDF Organization", (".pdf",), "Enter every page once in the desired order.", maximum=1),
    Tool("pdf_delete", "Delete pages", "PDF Organization", (".pdf",), "Choose pages to remove; originals are preserved.", maximum=1),
    Tool("pdf_import", "Import pages", "PDF Organization", (".pdf",), "First file: destination. Second file: pages to import.", 2, 2),
    Tool("pdf_rotate", "Rotate pages", "PDF Organization", (".pdf",), "Rotate selected pages clockwise."),
    Tool("pdf_jpeg", "PDF → JPEG", "PDF Conversion", (".pdf",), "Render selected pages into JPEG images."),
    Tool("pdf_png", "PDF → PNG", "PDF Conversion", (".pdf",), "Render selected pages into PNG images."),
    Tool("image_pdf", "Images → PDF", "PDF Conversion", (".jpg", ".jpeg", ".png"), "One page per image, in selected order."),
    Tool("heic_jpeg", "HEIC → JPEG", "Image", (".heic", ".heif"), "Convert primary HEIC images locally."),
    Tool("heic_png", "HEIC → PNG", "Image", (".heic", ".heif"), "Convert primary HEIC images locally."),
    Tool("jpeg_png", "JPEG → PNG", "Image", (".jpg", ".jpeg"), "Batch convert and normalize orientation."),
    Tool("png_jpeg", "PNG → JPEG", "Image", (".png",), "Transparency is composited onto white."),
    Tool("image_resize", "Resize images", "Image", (".jpg", ".jpeg", ".png", ".heic", ".heif"), "Percentage or dimensions; optional aspect preservation."),
)
M2_TOOLS = (
    Tool("pdf_crop", "Crop PDF", "PDF Editing", (".pdf",), "Trim visible page margins in points; hidden content remains."),
    Tool("pdf_watermark", "Watermark", "PDF Editing", (".pdf",), "Add text to selected pages."),
    Tool("pdf_numbers", "Page numbers", "PDF Editing", (".pdf",), "Number selected pages in document order."),
    Tool("pdf_protect", "Protect PDF", "PDF Security", (".pdf",), "Save a password-protected AES-256 copy."),
    Tool("pdf_unlock", "Remove password", "PDF Security", (".pdf",), "Remove protection using the correct supplied password."),
    Tool("pdf_signature", "Insert signature image", "PDF Editing", (".pdf",), "Place a signature image; no certificate signing is performed."),
    Tool("pdf_redact", "Secure redaction", "PDF Security", (".pdf",), "Remove marked regions by rebuilding every page as a lossless raster image.", maximum=1),
    Tool("pdf_compare", "Compare PDFs", "PDF Analysis", (".pdf",), "Compare page visuals and create highlighted differences plus a report.", 2, 2),
    Tool("pdf_forms", "PDF forms", "PDF Editing", (".pdf",), "Inspect/fill basic AcroForm fields; optionally flatten.", maximum=1),
)
TOOLS = M1_TOOLS + M2_TOOLS
M2_IDS = frozenset(tool.id for tool in M2_TOOLS)
TOOL_BY_ID = {tool.id: tool for tool in TOOLS}


@dataclass(frozen=True)
class Options:
    pages: str = ""
    rotation: int = 90
    dpi: int = 144
    insert_after: int = 0
    percent: float = 100
    width: int = 0
    height: int = 0
    keep_aspect: bool = True
    image_format: str = "PNG"
    quality: int = 90
    margins: tuple[float, float, float, float] = (10, 10, 10, 10)  # left, top, right, bottom
    text: str = ""
    font_path: str = ""
    font_size: float = 12
    opacity: float = 0.25
    angle: float = 45
    start_number: int = 1
    password: str = field(default="", repr=False)
    new_password: str = field(default="", repr=False)
    signature_path: str = ""
    rect: tuple[float, float, float, float] = (20, 20, 120, 50)  # left, top, width, height
    redactions: tuple[tuple[int, float, float, float, float], ...] = ()
    compare_threshold: int = 8
    form_values: tuple[tuple[str, str], ...] = field(default=(), repr=False)
    flatten_forms: bool = False
