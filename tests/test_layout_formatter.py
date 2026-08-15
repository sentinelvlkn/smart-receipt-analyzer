from app.services.layout_formatter import LayoutFormatter
from app.services.layout_service import TextRegion, VisualRow
from app.services.ocr_service import OCRPage


def test_formats_rows_with_relative_positions():
    page = OCRPage(
        page_number=1,
        width=1000,
        height=1400,
        words=(),
    )

    row = VisualRow(
        page_number=1,
        regions=(
            TextRegion(
                page_number=1,
                text="SELLER",
                left=50,
                top=100,
                right=200,
                bottom=130,
                words=(),
            ),
            TextRegion(
                page_number=1,
                text="CUSTOMER",
                left=500,
                top=100,
                right=700,
                bottom=130,
                words=(),
            ),
        ),
        top=100,
        bottom=130,
    )

    formatter = LayoutFormatter()

    result = formatter.format_page(
        page,
        [row],
    )

    assert "PAGE 1" in result
    assert "ROW 1:" in result
    assert "[x=5.0%] SELLER" in result
    assert "[x=50.0%] CUSTOMER" in result