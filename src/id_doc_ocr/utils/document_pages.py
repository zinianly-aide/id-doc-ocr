from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path


PDF_MIME_TYPES = {"application/pdf", "application/x-pdf"}
PDF_MAGIC = b"%PDF-"


@dataclass(frozen=True, slots=True)
class DocumentPage:
    content: bytes
    page_number: int
    page_count: int
    filename: str | None = None
    content_type: str | None = None
    document_kind: str = "image"
    source_filename: str | None = None


def is_pdf_document(content: bytes, *, filename: str | None = None, content_type: str | None = None) -> bool:
    stripped = content.lstrip()
    if stripped.startswith(PDF_MAGIC):
        return True
    normalized_content_type = str(content_type or "").split(";", 1)[0].strip().lower()
    if normalized_content_type in PDF_MIME_TYPES:
        return True
    return bool(filename and Path(filename).suffix.lower() == ".pdf")


def expand_document_pages(
    content: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> list[DocumentPage]:
    if not content:
        raise ValueError("document content is empty")
    if is_pdf_document(content, filename=filename, content_type=content_type):
        return render_pdf_pages(content, filename=filename)
    return [
        DocumentPage(
            content=content,
            page_number=1,
            page_count=1,
            filename=filename,
            content_type=content_type,
            document_kind="image",
            source_filename=filename,
        )
    ]


def render_pdf_pages(content: bytes, *, filename: str | None = None, scale: float = 2.0) -> list[DocumentPage]:
    try:
        import pypdfium2 as pdfium  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("PDF attachments require pypdfium2. Install the project with PDF support or run: pip install pypdfium2") from exc

    try:
        document = pdfium.PdfDocument(content)
    except Exception as exc:
        raise ValueError(f"failed to open PDF attachment: {exc}") from exc

    pages: list[DocumentPage] = []
    try:
        page_count = len(document)
        if page_count <= 0:
            raise ValueError("PDF attachment has no pages")
        stem = Path(filename).stem if filename else "attachment"
        for index in range(page_count):
            page = document[index]
            bitmap = None
            try:
                bitmap = page.render(scale=scale)
                pil_image = bitmap.to_pil()
                output = BytesIO()
                pil_image.save(output, format="PNG")
                pages.append(
                    DocumentPage(
                        content=output.getvalue(),
                        page_number=index + 1,
                        page_count=page_count,
                        filename=f"{stem}-page-{index + 1}.png",
                        content_type="image/png",
                        document_kind="pdf",
                        source_filename=filename,
                    )
                )
            finally:
                with suppress(Exception):
                    if bitmap is not None:
                        bitmap.close()
                with suppress(Exception):
                    page.close()
    finally:
        with suppress(Exception):
            document.close()
    return pages
