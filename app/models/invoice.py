from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

class Party(BaseModel):
    name: str
    identifier: str

class LineItem(BaseModel):
    description: str

    corrected_description: str | None = None
    category: str | None = None

    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    amount: Decimal = Field(ge=0)

class Invoice(BaseModel):
    invoice_number: str
    invoice_date: date

    issuer: Party
    receiver: Party

    items: list[LineItem] = Field(min_length=1)

    total_amount: Decimal = Field(ge=0)
    currency: str
