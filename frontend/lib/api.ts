export type DocumentItem = {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  storage_path: string;
  document_type: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type DocumentDetail = DocumentItem & {
  pages: Array<{
    id: string;
    page_number: number;
    image_path: string | null;
    width: number | null;
    height: number | null;
  }>;
};

export type OcrRun = {
  id: string;
  document_id: string;
  engine_name: string;
  status: string;
};

export type OcrBlock = {
  id: string;
  page_number: number | null;
  block_index: number;
  text: string;
  confidence: number;
  bbox: Record<string, unknown>;
};

export type ExtractedField = {
  id: string;
  field_name: string;
  normalized_value: string | null;
  confidence: number;
  is_reviewed: boolean;
};

export type ExportJob = {
  id: string;
  format: string;
  storage_path: string;
  status: string;
};

export type EvaluationReport = {
  filename: string;
  format: string;
  size_bytes: number;
  modified_at: number;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store"
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  return apiFetch<DocumentItem[]>("/documents");
}

export async function getDocument(id: string): Promise<DocumentDetail> {
  return apiFetch<DocumentDetail>(`/documents/${id}`);
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<DocumentItem>("/documents/upload", {
    method: "POST",
    body: form
  });
}

export async function runOcr(documentId: string): Promise<OcrRun> {
  return apiFetch<OcrRun>(`/documents/${documentId}/ocr-runs`, { method: "POST" });
}

export async function getOcrBlocks(ocrRunId: string): Promise<OcrBlock[]> {
  return apiFetch<OcrBlock[]>(`/ocr-runs/${ocrRunId}/blocks`);
}

export async function getLatestOcrBlocks(documentId: string): Promise<OcrBlock[]> {
  return apiFetch<OcrBlock[]>(`/documents/${documentId}/ocr-blocks`);
}

export async function getFields(documentId: string): Promise<ExtractedField[]> {
  return apiFetch<ExtractedField[]>(`/documents/${documentId}/fields`);
}

export async function updateField(fieldId: string, value: string): Promise<ExtractedField> {
  return apiFetch<ExtractedField>(`/extracted-fields/${fieldId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ normalized_value: value, corrected_by: "review-ui" })
  });
}

export async function approveDocument(documentId: string): Promise<{ ok: boolean; status: string }> {
  return apiFetch(`/documents/${documentId}/review/approve`, { method: "POST" });
}

export async function createExport(documentId: string, format: "json" | "csv" | "xlsx"): Promise<ExportJob> {
  return apiFetch<ExportJob>(`/documents/${documentId}/exports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format })
  });
}

export function exportDownloadUrl(exportId: string): string {
  return `${API_BASE_URL}/exports/${exportId}/download`;
}

export function pageImageUrl(pageId: string): string {
  return `${API_BASE_URL}/documents/pages/${pageId}/image`;
}

export async function listEvaluationReports(): Promise<EvaluationReport[]> {
  return apiFetch<EvaluationReport[]>("/evaluations/reports");
}

export function evaluationReportUrl(filename: string): string {
  return `${API_BASE_URL}/evaluations/reports/${encodeURIComponent(filename)}`;
}
