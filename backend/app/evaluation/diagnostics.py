import re
from datetime import UTC, datetime
from pathlib import Path

from app.evaluation.normalize import normalize_text


PREVIEW_LINE_LIMIT = 20


def write_diagnostics_report(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    engine_name = report.get("engine", "unknown")
    path = output_dir / f"{timestamp}-{engine_name}-diagnostics.md"
    path.write_text(build_diagnostics_markdown(report), encoding="utf-8")
    return path


def build_diagnostics_markdown(report: dict) -> str:
    engine_name = report.get("engine", "unknown")
    model_name = report.get("model_name", "unknown")
    failed_documents = [document for document in report.get("documents", []) if not document.get("passed")]
    skipped_documents = report.get("skipped_documents", [])

    lines = [
        f"# Evaluation Diagnostics - {engine_name}",
        "",
        f"- generated_at: `{datetime.now(UTC).isoformat()}`",
        f"- engine_name: `{engine_name}`",
        f"- model_name: `{model_name}`",
        f"- failed_samples: {len(failed_documents)}",
        f"- skipped_samples: {len(skipped_documents)}",
        "",
    ]

    if skipped_documents:
        lines.extend(_build_skipped_section(skipped_documents))

    if not failed_documents:
        lines.append("No failed samples.")
        lines.append("")
        return "\n".join(lines)

    for document in failed_documents:
        lines.extend(_build_document_section(document))

    return "\n".join(lines)


def _build_skipped_section(skipped_documents: list[dict]) -> list[str]:
    lines = [
        "## Skipped Mock-Only Samples",
        "",
        "These fixtures were skipped because their expected JSON is for deterministic mock OCR, not visible real OCR content.",
        "",
    ]
    for document in skipped_documents:
        lines.append(
            "- `{sample_id}` ({document_type}): {reason}".format(
                sample_id=document.get("sample_id", "unknown"),
                document_type=document.get("document_type", "unknown"),
                reason=document.get("reason", "skipped"),
            )
        )
    lines.append("")
    return lines


def _build_document_section(document: dict) -> list[str]:
    exact_accuracy, normalized_accuracy = _sample_accuracy(document)
    ocr_lines = [str(line) for line in document.get("ocr_text_lines", [])]
    preview_lines = ocr_lines[:PREVIEW_LINE_LIMIT]
    normalized_preview_lines = [normalize_text(line) for line in preview_lines]
    missing_count = sum(1 for field in document.get("fields", []) if _field_status(field) == "missing")
    wrong_count = sum(1 for field in document.get("fields", []) if _field_status(field) == "wrong")

    lines = [
        f"## {document.get('sample_id', 'unknown')}",
        "",
        "### Sample Metadata",
        "",
        f"- sample_id: `{document.get('sample_id', 'unknown')}`",
        f"- document_type: `{document.get('document_type', 'unknown')}`",
        f"- engine_name: `{document.get('engine_name', document.get('engine', 'unknown'))}`",
        f"- model_name: `{document.get('model_name', 'unknown')}`",
        f"- Exact Accuracy: {exact_accuracy:.2%}",
        f"- Normalized Accuracy: {normalized_accuracy:.2%}",
        "",
        "### OCR Text Preview",
        "",
        f"- OCR Block Count: {document.get('ocr_block_count', len(ocr_lines))}",
        "",
        "```text",
        *preview_lines,
        "```",
        "",
        "### Normalized OCR Text Preview",
        "",
        "```text",
        *normalized_preview_lines,
        "```",
        "",
        "### Expected vs Extracted Fields",
        "",
        "| field | expected | extracted | status |",
        "| --- | --- | --- | --- |",
    ]

    for field in document.get("fields", []):
        lines.append(
            "| {field} | {expected} | {extracted} | {status} |".format(
                field=_escape_table_text(field.get("field_name", "")),
                expected=_format_table_value(field.get("expected")),
                extracted=_format_table_value(field.get("actual")),
                status=_field_status(field),
            )
        )

    lines.extend(
        [
            "",
            "### Failure Summary",
            "",
            f"- Missing Fields: {missing_count}",
            f"- Wrong Fields: {wrong_count}",
            f"- Likely Failure Category: {_likely_failure_category(document)}",
            "",
        ]
    )
    return lines


def _sample_accuracy(document: dict) -> tuple[float, float]:
    fields = document.get("fields", [])
    total = len(fields)
    if total == 0:
        return 0.0, 0.0
    exact_matches = sum(1 for field in fields if field.get("exact_match"))
    normalized_matches = sum(1 for field in fields if field.get("normalized_match"))
    return exact_matches / total, normalized_matches / total


def _field_status(field: dict) -> str:
    if field.get("normalized_match"):
        return "pass"
    if field.get("missing"):
        return "missing"
    return "wrong"


def _likely_failure_category(document: dict) -> str:
    failed_fields = [field for field in document.get("fields", []) if _field_status(field) != "pass"]
    ocr_text = "\n".join(str(line) for line in document.get("ocr_text_lines", []))
    if document.get("ocr_block_count", 0) == 0 or not ocr_text.strip():
        return "OCR missing text"
    if any(_value_appears_in_ocr(field.get("expected"), ocr_text) for field in failed_fields):
        return "extraction rule miss"
    if any(_similar_value_appears_in_ocr(field.get("expected"), ocr_text) for field in failed_fields):
        return "OCR text mismatch"
    if any(_formatting_difference(field) for field in failed_fields):
        return "normalization mismatch"
    return "unknown"


def _value_appears_in_ocr(value: str | None, ocr_text: str) -> bool:
    if not value:
        return False
    value_text = str(value).strip()
    if not value_text:
        return False
    if value_text in ocr_text:
        return True
    return normalize_text(value_text) in normalize_text(ocr_text)


def _similar_value_appears_in_ocr(value: str | None, ocr_text: str) -> bool:
    if not value:
        return False
    value_text = str(value)
    expected_digits = re.sub(r"\D", "", value_text)
    ocr_digits = re.sub(r"\D", "", ocr_text)
    if len(expected_digits) >= 4 and expected_digits[:4] in ocr_digits:
        return True

    expected_tokens = [token for token in normalize_text(value_text).split() if len(token) >= 4]
    ocr_normalized = normalize_text(ocr_text)
    matched_tokens = sum(1 for token in expected_tokens if token in ocr_normalized)
    return bool(expected_tokens) and 0 < matched_tokens < len(expected_tokens)


def _formatting_difference(field: dict) -> bool:
    expected = field.get("expected")
    actual = field.get("actual")
    if not expected or not actual:
        return False
    expected_compact = _compact_for_formatting(str(expected))
    actual_compact = _compact_for_formatting(str(actual))
    return bool(expected_compact) and expected_compact == actual_compact


def _compact_for_formatting(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", normalize_text(value))


def _format_table_value(value: str | None) -> str:
    if value is None or str(value) == "":
        return ""
    escaped = _escape_table_text(str(value).replace("\r", " ").replace("\n", " "))
    return f"`{escaped}`"


def _escape_table_text(value: str) -> str:
    return value.replace("`", "\\`").replace("|", "\\|")
