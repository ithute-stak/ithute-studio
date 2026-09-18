from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from .models import GenerateDocumentRequest, HealthResponse, ResolveTemplateRequest, RenderRequest, SaveDocumentRequest
from .template_engine import generate_document, resolve_doc_json
from .html_renderer import render_html
from .document_renderer import render_pdf, render_docx
from . import storage

@asynccontextmanager
async def lifespan(_: FastAPI):
    storage.init_db(); yield
app = FastAPI(title="Ithute Document Studio API", version="0.1.0", description="Product-neutral document editing, template resolution and rendering API.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse: return HealthResponse()
@app.get("/v1/templates")
def templates(): return storage.list_templates()
@app.post("/v1/templates", status_code=201)
def create_template(payload:dict): return storage.put_template(payload)
@app.get("/v1/templates/{template_id}")
def template(template_id:str):
    item=storage.get_template(template_id)
    if not item: raise HTTPException(404,"Template not found")
    return item
@app.put("/v1/templates/{template_id}")
def update_template(template_id:str,payload:dict): return storage.put_template(payload,template_id)
@app.delete("/v1/templates/{template_id}", status_code=204)
def delete_template(template_id:str):
    if not storage.delete_template(template_id): raise HTTPException(404,"Template not found")
    return Response(status_code=204)

@app.get("/v1/documents")
def documents(): return storage.list_documents()
@app.post("/v1/documents", status_code=201)
def create_document(payload:dict): return storage.create_document(payload)
@app.get("/v1/documents/{document_id}")
def document(document_id:str):
    item=storage.get_document(document_id)
    if not item: raise HTTPException(404,"Document not found")
    return item
@app.put("/v1/documents/{document_id}")
def save_document(document_id:str,request:SaveDocumentRequest):
    try:item=storage.save_document(document_id,request.document,request.expected_version)
    except ValueError: raise HTTPException(409,"Document changed since the supplied version")
    if not item: raise HTTPException(404,"Document not found")
    return item

@app.post("/v1/templates/resolve")
def resolve_template(request: ResolveTemplateRequest):
    doc = request.document.copy()
    for region in ("header", "body", "footer"): doc[region] = resolve_doc_json(doc.get(region), request.data)
    doc["variables"] = request.data; return doc
@app.post("/v1/documents/from-template", status_code=201)
def from_template(request: GenerateDocumentRequest):
    template=request.template or storage.get_template(request.template_id or "")
    if not template: raise HTTPException(404,"Template not found")
    # Template records may wrap the canonical document under `document`.
    template_document=template.get("document") if isinstance(template.get("document"),dict) else template
    source = request.source.model_dump(by_alias=True) if request.source else None
    generated=generate_document(template_document, request.data, source)
    return storage.create_document(generated) if request.persist else generated
@app.post("/v1/render")
def render(request: RenderRequest):
    title=str((request.document.get("properties") or {}).get("title") or "document").replace("/","-")
    if request.format == "html": return Response(render_html(request.document), media_type="text/html", headers={"Content-Disposition":f'inline; filename="{title}.html"'})
    if request.format == "pdf": return Response(render_pdf(request.document), media_type="application/pdf", headers={"Content-Disposition":f'attachment; filename="{title}.pdf"'})
    if request.format == "docx": return Response(render_docx(request.document), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition":f'attachment; filename="{title}.docx"'})
    raise HTTPException(status_code=400, detail="Unsupported format")
