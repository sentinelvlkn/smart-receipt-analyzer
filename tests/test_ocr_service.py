from pathlib import Path

import pytest

from app.services.ocr_service import OCRService


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCANNED_INVOICES_DIR = (
    PROJECT_ROOT
    / "samples"
    / "scanned_invoices"
)


def test_ocr_extracts_text_from_scanned_pdf():
    service = OCRService()

    pdf_path = (
        SCANNED_INVOICES_DIR
        / "invoice_scanned_bg.pdf"
    )

    result = service.extract_text(pdf_path)

    assert result.page_count >= 1
    assert result.character_count > 100
    assert result.text.strip()
    assert result.languages == "bul+eng"

    assert len(result.pages) > 0

    first_page = result.pages[0]

    assert first_page.page_number == 1
    assert first_page.width > 0
    assert first_page.height > 0
    assert len(first_page.words) > 0

    first_word = first_page.words[0]

    assert first_word.text
    assert first_word.left >= 0
    assert first_word.top >= 0
    assert first_word.width > 0
    assert first_word.height > 0


def test_ocr_missing_pdf_raises_error():
    service = OCRService()

    pdf_path = (
        SCANNED_INVOICES_DIR
        / "missing.pdf"
    )

    with pytest.raises(FileNotFoundError):
        service.extract_text(pdf_path)
