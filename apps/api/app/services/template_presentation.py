from __future__ import annotations

from copy import deepcopy
from typing import Any

Json = dict[str, Any]

BRANDING_PROFILE = "premium-2026-09"
LOGO_PATH = "company.logoUrl"


def brand_template(template: Json) -> Json:
    """Return a built-in template with the universal Studio branding contract."""
    item = deepcopy(template)
    document = item.get("document")
    if not isinstance(document, dict):
        return item

    design = document.setdefault("design", {})
    if isinstance(design, dict):
        design.setdefault("logoUrl", f"{{{{{LOGO_PATH}}}}}")
        design.setdefault("brandMode", "logo-with-monogram-fallback")
        design.setdefault("visualProfile", BRANDING_PROFILE)

    item["branding"] = {
        "profile": BRANDING_PROFILE,
        "logoPath": LOGO_PATH,
        "logoRequired": True,
        "fallback": "company-monogram",
        "appliesTo": ["editor", "preview", "pdf", "docx", "html"],
    }
    return item


def brand_templates(templates: list[Json]) -> list[Json]:
    return [brand_template(item) for item in templates]
