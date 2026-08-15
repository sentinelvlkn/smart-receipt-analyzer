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

@dataclass(frozen=True, slots=True)
class VisualRow:
    page_number: int
    regions: tuple[TextRegion, ...]

    top: int
    bottom: int

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

    def build_rows(
        self,
        regions: list[TextRegion],
    ) -> list[VisualRow]:
        if not regions:
            return []

        sorted_regions = sorted(
            regions,
            key=lambda region: (
                self._vertical_center(region),
                region.left,
            ),
        )

        rows: list[list[TextRegion]] = []

        for region in sorted_regions:
            if not rows:
                rows.append([region])
                continue

            current_row = rows[-1]

            if self._belongs_to_same_row(
                region,
                current_row,
            ):
                current_row.append(region)
            else:
                rows.append([region])

        return [
            self._create_visual_row(row_regions)
            for row_regions in rows
        ]

    @staticmethod
    def _vertical_center(region: TextRegion) -> float:
        return (region.top + region.bottom) / 2


    def _belongs_to_same_row(
        self,
        region: TextRegion,
        row_regions: list[TextRegion],
        ) -> bool:
        row_top = min(
            item.top for item in row_regions
        )

        row_bottom = max(
            item.bottom for item in row_regions
        )

        row_center = (row_top + row_bottom) / 2
        region_center = self._vertical_center(region)

        row_height = row_bottom - row_top
        region_height = region.bottom - region.top

        allowed_distance = max(
            row_height,
            region_height,
        ) * 0.6

        return (
            abs(region_center - row_center)
            <= allowed_distance
        )


    @staticmethod
    def _create_visual_row(
        regions: list[TextRegion],
    ) -> VisualRow:
        ordered_regions = sorted(
            regions,
            key=lambda region: region.left,
        )

        return VisualRow(
            page_number=ordered_regions[0].page_number,
            regions=tuple(ordered_regions),
            top=min(
                region.top
                for region in ordered_regions
            ),
            bottom=max(
                region.bottom
                for region in ordered_regions
            ),
        )