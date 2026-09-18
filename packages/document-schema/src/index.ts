export type PageSize = "a4" | "letter";
export type Orientation = "portrait" | "landscape";
export type TemplateCategory =
  | "general-business" | "finance" | "lending" | "legal" | "hr"
  | "education" | "fleet" | "construction" | "risk" | "payments" | "government-official" | "custom";

export type JsonObject = Record<string, unknown>;
export type TiptapMark = { type: string; attrs?: JsonObject };
export type TiptapJson = { type: string; attrs?: JsonObject; content?: TiptapJson[]; marks?: TiptapMark[]; text?: string };

export interface PageMarginsMm { top: number; right: number; bottom: number; left: number; }

export interface DocumentSettings {
  pageSize: PageSize;
  orientation: Orientation;
  marginsMm: PageMarginsMm;
  columns: 1 | 2 | 3;
  headerDistanceMm: number;
  footerDistanceMm: number;
  showRulers: boolean;
  watermark?: { text?: string; imageUrl?: string; opacity: number; rotation: number };
  pageNumbering?: { enabled: boolean; startAt: number; format: "1" | "i" | "I" | "a" | "A"; position: "header" | "footer" };
}

export interface DocumentDesign {
  preset?: string;
  primaryColor?: string;
  secondaryColor?: string;
  accentColor?: string;
  textColor?: string;
  mutedColor?: string;
  borderColor?: string;
  fontFamily?: string;
  headerStyle?: "band" | "split" | "left-accent" | "minimal" | "ledger" | string;
  footerStyle?: "line" | "band" | "double-line" | "minimal" | string;
  documentLabel?: string;
  documentPrefix?: string;
  logoUrl?: string;
}

export interface DocumentProperties {
  title: string;
  subject?: string;
  author?: string;
  company?: string;
  category?: string;
  keywords?: string[];
  description?: string;
  language?: string;
}

export interface SourceReference {
  provider?: string;
  entityType?: string;
  entityId?: string;
  externalUrl?: string;
  metadata?: JsonObject;
}

export interface IthuteDocumentV1 {
  schemaVersion: 1;
  id: string;
  workspaceId: string;
  templateId?: string;
  properties: DocumentProperties;
  settings: DocumentSettings;
  design?: DocumentDesign;
  header: TiptapJson;
  body: TiptapJson;
  footer: TiptapJson;
  variables: Record<string, unknown>;
  source?: SourceReference;
  createdAt: string;
  updatedAt: string;
  version: number;
}

export type DataFieldType = "text" | "number" | "currency" | "date" | "boolean" | "image" | "url" | "object" | "collection";

export interface DataDictionaryField {
  key?: string;
  label: string;
  path: string;
  type: DataFieldType;
  description?: string;
  group?: string;
  children?: DataDictionaryField[];
  itemFields?: DataDictionaryField[];
}

export interface DataDictionary {
  id: string;
  name: string;
  description?: string;
  version?: string;
  fields: DataDictionaryField[];
}

export interface TemplateDefinition {
  id: string;
  workspaceId?: string;
  name: string;
  description?: string;
  category: TemplateCategory;
  tags: string[];
  document: IthuteDocumentV1;
  dataDictionaryId?: string;
  isPublished: boolean;
  createdAt: string;
  updatedAt: string;
}

export const DEFAULT_DOCUMENT_SETTINGS: DocumentSettings = {
  pageSize: "a4",
  orientation: "portrait",
  marginsMm: { top: 20, right: 20, bottom: 20, left: 20 },
  columns: 1,
  headerDistanceMm: 10,
  footerDistanceMm: 10,
  showRulers: true,
  pageNumbering: { enabled: true, startAt: 1, format: "1", position: "footer" }
};

export const emptyDoc = (): TiptapJson => ({ type: "doc", content: [{ type: "paragraph" }] });
