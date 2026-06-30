from id_doc_ocr.utils import document_pages


def test_is_pdf_document_detects_magic_content_type_and_filename():
    assert document_pages.is_pdf_document(b"%PDF-1.7\n...", filename="scan.bin", content_type="application/octet-stream")
    assert document_pages.is_pdf_document(b"not-pdf", filename="scan.bin", content_type="application/pdf")
    assert document_pages.is_pdf_document(b"not-pdf", filename="scan.PDF", content_type="application/octet-stream")


def test_expand_document_pages_keeps_non_pdf_as_single_page():
    pages = document_pages.expand_document_pages(b"image-bytes", filename="scan.jpg", content_type="image/jpeg")

    assert len(pages) == 1
    assert pages[0].content == b"image-bytes"
    assert pages[0].page_number == 1
    assert pages[0].page_count == 1
    assert pages[0].document_kind == "image"


def test_expand_document_pages_renders_pdf_pages(monkeypatch):
    def fake_render_pdf_pages(content, *, filename=None):
        return [
            document_pages.DocumentPage(content=b"p1", page_number=1, page_count=2, filename="scan-page-1.png", content_type="image/png", document_kind="pdf"),
            document_pages.DocumentPage(content=b"p2", page_number=2, page_count=2, filename="scan-page-2.png", content_type="image/png", document_kind="pdf"),
        ]

    monkeypatch.setattr(document_pages, "render_pdf_pages", fake_render_pdf_pages)

    pages = document_pages.expand_document_pages(b"%PDF-1.7\n...", filename="scan.pdf", content_type="application/pdf")

    assert [page.content for page in pages] == [b"p1", b"p2"]
    assert [page.filename for page in pages] == ["scan-page-1.png", "scan-page-2.png"]
