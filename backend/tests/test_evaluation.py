from pathlib import Path

from app.evaluation.metrics import compare_fields
from app.evaluation.normalize import (
    normalize_currency,
    normalize_date,
    normalize_money,
    normalize_tax_code,
    normalize_text,
)
from app.evaluation.report import write_reports
from app.evaluation.run import REPO_ROOT, run_evaluation
from app.services.extraction.rules import ExtractedFieldResult


def test_normalization_functions_handle_vietnamese_business_values() -> None:
    assert normalize_money("1.100.000 VND") == "1100000"
    assert normalize_money("1,100,000") == "1100000"
    assert normalize_currency("VNĐ") == "VND"
    assert normalize_tax_code("031-234 5678") == "0312345678"
    assert normalize_date("12-06-2026") == "2026-06-12"
    assert normalize_text("CÔNG   TY") == "cong ty"


def test_field_comparison_marks_missing_and_wrong_fields() -> None:
    expected = {
        "supplier_name": "CONG TY A",
        "tax_code": "031-234 5678",
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
        ExtractedFieldResult("tax_code", "0312345678", "0312345678", 0.8, []),
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

    assert report["summary"]["total_documents"] == 3
    assert report["summary"]["passed_documents"] == 3
    assert report["summary"]["exact_match_accuracy"] == 1.0
    assert report["summary"]["normalized_match_accuracy"] == 1.0
    assert report["field_metrics"]["tax_code"]["missing_count"] == 0


def test_evaluation_report_writes_json_and_markdown(tmp_path: Path) -> None:
    report = run_evaluation(
        engine="mock",
        dataset_dir=REPO_ROOT / "data" / "eval",
        storage_dir=tmp_path / "storage",
    )

    json_path, markdown_path = write_reports(report, tmp_path / "reports")

    assert json_path.exists()
    assert markdown_path.exists()
    assert "Evaluation Report - mock" in markdown_path.read_text(encoding="utf-8")
