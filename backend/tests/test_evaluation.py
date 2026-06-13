from pathlib import Path

from app.evaluation.dataset import EVAL_MODE_MOCK_ONLY, EVAL_MODE_REAL_OCR, load_eval_samples
from app.evaluation.diagnostics import build_diagnostics_markdown, write_diagnostics_report
from app.evaluation.metrics import compare_fields
from app.evaluation.normalize import (
    normalize_currency,
    normalize_date,
    normalize_money,
    normalize_tax_code,
    normalize_text,
)
from app.evaluation.report import build_markdown_summary, build_report, write_reports
from app.evaluation.run import REPO_ROOT, run_evaluation, select_eval_samples
from app.services.extraction.rules import ExtractedFieldResult


def test_normalization_functions_handle_vietnamese_business_values() -> None:
    assert normalize_money("1.100.000 VND") == "1100000"
    assert normalize_money("1,100,000") == "1100000"
    assert normalize_currency("VNĐ") == "VND"
    assert normalize_tax_code("000-000 0000") == "0000000000"
    assert normalize_date("12-06-2026") == "2026-06-12"
    assert normalize_text("CÔNG   TY") == "cong ty"


def test_field_comparison_marks_missing_and_wrong_fields() -> None:
    expected = {
        "supplier_name": "CONG TY A",
        "tax_code": "000-000 0000",
        "document_number": "HD-01",
        "document_date": "12/06/2026",
        "subtotal": "1000000",
        "vat_amount": "100000",
        "total_amount": "1100000",
        "currency": "VND",
        "notes": "Demo",
    }
    actual = [
        ExtractedFieldResult("supplier_name", "Công ty A", "Công ty A", 0.8, []),
        ExtractedFieldResult("tax_code", "0000000000", "0000000000", 0.8, []),
        ExtractedFieldResult("document_number", "HD-02", "HD-02", 0.8, []),
        ExtractedFieldResult("document_date", None, None, 0.0, []),
        ExtractedFieldResult("subtotal", "1.000.000", "1.000.000", 0.8, []),
        ExtractedFieldResult("vat_amount", "100000", "100000", 0.8, []),
        ExtractedFieldResult("total_amount", "1100000", "1100000", 0.8, []),
        ExtractedFieldResult("currency", "VNĐ", "VNĐ", 0.8, []),
        ExtractedFieldResult("notes", "Demo", "Demo", 0.8, []),
    ]

    comparisons = {item.field_name: item for item in compare_fields(expected_fields=expected, extracted_fields=actual)}

    assert comparisons["supplier_name"].normalized_match is True
    assert comparisons["tax_code"].normalized_match is True
    assert comparisons["currency"].normalized_match is True
    assert comparisons["document_number"].wrong is True
    assert comparisons["document_date"].missing is True


def test_mock_evaluation_generates_perfect_synthetic_report(tmp_path: Path) -> None:
    report = run_evaluation(
        engine="mock",
        dataset_dir=REPO_ROOT / "data" / "eval",
        storage_dir=tmp_path / "storage",
    )

    assert report["engine"] == "mock"
    assert report["model_name"] == "mock_synthetic"
    assert report["summary"]["total_documents"] == 9
    assert report["summary"]["skipped_documents"] == 0
    assert report["summary"]["passed_documents"] == 9
    assert report["summary"]["exact_match_accuracy"] == 1.0
    assert report["summary"]["normalized_match_accuracy"] == 1.0
    assert report["field_metrics"]["tax_code"]["missing_count"] == 0
    assert all(document["model_name"] == "mock_synthetic" for document in report["documents"])
    assert {document["eval_mode"] for document in report["documents"]} == {EVAL_MODE_MOCK_ONLY, EVAL_MODE_REAL_OCR}


def test_eval_sample_metadata_separates_mock_only_and_real_ocr_fixtures() -> None:
    samples = load_eval_samples(REPO_ROOT / "data" / "eval")
    by_id = {sample.sample_id: sample for sample in samples}

    assert by_id["invoice-synthetic"].eval_mode == EVAL_MODE_REAL_OCR
    assert by_id["delivery-note-synthetic"].eval_mode == EVAL_MODE_REAL_OCR
    assert by_id["invoice-alt-labels"].eval_mode == EVAL_MODE_MOCK_ONLY
    assert by_id["invoice-split-values"].eval_mode == EVAL_MODE_MOCK_ONLY
    assert by_id["receipt-synthetic"].eval_mode == EVAL_MODE_MOCK_ONLY


def test_mock_engine_includes_mock_only_fixtures_by_default() -> None:
    samples = load_eval_samples(REPO_ROOT / "data" / "eval")

    selected, skipped = select_eval_samples(samples, engine="mock")

    assert len(selected) == 9
    assert skipped == []
    assert any(sample.eval_mode == EVAL_MODE_MOCK_ONLY for sample in selected)


def test_real_ocr_engines_skip_mock_only_fixtures_by_default() -> None:
    samples = load_eval_samples(REPO_ROOT / "data" / "eval")

    for engine in ("paddle", "ppocrv6"):
        selected, skipped = select_eval_samples(samples, engine=engine)

        assert [sample.sample_id for sample in selected] == ["delivery-note-synthetic", "invoice-synthetic"]
        assert len(skipped) == 7
        assert all(item["eval_mode"] == EVAL_MODE_MOCK_ONLY for item in skipped)


def test_real_ocr_engines_can_explicitly_include_mock_only_fixtures() -> None:
    samples = load_eval_samples(REPO_ROOT / "data" / "eval")

    selected, skipped = select_eval_samples(samples, engine="paddle", include_mock_only=True)

    assert len(selected) == 9
    assert skipped == []


def test_evaluation_report_writes_json_and_markdown(tmp_path: Path) -> None:
    report = run_evaluation(
        engine="mock",
        dataset_dir=REPO_ROOT / "data" / "eval",
        storage_dir=tmp_path / "storage",
    )

    json_path, markdown_path = write_reports(report, tmp_path / "reports")

    assert json_path.exists()
    assert markdown_path.exists()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Evaluation Report - mock" in markdown
    assert "OCR Model: `mock_synthetic`" in markdown
    assert "Skipped Documents: 0" in markdown


def test_report_summary_includes_skipped_sample_count() -> None:
    samples = load_eval_samples(REPO_ROOT / "data" / "eval")
    _, skipped = select_eval_samples(samples, engine="paddle")

    report = build_report(engine="paddle", model_name="fake_paddle", document_results=[], skipped_samples=skipped)
    markdown = build_markdown_summary(report)

    assert report["summary"]["total_documents"] == 0
    assert report["summary"]["skipped_documents"] == 7
    assert report["skipped_documents"][0]["reason"] == "mock_only fixture skipped for real OCR engine"
    assert "Skipped Documents: 7" in markdown
    assert "Skipped Documents" in markdown
    assert "`invoice-alt-labels`" in markdown


def test_diagnostics_report_writes_failed_sample_details(tmp_path: Path) -> None:
    report = {
        "engine": "fake",
        "model_name": "fake_model",
        "skipped_documents": [
            {
                "sample_id": "invoice-alt-labels",
                "document_type": "invoice",
                "eval_mode": "mock_only",
                "reason": "mock_only fixture skipped for real OCR engine",
            }
        ],
        "documents": [
            {
                "sample_id": "invoice-failed",
                "document_type": "invoice",
                "engine_name": "fake",
                "model_name": "fake_model",
                "ocr_block_count": 3,
                "ocr_text_lines": [
                    "CÔNG TY TNHH DEMO OCR",
                    "Số hóa đơn: HD-001",
                    "Ngày lập: 12/06/2026",
                ],
                "passed": False,
                "fields": [
                    {
                        "field_name": "supplier_name",
                        "expected": "CONG TY TNHH DEMO OCR",
                        "actual": "CONG TY TNHH DEMO OCR",
                        "exact_match": True,
                        "normalized_match": True,
                        "missing": False,
                        "wrong": False,
                    },
                    {
                        "field_name": "document_number",
                        "expected": "HD-001",
                        "actual": "HD-002",
                        "exact_match": False,
                        "normalized_match": False,
                        "missing": False,
                        "wrong": True,
                    },
                    {
                        "field_name": "document_date",
                        "expected": "12/06/2026",
                        "actual": None,
                        "exact_match": False,
                        "normalized_match": False,
                        "missing": True,
                        "wrong": False,
                    },
                ],
            }
        ],
    }

    diagnostics_path = write_diagnostics_report(report, tmp_path)

    assert diagnostics_path.exists()
    assert diagnostics_path.name.endswith("-fake-diagnostics.md")
    markdown = diagnostics_path.read_text(encoding="utf-8")
    assert "sample_id: `invoice-failed`" in markdown
    assert "engine_name: `fake`" in markdown
    assert "model_name: `fake_model`" in markdown
    assert "Exact Accuracy: 33.33%" in markdown
    assert "Normalized Accuracy: 33.33%" in markdown
    assert "OCR Block Count: 3" in markdown
    assert "CÔNG TY TNHH DEMO OCR" in markdown
    assert "cong ty tnhh demo ocr" in markdown
    assert "| document_number | `HD-001` | `HD-002` | wrong |" in markdown
    assert "| document_date | `12/06/2026` |  | missing |" in markdown
    assert "Missing Fields: 1" in markdown
    assert "Wrong Fields: 1" in markdown
    assert "Likely Failure Category: extraction rule miss" in markdown
    assert "Skipped Mock-Only Samples" in markdown
    assert "`invoice-alt-labels`" in markdown


def test_diagnostics_report_can_run_for_mock_engine(tmp_path: Path) -> None:
    report = run_evaluation(
        engine="mock",
        dataset_dir=REPO_ROOT / "data" / "eval",
        storage_dir=tmp_path / "storage",
    )

    diagnostics_path = write_diagnostics_report(report, tmp_path)

    assert diagnostics_path.exists()
    assert diagnostics_path.name.endswith("-mock-diagnostics.md")
    markdown = diagnostics_path.read_text(encoding="utf-8")
    assert "Evaluation Diagnostics - mock" in markdown
    assert "model_name: `mock_synthetic`" in markdown
    assert "skipped_samples: 0" in markdown
    assert "No failed samples." in markdown


def test_generated_eval_reports_are_ignored_by_git() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "storage/dev/eval_reports/*" in gitignore
    assert "!storage/dev/eval_reports/.gitkeep" in gitignore
