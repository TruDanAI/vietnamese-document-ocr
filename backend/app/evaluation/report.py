import json
from datetime import UTC, datetime
from pathlib import Path

from app.evaluation.metrics import summarize_field_metrics


def build_report(
    *,
    engine: str,
    model_name: str = "unknown",
    document_results: list[dict],
    skipped_samples: list[dict] | None = None,
) -> dict:
    skipped_samples = skipped_samples or []
    total_documents = len(document_results)
    passed_documents = sum(1 for item in document_results if item["passed"])
    total_fields = sum(len(item["fields"]) for item in document_results)
    exact_matches = sum(1 for item in document_results for field in item["fields"] if field["exact_match"])
    normalized_matches = sum(1 for item in document_results for field in item["fields"] if field["normalized_match"])
    missing_fields = sum(1 for item in document_results for field in item["fields"] if field["missing"])
    wrong_fields = sum(1 for item in document_results for field in item["fields"] if field["wrong"])

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "engine": engine,
        "model_name": model_name,
        "summary": {
            "total_documents": total_documents,
            "evaluated_documents": total_documents,
            "skipped_documents": len(skipped_samples),
            "passed_documents": passed_documents,
            "failed_documents": total_documents - passed_documents,
            "document_pass_rate": _ratio(passed_documents, total_documents),
            "total_fields": total_fields,
            "exact_match_accuracy": _ratio(exact_matches, total_fields),
            "normalized_match_accuracy": _ratio(normalized_matches, total_fields),
            "missing_field_count": missing_fields,
            "wrong_field_count": wrong_fields,
        },
        "field_metrics": summarize_field_metrics(document_results),
        "skipped_documents": skipped_samples,
        "documents": document_results,
    }


def write_reports(report: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    stem = f"eval-{report['engine']}-{timestamp}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(build_markdown_summary(report), encoding="utf-8")
    return json_path, markdown_path


def build_markdown_summary(report: dict) -> str:
    summary = report["summary"]
    lines = [
        f"# Evaluation Report - {report['engine']}",
        "",
        f"- Generated At: `{report['generated_at']}`",
        f"- OCR Model: `{report.get('model_name', 'unknown')}`",
        f"- Documents: {summary['passed_documents']}/{summary['total_documents']} passed",
        f"- Skipped Documents: {summary.get('skipped_documents', 0)}",
        f"- Exact Match Accuracy: {summary['exact_match_accuracy']:.2%}",
        f"- Normalized Match Accuracy: {summary['normalized_match_accuracy']:.2%}",
        f"- Missing Fields: {summary['missing_field_count']}",
        f"- Wrong Fields: {summary['wrong_field_count']}",
        "",
        "## Field Metrics",
        "",
        "| Field | Exact | Normalized | Missing | Wrong | Avg Confidence |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for field_name, metrics in report["field_metrics"].items():
        lines.append(
            "| {field} | {exact:.2%} | {normalized:.2%} | {missing} | {wrong} | {confidence:.2f} |".format(
                field=field_name,
                exact=metrics["exact_match_accuracy"],
                normalized=metrics["normalized_match_accuracy"],
                missing=metrics["missing_count"],
                wrong=metrics["wrong_count"],
                confidence=metrics["average_confidence"],
            )
        )

    lines.extend(["", "## Documents", ""])
    for document in report["documents"]:
        status = "PASS" if document["passed"] else "FAIL"
        lines.append(f"- `{document['sample_id']}` ({document['document_type']}): {status}")
    lines.append("")

    skipped_documents = report.get("skipped_documents", [])
    if skipped_documents:
        lines.extend(["## Skipped Documents", ""])
        for document in skipped_documents:
            lines.append(
                "- `{sample_id}` ({document_type}): {eval_mode} - {reason}".format(
                    sample_id=document.get("sample_id", "unknown"),
                    document_type=document.get("document_type", "unknown"),
                    eval_mode=document.get("eval_mode", "unknown"),
                    reason=document.get("reason", "skipped"),
                )
            )
        lines.append("")
    return "\n".join(lines)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
