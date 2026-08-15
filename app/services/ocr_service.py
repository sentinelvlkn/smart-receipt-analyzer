from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
from pytesseract import Output


@dataclass(frozen=True, slots=True)
class OCRWord:
    text: str
    confidence: float

    block_number: int
    paragraph_number: int
    line_number: int
    word_number: int

    left: int
    top: int
    width: int
    height: int

@dataclass(frozen=True, slots=True)
class OCRPage:
    page_number: int
    width: int
    height: int
    words: tuple[OCRWord, ...]

@dataclass(frozen=True, slots=True)
class OCRResult:
    text: str
    pages: tuple[OCRPage, ...]

    page_count: int
    character_count: int
    languages: str


class OCRService:
    def __init__(
        self,
        languages: str = "bul+eng",
        dpi: int = 300,
    ) -> None:
        self.languages = languages
        self.dpi = dpi

    def extract_text(self, pdf_path: str | Path) -> OCRResult:
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {path.suffix}")

        pages: list[OCRPage] = []
        page_texts: list[str] = []

        try:
            with pymupdf.open(path) as document:
                page_count = document.page_count

                for page_index, page in enumerate(document):
                    pixmap = page.get_pixmap(
                        dpi=self.dpi,
                        alpha=False,
                    )

                    image_bytes = pixmap.tobytes("png")

                    with Image.open(BytesIO(image_bytes)) as image:
                        page_width, page_height = image.size

                        data = pytesseract.image_to_data(
                            image,
                            lang=self.languages,
                            output_type=Output.DICT,
                        )

                    page_words: list[OCRWord] = []

                    for index, raw_text in enumerate(data["text"]):
                        text = raw_text.strip()

                        if not text:
                            continue

                        confidence = float(data["conf"][index])

                        word = OCRWord(
                            text=text,
                            confidence=confidence,

                            block_number=int(
                                data["block_num"][index]
                            ),
                            paragraph_number=int(
                                data["par_num"][index]
                            ),
                            line_number=int(
                                data["line_num"][index]
                            ),
                            word_number=int(
                                data["word_num"][index]
                            ),

                            left=int(data["left"][index]),
                            top=int(data["top"][index]),
                            width=int(data["width"][index]),
                            height=int(data["height"][index]),
                        )

                        page_words.append(word)

                    pages.append(
                        OCRPage(
                            page_number=page_index + 1,
                            width=page_width,
                            height=page_height,
                            words=tuple(page_words),
                        )
                    )

                    page_texts.append(
                        self._build_plain_text(page_words)
                    )

        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Tesseract OCR is not installed "
                "or is not available in PATH."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                f"OCR processing failed for PDF: {path}"
            ) from exc

        combined_text = "\n\n".join(page_texts).strip()

        return OCRResult(
            text=combined_text,
            pages=tuple(pages),
            page_count=page_count,
            character_count=len(combined_text),
            languages=self.languages,
        ) 

    @staticmethod
    def _build_plain_text(words: list[OCRWord]) -> str:
        if not words:
            return ""

        lines: list[str] = []
        current_line_key: tuple[int, int, int] | None = None
        current_words: list[str] = []

        for word in words:
            line_key = (
                word.block_number,
                word.paragraph_number,
                word.line_number,
            )

            if current_line_key is not None and line_key != current_line_key:
                lines.append(" ".join(current_words))
                current_words = []

            current_line_key = line_key
            current_words.append(word.text)

        if current_words:
            lines.append(" ".join(current_words))

        return "\n".join(lines)
