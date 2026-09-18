"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { TextStyle } from "@tiptap/extension-text-style";
import { FontFamily } from "@tiptap/extension-font-family";
import { Color } from "@tiptap/extension-color";
import { Highlight } from "@tiptap/extension-highlight";
import { Underline } from "@tiptap/extension-underline";
import { Link } from "@tiptap/extension-link";
import { Image } from "@tiptap/extension-image";
import { Placeholder } from "@tiptap/extension-placeholder";
import { TextAlign } from "@tiptap/extension-text-align";
import { Table, TableRow, TableHeader, TableCell } from "@tiptap/extension-table";
import type { DataDictionary, DataDictionaryField, DocumentSettings, IthuteDocumentV1, TiptapJson } from "@ithute/document-schema";
import { DEFAULT_DOCUMENT_SETTINGS, emptyDoc } from "@ithute/document-schema";
import { PageBreak, Variable, DynamicTable, TextBox, Signature, Stamp, QrCode, Chart, Logo, Letterhead, TextMetrics, ParagraphLayout } from "../extensions";
import { DataPanel, ITHUTE_DATA_FIELD_MIME } from "./DataPanel";
import { Ruler } from "./Ruler";
import { PageSetupPanel } from "./PageSetupPanel";
import { DocumentPropertiesPanel } from "./DocumentPropertiesPanel";
import {
  AlignCenter, AlignJustify, AlignLeft, AlignRight, Bold, ChevronDown, Columns3, FileText, Highlighter, Image as ImageIcon,
  Italic, Link as LinkIcon, List, ListOrdered, Minus, PanelLeft, PanelRight, Pilcrow, Plus, Printer, Redo2, Save,
  Scissors, Table2, Underline as UnderlineIcon, Undo2, Variable as VariableIcon, ZoomIn, ZoomOut
} from "lucide-react";

export type SaveState = "saved" | "saving" | "dirty" | "error";
export interface StudioEditorProps {
  document: IthuteDocumentV1;
  dataDictionary?: DataDictionary;
  readOnly?: boolean;
  autosaveMs?: number;
  onChange?: (document: IthuteDocumentV1) => void;
  onSave?: (document: IthuteDocumentV1) => Promise<IthuteDocumentV1 | void> | IthuteDocumentV1 | void;
  onExport?: (document: IthuteDocumentV1, format: "pdf" | "docx") => Promise<void> | void;
}

type Tab = "Home" | "Insert" | "Layout" | "Design";
type ActiveRegion = "header" | "body" | "footer";

const fontFamilies = ["Arial", "Aptos", "Calibri", "Georgia", "Times New Roman", "Verdana"];
const fontSizes = [8,9,10,11,12,14,16,18,20,24,28,32,36,48,72];
const commonExtensions = (placeholder: string) => [
  StarterKit.configure({ link: false, underline: false }), TextStyle, FontFamily, TextMetrics, Color,
  Highlight.configure({ multicolor: true }), Underline, Link.configure({ openOnClick: false, autolink: true }),
  Image.configure({ inline: false, allowBase64: true }), TextAlign.configure({ types: ["heading", "paragraph"] }),
  Placeholder.configure({ placeholder }), Table.configure({ resizable: true }), TableRow, TableHeader, TableCell,
  PageBreak, Variable, DynamicTable, TextBox, Signature, Stamp, QrCode, Chart, Logo, Letterhead, ParagraphLayout
];

function pageDimensions(settings: DocumentSettings) {
  let width = settings.pageSize === "letter" ? 215.9 : 210;
  let height = settings.pageSize === "letter" ? 279.4 : 297;
  if (settings.orientation === "landscape") [width, height] = [height, width];
  return { width, height };
}

function ToolButton({ title, active, disabled, onClick, children }: { title: string; active?: boolean; disabled?: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" title={title} aria-label={title} disabled={disabled} className={`ithute-tool-button${active ? " active" : ""}`} onMouseDown={(e) => e.preventDefault()} onClick={onClick}>{children}</button>;
}

function useRegionEditor(content: TiptapJson, placeholder: string, readOnly: boolean, onFocus: () => void, onUpdate: (json:TiptapJson) => void) {
  return useEditor({
    immediatelyRender: false,
    editable: !readOnly,
    extensions: commonExtensions(placeholder),
    content,
    onFocus,
    onUpdate: ({ editor }) => onUpdate(editor.getJSON() as TiptapJson),
    editorProps: {
      handleDrop(view, event) {
        const raw = event.dataTransfer?.getData(ITHUTE_DATA_FIELD_MIME);
        if (!raw) return false;
        event.preventDefault();
        try {
          const field = JSON.parse(raw) as DataDictionaryField;
          const coordinates = view.posAtCoords({ left: event.clientX, top: event.clientY });
          const pos = coordinates?.pos ?? view.state.selection.from;
          if (field.type === "collection") {
            const columns = (field.itemFields || []).slice(0, 6).map((item) => ({ label: item.label, path: item.path }));
            view.dispatch(view.state.tr.insert(pos, view.state.schema.nodes.dynamicTable.create({ collectionPath: field.path, label: field.label, columns })));
          } else {
            view.dispatch(view.state.tr.insert(pos, view.state.schema.nodes.variable.create({ path: field.path, label: field.label, format: field.type })));
          }
          return true;
        } catch { return false; }
      }
    }
  });
}

export function StudioEditor({ document: initialDocument, dataDictionary, readOnly = false, autosaveMs = 1200, onChange, onSave, onExport }: StudioEditorProps) {
  const [doc, setDoc] = useState<IthuteDocumentV1>({ ...initialDocument, settings: initialDocument.settings || DEFAULT_DOCUMENT_SETTINGS });
  const [activeRegion, setActiveRegion] = useState<ActiveRegion>("body");
  const [tab, setTab] = useState<Tab>("Home");
  const [zoom, setZoom] = useState(100);
  const [leftPanel, setLeftPanel] = useState(true);
  const [rightPanel, setRightPanel] = useState<"none"|"page"|"properties">("none");
  const [saveState, setSaveState] = useState<SaveState>("saved");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [fontSize, setFontSize] = useState(11);
  const [fontFamily, setFontFamily] = useState("Aptos");
  const saveTimer = useRef<number | undefined>(undefined);
  const imageInputRef = useRef<HTMLInputElement | null>(null);

  const patchRegion = useCallback((region: ActiveRegion, json: TiptapJson) => {
    setDoc((current) => {
      const next = { ...current, [region]: json, updatedAt: new Date().toISOString() } as IthuteDocumentV1;
      onChange?.(next); return next;
    });
    setSaveState("dirty");
  }, [onChange]);

  const headerEditor = useRegionEditor(doc.header || emptyDoc(), "Header", readOnly, () => setActiveRegion("header"), (json) => patchRegion("header", json));
  const bodyEditor = useRegionEditor(doc.body || emptyDoc(), "Start writing…", readOnly, () => setActiveRegion("body"), (json) => patchRegion("body", json));
  const footerEditor = useRegionEditor(doc.footer || emptyDoc(), "Footer", readOnly, () => setActiveRegion("footer"), (json) => patchRegion("footer", json));
  const activeEditor = (activeRegion === "header" ? headerEditor : activeRegion === "footer" ? footerEditor : bodyEditor) as Editor | null;

  const doSave = useCallback(async () => {
    if (!onSave || readOnly) return;
    setSaveState("saving");
    try {
      const saved = await onSave(doc);
      if (saved) setDoc(saved);
      setSaveState("saved"); setLastSavedAt(new Date());
    } catch { setSaveState("error"); }
  }, [doc, onSave, readOnly]);

  useEffect(() => {
    if (saveState !== "dirty" || !onSave || readOnly) return;
    window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => void doSave(), autosaveMs);
    return () => window.clearTimeout(saveTimer.current);
  }, [autosaveMs, doSave, onSave, readOnly, saveState]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") { event.preventDefault(); void doSave(); }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "p") { event.preventDefault(); window.print(); }
    };
    window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler);
  }, [doSave]);

  const patchSettings = (settings: DocumentSettings) => {
    const next = { ...doc, settings, updatedAt: new Date().toISOString() };
    setDoc(next); onChange?.(next); setSaveState("dirty");
  };
  const patchProperties = (properties: IthuteDocumentV1["properties"]) => {
    const next = { ...doc, properties, updatedAt: new Date().toISOString() };
    setDoc(next); onChange?.(next); setSaveState("dirty");
  };
  const dimensions = pageDimensions(doc.settings);
  const pageStyle = useMemo(() => ({
    width: `${dimensions.width}mm`, minHeight: `${dimensions.height}mm`,
    transform: `scale(${zoom/100})`, transformOrigin: "top center",
    marginBottom: `${dimensions.height * (zoom/100 - 1) + 28}px`,
    "--page-width-mm": dimensions.width, "--page-height-mm": dimensions.height,
    "--margin-top": `${doc.settings.marginsMm.top}mm`, "--margin-right": `${doc.settings.marginsMm.right}mm`,
    "--margin-bottom": `${doc.settings.marginsMm.bottom}mm`, "--margin-left": `${doc.settings.marginsMm.left}mm`,
    "--column-count": doc.settings.columns
  } as React.CSSProperties), [dimensions.height, dimensions.width, doc.settings, zoom]);

  const insertField = (field: DataDictionaryField) => {
    const editor = activeEditor || bodyEditor; if (!editor) return;
    if (field.type === "collection") {
      const columns = (field.itemFields || []).slice(0, 6).map((item) => ({ label: item.label, path: item.path }));
      editor.chain().focus().insertContent({ type: "dynamicTable", attrs: { collectionPath: field.path, label: field.label, columns } }).run();
    } else editor.chain().focus().insertContent({ type: "variable", attrs: { path: field.path, label: field.label, format: field.type } }).run();
  };

  const setFontSizeMark = (size: number) => { setFontSize(size); activeEditor?.chain().focus().setMark("textStyle", { fontSize: `${size}pt` }).run(); };
  const insertImageUrl = () => {
    const url = window.prompt("Image URL"); if (url?.trim()) activeEditor?.chain().focus().setImage({ src: url.trim() }).run();
  };
  const insertImageFile = (file?: File) => {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader(); reader.onload = () => activeEditor?.chain().focus().setImage({src:String(reader.result),alt:file.name}).run(); reader.readAsDataURL(file);
  };
  const insertQr = () => { const value=window.prompt("QR code value or URL", "https://"); if(value?.trim()) activeEditor?.chain().focus().insertContent({type:"qrCode",attrs:{value:value.trim(),label:"QR code"}}).run(); };
  const insertLink = () => {
    const old = activeEditor?.getAttributes("link").href as string | undefined;
    const url = window.prompt("Link URL", old || "https://"); if (url === null) return;
    if (!url.trim()) activeEditor?.chain().focus().extendMarkRange("link").unsetLink().run(); else activeEditor?.chain().focus().extendMarkRange("link").setLink({ href: url.trim() }).run();
  };

  const wordCount = bodyEditor?.getText().trim().split(/\s+/).filter(Boolean).length ?? 0;

  return <div className="ithute-studio-shell">
    <header className="ithute-titlebar">
      <div className="ithute-brand-mark">I</div><div className="ithute-document-name"><strong>{doc.properties.title || "Untitled document"}</strong><small>Ithute Document Studio</small></div>
      <div className={`ithute-save-state ${saveState}`}>{saveState === "saving" ? "Saving…" : saveState === "dirty" ? "Unsaved" : saveState === "error" ? "Save failed" : `Saved${lastSavedAt ? ` ${lastSavedAt.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}` : ""}`}</div>
      <ToolButton title="Save (Ctrl+S)" disabled={!onSave || readOnly} onClick={() => void doSave()}><Save size={17}/></ToolButton>
      <ToolButton title="Print preview (Ctrl+P)" onClick={() => window.print()}><Printer size={17}/></ToolButton>{onExport && <><button type="button" className="ithute-title-action" onClick={() => void onExport(doc,"pdf")}>PDF</button><button type="button" className="ithute-title-action" onClick={() => void onExport(doc,"docx")}>DOCX</button></>}
    </header>

    <div className="ithute-tabs">{(["Home","Insert","Layout","Design"] as Tab[]).map((name) => <button type="button" key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>{name}</button>)}</div>
    <div className="ithute-ribbon">
      {tab === "Home" && <>
        <section><span className="ithute-ribbon-label">History</span><ToolButton title="Undo" onClick={() => activeEditor?.chain().focus().undo().run()}><Undo2 size={16}/></ToolButton><ToolButton title="Redo" onClick={() => activeEditor?.chain().focus().redo().run()}><Redo2 size={16}/></ToolButton></section>
        <section className="wide"><span className="ithute-ribbon-label">Font</span>
          <select value={fontFamily} onChange={(e) => { setFontFamily(e.target.value); activeEditor?.chain().focus().setFontFamily(e.target.value).run(); }}>{fontFamilies.map((f) => <option key={f}>{f}</option>)}</select>
          <select value={fontSize} onChange={(e) => setFontSizeMark(Number(e.target.value))}>{fontSizes.map((s) => <option key={s}>{s}</option>)}</select>
          <ToolButton title="Bold" active={activeEditor?.isActive("bold")} onClick={() => activeEditor?.chain().focus().toggleBold().run()}><Bold size={16}/></ToolButton>
          <ToolButton title="Italic" active={activeEditor?.isActive("italic")} onClick={() => activeEditor?.chain().focus().toggleItalic().run()}><Italic size={16}/></ToolButton>
          <ToolButton title="Underline" active={activeEditor?.isActive("underline")} onClick={() => activeEditor?.chain().focus().toggleUnderline().run()}><UnderlineIcon size={16}/></ToolButton>
          <input title="Text colour" type="color" onChange={(e) => activeEditor?.chain().focus().setColor(e.target.value).run()} />
          <input title="Highlight" type="color" defaultValue="#fff2a8" onChange={(e) => activeEditor?.chain().focus().toggleHighlight({ color:e.target.value }).run()} />
        </section>
        <section><span className="ithute-ribbon-label">Paragraph</span>
          <ToolButton title="Bullets" onClick={() => activeEditor?.chain().focus().toggleBulletList().run()}><List size={16}/></ToolButton>
          <ToolButton title="Numbering" onClick={() => activeEditor?.chain().focus().toggleOrderedList().run()}><ListOrdered size={16}/></ToolButton>
          <ToolButton title="Align left" onClick={() => activeEditor?.chain().focus().setTextAlign("left").run()}><AlignLeft size={16}/></ToolButton>
          <ToolButton title="Center" onClick={() => activeEditor?.chain().focus().setTextAlign("center").run()}><AlignCenter size={16}/></ToolButton>
          <ToolButton title="Align right" onClick={() => activeEditor?.chain().focus().setTextAlign("right").run()}><AlignRight size={16}/></ToolButton>
          <ToolButton title="Justify" onClick={() => activeEditor?.chain().focus().setTextAlign("justify").run()}><AlignJustify size={16}/></ToolButton>
          <ToolButton title="Decrease indent" onClick={() => activeEditor?.chain().focus().updateAttributes(activeEditor.isActive("heading") ? "heading" : "paragraph", { indent: Math.max(0, Number(activeEditor.getAttributes(activeEditor.isActive("heading") ? "heading" : "paragraph").indent || 0)-1) }).run()}><Minus size={16}/></ToolButton>
          <ToolButton title="Increase indent" onClick={() => activeEditor?.chain().focus().updateAttributes(activeEditor.isActive("heading") ? "heading" : "paragraph", { indent: Number(activeEditor.getAttributes(activeEditor.isActive("heading") ? "heading" : "paragraph").indent || 0)+1 }).run()}><Plus size={16}/></ToolButton>
        </section>
        <section><span className="ithute-ribbon-label">Styles</span>
          <button type="button" onClick={() => activeEditor?.chain().focus().setParagraph().run()}>Normal</button><button type="button" onClick={() => activeEditor?.chain().focus().toggleHeading({level:1}).run()}>Title</button><button type="button" onClick={() => activeEditor?.chain().focus().toggleHeading({level:2}).run()}>Heading 1</button><button type="button" onClick={() => activeEditor?.chain().focus().toggleHeading({level:3}).run()}>Heading 2</button>
        </section>
      </>}
      {tab === "Insert" && <>
        <section><span className="ithute-ribbon-label">Pages</span><button type="button" onClick={() => activeEditor?.chain().focus().insertContent({type:"pageBreak"}).run()}><FileText size={16}/> Page break</button></section>
        <section><span className="ithute-ribbon-label">Tables & media</span><button type="button" onClick={() => activeEditor?.chain().focus().insertTable({rows:3,cols:3,withHeaderRow:true}).run()}><Table2 size={16}/> Table</button><button type="button" onClick={() => imageInputRef.current?.click()}><ImageIcon size={16}/> Image</button><button type="button" onClick={insertImageUrl}>Image URL</button><input ref={imageInputRef} hidden type="file" accept="image/*" onChange={(e)=>insertImageFile(e.target.files?.[0])}/><button type="button" onClick={insertLink}><LinkIcon size={16}/> Link</button></section>
        <section><span className="ithute-ribbon-label">Objects</span><button type="button" onClick={() => activeEditor?.chain().focus().insertContent({type:"textBox",content:[{type:"paragraph",content:[{type:"text",text:"Text box"}]}]}).run()}>Text box</button><button type="button" onClick={() => activeEditor?.chain().focus().insertContent({type:"signature"}).run()}>Signature</button><button type="button" onClick={() => activeEditor?.chain().focus().insertContent({type:"stamp"}).run()}>Stamp</button><button type="button" onClick={insertQr}>QR</button><button type="button" onClick={() => activeEditor?.chain().focus().insertContent({type:"chart"}).run()}>Chart</button><button type="button" onClick={() => activeEditor?.chain().focus().insertContent({type:"logo"}).run()}>Logo</button><button type="button" onClick={() => activeEditor?.chain().focus().insertContent({type:"letterhead"}).run()}>Letterhead</button></section>
        <section><span className="ithute-ribbon-label">Data</span><button type="button" onClick={() => setLeftPanel(true)}><VariableIcon size={16}/> Variable</button><button type="button" onClick={() => setLeftPanel(true)}><Table2 size={16}/> Dynamic table</button></section>
      </>}
      {tab === "Layout" && <>
        <section><span className="ithute-ribbon-label">Page setup</span><select value={doc.settings.pageSize} onChange={(e) => patchSettings({...doc.settings,pageSize:e.target.value as "a4"|"letter"})}><option value="a4">A4</option><option value="letter">Letter</option></select><select value={doc.settings.orientation} onChange={(e) => patchSettings({...doc.settings,orientation:e.target.value as "portrait"|"landscape"})}><option value="portrait">Portrait</option><option value="landscape">Landscape</option></select><button type="button" onClick={() => setRightPanel("page")}>Margins</button><button type="button" onClick={() => setRightPanel("page")}><Columns3 size={16}/> Columns</button></section>
      </>}
      {tab === "Design" && <>
        <section><span className="ithute-ribbon-label">Document</span><button type="button" onClick={() => setRightPanel("page")}>Watermark</button><button type="button" onClick={() => setRightPanel("properties")}>Properties</button><button type="button" onClick={() => setActiveRegion("header")}>Edit header</button><button type="button" onClick={() => setActiveRegion("footer")}>Edit footer</button></section><section><span className="ithute-ribbon-label">Paragraph appearance</span><button type="button" onClick={() => activeEditor?.chain().focus().updateAttributes(activeEditor.isActive("heading") ? "heading" : "paragraph", {border:"1px solid #9aa4b2"}).run()}>Border</button><input title="Paragraph shading" type="color" defaultValue="#ffffff" onChange={(e)=>activeEditor?.chain().focus().updateAttributes(activeEditor.isActive("heading") ? "heading" : "paragraph", {shading:e.target.value}).run()}/></section>
      </>}
    </div>

    <div className="ithute-workspace">
      {leftPanel && <DataPanel dictionary={dataDictionary} onInsert={insertField} />}
      <main className="ithute-canvas-area">
        <div className="ithute-canvas-controls"><ToolButton title="Toggle data panel" active={leftPanel} onClick={() => setLeftPanel(v=>!v)}><PanelLeft size={16}/></ToolButton><span>{zoom}%</span><ToolButton title="Zoom out" onClick={() => setZoom(z=>Math.max(50,z-10))}><ZoomOut size={16}/></ToolButton><input type="range" min="50" max="180" step="10" value={zoom} onChange={(e)=>setZoom(Number(e.target.value))}/><ToolButton title="Zoom in" onClick={() => setZoom(z=>Math.min(180,z+10))}><ZoomIn size={16}/></ToolButton><ToolButton title="Page setup" active={rightPanel!=="none"} onClick={() => setRightPanel(v=>v==="none"?"page":"none")}><PanelRight size={16}/></ToolButton></div>
        {doc.settings.showRulers && <div className="ithute-ruler-wrap" style={{ width:`${dimensions.width}mm`, transform:`scale(${zoom/100})`, transformOrigin:"top center" }}><Ruler widthMm={dimensions.width} margins={doc.settings.marginsMm}/></div>}
        <div className="ithute-paper" style={pageStyle}>
          {doc.settings.watermark?.text ? <div className="ithute-watermark" style={{opacity:doc.settings.watermark.opacity,transform:`translate(-50%,-50%) rotate(${doc.settings.watermark.rotation}deg)`}}>{doc.settings.watermark.text}</div> : null}
          <div className={`ithute-header-region${activeRegion === "header" ? " active" : ""}`} style={{paddingLeft:"var(--margin-left)",paddingRight:"var(--margin-right)",paddingTop:`${doc.settings.headerDistanceMm}mm`}}><EditorContent editor={headerEditor}/></div>
          <div className={`ithute-body-region${activeRegion === "body" ? " active" : ""}`} style={{padding:"var(--margin-top) var(--margin-right) var(--margin-bottom) var(--margin-left)",columnCount:doc.settings.columns}}><EditorContent editor={bodyEditor}/></div>
          <div className={`ithute-footer-region${activeRegion === "footer" ? " active" : ""}`} style={{paddingLeft:"var(--margin-left)",paddingRight:"var(--margin-right)",paddingBottom:`${doc.settings.footerDistanceMm}mm`}}><EditorContent editor={footerEditor}/>{doc.settings.pageNumbering?.enabled && <span className="ithute-page-number">1</span>}</div>
        </div>
      </main>
      {rightPanel === "page" && <PageSetupPanel settings={doc.settings} onChange={patchSettings} />}
      {rightPanel === "properties" && <DocumentPropertiesPanel properties={doc.properties} onChange={patchProperties} onClose={()=>setRightPanel("none")} />}
    </div>
    <footer className="ithute-statusbar"><span>Page 1</span><span>{wordCount} words</span><span>{activeRegion[0].toUpperCase()+activeRegion.slice(1)}</span><span>{doc.settings.pageSize.toUpperCase()} · {doc.settings.orientation}</span><span>Schema v{doc.schemaVersion}</span></footer>
  </div>;
}
