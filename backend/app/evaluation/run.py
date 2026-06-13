import argparse
import mimetypes
from pathlib import Path

from app.evaluation.dataset import EVAL_MODE_MOCK_ONLY, EVAL_MODE_REAL_OCR, EvalSample, load_eval_samples
from app.evaluation.diagnostics import write_diagnostics_report
from app.evaluation.metrics import compare_fields
from app.evaluation.report import build_report, write_reports
from app.models import OcrBlock
from app.services.extraction.rules import extract_fields
from app.services.ocr.factory import build_ocr_adapter
from app.services.preprocessing import create_page_images
from app.services.storage.local import LocalStorageService


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_DIR = REPO_ROOT / "data" / "eval"
DEFAULT_STORAGE_DIR = REPO_ROOT / "storage" / "dev"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OCR/extraction evaluation.")
    parser.add_argument(
        "--engine",
        default="mock",
        help="OCR engine: mock, paddle, or experimental ppocrv6.",
    )
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--storage-dir", default=str(DEFAULT_STORAGE_DIR))
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Write a failed-sample diagnostics markdown report.",
    )
    parser.add_argument(
        "--include-mock-only",
        action="store_true",
        help="Include mock-only fixtures when running real OCR engines.",
    )
    args = parser.parse_args()

    try:
        report = run_evaluation(
            engine=args.engine,
            dataset_dir=Path(args.dataset_dir),
            storage_dir=Path(args.storage_dir),
            include_mock_only=args.include_mock_only,
        )
    except (RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    report_dir = Path(args.storage_dir) / "eval_reports"
    json_path, markdown_path = write_reports(report, report_dir)
    diagnostics_path = write_diagnostics_report(report, report_dir) if args.diagnostics else None
    summary = report["summary"]
    print(f"Evaluation complete for engine={args.engine}")
    print(f"OCR model: {report['model_name']}")
    print(f"Documents passed: {summary['passed_documents']}/{summary['total_documents']}")
    print(f"Skipped samples: {summary['skipped_documents']}")
    print(f"Exact match accuracy: {summary['exact_match_accuracy']:.2%}")
    print(f"Normalized match accuracy: {summary['normalized_match_accuracy']:.2%}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    if diagnostics_path:
        print(f"Diagnostics report: {diagnostics_path}")


def run_evaluation(*, engine: str, dataset_dir: Path, storage_dir: Path, include_mock_only: bool = False) -> dict:
    samples = load_eval_samples(dataset_dir)
    storage = LocalStorageService(storage_dir)
    adapter = build_ocr_adapter(engine)
    selected_samples, skipped_samples = select_eval_samples(
        samples,
        engine=adapter.engine_name,
        include_mock_only=include_mock_only,
    )
    document_results = [
        _evaluate_sample(sample, storage, adapter.engine_name, adapter.model_name, adapter) for sample in selected_samples
    ]
    return build_report(
        engine=adapter.engine_name,
        model_name=adapter.model_name,
        document_results=document_results,
        skipped_samples=skipped_samples,
    )


def select_eval_samples(
    samples: list[EvalSample],
    *,
    engine: str,
    include_mock_only: bool = False,
) -> tuple[list[EvalSample], list[dict]]:
    if _uses_mock_fixture_set(engine) or include_mock_only:
        return list(samples), []

    selected: list[EvalSample] = []
    skipped: list[dict] = []
    for sample in samples:
        if sample.eval_mode == EVAL_MODE_REAL_OCR:
            selected.append(sample)
            continue
        if sample.eval_mode == EVAL_MODE_MOCK_ONLY:
            skipped.append(_skipped_mock_only_sample(sample))
    return selected, skipped


def _uses_mock_fixture_set(engine: str) -> bool:
    return engine.lower().strip() == "mock"


def _skipped_mock_only_sample(sample: EvalSample) -> dict:
    return {
        "sample_id": sample.sample_id,
        "document_type": sample.document_type,
        "eval_mode": sample.eval_mode,
        "source_file": str(sample.source_file),
        "expected_file": str(sample.expected_file),
        "reason": "mock_only fixture skipped for real OCR engine",
    }


def _evaluate_sample(
    sample: EvalSample,
    storage: LocalStorageService,
    engine_name: str,
    model_name: str,
    adapter,
) -> dict:
    content_type = mimetypes.guess_type(sample.source_file.name)[0] or "application/octet-stream"
    pages = create_page_images(
        document_id=sample.sample_id,
        storage_path=str(sample.source_file),
        content_type=content_type,
        storage=storage,
    )

    blocks: list[OcrBlock] = []
    global_block_index = 0
    for page in pages:
        page_number = int(page["page_number"])
        page_id = f"{sample.sample_id}-page-{page_number}"
        for result in adapter.run_page(page["image_path"], page_number):
            blocks.append(
                OcrBlock(
                    id=f"{sample.sample_id}-block-{global_block_index}",
                    ocr_run_id=f"{sample.sample_id}-ocr",
                    page_id=page_id,
                    block_index=global_block_index,
                    text=result.text,
                    confidence=result.confidence,
                    bbox=result.bbox,
                )
            )
            global_block_index += 1

    extracted = extract_fields(blocks)
    comparisons = compare_fields(expected_fields=sample.expected_fields, extracted_fields=extracted)
    fields = [comparison.__dict__ for comparison in comparisons]
    return {
        "sample_id": sample.sample_id,
        "document_type": sample.document_type,
        "eval_mode": sample.eval_mode,
        "source_file": str(sample.source_file),
        "expected_file": str(sample.expected_file),
        "engine": engine_name,
        "engine_name": engine_name,
        "model_name": model_name,
        "page_count": len(pages),
        "ocr_block_count": len(blocks),
        "ocr_text_lines": [block.text for block in blocks],
        "average_extraction_confidence": _average([comparison.confidence for comparison in comparisons]),
        "passed": all(comparison.normalized_match for comparison in comparisons),
        "fields": fields,
    }


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


if __name__ == "__main__":
    main()
