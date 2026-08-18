from datetime import date
from decimal import Decimal, InvalidOperation

from app.models.invoice import Invoice, LineItem, Party
from app.models.invoice_extraction import (
    ExtractedLineItem,
    InvoiceExtraction,
)


class InvoiceMappingError(ValueError):
    pass


class InvoiceMapper:
    def map(
        self,
        extraction: InvoiceExtraction,
    ) -> Invoice:
        return Invoice(
            invoice_number=self._required(
                extraction.invoice_number,
                "invoice_number",
            ),
            invoice_date=self._parse_date(
                extraction.invoice_date,
            ),
            issuer=Party(
                name=self._required(
                    extraction.issuer.name,
                    "issuer.name",
                ),
                identifier=self._required(
                    extraction.issuer.identifier,
                    "issuer.identifier",
                ),
            ),
            receiver=Party(
                name=self._required(
                    extraction.receiver.name,
                    "receiver.name",
                ),
                identifier=self._required(
                    extraction.receiver.identifier,
                    "receiver.identifier",
                ),
            ),
            items=[
                self._map_item(
                    item,
                    index=index,
                )
                for index, item in enumerate(
                    extraction.items,
                    start=1,
                )
            ],
            total_amount=self._parse_decimal(
                extraction.total_amount,
                "total_amount",
            ),
            currency=self._required(
                extraction.currency,
                "currency",
            ),
        )

    def _map_item(
        self,
        item: ExtractedLineItem,
        index: int,
    ) -> LineItem:
        return LineItem(
            description=item.description,
            corrected_description=(
                item.corrected_description
            ),
            category=item.category,
            quantity=self._parse_decimal(
                item.quantity,
                f"items[{index}].quantity",
            ),
            unit_price=self._parse_decimal(
                item.unit_price,
                f"items[{index}].unit_price",
            ),
            amount=self._parse_decimal(
                item.amount,
                f"items[{index}].amount",
            ),
        )

    @staticmethod
    def _required(
        value: str | None,
        field_name: str,
    ) -> str:
        if value is None or not value.strip():
            raise InvoiceMappingError(
                f"Required field is missing: {field_name}"
            )

        return value.strip()

    @staticmethod
    def _parse_date(
        value: str | None,
    ) -> date:
        if value is None:
            raise InvoiceMappingError(
                "Required field is missing: invoice_date"
            )

        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise InvoiceMappingError(
                f"Invalid invoice date: {value}"
            ) from exc

    @staticmethod
    def _parse_decimal(
        value: str | None,
        field_name: str,
    ) -> Decimal:
        if value is None:
            raise InvoiceMappingError(
                f"Required field is missing: {field_name}"
            )

        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise InvoiceMappingError(
                f"Invalid decimal value for "
                f"{field_name}: {value}"
            ) from exc