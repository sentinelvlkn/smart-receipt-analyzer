import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_receipt_repository,
    get_receipt_processor,
)
from app.db.models import ReceiptItemORM, ReceiptORM
from app.main import app
from app.services.receipt_processor import ReceiptProcessor
from app.repositories.receipt_repository import ReceiptRepository
from app.services.invoice_mapper import InvoiceMappingError

@pytest.fixture
def client():
    app.dependency_overrides.clear()

    yield TestClient(app)

    app.dependency_overrides.clear()

def create_receipt() -> ReceiptORM:
    receipt = ReceiptORM(
        id=1,
        invoice_number="INV-001",
        invoice_date=date(2026, 8, 13),
        issuer_name="Seller Ltd",
        issuer_identifier="123456789",
        receiver_name="Customer Ltd",
        receiver_identifier="987654321",
        total_amount=Decimal("1000.00"),
        currency="EUR",
        expense_summary="IT equipment purchase.",
        source_filename="invoice.pdf",
        extraction_method="ocr_layout",
        llm_model="test-model",
        raw_llm_response="{}",
        parsed_llm_result={},
        created_at=datetime(
            2026,
            8,
            13,
            tzinfo=timezone.utc,
        ),
    )

    receipt.items = [
        ReceiptItemORM(
            id=1,
            receipt_id=1,
            position=1,
            description="Laptop",
            corrected_description=None,
            category="IT Equipment",
            quantity=Decimal("1"),
            unit_price=Decimal("1000.00"),
            amount=Decimal("1000.00"),
        )
    ]

    return receipt

def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }

def test_list_receipts():
    repository = Mock()
    repository.list_receipts.return_value = [
        create_receipt()
    ]

    app.dependency_overrides[
        get_receipt_repository
    ] = lambda: repository

    try:
        client = TestClient(app)

        response = client.get("/receipts")

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["invoice_number"] == "INV-001"
        assert data[0]["source_filename"] == "invoice.pdf"

    finally:
        app.dependency_overrides.clear()

def test_get_receipt():
    repository = Mock()
    repository.get_by_id.return_value = (
        create_receipt()
    )

    app.dependency_overrides[
        get_receipt_repository
    ] = lambda: repository

    try:
        client = TestClient(app)

        response = client.get("/receipts/1")

        assert response.status_code == 200
        assert (
            response.json()["invoice_number"]
            == "INV-001"
        )

        repository.get_by_id.assert_called_once_with(
            1
        )

    finally:
        app.dependency_overrides.clear()

def test_get_receipt_returns_404():
    repository = Mock()
    repository.get_by_id.return_value = None

    app.dependency_overrides[
        get_receipt_repository
    ] = lambda: repository

    try:
        client = TestClient(app)

        response = client.get(
            "/receipts/999"
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Receipt not found."
        }

    finally:
        app.dependency_overrides.clear()

def test_process_receipt(client: TestClient):
    processor = Mock(spec=ReceiptProcessor)
    repository = Mock(spec=ReceiptRepository)

    processing_result = Mock()
    processing_result.receipt_id = 1

    processor.process.return_value = processing_result
    repository.get_by_id.return_value = create_receipt()

    app.dependency_overrides[
        get_receipt_processor
    ] = lambda: processor

    app.dependency_overrides[
        get_receipt_repository
    ] = lambda: repository

    response = client.post(
        "/receipts",
        files={
            "file": (
                "invoice.pdf",
                b"%PDF-1.4 fake test content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["invoice_number"] == "INV-001"
    assert data["source_filename"] == "invoice.pdf"

    processor.process.assert_called_once()

    call = processor.process.call_args

    assert call.kwargs[
        "source_filename"
    ] == "invoice.pdf"

    repository.get_by_id.assert_called_once_with(1)

def test_process_receipt_rejects_non_pdf(
    client: TestClient,
):
    processor = Mock(spec=ReceiptProcessor)
    repository = Mock(spec=ReceiptRepository)

    app.dependency_overrides[
        get_receipt_processor
    ] = lambda: processor

    app.dependency_overrides[
        get_receipt_repository
    ] = lambda: repository

    response = client.post(
        "/receipts",
        files={
            "file": (
                "invoice.txt",
                b"not a pdf",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only PDF files are supported."
    }

    processor.process.assert_not_called()

def test_process_receipt_returns_422_for_invalid_invoice(
    client: TestClient,
):
    processor = Mock(spec=ReceiptProcessor)
    repository = Mock(spec=ReceiptRepository)

    processor.process.side_effect = InvoiceMappingError(
        "Required field is missing: issuer.identifier"
    )

    app.dependency_overrides[
        get_receipt_processor
    ] = lambda: processor

    app.dependency_overrides[
        get_receipt_repository
    ] = lambda: repository

    response = client.post(
        "/receipts",
        files={
            "file": (
                "invoice.pdf",
                b"%PDF-1.4 fake test content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Required field is missing: "
            "issuer.identifier"
        )
    }

    processor.process.assert_called_once()
    repository.get_by_id.assert_not_called()