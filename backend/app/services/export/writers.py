import csv
import io
import json

from app.models import Document, ExtractedField


def build_export_content(document: Document, fields: list[ExtractedField], export_format: str) -> tuple[str, str]:
    if export_format == "json":
        payload = {
            "document_id": document.id,
            "filename": document.original_filename,
            "status": document.status,
            "fields": {
                field.field_name: {
                    "value": field.normalized_value,
                    "confidence": field.confidence,
                    "reviewed": field.is_reviewed,
                }
                for field in fields
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2), "json"

    if export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["field_name", "value", "confidence", "reviewed"])
        for field in fields:
            writer.writerow([field.field_name, field.normalized_value or "", field.confidence, field.is_reviewed])
        return output.getvalue(), "csv"

    raise ValueError(f"Unsupported export format: {export_format}")
