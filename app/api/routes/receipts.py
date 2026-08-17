import logging
import shutil
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from app.api.dependencies import (
    get_receipt_processor,
    get_receipt_repository,
)
from app.api.schemas import (
    ReceiptResponse,
    receipt_to_response,
)
from app.repositories.receipt_repository import ReceiptRepository
from app.services.invoice_mapper import InvoiceMappingError
from app.services.receipt_processor import ReceiptProcessor


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/receipts",
    tags=["receipts"],
)


@router.post(
    "",
    response_model=ReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def process_receipt(
    file: Annotated[UploadFile, File()],
    processor: Annotated[
        ReceiptProcessor,
        Depends(get_receipt_processor),
    ],
    repository: Annotated[
        ReceiptRepository,
        Depends(get_receipt_repository),
    ],
) -> ReceiptResponse:
    original_filename = Path(
        file.filename or "invoice.pdf"
    ).name

    if Path(original_filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    temporary_path = (
        uploads_dir
        / f"{uuid4().hex}_{original_filename}"
    )

    try:
        with temporary_path.open("wb") as destination:
            shutil.copyfileobj(
                file.file,
                destination,
            )

        result = processor.process(
            temporary_path,
            source_filename=original_filename,
        )

        if result.receipt_id is None:
            raise RuntimeError(
                "Receipt was processed without a database ID."
            )

        receipt = repository.get_by_id(
            result.receipt_id
        )

        if receipt is None:
            raise RuntimeError(
                "Saved receipt could not be loaded."
            )

        return receipt_to_response(receipt)

    except InvoiceMappingError as exc:
        logger.warning(
            "Invoice validation failed for file %s: %s",
            original_filename,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Receipt processing failed for file: %s",
            original_filename,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Receipt processing failed.",
        ) from exc

    finally:
        temporary_path.unlink(
            missing_ok=True
        )


@router.get(
    "",
    response_model=list[ReceiptResponse],
)
def list_receipts(
    repository: Annotated[
        ReceiptRepository,
        Depends(get_receipt_repository),
    ],
    limit: int = 100,
    offset: int = 0,
) -> list[ReceiptResponse]:
    receipts = repository.list_receipts(
        limit=limit,
        offset=offset,
    )

    return [
        receipt_to_response(receipt)
        for receipt in receipts
    ]


@router.get(
    "/{receipt_id}",
    response_model=ReceiptResponse,
)
def get_receipt(
    receipt_id: int,
    repository: Annotated[
        ReceiptRepository,
        Depends(get_receipt_repository),
    ],
) -> ReceiptResponse:
    receipt = repository.get_by_id(
        receipt_id
    )

    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found.",
        )

    return receipt_to_response(receipt)