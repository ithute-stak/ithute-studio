export type PdfCoordinateSpace = "pdf-points-top-left";
export type PdfProjectStatus = "draft" | "review" | "approved" | "signed" | "locked" | "archived";
export type PdfExportProfile = "standard" | "print" | "web" | "flattened";
export type PdfObjectType =
  | "text"
  | "cover"
  | "rectangle"
  | "ellipse"
  | "highlight"
  | "image"
  | "path"
  | "link"
  | "annotation"
  | "form-field"
  | "signature"
  | "stamp"
  | "qr"
  | "redaction";

export interface PdfBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface IthutePdfObjectV1 extends PdfBounds {
  id: string;
  page: number;
  type: PdfObjectType;
  text?: string;
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  opacity?: number;
  rotation?: number;
  zIndex?: number;
  visible?: boolean;
  locked?: boolean;
  assetId?: string;
  dataUrl?: string;
  eraseOriginal?: boolean;
  properties?: Record<string, unknown>;
}

export interface PdfDocumentMetadata {
  title?: string;
  author?: string;
  subject?: string;
  keywords: string[];
  language?: string;
  custom: Record<string, string>;
}

export interface PdfPageMetadata {
  index: number;
  width: number;
  height: number;
}

export interface IthutePdfProjectV1 {
  id: string;
  workspaceId?: string | null;
  schemaVersion: 1;
  name: string;
  status: PdfProjectStatus;
  originalFilename: string;
  sourceSha256: string;
  sourceSize: number;
  pageCount: number;
  pageOrder: number[];
  pageMetadata: PdfPageMetadata[];
  pageRotations: Record<string, number>;
  objects: IthutePdfObjectV1[];
  objectIndex: Array<Record<string, unknown>>;
  fontCatalog: Array<Record<string, unknown>>;
  metadata: PdfDocumentMetadata;
  security: Record<string, unknown>;
  importState: Record<string, unknown>;
  defaultExportProfile: PdfExportProfile;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export function viewportToPdfBounds(
  bounds: PdfBounds,
  viewport: { width: number; height: number },
  page: { width: number; height: number },
): PdfBounds {
  if (viewport.width <= 0 || viewport.height <= 0) throw new Error("Viewport dimensions must be positive");
  return {
    x: (bounds.x * page.width) / viewport.width,
    y: (bounds.y * page.height) / viewport.height,
    width: (bounds.width * page.width) / viewport.width,
    height: (bounds.height * page.height) / viewport.height,
  };
}

export function pdfToViewportBounds(
  bounds: PdfBounds,
  viewport: { width: number; height: number },
  page: { width: number; height: number },
): PdfBounds {
  if (page.width <= 0 || page.height <= 0) throw new Error("Page dimensions must be positive");
  return {
    x: (bounds.x * viewport.width) / page.width,
    y: (bounds.y * viewport.height) / page.height,
    width: (bounds.width * viewport.width) / page.width,
    height: (bounds.height * viewport.height) / page.height,
  };
}
