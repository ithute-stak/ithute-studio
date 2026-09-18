"use client";

import Link from "next/link";
import { ChangeEvent, PointerEvent, useEffect, useMemo, useRef, useState } from "react";
import styles from "./pdf-editor.module.css";

const API = process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API ?? "http://localhost:8000";

type PageMeta = { index: number; width: number; height: number };
type LayerType = "text" | "cover" | "rectangle" | "ellipse" | "highlight" | "image";
type PdfLayer = {
  id: string;
  page: number;
  type: LayerType;
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string;
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  opacity?: number;
  rotation?: number;
  dataUrl?: string;
  eraseOriginal?: boolean;
};
type PdfProject = {
  id: string;
  name: string;
  originalFilename: string;
  pageCount: number;
  pageOrder: number[];
  pageMetadata: PageMeta[];
  pageRotations: Record<string, number>;
  edits: PdfLayer[];
  version: number;
  createdAt: string;
  updatedAt: string;
};
type TextRun = {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  fontSize?: number;
  fontFamily?: string;
};
type DragState = {
  id: string;
  mode: "move" | "resize";
  startX: number;
  startY: number;
  x: number;
  y: number;
  width: number;
  height: number;
};

function uid(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

export default function PdfEditorPage() {
  const [projects, setProjects] = useState<PdfProject[]>([]);
  const [project, setProject] = useState<PdfProject | null>(null);
  const [pagePosition, setPagePosition] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [textRuns, setTextRuns] = useState<TextRun[]>([]);
  const [showTextMap, setShowTextMap] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");
  const drag = useRef<DragState | null>(null);
  const imageInput = useRef<HTMLInputElement | null>(null);

  const sourcePage = project?.pageOrder[pagePosition] ?? 0;
  const pageMeta = project?.pageMetadata.find((item) => item.index === sourcePage);
  const currentLayers = useMemo(
    () => project?.edits.filter((item) => item.page === sourcePage) ?? [],
    [project, sourcePage],
  );
  const selectedLayer = project?.edits.find((item) => item.id === selectedId) ?? null;

  async function refreshProjects() {
    try {
      const response = await fetch(`${API}/v1/pdf/projects`, { cache: "no-store" });
      if (response.ok) setProjects(await response.json());
    } catch {
      // The upload surface remains usable even if the recent-project list is unavailable.
    }
  }

  useEffect(() => {
    void refreshProjects();
  }, []);

  useEffect(() => {
    if (!project) return;
    let cancelled = false;
    fetch(`${API}/v1/pdf/projects/${project.id}/pages/${sourcePage}/text`)
      .then((response) => (response.ok ? response.json() : { items: [] }))
      .then((payload) => {
        if (!cancelled) setTextRuns(payload.items ?? []);
      })
      .catch(() => {
        if (!cancelled) setTextRuns([]);
      });
    return () => {
      cancelled = true;
    };
  }, [project?.id, sourcePage]);

  function updateProject(mutator: (value: PdfProject) => PdfProject) {
    setProject((value) => (value ? mutator(value) : value));
    setStatus("Unsaved changes");
  }

  function patchLayer(id: string, patch: Partial<PdfLayer>) {
    updateProject((value) => ({
      ...value,
      edits: value.edits.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    }));
  }

  async function uploadPdf(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    setStatus("Uploading PDF…");
    const form = new FormData();
    form.append("file", file);
    form.append("name", file.name.replace(/\.pdf$/i, ""));
    try {
      const response = await fetch(`${API}/v1/pdf/projects`, { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "PDF upload failed");
      setProject(payload);
      setPagePosition(0);
      setSelectedId(null);
      setStatus("PDF imported");
      await refreshProjects();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "PDF upload failed");
      setStatus("Upload failed");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function openProject(id: string) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API}/v1/pdf/projects/${id}`, { cache: "no-store" });
      if (!response.ok) throw new Error("Could not open PDF project");
      setProject(await response.json());
      setPagePosition(0);
      setSelectedId(null);
      setStatus("Project loaded");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not open project");
    } finally {
      setBusy(false);
    }
  }

  async function saveProject() {
    if (!project) return;
    setBusy(true);
    setError("");
    setStatus("Saving…");
    try {
      const response = await fetch(`${API}/v1/pdf/projects/${project.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: project.name,
          pageOrder: project.pageOrder,
          pageRotations: project.pageRotations,
          edits: project.edits,
          expectedVersion: project.version,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Save failed");
      setProject(payload);
      setStatus(`Saved · v${payload.version}`);
      await refreshProjects();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Save failed");
      setStatus("Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function exportPdf() {
    if (!project) return;
    setBusy(true);
    setError("");
    setStatus("Rendering final PDF on backend…");
    try {
      const response = await fetch(`${API}/v1/pdf/projects/${project.id}/export`, {
        method: "POST",
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? "PDF export failed");
      }
      const blob = await response.blob();
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.download = `${project.name || "edited-document"}.pdf`;
      anchor.click();
      URL.revokeObjectURL(href);
      setStatus("Backend PDF rendered");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "PDF export failed");
      setStatus("Export failed");
    } finally {
      setBusy(false);
    }
  }

  function addLayer(type: LayerType) {
    if (!project) return;
    const defaults: Record<LayerType, Partial<PdfLayer>> = {
      text: { width: 190, height: 32, text: "New text", fontSize: 16, color: "#111111", fill: "#ffffff" },
      cover: { width: 160, height: 34, fill: "#ffffff", stroke: "#ffffff" },
      rectangle: { width: 160, height: 80, fill: "#ffffff", stroke: "#222222", opacity: 0.35 },
      ellipse: { width: 140, height: 80, fill: "#ffffff", stroke: "#222222", opacity: 0.35 },
      highlight: { width: 180, height: 24, fill: "#fff59d", stroke: "#fff59d", opacity: 0.45 },
      image: { width: 160, height: 100 },
    };
    const layer: PdfLayer = {
      id: uid(type),
      page: sourcePage,
      type,
      x: 60,
      y: 60,
      width: 120,
      height: 28,
      strokeWidth: 1,
      opacity: 1,
      fontFamily: "Helvetica",
      eraseOriginal: false,
      ...defaults[type],
    };
    updateProject((value) => ({ ...value, edits: [...value.edits, layer] }));
    setSelectedId(layer.id);
  }

  function replaceTextRun(run: TextRun) {
    if (!project) return;
    const layer: PdfLayer = {
      id: uid("replace"),
      page: sourcePage,
      type: "text",
      x: run.x,
      y: run.y,
      width: Math.max(24, run.width),
      height: Math.max(12, run.height),
      text: run.text,
      fontSize: run.fontSize ?? Math.max(8, run.height * 0.85),
      fontFamily: "Helvetica",
      color: "#111111",
      fill: "#ffffff",
      stroke: "#ffffff",
      strokeWidth: 0,
      opacity: 1,
      eraseOriginal: true,
    };
    updateProject((value) => ({ ...value, edits: [...value.edits, layer] }));
    setSelectedId(layer.id);
  }

  function removeSelected() {
    if (!project || !selectedId) return;
    updateProject((value) => ({ ...value, edits: value.edits.filter((item) => item.id !== selectedId) }));
    setSelectedId(null);
  }

  function reorderPage(offset: number) {
    if (!project) return;
    const next = pagePosition + offset;
    if (next < 0 || next >= project.pageOrder.length) return;
    const order = [...project.pageOrder];
    [order[pagePosition], order[next]] = [order[next], order[pagePosition]];
    updateProject((value) => ({ ...value, pageOrder: order }));
    setPagePosition(next);
  }

  function duplicatePage() {
    if (!project) return;
    const order = [...project.pageOrder];
    order.splice(pagePosition + 1, 0, sourcePage);
    updateProject((value) => ({ ...value, pageOrder: order }));
    setPagePosition(pagePosition + 1);
  }

  function deletePage() {
    if (!project || project.pageOrder.length <= 1) return;
    const order = project.pageOrder.filter((_, index) => index !== pagePosition);
    updateProject((value) => ({ ...value, pageOrder: order }));
    setPagePosition(Math.min(pagePosition, order.length - 1));
    setSelectedId(null);
  }

  function rotatePage() {
    if (!project) return;
    const current = project.pageRotations[String(sourcePage)] ?? 0;
    const next = (current + 90) % 360;
    updateProject((value) => ({
      ...value,
      pageRotations: { ...value.pageRotations, [String(sourcePage)]: next },
    }));
  }

  function beginDrag(event: PointerEvent, layer: PdfLayer, mode: "move" | "resize") {
    event.preventDefault();
    event.stopPropagation();
    setSelectedId(layer.id);
    drag.current = {
      id: layer.id,
      mode,
      startX: event.clientX,
      startY: event.clientY,
      x: layer.x,
      y: layer.y,
      width: layer.width,
      height: layer.height,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function continueDrag(event: PointerEvent<HTMLDivElement>) {
    if (!drag.current || !project || !pageMeta) return;
    const state = drag.current;
    const dx = (event.clientX - state.startX) / zoom;
    const dy = (event.clientY - state.startY) / zoom;
    if (state.mode === "move") {
      patchLayer(state.id, {
        x: clamp(state.x + dx, 0, pageMeta.width - 8),
        y: clamp(state.y + dy, 0, pageMeta.height - 8),
      });
    } else {
      patchLayer(state.id, {
        width: clamp(state.width + dx, 8, pageMeta.width - state.x),
        height: clamp(state.height + dy, 8, pageMeta.height - state.y),
      });
    }
  }

  function endDrag() {
    drag.current = null;
  }

  function insertImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !project) return;
    const reader = new FileReader();
    reader.onload = () => {
      const layer: PdfLayer = {
        id: uid("image"),
        page: sourcePage,
        type: "image",
        x: 70,
        y: 70,
        width: 180,
        height: 120,
        opacity: 1,
        dataUrl: String(reader.result),
      };
      updateProject((value) => ({ ...value, edits: [...value.edits, layer] }));
      setSelectedId(layer.id);
    };
    reader.readAsDataURL(file);
    event.target.value = "";
  }

  if (!project) {
    return (
      <main className={styles.library}>
        <header className={styles.libraryHeader}>
          <Link href="/" className={styles.back}>← Document Studio</Link>
          <strong>PDF Studio</strong>
        </header>
        <section className={styles.uploadHero}>
          <div>
            <span className={styles.eyebrow}>BACKEND PDF EDITOR</span>
            <h1>Edit an existing PDF like a design canvas.</h1>
            <p>Upload a PDF, select existing text, add or replace objects, rearrange pages, and export a new file rendered by Ithute Studio’s backend.</p>
          </div>
          <label className={styles.uploadButton}>
            {busy ? "Importing…" : "Upload PDF"}
            <input type="file" accept="application/pdf,.pdf" onChange={uploadPdf} disabled={busy} />
          </label>
          {error && <p className={styles.error}>{error}</p>}
        </section>
        <section className={styles.recent}>
          <h2>Recent PDF projects</h2>
          <div className={styles.projectGrid}>
            {projects.map((item) => (
              <button key={item.id} className={styles.projectCard} onClick={() => void openProject(item.id)}>
                <span className={styles.pdfBadge}>PDF</span>
                <strong>{item.name}</strong>
                <small>{item.pageOrder.length} pages · v{item.version}</small>
              </button>
            ))}
            {!projects.length && <p className={styles.empty}>No PDF projects yet.</p>}
          </div>
        </section>
      </main>
    );
  }

  const preview = `${API}/v1/pdf/projects/${project.id}/pages/${sourcePage}/preview?scale=1`;
  const rotation = project.pageRotations[String(sourcePage)] ?? 0;

  return (
    <main className={styles.editor}>
      <header className={styles.topbar}>
        <div className={styles.brandRow}>
          <button className={styles.iconButton} onClick={() => setProject(null)}>←</button>
          <div><strong>Ithute PDF Studio</strong><small>{project.originalFilename}</small></div>
        </div>
        <input
          className={styles.titleInput}
          value={project.name}
          onChange={(event) => updateProject((value) => ({ ...value, name: event.target.value }))}
        />
        <div className={styles.topActions}>
          <span className={styles.status}>{status}</span>
          <button onClick={() => void saveProject()} disabled={busy}>Save</button>
          <button className={styles.primary} onClick={() => void exportPdf()} disabled={busy}>Export PDF</button>
        </div>
      </header>

      <section className={styles.toolbar}>
        <div className={styles.toolGroup}>
          <button onClick={() => addLayer("text")}>T Text</button>
          <button onClick={() => addLayer("cover")}>▭ Cover</button>
          <button onClick={() => addLayer("highlight")}>▰ Highlight</button>
          <button onClick={() => addLayer("rectangle")}>□ Rectangle</button>
          <button onClick={() => addLayer("ellipse")}>○ Ellipse</button>
          <button onClick={() => imageInput.current?.click()}>▧ Image</button>
          <input ref={imageInput} hidden type="file" accept="image/png,image/jpeg,image/webp" onChange={insertImage} />
        </div>
        <div className={styles.toolGroup}>
          <button onClick={() => setShowTextMap((value) => !value)} className={showTextMap ? styles.activeTool : ""}>Existing text</button>
          <button onClick={() => reorderPage(-1)}>← Page</button>
          <button onClick={() => reorderPage(1)}>Page →</button>
          <button onClick={duplicatePage}>Duplicate</button>
          <button onClick={deletePage} disabled={project.pageOrder.length <= 1}>Delete page</button>
          <button onClick={rotatePage}>Rotate export {rotation}°</button>
        </div>
        <div className={styles.zoomControl}>
          <button onClick={() => setZoom((value) => clamp(value - 0.1, 0.5, 2.5))}>−</button>
          <span>{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom((value) => clamp(value + 0.1, 0.5, 2.5))}>+</button>
        </div>
      </section>

      <div className={styles.body}>
        <aside className={styles.pages}>
          <div className={styles.panelTitle}>Pages</div>
          {project.pageOrder.map((pageIndex, position) => (
            <button
              key={`${pageIndex}-${position}`}
              className={`${styles.thumbnail} ${position === pagePosition ? styles.thumbnailActive : ""}`}
              onClick={() => { setPagePosition(position); setSelectedId(null); }}
            >
              <img src={`${API}/v1/pdf/projects/${project.id}/pages/${pageIndex}/preview?scale=.25`} alt="" />
              <span>{position + 1}</span>
            </button>
          ))}
        </aside>

        <section className={styles.workspace} onPointerMove={continueDrag} onPointerUp={endDrag} onPointerCancel={endDrag}>
          <div className={styles.canvasInfo}>Source page {sourcePage + 1} · {Math.round(pageMeta?.width ?? 0)} × {Math.round(pageMeta?.height ?? 0)} pt</div>
          {pageMeta && (
            <div
              className={styles.pageCanvas}
              style={{ width: pageMeta.width * zoom, height: pageMeta.height * zoom }}
              onPointerDown={() => setSelectedId(null)}
            >
              <img className={styles.pageImage} src={preview} alt={`PDF page ${pagePosition + 1}`} />
              {showTextMap && textRuns.map((run, index) => (
                <button
                  key={`${index}-${run.x}-${run.y}`}
                  title={`Edit: ${run.text}`}
                  className={styles.textMap}
                  style={{
                    left: run.x * zoom,
                    top: run.y * zoom,
                    width: Math.max(6, run.width * zoom),
                    height: Math.max(6, run.height * zoom),
                  }}
                  onPointerDown={(event) => event.stopPropagation()}
                  onDoubleClick={() => replaceTextRun(run)}
                />
              ))}
              {currentLayers.map((layer) => (
                <div
                  key={layer.id}
                  className={`${styles.layer} ${selectedId === layer.id ? styles.selected : ""}`}
                  style={{
                    left: layer.x * zoom,
                    top: layer.y * zoom,
                    width: layer.width * zoom,
                    height: layer.height * zoom,
                    opacity: layer.opacity ?? 1,
                  }}
                  onPointerDown={(event) => beginDrag(event, layer, "move")}
                >
                  {layer.type === "text" && <span style={{ fontSize: (layer.fontSize ?? 12) * zoom, color: layer.color, background: layer.eraseOriginal ? layer.fill : "transparent" }}>{layer.text}</span>}
                  {layer.type === "cover" && <span className={styles.shape} style={{ background: layer.fill ?? "#fff" }} />}
                  {layer.type === "highlight" && <span className={styles.shape} style={{ background: layer.fill ?? "#fff59d" }} />}
                  {layer.type === "rectangle" && <span className={styles.shape} style={{ background: layer.fill, border: `${layer.strokeWidth ?? 1}px solid ${layer.stroke ?? "#111"}` }} />}
                  {layer.type === "ellipse" && <span className={`${styles.shape} ${styles.ellipse}`} style={{ background: layer.fill, border: `${layer.strokeWidth ?? 1}px solid ${layer.stroke ?? "#111"}` }} />}
                  {layer.type === "image" && layer.dataUrl && <img className={styles.layerImage} src={layer.dataUrl} alt="Inserted" />}
                  {selectedId === layer.id && <button className={styles.resizeHandle} onPointerDown={(event) => beginDrag(event, layer, "resize")} aria-label="Resize" />}
                </div>
              ))}
            </div>
          )}
          <p className={styles.hint}>Double-click a blue text outline to replace existing PDF text. Drag Studio layers to position them.</p>
        </section>

        <aside className={styles.inspector}>
          <div className={styles.panelTitle}>Properties</div>
          {selectedLayer ? (
            <div className={styles.properties}>
              <strong>{selectedLayer.type.toUpperCase()}</strong>
              {selectedLayer.type === "text" && (
                <>
                  <label>Text<textarea value={selectedLayer.text ?? ""} onChange={(event) => patchLayer(selectedLayer.id, { text: event.target.value })} /></label>
                  <label>Font size<input type="number" min="4" max="240" value={selectedLayer.fontSize ?? 12} onChange={(event) => patchLayer(selectedLayer.id, { fontSize: Number(event.target.value) })} /></label>
                  <label>Text color<input type="color" value={selectedLayer.color ?? "#111111"} onChange={(event) => patchLayer(selectedLayer.id, { color: event.target.value })} /></label>
                  <label className={styles.check}><input type="checkbox" checked={Boolean(selectedLayer.eraseOriginal)} onChange={(event) => patchLayer(selectedLayer.id, { eraseOriginal: event.target.checked })} /> Cover original area</label>
                </>
              )}
              {selectedLayer.type !== "image" && <label>Fill<input type="color" value={selectedLayer.fill ?? "#ffffff"} onChange={(event) => patchLayer(selectedLayer.id, { fill: event.target.value })} /></label>}
              <label>Opacity<input type="range" min="0" max="1" step="0.05" value={selectedLayer.opacity ?? 1} onChange={(event) => patchLayer(selectedLayer.id, { opacity: Number(event.target.value) })} /></label>
              <div className={styles.coordinateGrid}>
                {(["x", "y", "width", "height"] as const).map((key) => (
                  <label key={key}>{key.toUpperCase()}<input type="number" value={Math.round(selectedLayer[key])} onChange={(event) => patchLayer(selectedLayer.id, { [key]: Number(event.target.value) })} /></label>
                ))}
              </div>
              <button className={styles.danger} onClick={removeSelected}>Delete layer</button>
            </div>
          ) : (
            <div className={styles.noSelection}>
              <p>Select a Studio layer to edit its properties.</p>
              <p><b>Existing PDF text:</b> double-click a blue outline to make a replaceable text layer.</p>
              <p><b>Cover</b> hides source content visually. It is not secure redaction.</p>
            </div>
          )}
          {error && <p className={styles.error}>{error}</p>}
        </aside>
      </div>
    </main>
  );
}
