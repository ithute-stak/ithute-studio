import pytest

from app.services.pdf_geometry import (
    PdfBounds,
    pdf_to_viewport,
    rotate_bounds,
    viewport_to_pdf,
)


def test_pdf_viewport_coordinate_round_trip():
    original = PdfBounds(x=25, y=50, width=100, height=40)
    pdf_bounds = viewport_to_pdf(
        original,
        viewport_width=600,
        viewport_height=800,
        page_width=300,
        page_height=400,
    )
    assert pdf_bounds == PdfBounds(x=12.5, y=25, width=50, height=20)
    restored = pdf_to_viewport(
        pdf_bounds,
        viewport_width=600,
        viewport_height=800,
        page_width=300,
        page_height=400,
    )
    assert restored == original


def test_rotation_transform_uses_top_left_coordinate_space():
    bounds = PdfBounds(x=10, y=20, width=30, height=40)
    rotated, width, height = rotate_bounds(
        bounds,
        page_width=300,
        page_height=400,
        rotation=90,
    )
    assert rotated == PdfBounds(x=340, y=10, width=40, height=30)
    assert (width, height) == (400, 300)


def test_rotation_rejects_arbitrary_angle():
    with pytest.raises(ValueError, match="Rotation"):
        rotate_bounds(
            PdfBounds(x=0, y=0, width=1, height=1),
            page_width=10,
            page_height=10,
            rotation=45,
        )
