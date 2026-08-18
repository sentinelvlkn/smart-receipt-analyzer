from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from app.models.invoice import (
    Invoice,
    LineItem,
    Party,
)
from app.models.invoice_extraction import (
    ExtractedLineItem,
    ExtractedParty,
    InvoiceExtraction,
)
from app.services.document_text_extractor import (
    DocumentTextExtractor,
    DocumentTextResult,
)
from app.services.invoice_mapper import (
    InvoiceMapper,
    InvoiceMappingError,
)
from app.services.llm_service import (
    LLMResult,
    LLMService,
)
from app.services.pdf_report_service import (
    PDFReportService,
)
from app.services.receipt_processor import (
    ReceiptProcessor,
)


def make_extraction(
    quantity: str | None = "1",
) -> InvoiceExtraction:
    return InvoiceExtraction(
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
                quantity=quantity,
                unit_price="1000.00",
                amount="1000.00",
            )
        ],
        total_amount="1000.00",
        currency="EUR",
        expense_summary="IT equipment purchase.",
    )


def make_invoice() -> Invoice:
    return Invoice(
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


def make_document_result() -> DocumentTextResult:
    return DocumentTextResult(
        text="invoice text",
        page_count=1,
        character_count=12,
        extraction_method="ocr_layout",
    )


def test_process_runs_full_pipeline():
    repository = Mock()
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

    pdf_report_service = Mock(
        spec=PDFReportService
    )

    document_result = make_document_result()
    extraction = make_extraction()
    invoice = make_invoice()

    llm_result = LLMResult(
        raw_response=(
            '{"invoice_number":"INV-001"}'
        ),
        parsed=extraction,
        model="test-model",
    )

    document_extractor.extract.return_value = (
        document_result
    )

    llm_service.analyze_invoice.return_value = (
        llm_result
    )

    invoice_mapper.map.return_value = (
        invoice
    )

    pdf_report_service.generate.return_value = (
        Path("reports/receipt_123.pdf")
    )

    processor = ReceiptProcessor(
        repository=repository,
        document_extractor=document_extractor,
        llm_service=llm_service,
        invoice_mapper=invoice_mapper,
        pdf_report_service=pdf_report_service,
    )

    result = processor.process(
        "invoice.pdf"
    )

    document_extractor.extract.assert_called_once_with(
        Path("invoice.pdf")
    )

    llm_service.analyze_invoice.assert_called_once_with(
        "invoice text"
    )

    invoice_mapper.map.assert_called_once_with(
        extraction
    )

    repository.save.assert_called_once()

    saved_call = repository.save.call_args

    assert (
        saved_call.kwargs["source_filename"]
        == "invoice.pdf"
    )

    saved_result = saved_call.kwargs["result"]

    assert (
        saved_result.document
        == document_result
    )

    assert (
        saved_result.llm
        == llm_result
    )

    assert (
        saved_result.invoice
        == invoice
    )

    pdf_report_service.generate.assert_called_once_with(
        invoice=invoice,
        expense_summary=(
            llm_result.parsed.expense_summary
        ),
        receipt_id=123,
    )

    assert result.receipt_id == 123

    assert result.report_path == Path(
        "reports/receipt_123.pdf"
    )


def test_process_retries_missing_item_numeric_field():
    repository = Mock()
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

    pdf_report_service = Mock(
        spec=PDFReportService
    )

    document_result = make_document_result()

    first_extraction = make_extraction(
        quantity=None
    )

    retry_extraction = make_extraction(
        quantity="1"
    )

    first_llm_result = LLMResult(
        raw_response=(
            '{"quantity":null}'
        ),
        parsed=first_extraction,
        model="test-model",
    )

    retry_llm_result = LLMResult(
        raw_response=(
            '{"quantity":"1"}'
        ),
        parsed=retry_extraction,
        model="test-model",
    )

    invoice = make_invoice()

    document_extractor.extract.return_value = (
        document_result
    )

    llm_service.analyze_invoice.side_effect = [
        first_llm_result,
        retry_llm_result,
    ]

    invoice_mapper.map.side_effect = [
        InvoiceMappingError(
            "Required field is missing: "
            "items[1].quantity"
        ),
        invoice,
    ]

    pdf_report_service.generate.return_value = (
        Path("reports/receipt_123.pdf")
    )

    processor = ReceiptProcessor(
        repository=repository,
        document_extractor=document_extractor,
        llm_service=llm_service,
        invoice_mapper=invoice_mapper,
        pdf_report_service=pdf_report_service,
    )

    result = processor.process(
        "invoice.pdf"
    )

    assert (
        llm_service.analyze_invoice.call_count
        == 2
    )

    assert (
        invoice_mapper.map.call_count
        == 2
    )

    first_llm_call = (
        llm_service
        .analyze_invoice
        .call_args_list[0]
    )

    assert first_llm_call.args == (
        "invoice text",
    )

    second_llm_call = (
        llm_service
        .analyze_invoice
        .call_args_list[1]
    )

    assert second_llm_call.args == (
        "invoice text",
    )

    assert second_llm_call.kwargs[
        "retry_instruction"
    ] == (
        "Required field is missing: "
        "items[1].quantity"
    )

    assert (
        invoice_mapper.map.call_args_list[0].args
        == (first_extraction,)
    )

    assert (
        invoice_mapper.map.call_args_list[1].args
        == (retry_extraction,)
    )

    repository.save.assert_called_once()

    saved_result = (
        repository
        .save
        .call_args
        .kwargs["result"]
    )

    # Important:
    # the successful retry result is persisted,
    # not the failed first extraction.
    assert (
        saved_result.llm
        == retry_llm_result
    )

    assert (
        saved_result.invoice
        == invoice
    )

    pdf_report_service.generate.assert_called_once_with(
        invoice=invoice,
        expense_summary=(
            retry_llm_result
            .parsed
            .expense_summary
        ),
        receipt_id=123,
    )

    assert result.llm == retry_llm_result
    assert result.invoice == invoice
    assert result.receipt_id == 123

    assert result.report_path == Path(
        "reports/receipt_123.pdf"
    )


def test_process_does_not_retry_non_item_error():
    repository = Mock()

    document_extractor = Mock(
        spec=DocumentTextExtractor
    )

    llm_service = Mock(
        spec=LLMService
    )

    invoice_mapper = Mock(
        spec=InvoiceMapper
    )

    pdf_report_service = Mock(
        spec=PDFReportService
    )

    document_result = make_document_result()
    extraction = make_extraction()

    llm_result = LLMResult(
        raw_response="{}",
        parsed=extraction,
        model="test-model",
    )

    document_extractor.extract.return_value = (
        document_result
    )

    llm_service.analyze_invoice.return_value = (
        llm_result
    )

    invoice_mapper.map.side_effect = (
        InvoiceMappingError(
            "Required field is missing: "
            "issuer.identifier"
        )
    )

    processor = ReceiptProcessor(
        repository=repository,
        document_extractor=document_extractor,
        llm_service=llm_service,
        invoice_mapper=invoice_mapper,
        pdf_report_service=pdf_report_service,
    )

    try:
        processor.process(
            "invoice.pdf"
        )

    except InvoiceMappingError:
        pass

    else:
        raise AssertionError(
            "InvoiceMappingError was not raised."
        )

    llm_service.analyze_invoice.assert_called_once_with(
        "invoice text"
    )

    invoice_mapper.map.assert_called_once_with(
        extraction
    )

    repository.save.assert_not_called()

    pdf_report_service.generate.assert_not_called()