"use client";
import { useMemo, useState } from "react";
import { StudioEditor } from "@ithute/document-editor";
import { DEFAULT_DOCUMENT_SETTINGS, emptyDoc, type DataDictionary, type IthuteDocumentV1 } from "@ithute/document-schema";

const dictionary: DataDictionary = {
  id: "demo-dictionary", name: "Sample data", version: "1",
  fields: [
    { path:"organization.name", label:"Organization name", type:"text", group:"Organization" },
    { path:"organization.registrationNumber", label:"Registration number", type:"text", group:"Organization" },
    { path:"contact.fullName", label:"Full name", type:"text", group:"Contact" },
    { path:"contact.email", label:"Email", type:"text", group:"Contact" },
    { path:"record.reference", label:"Reference", type:"text", group:"Record" },
    { path:"record.date", label:"Date", type:"date", group:"Record" },
    { path:"record.amount", label:"Amount", type:"currency", group:"Record" },
    { path:"items", label:"Items", type:"collection", group:"Collections", itemFields:[
      {path:"description",label:"Description",type:"text"},{path:"quantity",label:"Quantity",type:"number"},{path:"unitPrice",label:"Unit price",type:"currency"},{path:"total",label:"Total",type:"currency"}
    ] }
  ]
};

function createDocument(): IthuteDocumentV1 {
  const now = new Date().toISOString();
  return {schemaVersion:1,id:"demo-document",workspaceId:"demo",properties:{title:"Untitled document",author:"Ithute Document Studio",language:"en"},settings:DEFAULT_DOCUMENT_SETTINGS,header:emptyDoc(),body:{type:"doc",content:[{type:"heading",attrs:{level:1},content:[{type:"text",text:"Document title"}]},{type:"paragraph",content:[{type:"text",text:"Start writing here, or use the Data panel to insert variables."}]}]},footer:emptyDoc(),variables:{},version:1,createdAt:now,updatedAt:now};
}
export default function EditorPage(){
  const initial = useMemo(createDocument,[]); const [saved,setSaved]=useState(initial);
  const exportDocument=async(document:IthuteDocumentV1,format:"pdf"|"docx")=>{
    const base=process.env.NEXT_PUBLIC_DOCUMENT_STUDIO_API||"http://localhost:8000";
    const response=await fetch(`${base}/v1/render`,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({document,format})});
    if(!response.ok) throw new Error(await response.text());
    const blob=await response.blob(); const url=URL.createObjectURL(blob); const a=window.document.createElement("a"); a.href=url; a.download=`${document.properties.title||"document"}.${format}`; a.click(); URL.revokeObjectURL(url);
  };
  return <StudioEditor document={saved} dataDictionary={dictionary} onSave={async(next)=>{localStorage.setItem("ithute-document-studio-demo",JSON.stringify(next));setSaved(next);return next;}} onExport={exportDocument}/>;
}
