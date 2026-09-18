"use client";
import type { DocumentSettings } from "@ithute/document-schema";
export function PageSetupPanel({ settings, onChange }: { settings: DocumentSettings; onChange: (next: DocumentSettings) => void }) {
  const setMargin = (key: keyof DocumentSettings["marginsMm"], value: number) => onChange({...settings, marginsMm: {...settings.marginsMm, [key]: Math.max(0, Math.min(60, value))}});
  return <aside className="ithute-properties-panel">
    <div className="ithute-panel-heading"><div><strong>Page setup</strong><small>Paper and document layout</small></div></div>
    <label>Paper size<select value={settings.pageSize} onChange={(e) => onChange({...settings, pageSize: e.target.value as "a4" | "letter"})}><option value="a4">A4</option><option value="letter">Letter</option></select></label>
    <label>Orientation<select value={settings.orientation} onChange={(e) => onChange({...settings, orientation: e.target.value as "portrait" | "landscape"})}><option value="portrait">Portrait</option><option value="landscape">Landscape</option></select></label>
    <label>Columns<select value={settings.columns} onChange={(e) => onChange({...settings, columns: Number(e.target.value) as 1|2|3})}><option value="1">One</option><option value="2">Two</option><option value="3">Three</option></select></label>
    <fieldset><legend>Margins (mm)</legend>
      {(["top","right","bottom","left"] as const).map((key) => <label key={key}>{key[0].toUpperCase()+key.slice(1)}<input type="number" min="0" max="60" value={settings.marginsMm[key]} onChange={(e) => setMargin(key, Number(e.target.value))} /></label>)}
    </fieldset>
    <fieldset><legend>Header & footer</legend>
      <label>Header distance<input type="number" value={settings.headerDistanceMm} onChange={(e) => onChange({...settings, headerDistanceMm:Number(e.target.value)})} /></label>
      <label>Footer distance<input type="number" value={settings.footerDistanceMm} onChange={(e) => onChange({...settings, footerDistanceMm:Number(e.target.value)})} /></label>
    </fieldset>
    <fieldset><legend>Watermark</legend>
      <label>Text<input value={settings.watermark?.text || ""} onChange={(e) => onChange({...settings, watermark:{opacity:.12,rotation:-35,...settings.watermark,text:e.target.value}})} placeholder="DRAFT" /></label>
      <label>Opacity<input type="range" min="0" max="0.5" step="0.01" value={settings.watermark?.opacity ?? .12} onChange={(e) => onChange({...settings, watermark:{text:"",rotation:-35,...settings.watermark,opacity:Number(e.target.value)}})} /></label>
    </fieldset>
  </aside>;
}
