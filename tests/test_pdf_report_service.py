from datetime import date
from decimal import Decimal
from typing import cast

import pymupdf

from app.models.invoice import (
    Invoice,
    LineItem,
    Party,
)
from app.services.pdf_report_service import (
    PDFReportService,
)


def test_generates_pdf_report(tmp_path):
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2026, 8, 13),
        issuer=Party(
            name="Black Mesa Research",
            identifier="123456789",
        ),
        receiver=Party(
            name="Клиент образец",
            identifier="987654321",
        ),
        items=[
            LineItem(
                description="НОМ! кабел",
                corrected_description="HDMI кабел",
                category="Cables",
                quantity=Decimal("1"),
                unit_price=Decimal("5.00"),
                amount=Decimal("5.00"),
            ),
            LineItem(
                description="Монитор",
                corrected_description=None,
                category="IT Equipment",
                quantity=Decimal("1"),
                unit_price=Decimal("400.00"),
                amount=Decimal("400.00"),
            ),
        ],
        total_amount=Decimal("486.00"),
        currency="EUR",
    )

    service = PDFReportService(
        output_dir=tmp_path
    )

    report_path = service.generate(
        invoice=invoice,
        expense_summary=(
            "Purchase of IT equipment."
        ),
        receipt_id=42,
    )

    assert report_path.exists()
    assert report_path.name == "receipt_42.pdf"

    
    with pymupdf.open(report_path) as document:
        assert document.page_count >= 1

        text = "\n".join(
            cast(
                str,
                page.get_text("text"),
            )
            for page in document
        )

    assert "INV-001" in text
    assert "Black Mesa Research" in text
    assert "HDMI кабел" in text
    assert "Cables" in text
    assert "486.00 EUR" in text