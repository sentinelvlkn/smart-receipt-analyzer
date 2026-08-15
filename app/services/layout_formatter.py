from app.services.layout_service import VisualRow
from app.services.ocr_service import OCRPage


class LayoutFormatter:
    def format_page(
        self,
        page: OCRPage,
        rows: list[VisualRow],
    ) -> str:
        lines = [
            f"PAGE {page.page_number}",
            "",
        ]

        for row_index, row in enumerate(rows, start=1):
            lines.append(f"ROW {row_index}:")

            for region in row.regions:
                relative_x = region.left / page.width

                lines.append(
                    f"[x={relative_x:.1%}] {region.text}"
                )

            lines.append("")

        return "\n".join(lines).strip()