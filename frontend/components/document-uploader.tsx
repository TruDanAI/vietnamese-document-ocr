"use client";

import { FormEvent, useState } from "react";
import { uploadDocument } from "../lib/api";

export function DocumentUploader({ onUploaded }: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setMessage(null);
    try {
      await uploadDocument(file);
      setFile(null);
      setMessage("Uploaded.");
      onUploaded();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="surface toolbar" onSubmit={onSubmit}>
      <input
        type="file"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        aria-label="Upload document"
      />
      <button className="button" disabled={!file || busy} type="submit">
        {busy ? "Uploading..." : "Upload"}
      </button>
      {message ? <span className="muted">{message}</span> : null}
    </form>
  );
}
