from typing import Annotated

from fastapi import Depends

from app.db.database import Database
from app.repositories.receipt_repository import ReceiptRepository
from app.services.receipt_processor import ReceiptProcessor


database = Database()


def get_receipt_repository() -> ReceiptRepository:
    return ReceiptRepository(
        session_factory=database.session_factory
    )


def get_receipt_processor(
    repository: Annotated[
        ReceiptRepository,
        Depends(get_receipt_repository),
    ],
) -> ReceiptProcessor:
    return ReceiptProcessor(
        repository=repository
    )