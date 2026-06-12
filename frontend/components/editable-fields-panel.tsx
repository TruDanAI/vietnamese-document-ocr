"use client";

import { useState } from "react";
import { ExtractedField, updateField } from "../lib/api";

export function EditableFieldsPanel({
  fields,
  onChanged
}: {
  documentId: string;
  fields: ExtractedField[];
  onChanged: () => void;
}) {
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);

  async function save(field: ExtractedField) {
    setSavingId(field.id);
    try {
      await updateField(field.id, drafts[field.id] ?? field.normalized_value ?? "");
      onChanged();
    } finally {
      setSavingId(null);
    }
  }

  return (
    <section className="surface">
      <h2>Review fields</h2>
      {fields.length === 0 ? <p className="muted">No extracted fields yet.</p> : null}
      {fields.map((field) => {
        const value = drafts[field.id] ?? field.normalized_value ?? "";
        return (
          <div className="field-row" key={field.id}>
            <label htmlFor={field.id}>
              {field.field_name}
              <br />
              <span className="muted">{Math.round(field.confidence * 100)}%</span>
            </label>
            <div className="toolbar">
              <input
                id={field.id}
                value={value}
                onChange={(event) => setDrafts((current) => ({ ...current, [field.id]: event.target.value }))}
              />
              <button className="button secondary" disabled={savingId === field.id} onClick={() => save(field)}>
                Save
              </button>
            </div>
          </div>
        );
      })}
    </section>
  );
}
