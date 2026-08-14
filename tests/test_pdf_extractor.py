from pathlib import Path

import pytest

from app.services.pdf_extractor import PDFExtractor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = PROJECT_ROOT / "samples"
DIGITAL_INVOICES_DIR = PROJECT_ROOT / "samples" / "digital_invoices"
SCANNED_INVOICES_DIR = PROJECT_ROOT / "samples" / "scanned_invoices"

def test_digital_pdf_has_embedded_text():
    extractor = PDFExtractor()

    pdf_path = DIGITAL_INVOICES_DIR / "invoice_digital_bg.pdf"

    result = extractor.extract(pdf_path)

    assert result.page_count >= 1
    assert result.character_count > 50
    assert result.needs_ocr is False


def test_scanned_pdf_requires_ocr():
    extractor = PDFExtractor()

    pdf_path = SCANNED_INVOICES_DIR /"invoice_scanned_bg.pdf"

    result = extractor.extract(pdf_path)

    assert result.page_count >= 1
    assert result.needs_ocr is True


def test_missing_pdf_raises_error():
    extractor = PDFExtractor()

    pdf_path = SAMPLES_DIR / "does_not_exist.pdf"

    with pytest.raises(FileNotFoundError):
        extractor.extract(pdf_path)
