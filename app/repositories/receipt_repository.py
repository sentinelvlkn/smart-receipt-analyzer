from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import ReceiptItemORM, ReceiptORM
from app.services.receipt_processor import ReceiptProcessingResult


class ReceiptRepository:
    def __init__(
        self,
        session_factory: Callable[[], Session],
    ) -> None:
        self.session_factory = session_factory

    def save(
        self,
        result: ReceiptProcessingResult,
        source_filename: str,
    ) -> int:
        invoice = result.invoice
        llm_result = result.llm
        document = result.document

        receipt = ReceiptORM(
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            issuer_name=invoice.issuer.name,
            issuer_identifier=invoice.issuer.identifier,
            receiver_name=invoice.receiver.name,
            receiver_identifier=invoice.receiver.identifier,
            total_amount=invoice.total_amount,
            currency=invoice.currency,
            expense_summary=(
                llm_result.parsed.expense_summary
            ),
            source_filename=source_filename,
            extraction_method=(
                document.extraction_method
            ),
            llm_model=llm_result.model,
            raw_llm_response=(
                llm_result.raw_response
            ),
            parsed_llm_result=(
                llm_result.parsed.model_dump(
                    mode="json"
                )
            ),
        )

        receipt.items = [
            ReceiptItemORM(
                position=position,
                description=item.description,
                corrected_description=(
                    item.corrected_description
                ),
                category=item.category,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
            )
            for position, item in enumerate(
                invoice.items,
                start=1,
            )
        ]

        with self.session_factory() as session:
            with session.begin():
                session.add(receipt)
                session.flush()

                if receipt.id is None:
                    raise RuntimeError(
                        "Receipt was saved without an ID."
                    )

                receipt_id = receipt.id

        return receipt_id

    def get_by_id(
        self,
        receipt_id: int,
    ) -> ReceiptORM | None:
        statement = (
            select(ReceiptORM)
            .options(
                selectinload(ReceiptORM.items)
            )
            .where(
                ReceiptORM.id == receipt_id
            )
        )

        with self.session_factory() as session:
            return session.scalar(statement)

    def list_receipts(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReceiptORM]:
        statement = (
            select(ReceiptORM)
            .options(
                selectinload(ReceiptORM.items)
            )
            .order_by(
                ReceiptORM.created_at.desc(),
                ReceiptORM.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        with self.session_factory() as session:
            return list(
                session.scalars(statement)
            )