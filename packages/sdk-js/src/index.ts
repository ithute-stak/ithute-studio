import type { IthuteDocumentV1, SourceReference } from "@ithute/document-schema";
export class IthuteDocumentStudioClient {
  constructor(public readonly baseUrl:string, private readonly token?:string){}
  private async request<T>(path:string,init:RequestInit={}):Promise<T>{const response=await fetch(`${this.baseUrl.replace(/\/$/,"")}${path}`,{...init,headers:{"content-type":"application/json",...(this.token?{authorization:`Bearer ${this.token}`}:{...{}}),...(init.headers||{})}});if(!response.ok)throw new Error(`Document Studio ${response.status}: ${await response.text()}`);return response.json() as Promise<T>;}
  generateFromTemplate(template:IthuteDocumentV1,data:Record<string,unknown>,source?:SourceReference){return this.request<IthuteDocumentV1>("/v1/documents/from-template",{method:"POST",body:JSON.stringify({template,data,source})});}
}
