from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.db.models import ReceiptORM


class PartyResponse(BaseModel):
    name: str
    identifier: str


class ReceiptItemResponse(BaseModel):
    position: int
    description: str
    corrected_description: str | None
    category: str | None

    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class ReceiptResponse(BaseModel):
    id: int

    invoice_number: str
    invoice_date: date

    issuer: PartyResponse
    receiver: PartyResponse

    items: list[ReceiptItemResponse]

    total_amount: Decimal
    currency: str

    expense_summary: str

    source_filename: str
    extraction_method: str
    llm_model: str

    created_at: datetime


def receipt_to_response(
    receipt: ReceiptORM,
) -> ReceiptResponse:
    return ReceiptResponse(
        id=receipt.id,
        invoice_number=receipt.invoice_number,
        invoice_date=receipt.invoice_date,
        issuer=PartyResponse(
            name=receipt.issuer_name,
            identifier=receipt.issuer_identifier,
        ),
        receiver=PartyResponse(
            name=receipt.receiver_name,
            identifier=receipt.receiver_identifier,
        ),
        items=[
            ReceiptItemResponse(
                position=item.position,
                description=item.description,
                corrected_description=(
                    item.corrected_description
                ),
                category=item.category,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
            )
            for item in receipt.items
        ],
        total_amount=receipt.total_amount,
        currency=receipt.currency,
        expense_summary=receipt.expense_summary,
        source_filename=receipt.source_filename,
        extraction_method=receipt.extraction_method,
        llm_model=receipt.llm_model,
        created_at=receipt.created_at,
    )