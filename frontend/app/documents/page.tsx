"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DocumentItem, listDocuments } from "../../lib/api";
import { DocumentUploader } from "../../components/document-uploader";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setDocuments(await listDocuments());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <>
      <div className="header">
        <h1>Documents</h1>
      </div>

      <section className="section">
        <DocumentUploader onUploaded={refresh} />
      </section>

      {error ? <p className="surface">{error}</p> : null}

      <section className="surface">
        <table className="table">
          <thead>
            <tr>
              <th>File</th>
              <th>Status</th>
              <th>Type</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td>{document.original_filename}</td>
                <td>
                  <span className="badge">{document.status}</span>
                </td>
                <td>{document.document_type}</td>
                <td>{new Date(document.created_at).toLocaleString()}</td>
                <td>
                  <Link className="link" href={`/documents/${document.id}`}>
                    Review
                  </Link>
                </td>
              </tr>
            ))}
            {documents.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No documents uploaded yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>
    </>
  );
}
