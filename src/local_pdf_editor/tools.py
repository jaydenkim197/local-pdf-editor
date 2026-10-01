from dataclasses import dataclass

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


TOOLS = (
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
