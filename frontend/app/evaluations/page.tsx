"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { EvaluationReport, evaluationReportUrl, listEvaluationReports } from "../../lib/api";

export default function EvaluationsPage() {
  const [reports, setReports] = useState<EvaluationReport[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listEvaluationReports()
      .then((items) => {
        setReports(items);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load reports"));
  }, []);

  return (
    <>
      <div className="header">
        <h1>Evaluation Reports</h1>
      </div>
      <div className="section toolbar">
        <Link className="link" href="/documents">
          Documents
        </Link>
      </div>
      {error ? <p className="surface">{error}</p> : null}
      <section className="surface">
        <table className="table">
          <thead>
            <tr>
              <th>Report</th>
              <th>Format</th>
              <th>Size</th>
              <th>Modified</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.filename}>
                <td>
                  <a className="link" href={evaluationReportUrl(report.filename)}>
                    {report.filename}
                  </a>
                </td>
                <td>{report.format}</td>
                <td>{report.size_bytes} bytes</td>
                <td>{new Date(report.modified_at * 1000).toLocaleString()}</td>
              </tr>
            ))}
            {reports.length === 0 ? (
              <tr>
                <td colSpan={4} className="muted">
                  No reports yet. Run `python -m app.evaluation.run --engine mock` from the backend folder.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>
    </>
  );
}
