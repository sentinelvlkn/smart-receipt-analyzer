from app.services.layout_service import LayoutService, TextRegion
from app.services.ocr_service import OCRPage, OCRWord


def make_word(
    text: str,
    left: int,
    width: int,
) -> OCRWord:
    return OCRWord(
        text=text,
        confidence=95.0,
        block_number=1,
        paragraph_number=1,
        line_number=1,
        word_number=1,
        left=left,
        top=100,
        width=width,
        height=30,
    )


def test_large_horizontal_gaps_create_separate_regions():
    page = OCRPage(
        page_number=1,
        width=2480,
        height=3508,
        words=(
            make_word("Black", 190, 115),
            make_word("Mesa", 325, 110),
            make_word("Research", 455, 180),

            make_word("гр.", 850, 40),
            make_word("София", 910, 100),

            make_word("Велика", 2000, 145),
            make_word("Банка", 2165, 120),
        ),
    )

    service = LayoutService()

    regions = service.build_regions(page)

    texts = [
        region.text
        for region in regions
    ]

    assert "Black Mesa Research" in texts
    assert "гр. София" in texts
    assert "Велика Банка" in texts

from app.services.layout_service import (
    LayoutService,
    TextRegion,
)


def test_regions_with_small_vertical_offset_form_same_row():
    regions = [
        TextRegion(
            page_number=1,
            text="USB-H7 USB-C Hub",
            left=100,
            top=500,
            right=600,
            bottom=530,
            words=(),
        ),
        TextRegion(
            page_number=1,
            text="2",
            left=1000,
            top=500,
            right=1020,
            bottom=530,
            words=(),
        ),
        TextRegion(
            page_number=1,
            text="pcs",
            left=1100,
            top=505,
            right=1160,
            bottom=535,
            words=(),
        ),
        TextRegion(
            page_number=1,
            text="€18.90",
            left=1300,
            top=500,
            right=1400,
            bottom=530,
            words=(),
        ),
    ]

    service = LayoutService()

    rows = service.build_rows(regions)

    assert len(rows) == 1

    texts = [
        region.text
        for region in rows[0].regions
    ]

    assert texts == [
        "USB-H7 USB-C Hub",
        "2",
        "pcs",
        "€18.90",
    ]

def test_regions_far_apart_vertically_form_different_rows():
    regions = [
        TextRegion(
            page_number=1,
            text="Laptop",
            left=100,
            top=500,
            right=300,
            bottom=530,
            words=(),
        ),
        TextRegion(
            page_number=1,
            text="Printer",
            left=100,
            top=570,
            right=300,
            bottom=600,
            words=(),
        ),
    ]

    service = LayoutService()

    rows = service.build_rows(regions)

    assert len(rows) == 2