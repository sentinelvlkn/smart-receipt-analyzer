from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.invoice import Invoice, LineItem, Party


def test_valid_invoice():
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date="2026-08-13",
        issuer=Party(
            name="Seller Ltd.",
            identifier="123456789",
        ),
        receiver=Party(
            name="Buyer Ltd.",
            identifier="987654321",
        ),
        items=[
            LineItem(
                description="Milk 1L",
                quantity=Decimal("2"),
                unit_price=Decimal("1.50"),
                amount=Decimal("3.00"),
            )
        ],
        total_amount=Decimal("3.00"),
        currency="EUR",
    )

    assert invoice.invoice_number == "INV-001"
    assert invoice.total_amount == Decimal("3.00")


def test_negative_quantity_is_invalid():
    with pytest.raises(ValidationError):
        LineItem(
            description="Milk 1L",
            quantity=Decimal("-1"),
            unit_price=Decimal("1.50"),
            amount=Decimal("1.50"),
        )


def test_missing_identifier_is_invalid():
    with pytest.raises(ValidationError):
        Party(
            name="Seller Ltd.",
        )
