from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from pathlib import Path

from app.models.invoice import Invoice, LineItem, Party
from app.models.invoice_extraction import (
    ExtractedLineItem,
    ExtractedParty,
    InvoiceExtraction,
)
from app.services.document_text_extractor import (
    DocumentTextExtractor,
    DocumentTextResult,
)
from app.services.invoice_mapper import InvoiceMapper
from app.services.llm_service import LLMResult, LLMService
from app.services.receipt_processor import ReceiptProcessor


repository = Mock()

def test_process_runs_full_pipeline():

    repository.save.return_value = 123

    document_extractor = Mock(
        spec=DocumentTextExtractor
    )
    llm_service = Mock(
        spec=LLMService
    )
    invoice_mapper = Mock(
        spec=InvoiceMapper
    )

    document_result = DocumentTextResult(
        text="invoice text",
        page_count=1,
        character_count=12,
        extraction_method="ocr_layout",
    )

    extraction = InvoiceExtraction(
        invoice_number="INV-001",
        invoice_date="2026-08-13",
        issuer=ExtractedParty(
            name="Seller Ltd",
            identifier="123456789",
        ),
        receiver=ExtractedParty(
            name="Customer Ltd",
            identifier="987654321",
        ),
        items=[
            ExtractedLineItem(
                description="Laptop",
                corrected_description=None,
                category="IT Equipment",
                quantity="1",
                unit_price="1000.00",
                amount="1000.00",
            )
        ],
        total_amount="1000.00",
        currency="EUR",
        expense_summary="IT equipment purchase.",
    )

    llm_result = LLMResult(
        raw_response='{"invoice_number":"INV-001"}',
        parsed=extraction,
        model="test-model",
    )

    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date=date(2026, 8, 13),
        issuer=Party(
            name="Seller Ltd",
            identifier="123456789",
        ),
        receiver=Party(
            name="Customer Ltd",
            identifier="987654321",
        ),
        items=[
            LineItem(
                description="Laptop",
                corrected_description=None,
                category="IT Equipment",
                quantity=Decimal("1"),
                unit_price=Decimal("1000.00"),
                amount=Decimal("1000.00"),
            )
        ],
        total_amount=Decimal("1000.00"),
        currency="EUR",
    )

    document_extractor.extract.return_value = (
        document_result
    )

    llm_service.analyze_invoice.return_value = (
        llm_result
    )

    invoice_mapper.map.return_value = invoice

    processor = ReceiptProcessor(
        repository=repository,
        document_extractor=document_extractor,
        llm_service=llm_service,
        invoice_mapper=invoice_mapper,
    )

    result = processor.process("invoice.pdf")

    assert result.receipt_id == 123

    repository.save.assert_called_once()

    saved_call = repository.save.call_args

    assert saved_call.kwargs["source_filename"] == "invoice.pdf"

    saved_result = saved_call.kwargs["result"]

    assert saved_result.document == document_result
    assert saved_result.llm == llm_result
    assert saved_result.invoice == invoice

    document_extractor.extract.assert_called_once_with(
        Path("invoice.pdf")
    )

    llm_service.analyze_invoice.assert_called_once_with(
        "invoice text"
    )

    invoice_mapper.map.assert_called_once_with(
        extraction
    )