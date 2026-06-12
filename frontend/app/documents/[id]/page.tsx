"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  DocumentDetail,
  ExportJob,
  ExtractedField,
  OcrBlock,
  approveDocument,
  createExport,
  exportDownloadUrl,
  getDocument,
  getFields,
  getLatestOcrBlocks,
  getOcrBlocks,
  pageImageUrl,
  runOcr
} from "../../../lib/api";
import { EditableFieldsPanel } from "../../../components/editable-fields-panel";

export default function DocumentReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [blocks, setBlocks] = useState<OcrBlock[]>([]);
  const [exportJob, setExportJob] = useState<ExportJob | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [activeBlockId, setActiveBlockId] = useState<string | null>(null);

  async function refresh() {
    setDocument(await getDocument(id));
    setFields(await getFields(id));
    setBlocks(await getLatestOcrBlocks(id));
  }

  useEffect(() => {
    void refresh();
  }, [id]);

  async function handleRunOcr() {
    setBusy(true);
    setMessage(null);
    try {
      const run = await runOcr(id);
      setBlocks(await getOcrBlocks(run.id));
      await refresh();
      setMessage("OCR and extraction completed.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "OCR failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleApprove() {
    setBusy(true);
    try {
      await approveDocument(id);
      await refresh();
      setMessage("Document approved.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Approve failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleExport(format: "json" | "csv" | "xlsx") {
    setBusy(true);
    try {
      setExportJob(await createExport(id, format));
      setMessage(`${format.toUpperCase()} export created.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(false);
    }
  }

  if (!document) {
    return <p className="surface">Loading...</p>;
  }

  return (
    <>
      <div className="header">
        <h1>{document.original_filename}</h1>
      </div>

      <div className="section toolbar">
        <Link className="link" href="/documents">
          Back
        </Link>
        <span className="badge">{document.status}</span>
        <button className="button" disabled={busy} onClick={handleRunOcr}>
          Run OCR
        </button>
        <button className="button secondary" disabled={busy || fields.length === 0} onClick={handleApprove}>
          Approve
        </button>
        <button className="button secondary" disabled={busy || fields.length === 0} onClick={() => handleExport("json")}>
          Export JSON
        </button>
        <button className="button secondary" disabled={busy || fields.length === 0} onClick={() => handleExport("csv")}>
          Export CSV
        </button>
        <button className="button secondary" disabled={busy || fields.length === 0} onClick={() => handleExport("xlsx")}>
          Export XLSX
        </button>
        {message ? <span className="muted">{message}</span> : null}
      </div>

      {exportJob ? (
        <p className="surface">
          Export ready:{" "}
          <a className="link" href={exportDownloadUrl(exportJob.id)}>
            Download {exportJob.format.toUpperCase()}
          </a>
        </p>
      ) : null}

      <div className="grid">
        <section className="surface">
          <h2>Page image and OCR blocks</h2>
          {document.pages[0] ? (
            <PageEvidence
              page={document.pages[0]}
              blocks={blocks}
              activeBlockId={activeBlockId}
            />
          ) : (
            <p className="muted">No page image available.</p>
          )}
          <h3>OCR text</h3>
          {blocks.length === 0 ? <p className="muted">Run OCR to see OCR text blocks.</p> : null}
          {blocks.map((block) => (
            <div
              className={`ocr-block ${activeBlockId === block.id ? "active" : ""}`}
              key={block.id}
              onClick={() => setActiveBlockId(block.id)}
            >
              <strong>{block.text}</strong>
              <div className="muted">confidence {(block.confidence * 100).toFixed(0)}%</div>
            </div>
          ))}
        </section>

        <EditableFieldsPanel documentId={id} fields={fields} onChanged={refresh} />
      </div>
    </>
  );
}

function PageEvidence({
  page,
  blocks,
  activeBlockId
}: {
  page: DocumentDetail["pages"][number];
  blocks: OcrBlock[];
  activeBlockId: string | null;
}) {
  const pageBlocks = blocks.filter((block) => block.page_number === page.page_number);
  const width = page.width || 1;
  const height = page.height || 1;

  return (
    <div className="page-preview">
      <img src={pageImageUrl(page.id)} alt={`Page ${page.page_number}`} />
      {pageBlocks.map((block) => {
        const bbox = block.bbox as { x?: number; y?: number; width?: number; height?: number };
        if (bbox.x == null || bbox.y == null || bbox.width == null || bbox.height == null) {
          return null;
        }
        return (
          <div
            key={block.id}
            className={`bbox ${activeBlockId === block.id ? "active" : ""}`}
            style={{
              left: `${(bbox.x / width) * 100}%`,
              top: `${(bbox.y / height) * 100}%`,
              width: `${(bbox.width / width) * 100}%`,
              height: `${(bbox.height / height) * 100}%`
            }}
          />
        );
      })}
    </div>
  );
}
