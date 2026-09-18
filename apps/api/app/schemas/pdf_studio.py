from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

PdfObjectType = Literal[
    "text",
    "cover",
    "rectangle",
    "ellipse",
    "highlight",
    "image",
    "path",
    "link",
    "annotation",
    "form-field",
    "signature",
    "stamp",
    "qr",
    "redaction",
]
PdfProjectStatus = Literal["draft", "review", "approved", "signed", "locked", "archived"]
PdfExportProfile = Literal["standard", "print", "web", "flattened"]
PdfCoordinateSpace = Literal["pdf-points-top-left"]


class PdfDocumentMetadata(BaseModel):
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = Field(default_factory=list)
    language: str | None = None
    custom: dict[str, str] = Field(default_factory=dict)


class PdfEditLayer(BaseModel):
    id: str
    page: int = Field(ge=0)
    type: PdfObjectType
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
    z_index: int = Field(default=0, alias="zIndex")
    visible: bool = True
    locked: bool = False
    asset_id: str | None = Field(default=None, alias="assetId")
    data_url: str | None = Field(default=None, alias="dataUrl")
    erase_original: bool = Field(default=False, alias="eraseOriginal")
    properties: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class PdfProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=240)
    status: PdfProjectStatus | None = None
    metadata: PdfDocumentMetadata | None = None
    default_export_profile: PdfExportProfile | None = Field(
        default=None, alias="defaultExportProfile"
    )
    page_order: list[int] | None = Field(default=None, alias="pageOrder")
    page_rotations: dict[str, int] | None = Field(default=None, alias="pageRotations")
    objects: list[PdfEditLayer] | None = None
    edits: list[PdfEditLayer] | None = None
    expected_version: int | None = Field(default=None, alias="expectedVersion", ge=1)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_rotations(self):
        if self.page_rotations:
            invalid = [
                value
                for value in self.page_rotations.values()
                if value not in {0, 90, 180, 270}
            ]
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


class PdfExportRequest(BaseModel):
    profile: PdfExportProfile | None = None


class PdfRevisionRestoreRequest(BaseModel):
    expected_version: int | None = Field(default=None, alias="expectedVersion", ge=1)

    model_config = {"populate_by_name": True}


class PdfProjectRead(BaseModel):
    id: str
    workspace_id: str | None = Field(alias="workspaceId")
    schema_version: int = Field(alias="schemaVersion")
    name: str
    status: PdfProjectStatus
    original_filename: str = Field(alias="originalFilename")
    source_sha256: str = Field(alias="sourceSha256")
    source_size: int = Field(alias="sourceSize")
    page_count: int = Field(alias="pageCount")
    page_order: list[int] = Field(alias="pageOrder")
    page_metadata: list[PdfPageMetadata] = Field(alias="pageMetadata")
    page_rotations: dict[str, int] = Field(alias="pageRotations")
    objects: list[PdfEditLayer]
    object_index: list[dict] = Field(alias="objectIndex")
    font_catalog: list[dict] = Field(alias="fontCatalog")
    metadata: PdfDocumentMetadata
    security: dict
    import_state: dict = Field(alias="importState")
    default_export_profile: PdfExportProfile = Field(alias="defaultExportProfile")
    version: int
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}
