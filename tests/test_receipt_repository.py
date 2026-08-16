from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.invoice import Invoice, LineItem, Party
from app.models.invoice_extraction import (
    ExtractedLineItem,
    ExtractedParty,
    InvoiceExtraction,
)
from app.repositories.receipt_repository import (
    ReceiptRepository,
)

from app.services.document_text_extractor import (
    DocumentTextResult,
)
from app.services.llm_service import LLMResult
from app.services.receipt_processor import (
    ReceiptProcessingResult,
)


def create_test_repository() -> ReceiptRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    return ReceiptRepository(
        session_factory=session_factory
    )


def create_processing_result() -> ReceiptProcessingResult:
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

    document = DocumentTextResult(
        text="invoice text",
        page_count=1,
        character_count=12,
        extraction_method="ocr_layout",
    )

    llm_result = LLMResult(
        raw_response='{"invoice_number":"INV-001"}',
        parsed=extraction,
        model="test-model",
    )

    return ReceiptProcessingResult(
        document=document,
        llm=llm_result,
        invoice=invoice,
    )

def test_saves_receipt_with_items():
    repository = create_test_repository()
    result = create_processing_result()

    receipt_id = repository.save(
        result=result,
        source_filename="invoice.pdf",
    )

    assert isinstance(receipt_id, int)

    receipt = repository.get_by_id(receipt_id)

    assert receipt is not None
    assert receipt.invoice_number == "INV-001"
    assert receipt.source_filename == "invoice.pdf"
    assert len(receipt.items) == 1

def test_list_receipts_returns_saved_receipts():
    repository = create_test_repository()
    result = create_processing_result()

    repository.save(
        result=result,
        source_filename="invoice.pdf",
    )

    receipts = repository.list_receipts()

    assert len(receipts) == 1
    assert receipts[0].invoice_number == "INV-001"