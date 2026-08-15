from app.services.layout_service import LayoutService
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
