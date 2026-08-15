from dataclasses import dataclass
from statistics import median

from app.services.ocr_service import OCRPage, OCRWord


@dataclass(frozen=True, slots=True)
class TextRegion:
    page_number: int
    text: str

    left: int
    top: int
    right: int
    bottom: int

    words: tuple[OCRWord, ...]


class LayoutService:
    def __init__(
        self,
        gap_multiplier: float = 4.0,
        minimum_gap_ratio: float = 0.03,
    ) -> None:
        self.gap_multiplier = gap_multiplier
        self.minimum_gap_ratio = minimum_gap_ratio

    def build_regions(self, page: OCRPage) -> list[TextRegion]:
        line_groups = self._group_words_by_line(page.words)

        threshold = self._calculate_gap_threshold(
            page,
            line_groups,
        )

        regions: list[TextRegion] = []

        for line_words in line_groups:
            regions.extend(
                self._split_line_into_regions(
                    page=page,
                    words=line_words,
                    gap_threshold=threshold,
                )
            )

        return sorted(
            regions,
            key=lambda region: (
                region.top,
                region.left,
            ),
        )

    @staticmethod
    def _group_words_by_line(
        words: tuple[OCRWord, ...],
    ) -> list[list[OCRWord]]:
        grouped: dict[
            tuple[int, int, int],
            list[OCRWord],
        ] = {}

        for word in words:
            key = (
                word.block_number,
                word.paragraph_number,
                word.line_number,
            )

            grouped.setdefault(key, []).append(word)

        lines = []

        for line_words in grouped.values():
            lines.append(
                sorted(
                    line_words,
                    key=lambda word: word.left,
                )
            )

        return lines

    def _calculate_gap_threshold(
        self,
        page: OCRPage,
        lines: list[list[OCRWord]],
    ) -> float:
        gap_ratios: list[float] = []

        for words in lines:
            for previous, current in zip(
                words,
                words[1:],
            ):
                previous_right = (
                    previous.left + previous.width
                )

                gap = current.left - previous_right

                if gap <= 0:
                    continue

                gap_ratios.append(
                    gap / page.width
                )

        if not gap_ratios:
            return self.minimum_gap_ratio

        typical_gap = median(gap_ratios)

        return max(
            self.minimum_gap_ratio,
            typical_gap * self.gap_multiplier,
        )

    def _split_line_into_regions(
        self,
        page: OCRPage,
        words: list[OCRWord],
        gap_threshold: float,
    ) -> list[TextRegion]:
        if not words:
            return []

        word_groups: list[list[OCRWord]] = []
        current_group = [words[0]]

        for previous, current in zip(
            words,
            words[1:],
        ):
            previous_right = (
                previous.left + previous.width
            )

            gap = current.left - previous_right
            gap_ratio = gap / page.width

            if gap_ratio > gap_threshold:
                word_groups.append(current_group)
                current_group = []

            current_group.append(current)

        word_groups.append(current_group)

        return [
            self._create_region(
                page.page_number,
                group,
            )
            for group in word_groups
        ]

    @staticmethod
    def _create_region(
        page_number: int,
        words: list[OCRWord],
    ) -> TextRegion:
        left = min(word.left for word in words)
        top = min(word.top for word in words)

        right = max(
            word.left + word.width
            for word in words
        )

        bottom = max(
            word.top + word.height
            for word in words
        )

        return TextRegion(
            page_number=page_number,
            text=" ".join(
                word.text for word in words
            ),
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            words=tuple(words),
        )
