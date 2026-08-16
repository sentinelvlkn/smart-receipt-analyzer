from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.models.invoice import Invoice
from app.services.document_text_extractor import (
    DocumentTextExtractor,
    DocumentTextResult,
)
from app.services.invoice_mapper import InvoiceMapper
from app.services.llm_service import LLMResult, LLMService


class ReceiptRepositoryProtocol(Protocol):
    def save(
        self,
        result: "ReceiptProcessingResult",
        source_filename: str,
    ) -> int:
        ...


@dataclass(frozen=True, slots=True)
class ReceiptProcessingResult:
    document: DocumentTextResult
    llm: LLMResult
    invoice: Invoice
    receipt_id: int | None = None


class ReceiptProcessor:
    def __init__(
        self,
        repository: ReceiptRepositoryProtocol,
        document_extractor: DocumentTextExtractor | None = None,
        llm_service: LLMService | None = None,
        invoice_mapper: InvoiceMapper | None = None,
    ) -> None:
        self.repository = repository
        self.document_extractor = (
            document_extractor or DocumentTextExtractor()
        )
        self.llm_service = (
            llm_service or LLMService()
        )
        self.invoice_mapper = (
            invoice_mapper or InvoiceMapper()
        )

    def process(
        self,
        pdf_path: str | Path,
        source_filename: str | None = None,
    ) -> ReceiptProcessingResult:
        path = Path(pdf_path)

        document = self.document_extractor.extract(path)

        llm_result = self.llm_service.analyze_invoice(
            document.text
        )

        invoice = self.invoice_mapper.map(
            llm_result.parsed
        )

        processing_result = ReceiptProcessingResult(
            document=document,
            llm=llm_result,
            invoice=invoice,
        )

        receipt_id = self.repository.save(
            result=processing_result,
            source_filename=source_filename or path.name,
        )

        return ReceiptProcessingResult(
            document=document,
            llm=llm_result,
            invoice=invoice,
            receipt_id=receipt_id,
        )