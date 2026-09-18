from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PdfBounds:
    x: float
    y: float
    width: float
    height: float


def clamp_bounds(bounds: PdfBounds, page_width: float, page_height: float) -> PdfBounds:
    x = min(max(bounds.x, 0.0), page_width)
    y = min(max(bounds.y, 0.0), page_height)
    width = min(max(bounds.width, 0.0), max(0.0, page_width - x))
    height = min(max(bounds.height, 0.0), max(0.0, page_height - y))
    return PdfBounds(x=x, y=y, width=width, height=height)


def viewport_to_pdf(
    bounds: PdfBounds,
    *,
    viewport_width: float,
    viewport_height: float,
    page_width: float,
    page_height: float,
) -> PdfBounds:
    if viewport_width <= 0 or viewport_height <= 0:
        raise ValueError("Viewport dimensions must be positive")
    result = PdfBounds(
        x=bounds.x * page_width / viewport_width,
        y=bounds.y * page_height / viewport_height,
        width=bounds.width * page_width / viewport_width,
        height=bounds.height * page_height / viewport_height,
    )
    return clamp_bounds(result, page_width, page_height)


def pdf_to_viewport(
    bounds: PdfBounds,
    *,
    viewport_width: float,
    viewport_height: float,
    page_width: float,
    page_height: float,
) -> PdfBounds:
    if page_width <= 0 or page_height <= 0:
        raise ValueError("Page dimensions must be positive")
    return PdfBounds(
        x=bounds.x * viewport_width / page_width,
        y=bounds.y * viewport_height / page_height,
        width=bounds.width * viewport_width / page_width,
        height=bounds.height * viewport_height / page_height,
    )


def rotate_bounds(
    bounds: PdfBounds,
    *,
    page_width: float,
    page_height: float,
    rotation: int,
) -> tuple[PdfBounds, float, float]:
    rotation %= 360
    if rotation == 0:
        return bounds, page_width, page_height
    if rotation == 90:
        return (
            PdfBounds(
                x=page_height - bounds.y - bounds.height,
                y=bounds.x,
                width=bounds.height,
                height=bounds.width,
            ),
            page_height,
            page_width,
        )
    if rotation == 180:
        return (
            PdfBounds(
                x=page_width - bounds.x - bounds.width,
                y=page_height - bounds.y - bounds.height,
                width=bounds.width,
                height=bounds.height,
            ),
            page_width,
            page_height,
        )
    if rotation == 270:
        return (
            PdfBounds(
                x=bounds.y,
                y=page_width - bounds.x - bounds.width,
                width=bounds.height,
                height=bounds.width,
            ),
            page_height,
            page_width,
        )
    raise ValueError("Rotation must be 0, 90, 180, or 270 degrees")
