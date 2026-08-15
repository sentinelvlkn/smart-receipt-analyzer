from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.services.layout_formatter import LayoutFormatter
from app.services.layout_service import LayoutService
from app.services.ocr_service import OCRService
from app.services.pdf_extractor import PDFExtractor


ExtractionMethod = Literal[
    "embedded_text",
    "ocr_layout",
]


@dataclass(frozen=True, slots=True)
class DocumentTextResult:
    text: str
    page_count: int
    character_count: int
    extraction_method: ExtractionMethod


class DocumentTextExtractor:
    def __init__(
        self,
        pdf_extractor: PDFExtractor | None = None,
        ocr_service: OCRService | None = None,
        layout_service: LayoutService | None = None,
        layout_formatter: LayoutFormatter | None = None,
    ) -> None:
        self.pdf_extractor = pdf_extractor or PDFExtractor()
        self.ocr_service = ocr_service or OCRService()
        self.layout_service = layout_service or LayoutService()
        self.layout_formatter = layout_formatter or LayoutFormatter()

    def extract(
        self,
        pdf_path: str | Path,
    ) -> DocumentTextResult:
        pdf_result = self.pdf_extractor.extract(pdf_path)

        if not pdf_result.needs_ocr:
            return DocumentTextResult(
                text=pdf_result.text,
                page_count=pdf_result.page_count,
                character_count=pdf_result.character_count,
                extraction_method="embedded_text",
            )

        ocr_result = self.ocr_service.extract_text(pdf_path)

        formatted_pages: list[str] = []

        for page in ocr_result.pages:
            regions = self.layout_service.build_regions(page)
            rows = self.layout_service.build_rows(regions)

            formatted_pages.append(
                self.layout_formatter.format_page(
                    page,
                    rows,
                )
            )

        text = "\n\n".join(formatted_pages).strip()

        return DocumentTextResult(
            text=text,
            page_count=ocr_result.page_count,
            character_count=len(text),
            extraction_method="ocr_layout",
        )