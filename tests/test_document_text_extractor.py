from pathlib import Path

from app.services.document_text_extractor import (
    DocumentTextExtractor,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DIGITAL_INVOICES_DIR = (
    PROJECT_ROOT
    / "samples"
    / "digital_invoices"
)

SCANNED_INVOICES_DIR = (
    PROJECT_ROOT
    / "samples"
    / "scanned_invoices"
)


def test_digital_pdf_uses_embedded_text():
    extractor = DocumentTextExtractor()

    result = extractor.extract(
        DIGITAL_INVOICES_DIR
        / "invoice_digital_bg.pdf"
    )

    assert result.extraction_method == "embedded_text"
    assert result.page_count >= 1
    assert result.character_count > 50
    assert result.text.strip()


def test_scanned_pdf_uses_ocr_layout():
    extractor = DocumentTextExtractor()

    result = extractor.extract(
        SCANNED_INVOICES_DIR
        / "invoice_scanned_bg.pdf"
    )

    assert result.extraction_method == "ocr_layout"
    assert result.page_count >= 1
    assert result.character_count > 100

    assert "PAGE 1" in result.text
    assert "ROW" in result.text