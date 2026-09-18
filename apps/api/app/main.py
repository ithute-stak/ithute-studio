from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.accounting import router as accounting_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.pdf_collaboration import router as pdf_collaboration_router
from app.api.routes.pdf_studio import router as pdf_studio_router
from app.api.routes.rendering import router as rendering_router
from app.api.routes.templates import router as templates_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.5.0",
    description=(
        "Product-neutral document editing, PDF platform services, accounting issuance, "
        "template resolution and backend rendering API."
    ),
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(health_router)
app.include_router(templates_router)
app.include_router(documents_router)
app.include_router(rendering_router)
app.include_router(accounting_router)
app.include_router(pdf_studio_router)
app.include_router(pdf_collaboration_router)
