from pydantic import BaseModel


class ExtractedParty(BaseModel):
    name: str | None
    identifier: str | None


class ExtractedLineItem(BaseModel):
    description: str
    corrected_description: str | None
    category: str

    quantity: str | None
    unit_price: str | None
    amount: str | None


class InvoiceExtraction(BaseModel):
    invoice_number: str | None
    invoice_date: str | None

    issuer: ExtractedParty
    receiver: ExtractedParty

    items: list[ExtractedLineItem]

    total_amount: str | None
    currency: str | None

    expense_summary: str