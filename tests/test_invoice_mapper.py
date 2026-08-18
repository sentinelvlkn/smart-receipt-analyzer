from decimal import Decimal

import pytest

from app.models.invoice_extraction import (
    ExtractedLineItem,
    ExtractedParty,
    InvoiceExtraction,
)
from app.services.invoice_mapper import (
    InvoiceMapper,
    InvoiceMappingError,
)


def make_valid_extraction() -> InvoiceExtraction:
    return InvoiceExtraction(
        invoice_number="NS-26/0817-A",
        invoice_date="2026-08-13",
        issuer=ExtractedParty(
            name="Orion Trade & Services Ltd",
            identifier="118294763",
        ),
        receiver=ExtractedParty(
            name="Vertex Solutions EOOD",
            identifier="207381945",
        ),
        items=[
            ExtractedLineItem(
                description="Notebook АБ, ruled",
                corrected_description="Notebook A5, ruled",
                category="Office supplies",
                quantity="10",
                unit_price="2.35",
                amount="23.50",
            )
        ],
        total_amount="274.98",
        currency="EUR",
        expense_summary=(
            "Office supplies. Invoice total EUR 274.98."
        ),
    )


def test_maps_valid_extraction_to_invoice():
    mapper = InvoiceMapper()

    extraction = make_valid_extraction()

    invoice = mapper.map(extraction)

    assert invoice.invoice_number == "NS-26/0817-A"
    assert invoice.invoice_date.isoformat() == "2026-08-13"

    assert invoice.issuer.name == "Orion Trade & Services Ltd"
    assert invoice.issuer.identifier == "118294763"

    assert invoice.receiver.name == "Vertex Solutions EOOD"
    assert invoice.receiver.identifier == "207381945"

    assert len(invoice.items) == 1

    item = invoice.items[0]

    assert item.description == "Notebook АБ, ruled"
    assert item.corrected_description == "Notebook A5, ruled"
    assert item.category == "Office supplies"

    assert item.quantity == Decimal("10")
    assert item.unit_price == Decimal("2.35")
    assert item.amount == Decimal("23.50")

    assert invoice.total_amount == Decimal("274.98")
    assert invoice.currency == "EUR"


def test_missing_required_field_raises_mapping_error():
    mapper = InvoiceMapper()

    extraction = make_valid_extraction()
    extraction.invoice_number = None

    with pytest.raises(
        InvoiceMappingError,
        match="invoice_number",
    ):
        mapper.map(extraction)



def test_invalid_decimal_raises_mapping_error():
    mapper = InvoiceMapper()

    extraction = make_valid_extraction()
    extraction.items[0].quantity = "ten"

    with pytest.raises(
        InvoiceMappingError,
        match=r"items\[1\]\.quantity",
    ):
        mapper.map(extraction)


def test_invalid_date_raises_mapping_error():
    mapper = InvoiceMapper()

    extraction = make_valid_extraction()
    extraction.invoice_date = "13-Aug-2026"

    with pytest.raises(
        InvoiceMappingError,
        match="Invalid invoice date",
    ):
        mapper.map(extraction)