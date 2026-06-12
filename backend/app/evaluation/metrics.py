from dataclasses import dataclass

from app.evaluation.normalize import normalize_value
from app.services.extraction.rules import FIELD_NAMES, ExtractedFieldResult


@dataclass(frozen=True)
class FieldComparison:
    field_name: str
    expected: str | None
    actual: str | None
    expected_normalized: str
    actual_normalized: str
    exact_match: bool
    normalized_match: bool
    missing: bool
    wrong: bool
    confidence: float


def compare_fields(
    *,
    expected_fields: dict[str, str | None],
    extracted_fields: list[ExtractedFieldResult],
) -> list[FieldComparison]:
    extracted_by_name = {field.field_name: field for field in extracted_fields}
    comparisons: list[FieldComparison] = []
    for field_name in FIELD_NAMES:
        expected = expected_fields.get(field_name)
        extracted = extracted_by_name.get(field_name)
        actual = extracted.normalized_value if extracted else None
        expected_stripped = _strip_or_empty(expected)
        actual_stripped = _strip_or_empty(actual)
        expected_normalized = normalize_value(field_name, expected)
        actual_normalized = normalize_value(field_name, actual)
        missing = bool(expected_stripped) and not bool(actual_stripped)
        normalized_match = expected_normalized == actual_normalized
        comparisons.append(
            FieldComparison(
                field_name=field_name,
                expected=expected,
                actual=actual,
                expected_normalized=expected_normalized,
                actual_normalized=actual_normalized,
                exact_match=expected_stripped == actual_stripped,
                normalized_match=normalized_match,
                missing=missing,
                wrong=bool(expected_stripped) and bool(actual_stripped) and not normalized_match,
                confidence=extracted.confidence if extracted else 0.0,
            )
        )
    return comparisons


def summarize_field_metrics(document_results: list[dict]) -> dict:
    field_metrics = {}
    for field_name in FIELD_NAMES:
        comparisons = [
            field
            for result in document_results
            for field in result["fields"]
            if field["field_name"] == field_name
        ]
        total = len(comparisons)
        field_metrics[field_name] = {
            "total": total,
            "exact_match_accuracy": _ratio(sum(1 for item in comparisons if item["exact_match"]), total),
            "normalized_match_accuracy": _ratio(sum(1 for item in comparisons if item["normalized_match"]), total),
            "missing_count": sum(1 for item in comparisons if item["missing"]),
            "wrong_count": sum(1 for item in comparisons if item["wrong"]),
            "average_confidence": _ratio(sum(float(item["confidence"]) for item in comparisons), total),
        }
    return field_metrics


def _strip_or_empty(value: str | None) -> str:
    return "" if value is None else str(value).strip()


def _ratio(numerator: float, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
