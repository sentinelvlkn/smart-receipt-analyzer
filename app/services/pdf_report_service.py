from collections import defaultdict
from decimal import Decimal
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.invoice import Invoice


class PDFReportService:
    def __init__(
        self,
        output_dir: str | Path = "reports",
    ) -> None:
        self.output_dir = Path(output_dir)

        regular_font, bold_font = self._find_fonts()

        pdfmetrics.registerFont(
            TTFont(
                "ReceiptFont",
                str(regular_font),
            )
        )

        pdfmetrics.registerFont(
            TTFont(
                "ReceiptFontBold",
                str(bold_font),
            )
        )

    def generate(
        self,
        invoice: Invoice,
        expense_summary: str,
        receipt_id: int,
    ) -> Path:
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            self.output_dir
            / f"receipt_{receipt_id}.pdf"
        )

        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReceiptTitle",
            parent=styles["Title"],
            fontName="ReceiptFontBold",
            fontSize=18,
            leading=22,
        )

        heading_style = ParagraphStyle(
            "ReceiptHeading",
            parent=styles["Heading2"],
            fontName="ReceiptFontBold",
            fontSize=12,
            leading=15,
        )

        normal_style = ParagraphStyle(
            "ReceiptNormal",
            parent=styles["Normal"],
            fontName="ReceiptFont",
            fontSize=9,
            leading=12,
        )

        grand_total_style = ParagraphStyle(
            "GrandTotal",
            parent=normal_style,
            fontName="ReceiptFontBold",
        )

        story: list[Flowable] = [
            Paragraph(
                "Smart Receipt Analyzer Report",
                title_style,
            ),
            Spacer(1, 6 * mm),
        ]

        metadata = [
            (
                "Invoice #",
                invoice.invoice_number,
            ),
            (
                "Date",
                invoice.invoice_date.isoformat(),
            ),
            (
                "Vendor",
                invoice.issuer.name,
            ),
            (
                "Vendor ID",
                invoice.issuer.identifier,
            ),
            (
                "Receiver",
                invoice.receiver.name,
            ),
            (
                "Receiver ID",
                invoice.receiver.identifier,
            ),
            (
                "Currency",
                invoice.currency,
            ),
        ]

        metadata_rows: list[list[Flowable]] = [
            [
                Paragraph(
                    escape(str(label)),
                    normal_style,
                ),
                Paragraph(
                    escape(str(value)),
                    normal_style,
                ),
            ]
            for label, value in metadata
        ]

        metadata_table = Table(
            metadata_rows,
            colWidths=[
                35 * mm,
                140 * mm,
            ],
        )

        metadata_table.setStyle(
            TableStyle(
                [
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "ReceiptFontBold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(metadata_table)
        story.append(
            Spacer(1, 6 * mm)
        )

        story.append(
            Paragraph(
                "Expense Summary",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                escape(expense_summary),
                normal_style,
            )
        )

        story.append(
            Spacer(1, 6 * mm)
        )

        story.append(
            Paragraph(
                "Items",
                heading_style,
            )
        )

        item_rows: list[
            list[str | Flowable]
        ] = [
            [
                "Description",
                "Category",
                "Qty",
                "Unit price",
                "Amount",
            ]
        ]

        for item in invoice.items:
            description = (
                item.corrected_description
                or item.description
            )

            category = (
                item.category
                or "Uncategorized"
            )

            item_rows.append(
                [
                    Paragraph(
                        escape(description),
                        normal_style,
                    ),
                    Paragraph(
                        escape(category),
                        normal_style,
                    ),
                    str(item.quantity),
                    f"{item.unit_price:.2f}",
                    f"{item.amount:.2f}",
                ]
            )

        items_table = Table(
            item_rows,
            colWidths=[
                63 * mm,
                38 * mm,
                18 * mm,
                28 * mm,
                28 * mm,
            ],
            repeatRows=1,
        )

        items_table.setStyle(
            TableStyle(
                [
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "ReceiptFontBold",
                    ),
                    (
                        "FONTNAME",
                        (0, 1),
                        (-1, -1),
                        "ReceiptFont",
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "ALIGN",
                        (2, 1),
                        (-1, -1),
                        "RIGHT",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(items_table)
        story.append(
            Spacer(1, 6 * mm)
        )

        category_totals: dict[
            str,
            Decimal,
        ] = defaultdict(Decimal)

        for item in invoice.items:
            category = (
                item.category
                or "Uncategorized"
            )

            category_totals[category] += (
                item.amount
            )

        totals_rows: list[
            list[str | Flowable]
        ] = [
            [
                "Category",
                "Amount",
            ]
        ]

        for category, amount in sorted(
            category_totals.items()
        ):
            totals_rows.append(
                [
                    Paragraph(
                        escape(category),
                        normal_style,
                    ),
                    (
                        f"{amount:.2f} "
                        f"{invoice.currency}"
                    ),
                ]
            )

        totals_rows.append(
            [
                Paragraph(
                    "Invoice Grand Total",
                    grand_total_style,
                ),
                (
                    f"{invoice.total_amount:.2f} "
                    f"{invoice.currency}"
                ),
            ]
        )

        totals_table = Table(
            totals_rows,
            colWidths=[
                120 * mm,
                55 * mm,
            ],
        )

        totals_table.setStyle(
            TableStyle(
                [
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "ReceiptFontBold",
                    ),
                    (
                        "FONTNAME",
                        (0, 1),
                        (-1, -2),
                        "ReceiptFont",
                    ),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "ReceiptFontBold",
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "RIGHT",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        category_totals_section = KeepTogether(
            [
                Paragraph(
                    "Item Totals by Category",
                    heading_style,
                ),
                Spacer(1, 2 * mm),
                totals_table,
            ]
        )

        story.append(category_totals_section)

        document.build(story)

        return output_path

    @staticmethod
    def _find_fonts() -> tuple[Path, Path]:
        candidates = [
            (
                Path(
                    "C:/Windows/Fonts/arial.ttf"
                ),
                Path(
                    "C:/Windows/Fonts/arialbd.ttf"
                ),
            ),
            (
                Path(
                    "/usr/share/fonts/truetype/"
                    "dejavu/DejaVuSans.ttf"
                ),
                Path(
                    "/usr/share/fonts/truetype/"
                    "dejavu/DejaVuSans-Bold.ttf"
                ),
            ),
        ]

        for regular, bold in candidates:
            if (
                regular.exists()
                and bold.exists()
            ):
                return regular, bold

        raise RuntimeError(
            "No Unicode TrueType font was found."
        )