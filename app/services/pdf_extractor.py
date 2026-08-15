from dataclasses import dataclass
from pathlib import Path

import pymupdf

@dataclass(frozen=True, slots=True)
class PDFTextResult:
    text: str
    page_count: int
    character_count: int
    needs_ocr: bool

class PDFExtractor:
    def __init__(self, min_text_characters: int = 50)->None:
        self.min_text_characters = min_text_characters

    def extract(self, pdf_path: str | Path) -> PDFTextResult:
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {path.suffix}")

        try:
            with pymupdf.open(path) as document:
                page_texts = [
                    page.get_text("text", sort=True)
                    for page in document
                ]
            
                page_count = document.page_count

        except Exception as exc:
            raise RuntimeError(
                f"Could not process PDF file: {path}"
            ) from exc

        text = "\n".join(page_texts).strip()

        #Ignore whitespaces when deciding whether the document contains
        #meaningful embedded text
        meaningful_character_count = len(
            "".join(text.split())
        )

        needs_ocr = (
            meaningful_character_count < self.min_text_characters
        )

        return PDFTextResult(
            text = text,
            page_count = page_count,
            character_count = len(text),
            needs_ocr = needs_ocr,
        )
