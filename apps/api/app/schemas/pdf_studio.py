from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

PdfLayerType = Literal[
    "text",
    "cover",
    "rectangle",
    "ellipse",
    "highlight",
    "image",
]


class PdfEditLayer(BaseModel):
    id: str
    page: int = Field(ge=0)
    type: PdfLayerType
    x: float = 0
    y: float = 0
    width: float = Field(default=120, ge=0)
    height: float = Field(default=28, ge=0)
    text: str | None = None
    font_size: float = Field(default=12, alias="fontSize", ge=4, le=240)
    font_family: str = Field(default="Helvetica", alias="fontFamily")
    color: str = "#111111"
    fill: str = "#ffffff"
    stroke: str = "#111111"
    stroke_width: float = Field(default=1, alias="strokeWidth", ge=0, le=50)
    opacity: float = Field(default=1, ge=0, le=1)
    rotation: float = 0
    data_url: str | None = Field(default=None, alias="dataUrl")
    erase_original: bool = Field(default=False, alias="eraseOriginal")

    model_config = {"populate_by_name": True}


class PdfProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=240)
    page_order: list[int] | None = Field(default=None, alias="pageOrder")
    page_rotations: dict[str, int] | None = Field(default=None, alias="pageRotations")
    edits: list[PdfEditLayer] | None = None
    expected_version: int | None = Field(default=None, alias="expectedVersion", ge=1)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_rotations(self):
        if self.page_rotations:
            invalid = [value for value in self.page_rotations.values() if value not in {0, 90, 180, 270}]
            if invalid:
                raise ValueError("page rotations must be 0, 90, 180, or 270 degrees")
        return self


class PdfTextRun(BaseModel):
    text: str
    x: float
    y: float
    width: float
    height: float


class PdfPageMetadata(BaseModel):
    index: int
    width: float
    height: float


class PdfProjectRead(BaseModel):
    id: str
    name: str
    original_filename: str = Field(alias="originalFilename")
    page_count: int = Field(alias="pageCount")
    page_order: list[int] = Field(alias="pageOrder")
    page_metadata: list[PdfPageMetadata] = Field(alias="pageMetadata")
    page_rotations: dict[str, int] = Field(alias="pageRotations")
    edits: list[PdfEditLayer]
    version: int
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}
