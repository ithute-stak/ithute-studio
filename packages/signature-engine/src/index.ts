import type { IthuteDocumentV1, TiptapJson } from "@ithute/document-schema";
export type SignatureFieldType="signature"|"initials"|"date"|"name"|"title"|"text"|"checkbox";
export interface SignatureField { id:string; type:SignatureFieldType; label:string; required:boolean; assigneeRole?:string; region:"header"|"body"|"footer"; }
export interface SignatureValue { fieldId:string; signerId:string; value:string|boolean; signedAt:string; method:"drawn"|"typed"|"uploaded"|"acknowledgement"; }
function walk(node:TiptapJson,region:SignatureField["region"],out:SignatureField[]){
  if(node.type==="signature"){const a=(node.attrs||{}) as Record<string,unknown>;out.push({id:String(a.fieldId||crypto.randomUUID()),type:String(a.fieldType||"signature") as SignatureFieldType,label:String(a.label||"Signature"),required:a.required!==false,assigneeRole:a.assigneeRole?String(a.assigneeRole):undefined,region});}
  for(const child of node.content||[]) walk(child,region,out);
}
export function listSignatureFields(document:IthuteDocumentV1){const out:SignatureField[]=[];walk(document.header,"header",out);walk(document.body,"body",out);walk(document.footer,"footer",out);return out;}
export function validateSignatureCompletion(document:IthuteDocumentV1,values:SignatureValue[]){const completed=new Set(values.map(v=>v.fieldId));return listSignatureFields(document).filter(f=>f.required&&!completed.has(f.id));}
