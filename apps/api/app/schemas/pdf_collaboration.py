from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

PdfPrincipalType = Literal["user", "service"]
PdfProjectRole = Literal["owner", "editor", "reviewer", "viewer"]


class PdfAccessGrantCreate(BaseModel):
    principal_type: PdfPrincipalType = Field(alias="principalType")
    principal_id: str = Field(alias="principalId", min_length=1, max_length=240)
    role: PdfProjectRole

    model_config = {"populate_by_name": True}


class PdfWebhookCreate(BaseModel):
    endpoint: HttpUrl
    events: list[str] = Field(default_factory=lambda: ["pdf.*"], min_length=1)

    @field_validator("events")
    @classmethod
    def validate_events(cls, values: list[str]) -> list[str]:
        normalized = []
        for value in values:
            event = value.strip()
            if event != "pdf.*" and not event.startswith("pdf."):
                raise ValueError("webhook events must be pdf.* or begin with pdf.")
            if event not in normalized:
                normalized.append(event)
        return normalized
