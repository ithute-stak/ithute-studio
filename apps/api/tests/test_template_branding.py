from app.services.accounting_templates import list_accounting_templates
from app.services.business_document_templates import list_business_document_templates
from app.services.institution_contract_templates import list_institution_contract_templates
from app.services.lesotho_template_packs import list_lesotho_templates
from app.services.template_presentation import BRANDING_PROFILE, LOGO_PATH, brand_templates


def test_every_builtin_template_has_universal_logo_contract() -> None:
    templates = brand_templates(
        list_accounting_templates()
        + list_lesotho_templates()
        + list_institution_contract_templates()
        + list_business_document_templates()
    )

    assert len(templates) == 1940
    assert len({item["id"] for item in templates}) == 1940

    for template in templates:
        branding = template["branding"]
        design = template["document"]["design"]

        assert branding["profile"] == BRANDING_PROFILE
        assert branding["logoPath"] == LOGO_PATH
        assert branding["logoRequired"] is True
        assert branding["fallback"] == "company-monogram"
        assert set(branding["appliesTo"]) == {"editor", "preview", "pdf", "docx", "html"}
        assert design["logoUrl"] == "{{company.logoUrl}}"
        assert design["brandMode"] == "logo-with-monogram-fallback"
        assert design["visualProfile"] == BRANDING_PROFILE
