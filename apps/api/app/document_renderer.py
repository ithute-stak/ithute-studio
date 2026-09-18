from __future__ import annotations
import base64, io, re
from html import escape
from typing import Any
from urllib.parse import unquote

from docx import Document as DocxDocument
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as PdfImage, PageBreak as PdfPageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)
import qrcode

Json = dict[str, Any]


def _attrs(node: Json) -> Json:
    return node.get("attrs") or {}


def _plain_text(node: Json | None) -> str:
    if not node:
        return ""
    if node.get("type") == "text":
        return str(node.get("text", ""))
    if node.get("type") == "hardBreak":
        return "\n"
    return "".join(_plain_text(child) for child in node.get("content") or [])


def _decode_data_uri(uri: str) -> bytes | None:
    match = re.match(r"^data:([^;,]+)?(;base64)?,(.*)$", uri, re.S)
    if not match:
        return None
    payload = match.group(3)
    try:
        return base64.b64decode(payload) if match.group(2) else unquote(payload).encode()
    except Exception:
        return None


def _page_size(settings: Json):
    size = LETTER if settings.get("pageSize") == "letter" else A4
    return landscape(size) if settings.get("orientation") == "landscape" else size


def _margins(settings: Json):
    values = settings.get("marginsMm") or {}
    return tuple(float(values.get(k, 20)) * mm for k in ("top", "right", "bottom", "left"))


def _pdf_markup(node: Json) -> str:
    if node.get("type") == "text":
        text = escape(str(node.get("text", "")))
        for mark in node.get("marks") or []:
            kind = mark.get("type")
            if kind == "bold": text = f"<b>{text}</b>"
            elif kind == "italic": text = f"<i>{text}</i>"
            elif kind == "underline": text = f"<u>{text}</u>"
            elif kind == "link": text = f'<link href="{escape(str((mark.get("attrs") or {}).get("href", "")))}">{text}</link>'
        return text
    if node.get("type") == "hardBreak":
        return "<br/>"
    return "".join(_pdf_markup(child) for child in node.get("content") or [])


def _pdf_alignment(node: Json):
    align = str(_attrs(node).get("textAlign") or "left")
    return {"left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT, "justify": TA_JUSTIFY}.get(align, TA_LEFT)


def _qr_image(value: str, width: float = 28 * mm):
    qr = qrcode.QRCode(box_size=6, border=2); qr.add_data(value or " "); qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO(); image.save(buf, format="PNG"); buf.seek(0)
    return PdfImage(buf, width=width, height=width)


def _pdf_story(nodes: list[Json], styles) -> list[Any]:
    story: list[Any] = []
    for node in nodes:
        kind = node.get("type")
        attrs = _attrs(node)
        if kind in {"paragraph", "heading"}:
            base = styles["BodyText"] if kind == "paragraph" else styles[f"Heading{min(3, int(attrs.get('level',1)))}"]
            style = ParagraphStyle(
                f"ithute-{id(node)}", parent=base, alignment=_pdf_alignment(node),
                leftIndent=float(attrs.get("indent") or 0) * 18,
                firstLineIndent=float(attrs.get("firstLineIndent") or 0) * mm,
                backColor=colors.HexColor(str(attrs["shading"])) if attrs.get("shading") else None,
                borderColor=colors.HexColor("#9aa4b2") if attrs.get("border") else None,
                borderWidth=0.6 if attrs.get("border") else 0,
                borderPadding=4 if attrs.get("border") else 0,
            )
            story.append(Paragraph(_pdf_markup(node) or "&nbsp;", style)); story.append(Spacer(1, 3))
        elif kind == "pageBreak":
            story.append(PdfPageBreak())
        elif kind == "horizontalRule":
            story.append(Table([[""]], colWidths=[170*mm], rowHeights=[1], style=TableStyle([("LINEABOVE",(0,0),(-1,-1),0.5,colors.grey)])))
        elif kind == "table":
            rows=[]
            for row in node.get("content") or []:
                rows.append([Paragraph(_pdf_markup(cell) or "&nbsp;", styles["BodyText"]) for cell in row.get("content") or []])
            if rows:
                t=Table(rows, repeatRows=1)
                t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#9aa4b2")),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eef1f5")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
                story.append(t); story.append(Spacer(1,6))
        elif kind == "image":
            src=str(attrs.get("src") or "")
            raw=_decode_data_uri(src)
            if raw:
                image=PdfImage(io.BytesIO(raw)); image._restrictSize(170*mm,120*mm); story.append(image); story.append(Spacer(1,6))
        elif kind == "qrCode":
            story.append(_qr_image(str(attrs.get("value") or attrs.get("label") or "Ithute Document"))); story.append(Spacer(1,6))
        elif kind in {"signature","stamp","logo","letterhead","chart"}:
            label=escape(str(attrs.get("label") or kind.title()))
            story.append(Paragraph(f"<b>{label}</b>", styles["BodyText"])); story.append(Spacer(1,12))
        elif kind == "textBox":
            inner=_pdf_story(node.get("content") or [], styles)
            # Platypus tables provide a simple visible box while keeping rich flowables.
            if inner: story.append(Table([[inner]], style=TableStyle([("BOX",(0,0),(-1,-1),0.7,colors.HexColor("#9aa4b2")),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)])))
        elif kind in {"bulletList","orderedList"}:
            for i,item in enumerate(node.get("content") or [],1):
                prefix="•" if kind=="bulletList" else f"{i}."
                story.append(Paragraph(f"{prefix} {_pdf_markup(item)}", styles["BodyText"]))
        else:
            if node.get("content"): story.extend(_pdf_story(node["content"],styles))
    return story


def render_pdf(document: Json) -> bytes:
    settings=document.get("settings") or {}; top,right,bottom,left=_margins(settings); buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=_page_size(settings),rightMargin=right,leftMargin=left,topMargin=top+12*mm,bottomMargin=bottom+12*mm,title=str((document.get("properties") or {}).get("title") or "Document"))
    styles=getSampleStyleSheet(); story=_pdf_story((document.get("body") or {}).get("content") or [],styles)
    header=_plain_text(document.get("header")); footer=_plain_text(document.get("footer")); watermark=(settings.get("watermark") or {}).get("text")
    numbering=settings.get("pageNumbering") or {}
    def decorate(canvas, _doc):
        canvas.saveState(); w,h=_page_size(settings)
        if watermark:
            canvas.setFillColor(colors.Color(0.5,0.5,0.5,alpha=float((settings.get('watermark') or {}).get('opacity',0.12)))); canvas.setFont("Helvetica-Bold",36); canvas.translate(w/2,h/2); canvas.rotate(float((settings.get('watermark') or {}).get('rotation',-35))); canvas.drawCentredString(0,0,str(watermark)); canvas.restoreState(); canvas.saveState()
        canvas.setFillColor(colors.HexColor("#555555")); canvas.setFont("Helvetica",8)
        if header: canvas.drawString(left,h-10*mm,header[:180])
        footer_text=footer[:150]
        if numbering.get("enabled",True): footer_text=(footer_text+"  " if footer_text else "")+f"Page {canvas.getPageNumber()}"
        if footer_text: canvas.drawString(left,7*mm,footer_text)
        canvas.restoreState()
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate); return buf.getvalue()


def _add_page_number(paragraph):
    run=paragraph.add_run(); fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); run._r.addnext(fld)


def _docx_add_inline(paragraph, node: Json):
    if node.get("type") == "text":
        run=paragraph.add_run(str(node.get("text", "")))
        for mark in node.get("marks") or []:
            kind=mark.get("type"); run.bold = run.bold or kind=="bold"; run.italic = run.italic or kind=="italic"; run.underline = run.underline or kind=="underline"
        return
    if node.get("type") == "hardBreak": paragraph.add_run().add_break(); return
    for child in node.get("content") or []: _docx_add_inline(paragraph,child)


def _docx_nodes(container, nodes:list[Json]):
    for node in nodes:
        kind=node.get("type"); attrs=_attrs(node)
        if kind in {"paragraph","heading"}:
            p=container.add_paragraph(style=(f"Heading {min(3,int(attrs.get('level',1)))}" if kind=="heading" else None)); _docx_add_inline(p,node)
            p.alignment={"left":WD_ALIGN_PARAGRAPH.LEFT,"center":WD_ALIGN_PARAGRAPH.CENTER,"right":WD_ALIGN_PARAGRAPH.RIGHT,"justify":WD_ALIGN_PARAGRAPH.JUSTIFY}.get(str(attrs.get("textAlign") or "left"),WD_ALIGN_PARAGRAPH.LEFT)
            if attrs.get("indent"): p.paragraph_format.left_indent=Mm(float(attrs["indent"])*6)
        elif kind=="pageBreak": container.add_page_break()
        elif kind=="table":
            rows=node.get("content") or []; cols=max([len(r.get("content") or []) for r in rows] or [1]); table=container.add_table(rows=len(rows),cols=cols); table.style="Table Grid"
            for r,row in enumerate(rows):
                for c,cell in enumerate(row.get("content") or []): table.cell(r,c).text=_plain_text(cell)
        elif kind=="image":
            raw=_decode_data_uri(str(attrs.get("src") or ""));
            if raw: container.add_picture(io.BytesIO(raw),width=Mm(120))
        elif kind=="qrCode":
            qr=qrcode.make(str(attrs.get("value") or attrs.get("label") or "Ithute Document")); qbuf=io.BytesIO(); qr.save(qbuf,format="PNG"); qbuf.seek(0); container.add_picture(qbuf,width=Mm(28))
        elif kind=="textBox":
            table=container.add_table(rows=1,cols=1); table.style="Table Grid"; _docx_nodes(table.cell(0,0),node.get("content") or [])
        elif kind in {"signature","stamp","logo","letterhead","chart"}:
            p=container.add_paragraph(); p.add_run(str(attrs.get("label") or kind.title())).bold=True
        elif kind in {"bulletList","orderedList"}:
            for item in node.get("content") or []:
                p=container.add_paragraph(style="List Bullet" if kind=="bulletList" else "List Number"); _docx_add_inline(p,item)
        elif node.get("content"): _docx_nodes(container,node["content"])


def render_docx(document: Json) -> bytes:
    out=DocxDocument(); section=out.sections[0]; settings=document.get("settings") or {}; size=_page_size(settings)
    w,h=size; section.page_width=Mm(w/mm); section.page_height=Mm(h/mm)
    if settings.get("orientation")=="landscape": section.orientation=WD_ORIENT.LANDSCAPE
    top,right,bottom,left=[x/mm for x in _margins(settings)]; section.top_margin=Mm(top); section.right_margin=Mm(right); section.bottom_margin=Mm(bottom); section.left_margin=Mm(left)
    header=section.header.paragraphs[0]; _docx_add_inline(header,document.get("header") or {})
    footer=section.footer.paragraphs[0]; _docx_add_inline(footer,document.get("footer") or {})
    if (settings.get("pageNumbering") or {}).get("enabled",True):
        if footer.text: footer.add_run("  ")
        footer.add_run("Page "); _add_page_number(footer)
    title=str((document.get("properties") or {}).get("title") or "Document"); out.core_properties.title=title; out.core_properties.author=str((document.get("properties") or {}).get("author") or "")
    normal=out.styles["Normal"]; normal.font.name="Arial"; normal.font.size=Pt(11)
    _docx_nodes(out,(document.get("body") or {}).get("content") or [])
    buf=io.BytesIO(); out.save(buf); return buf.getvalue()
