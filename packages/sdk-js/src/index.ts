import type { IthuteDocumentV1, SourceReference } from "@ithute/document-schema";
import type { IthutePdfProjectV1, PdfExportProfile } from "@ithute/pdf-schema";

export class IthuteDocumentStudioClient {
  constructor(public readonly baseUrl:string, private readonly token?:string){}

  private headers(init: RequestInit): HeadersInit {
    const base: Record<string,string> = this.token ? {authorization:`Bearer ${this.token}`} : {};
    if (!(init.body instanceof FormData)) base["content-type"] = "application/json";
    return {...base,...(init.headers||{})};
  }

  private async request<T>(path:string,init:RequestInit={}):Promise<T>{
    const response=await fetch(`${this.baseUrl.replace(/\/$/,"")}${path}`,{...init,headers:this.headers(init)});
    if(!response.ok)throw new Error(`Document Studio ${response.status}: ${await response.text()}`);
    return response.json() as Promise<T>;
  }

  private async requestBlob(path:string,init:RequestInit={}):Promise<Blob>{
    const response=await fetch(`${this.baseUrl.replace(/\/$/,"")}${path}`,{...init,headers:this.headers(init)});
    if(!response.ok)throw new Error(`Document Studio ${response.status}: ${await response.text()}`);
    return response.blob();
  }

  generateFromTemplate(template:IthuteDocumentV1,data:Record<string,unknown>,source?:SourceReference){
    return this.request<IthuteDocumentV1>("/v1/documents/from-template",{method:"POST",body:JSON.stringify({template,data,source})});
  }

  listPdfProjects(){return this.request<IthutePdfProjectV1[]>("/v1/pdf/projects");}
  getPdfProject(id:string){return this.request<IthutePdfProjectV1>(`/v1/pdf/projects/${id}`);}
  uploadPdf(file:Blob, options:{name?:string;workspaceId?:string;password?:string;filename?:string}={}){
    const form=new FormData();
    form.append("file",file,options.filename||"document.pdf");
    if(options.name)form.append("name",options.name);
    if(options.workspaceId)form.append("workspaceId",options.workspaceId);
    if(options.password)form.append("password",options.password);
    return this.request<IthutePdfProjectV1>("/v1/pdf/projects",{method:"POST",body:form});
  }
  savePdfProject(id:string, update:Record<string,unknown>){
    return this.request<IthutePdfProjectV1>(`/v1/pdf/projects/${id}`,{method:"PUT",body:JSON.stringify(update)});
  }
  listPdfRevisions(id:string){return this.request<Array<Record<string,unknown>>>(`/v1/pdf/projects/${id}/revisions`);}
  restorePdfRevision(id:string,version:number,expectedVersion?:number){
    return this.request<IthutePdfProjectV1>(`/v1/pdf/projects/${id}/revisions/${version}/restore`,{method:"POST",body:JSON.stringify(expectedVersion?{expectedVersion}:{})});
  }
  listPdfAssets(id:string){return this.request<Array<Record<string,unknown>>>(`/v1/pdf/projects/${id}/assets`);}
  uploadPdfAsset(id:string,file:Blob,filename="asset"){
    const form=new FormData(); form.append("file",file,filename);
    return this.request<Record<string,unknown>>(`/v1/pdf/projects/${id}/assets`,{method:"POST",body:form});
  }
  listPdfJobs(id:string){return this.request<Array<Record<string,unknown>>>(`/v1/pdf/projects/${id}/jobs`);}
  listPdfAudit(id:string){return this.request<Array<Record<string,unknown>>>(`/v1/pdf/projects/${id}/audit`);}
  exportPdf(id:string,profile?:PdfExportProfile){
    return this.requestBlob(`/v1/pdf/projects/${id}/export`,{method:"POST",body:JSON.stringify(profile?{profile}:{})});
  }
}
