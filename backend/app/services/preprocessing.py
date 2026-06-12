import io
from pathlib import Path

import fitz
from PIL import Image, UnidentifiedImageError

from app.services.storage.local import LocalStorageService


SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
    "image/bmp",
}


class UnsupportedDocumentError(ValueError):
    pass


def create_page_images(
    *,
    document_id: str,
    storage_path: str,
    content_type: str,
    storage: LocalStorageService,
) -> list[dict]:
    normalized_type = content_type.lower().split(";")[0].strip()
    path = Path(storage_path)
    suffix = path.suffix.lower()

    if normalized_type in SUPPORTED_IMAGE_TYPES or suffix in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}:
        return [_normalize_image_page(document_id=document_id, page_number=1, source_path=path, storage=storage)]

    if normalized_type == "application/pdf" or suffix == ".pdf":
        return _render_pdf_pages(document_id=document_id, source_path=path, storage=storage)

    raise UnsupportedDocumentError(
        "Unsupported file type. Upload a PDF or image file such as PNG, JPG, WEBP, TIFF, or BMP."
    )


def _normalize_image_page(
    *,
    document_id: str,
    page_number: int,
    source_path: Path,
    storage: LocalStorageService,
) -> dict:
    try:
        with Image.open(source_path) as image:
            image = image.convert("RGB")
            output = io.BytesIO()
            image.save(output, format="PNG")
            image_path = storage.write_page_image(document_id, page_number, output.getvalue())
            return {
                "page_number": page_number,
                "image_path": image_path,
                "width": image.width,
                "height": image.height,
            }
    except UnidentifiedImageError as exc:
        raise UnsupportedDocumentError("Uploaded image could not be opened.") from exc


def _render_pdf_pages(
    *,
    document_id: str,
    source_path: Path,
    storage: LocalStorageService,
) -> list[dict]:
    try:
        pdf = fitz.open(source_path)
    except Exception as exc:
        raise UnsupportedDocumentError("Uploaded PDF could not be opened.") from exc

    if pdf.page_count == 0:
        raise UnsupportedDocumentError("Uploaded PDF has no pages.")

    pages: list[dict] = []
    try:
        for index, page in enumerate(pdf, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image_path = storage.write_page_image(document_id, index, pixmap.tobytes("png"))
            pages.append(
                {
                    "page_number": index,
                    "image_path": image_path,
                    "width": pixmap.width,
                    "height": pixmap.height,
                }
            )
    finally:
        pdf.close()

    return pages
