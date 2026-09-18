from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
JsonObject = dict[str, Any]
class SourceReference(BaseModel):
    provider: str | None = None; entity_type: str | None = Field(default=None, alias="entityType"); entity_id: str | None = Field(default=None, alias="entityId"); external_url: str | None = Field(default=None, alias="externalUrl"); metadata: JsonObject = Field(default_factory=dict)
    model_config = {"populate_by_name": True}
class GenerateDocumentRequest(BaseModel):
    template: JsonObject | None = None; template_id: str | None = Field(default=None, alias="templateId"); data: JsonObject = Field(default_factory=dict); source: SourceReference | None = None; persist: bool = True
    model_config={"populate_by_name":True}
    @model_validator(mode="after")
    def template_required(self):
        if self.template is None and not self.template_id: raise ValueError("Provide template or templateId")
        return self
class ResolveTemplateRequest(BaseModel): document: JsonObject; data: JsonObject = Field(default_factory=dict)
class RenderRequest(BaseModel): document: JsonObject; format: Literal["html", "pdf", "docx"] = "html"
class SaveDocumentRequest(BaseModel): document: JsonObject; expected_version: int | None = Field(default=None, alias="expectedVersion"); model_config={"populate_by_name":True}
class HealthResponse(BaseModel): status: Literal["ok"] = "ok"; service: str = "ithute-document-studio-api"; schema_version: int = 1
