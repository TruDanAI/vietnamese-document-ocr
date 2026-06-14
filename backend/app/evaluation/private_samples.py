import argparse
import json
import mimetypes
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.models import OcrBlock
from app.services.extraction.rules import ExtractedFieldResult, extract_fields
from app.services.ocr.factory import build_ocr_adapter
from app.services.preprocessing import create_page_images


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORAGE_DIR = REPO_ROOT / "storage" / "dev"
DEFAULT_INPUT_DIR = DEFAULT_STORAGE_DIR / "private_samples"
DEFAULT_OUTPUT_DIR = DEFAULT_STORAGE_DIR / "eval_reports"
DEFAULT_PAGES_DIR = DEFAULT_STORAGE_DIR / "pages"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
OCR_PREVIEW_LINE_LIMIT = 20

SAFETY_WARNINGS = [
    "Use anonymized documents only.",
    "Do not include CCCD/CMND, passports, or faces.",
    "Do not include QR codes, bank accounts, real tax codes, addresses, phone numbers, emails, or unmasked identifiers.",
    "Generated reports may contain extracted sensitive data and must remain local-only.",
]


@dataclass(frozen=True)
class PrivateSampleRunResult:
    document_count: int
    markdown_path: Path | None = None
    json_path: Path | None = None
    report: dict | None = None


class PrivateSamplePageStorage:
    def __init__(self, pages_dir: Path) -> None:
        self.pages_dir = pages_dir

    def write_page_image(self, document_id: str, page_number: int, content: bytes) -> str:
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        safe_document_id = _safe_filename(document_id)
        path = self.pages_dir / f"{safe_document_id}-page-{page_number:03d}.png"
        path.write_bytes(content)
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local-only anonymized private sample OCR smoke testing.")
    parser.add_argument(
        "--engine",
        default="mock",
        help="OCR engine: mock, paddle, or experimental ppocrv6.",
    )
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--pages-dir",
        default=None,
        help="Directory for rendered pages. Defaults to storage/dev/pages for default output, or a pages sibling of a custom output dir.",
    )
    parser.add_argument(
        "--include-ocr-preview",
        action="store_true",
        help="Include a limited raw OCR text preview in local-only reports.",
    )
    args = parser.parse_args()

    try:
        result = run_private_sample_harness(
            engine=args.engine,
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            pages_dir=Path(args.pages_dir) if args.pages_dir else None,
            include_ocr_preview=args.include_ocr_preview,
        )
    except (RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    if result.document_count == 0:
        return

    print(f"Private sample smoke test complete for engine={args.engine}")
    print(f"Documents processed: {result.document_count}")
    print(f"Markdown report: {result.markdown_path}")
    print(f"JSON report: {result.json_path}")


def run_private_sample_harness(
    *,
    engine: str,
    input_dir: Path,
    output_dir: Path,
    pages_dir: Path | None = None,
    include_ocr_preview: bool = False,
) -> PrivateSampleRunResult:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    pages_dir = Path(pages_dir) if pages_dir is not None else output_dir.parent / "pages"

    print_safety_warning()
    sample_files = discover_private_samples(input_dir)
    if not sample_files:
        print(
            "No supported private sample files found in "
            f"{input_dir}. Add anonymized .png, .jpg, .jpeg, or .pdf files locally and re-run."
        )
        return PrivateSampleRunResult(document_count=0)

    unsupported_files = discover_unsupported_files(input_dir)
    adapter = build_ocr_adapter(engine)
    report = build_private_sample_report(
        sample_files=sample_files,
        unsupported_files=unsupported_files,
        adapter=adapter,
        pages_dir=pages_dir,
        include_ocr_preview=include_ocr_preview,
    )
    markdown_path, json_path = write_private_sample_reports(report, output_dir)
    return PrivateSampleRunResult(
        document_count=len(sample_files),
        markdown_path=markdown_path,
        json_path=json_path,
        report=report,
    )


def print_safety_warning() -> None:
    print("Local private sample safety warning:")
    for warning in SAFETY_WARNINGS:
        print(f"- {warning}")


def discover_private_samples(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        (
            path
            for path in input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )


def discover_unsupported_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        (
            path
            for path in input_dir.iterdir()
            if path.is_file() and path.suffix.lower() not in SUPPORTED_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )


def build_private_sample_report(
    *,
    sample_files: list[Path],
    unsupported_files: list[Path],
    adapter,
    pages_dir: Path,
    include_ocr_preview: bool,
) -> dict:
    document_results = [
        _process_private_sample(
            sample_file=sample_file,
            sample_index=index,
            adapter=adapter,
            pages_dir=pages_dir,
            include_ocr_preview=include_ocr_preview,
        )
        for index, sample_file in enumerate(sample_files, start=1)
    ]
    warnings = list(SAFETY_WARNINGS)
    if unsupported_files:
        warnings.append(
            "Ignored unsupported files: "
            + ", ".join(path.name for path in unsupported_files)
        )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "engine": adapter.engine_name,
        "model_name": adapter.model_name,
        "summary": {
            "document_count": len(document_results),
            "page_count": sum(document["page_count"] for document in document_results),
            "ocr_block_count": sum(document["ocr_block_count"] for document in document_results),
            "preview_included": include_ocr_preview,
        },
        "warnings": warnings,
        "documents": document_results,
    }


def write_private_sample_reports(report: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    engine_name = _safe_filename(str(report.get("engine", "unknown")))
    stem = f"private-samples-{timestamp}-{engine_name}"
    markdown_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"
    markdown_path.write_text(build_private_sample_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return markdown_path, json_path


def _process_private_sample(
    *,
    sample_file: Path,
    sample_index: int,
    adapter,
    pages_dir: Path,
    include_ocr_preview: bool,
) -> dict:
    document_id = f"private-{sample_index:03d}-{sample_file.stem}"
    document_warnings: list[str] = []

    try:
        content_type = mimetypes.guess_type(sample_file.name)[0] or "application/octet-stream"
        pages = create_page_images(
            document_id=document_id,
            storage_path=str(sample_file),
            content_type=content_type,
            storage=PrivateSamplePageStorage(pages_dir),
        )
        blocks = _run_ocr_pages(document_id=document_id, pages=pages, adapter=adapter)
        extracted_fields = extract_fields(blocks)
    except Exception as exc:
        pages = []
        blocks = []
        extracted_fields = []
        document_warnings.append(f"Processing failed: {exc}")

    result = {
        "file_name": sample_file.name,
        "engine_name": adapter.engine_name,
        "model_name": adapter.model_name,
        "page_count": len(pages),
        "ocr_block_count": len(blocks),
        "extracted_fields": [_serialize_field(field) for field in extracted_fields],
        "warnings": document_warnings,
    }
    if include_ocr_preview:
        result["ocr_preview"] = [block.text for block in blocks[:OCR_PREVIEW_LINE_LIMIT]]
    return result


def _run_ocr_pages(*, document_id: str, pages: list[dict], adapter) -> list[OcrBlock]:
    blocks: list[OcrBlock] = []
    global_block_index = 0
    for page in pages:
        page_number = int(page["page_number"])
        page_id = f"{document_id}-page-{page_number}"
        for result in adapter.run_page(page["image_path"], page_number):
            blocks.append(
                OcrBlock(
                    id=f"{document_id}-block-{global_block_index}",
                    ocr_run_id=f"{document_id}-ocr",
                    page_id=page_id,
                    block_index=global_block_index,
                    text=result.text,
                    confidence=result.confidence,
                    bbox=result.bbox,
                )
            )
            global_block_index += 1
    return blocks


def _serialize_field(field: ExtractedFieldResult) -> dict:
    return {
        "field_name": field.field_name,
        "raw_value": field.raw_value,
        "normalized_value": field.normalized_value,
        "confidence": field.confidence,
        "source_block_ids": field.source_block_ids,
    }


def build_private_sample_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        f"# Private Sample Smoke Report - {report['engine']}",
        "",
        f"- Generated At: `{report['generated_at']}`",
        f"- Engine: `{report['engine']}`",
        f"- OCR Model: `{report.get('model_name', 'unknown')}`",
        f"- Documents: {summary['document_count']}",
        f"- Pages: {summary['page_count']}",
        f"- OCR Blocks: {summary['ocr_block_count']}",
        f"- OCR Preview Included: {'yes' if summary['preview_included'] else 'no'}",
        "",
        "## Warnings",
        "",
    ]
    for warning in report.get("warnings", []):
        lines.append(f"- {warning}")

    lines.extend(["", "## Documents", ""])
    for document in report.get("documents", []):
        lines.extend(_build_document_markdown(document))
    return "\n".join(lines)


def _build_document_markdown(document: dict) -> list[str]:
    lines = [
        f"### {document.get('file_name', 'unknown')}",
        "",
        f"- Engine Name: `{document.get('engine_name', 'unknown')}`",
        f"- Model Name: `{document.get('model_name', 'unknown')}`",
        f"- Page Count: {document.get('page_count', 0)}",
        f"- OCR Block Count: {document.get('ocr_block_count', 0)}",
    ]
    warnings = document.get("warnings", [])
    if warnings:
        lines.append(f"- Warnings: {'; '.join(str(warning) for warning in warnings)}")
    else:
        lines.append("- Warnings: none")

    lines.extend(
        [
            "",
            "#### Extracted Fields",
            "",
            "| field | raw value | normalized value | confidence |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for field in document.get("extracted_fields", []):
        lines.append(
            "| {field} | {raw} | {normalized} | {confidence:.2f} |".format(
                field=_escape_table_text(str(field.get("field_name", ""))),
                raw=_format_table_value(field.get("raw_value")),
                normalized=_format_table_value(field.get("normalized_value")),
                confidence=float(field.get("confidence", 0.0) or 0.0),
            )
        )

    if "ocr_preview" in document:
        lines.extend(["", "#### OCR Preview", "", "```text"])
        lines.extend(str(line) for line in document.get("ocr_preview", []))
        lines.extend(["```"])

    lines.append("")
    return lines


def _format_table_value(value: str | None) -> str:
    if value is None or str(value) == "":
        return ""
    return f"`{_escape_table_text(str(value).replace(chr(13), ' ').replace(chr(10), ' '))}`"


def _escape_table_text(value: str) -> str:
    return value.replace("`", "\\`").replace("|", "\\|")


def _safe_filename(value: str) -> str:
    name = Path(value).name.strip() or "file"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


if __name__ == "__main__":
    main()
