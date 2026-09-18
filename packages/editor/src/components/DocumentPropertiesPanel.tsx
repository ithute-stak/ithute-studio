"use client";
import type { DocumentProperties } from "@ithute/document-schema";
export function DocumentPropertiesPanel({properties,onChange,onClose}:{properties:DocumentProperties;onChange:(value:DocumentProperties)=>void;onClose:()=>void}){
  const set=(key:keyof DocumentProperties,value:unknown)=>onChange({...properties,[key]:value});
  return <aside className="ithute-setup-panel"><div className="ithute-panel-heading"><div><strong>Document properties</strong><small>Metadata stored with the document</small></div><button type="button" onClick={onClose}>×</button></div>
    <label>Title<input value={properties.title||""} onChange={e=>set("title",e.target.value)}/></label>
    <label>Subject<input value={properties.subject||""} onChange={e=>set("subject",e.target.value)}/></label>
    <label>Author<input value={properties.author||""} onChange={e=>set("author",e.target.value)}/></label>
    <label>Company<input value={properties.company||""} onChange={e=>set("company",e.target.value)}/></label>
    <label>Category<input value={properties.category||""} onChange={e=>set("category",e.target.value)}/></label>
    <label>Language<input value={properties.language||"en"} onChange={e=>set("language",e.target.value)}/></label>
    <label>Description<textarea rows={5} value={properties.description||""} onChange={e=>set("description",e.target.value)}/></label>
    <label>Keywords<input value={(properties.keywords||[]).join(", ")} onChange={e=>set("keywords",e.target.value.split(",").map(v=>v.trim()).filter(Boolean))}/></label>
  </aside>;
}
