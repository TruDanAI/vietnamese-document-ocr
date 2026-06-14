import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.models import OcrBlock


REGEX_FLAGS = re.IGNORECASE | re.UNICODE
LABEL_WORD_MIN_SIMILARITY = 0.66
LABEL_MIN_AVERAGE_SIMILARITY = 0.82
AMOUNT_VALUE_PATTERN = r"([0-9][0-9.,\s]*)"
DOCUMENT_NUMBER_VALUE_PATTERN = r"([A-Za-z0-9][A-Za-z0-9\-\/]*)"
DOCUMENT_NUMBER_REJECT_VALUES = {"giao", "xuat", "nhap", "so", "phieu", "hoa", "don", "bien", "lai"}
CURRENCY_PATTERN = r"\b(?:VND|VNĐ|USD)\b|₫"
SUPPLIER_LABELS = (
    "Đơn vị bán",
    "Don vi ban",
    "Nhà cung cấp",
    "Nha cung cap",
    "Người gửi",
    "Nguoi gui",
    "Kho xuất",
    "Kho xuat",
)
TAX_CODE_LABELS = ("MST", "Mã số thuế", "Ma so thue", "Tax code")
DOCUMENT_DATE_LABELS = (
    "Ngày giao hàng",
    "Ngay giao hang",
    "Ngày giao",
    "Ngay giao",
    "Ngày lập",
    "Ngay lap",
    "Ngày bán",
    "Ngay ban",
    "Ngày xuất",
    "Ngay xuat",
    "Ngày",
    "Ngay",
    "Date",
)
DOCUMENT_NUMBER_LABELS = (
    "Số chứng từ",
    "So chung tu",
    "Số hóa đơn",
    "So hoa don",
    "Số HĐ",
    "So HD",
    "Số HD",
    "Số biên lai",
    "So bien lai",
    "Số phiếu giao",
    "So phieu giao",
    "Số phiếu xuất",
    "So phieu xuat",
    "Số phiếu",
    "So phieu",
    "Invoice No",
    "Invoice No.",
)
GENERIC_DOCUMENT_NUMBER_LABELS = ("Số", "So")
SUBTOTAL_LABELS = (
    "Tạm tính",
    "Tam tinh",
    "Cộng tiền hàng",
    "Cong tien hang",
    "Tổng tiền hàng",
    "Tong tien hang",
    "Subtotal",
    "Tiền hàng",
    "Tien hang",
    "Thành tiền",
    "Thanh tien",
)
VAT_LABELS = ("VAT", "Thuế GTGT", "Thue GTGT")
TOTAL_PAYABLE_LABELS = (
    "Tổng thanh toán",
    "Tong thanh toán",
    "Tong thanh toan",
    "Tổng cộng",
    "Tong cong",
    "Cần thanh toán",
    "Can thanh toan",
    "Tổng phải trả",
    "Tong phai tra",
    "Thành tiền thanh toán",
    "Thanh tien thanh toan",
)
TOTAL_WEAK_LABELS = (
    "Total",
    "Thanh toán",
    "Thanh toan",
)
TOTAL_LABELS = TOTAL_PAYABLE_LABELS + TOTAL_WEAK_LABELS
NOTES_LABELS = ("Ghi chú", "Ghi chu", "Note", "Ghi nhận", "Ghi nhan")

FIELD_NAMES = [
    "supplier_name",
    "tax_code",
    "document_number",
    "document_date",
    "subtotal",
    "vat_amount",
    "total_amount",
    "currency",
    "notes",
]


@dataclass(frozen=True)
class ExtractedFieldResult:
    field_name: str
    raw_value: str | None
    normalized_value: str | None
    confidence: float
    source_block_ids: list[str]


def extract_fields(blocks: list[OcrBlock]) -> list[ExtractedFieldResult]:
    text = "\n".join(block.text for block in blocks)
    by_text = {block.text: block.id for block in blocks}

    supplier = _first_supplier_line(blocks)
    tax_code = _find_tax_code(blocks, text)
    document_number = _find_document_number(blocks)
    document_date = _find_document_date(blocks, text)
    subtotal = _find_labeled_amount(blocks, text, SUBTOTAL_LABELS)
    vat_amount = _find_labeled_amount(blocks, text, VAT_LABELS)
    total_amount = _find_labeled_amount(
        blocks,
        text,
        TOTAL_PAYABLE_LABELS,
        prefer_last=True,
    )
    if total_amount is None:
        total_amount = _find_labeled_amount(blocks, text, TOTAL_WEAK_LABELS, prefer_last=True)
    currency = _normalize_currency(_find(r"\b(VND|VNĐ|USD)\b", text) or "VND")
    notes = _find_labeled_value(blocks, text, NOTES_LABELS, r"(.+)")

    values = {
        "supplier_name": supplier,
        "tax_code": tax_code,
        "document_number": document_number,
        "document_date": document_date,
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "total_amount": total_amount,
        "currency": currency,
        "notes": notes,
    }
    return [
        ExtractedFieldResult(
            field_name=name,
            raw_value=values.get(name),
            normalized_value=values.get(name),
            confidence=0.8 if values.get(name) else 0.0,
            source_block_ids=_source_ids_for_value(values.get(name), by_text),
        )
        for name in FIELD_NAMES
    ]


def _find(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=REGEX_FLAGS)
    return match.group(1).strip() if match else None


def _find_tax_code(blocks: list[OcrBlock], text: str) -> str | None:
    value = _find_labeled_value(blocks, text, TAX_CODE_LABELS, r"([0-9][0-9\s\-]{6,24}[0-9])")
    if value is None:
        return None
    normalized = re.sub(r"\D", "", value)
    return normalized if len(normalized) in {10, 13} else None


def _find_document_date(blocks: list[OcrBlock], text: str) -> str | None:
    return _find_labeled_value(blocks, text, DOCUMENT_DATE_LABELS, r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})")


def _find_labeled_amount(
    blocks: list[OcrBlock], text: str, labels: tuple[str, ...], *, prefer_last: bool = False
) -> str | None:
    values = _find_labeled_amount_values(blocks, labels)
    if not values:
        return None
    value = values[-1] if prefer_last else values[0]
    return re.sub(r"[^\d]", "", value)


def _find_document_number(blocks: list[OcrBlock]) -> str | None:
    for index, block in enumerate(blocks):
        if _line_starts_with_label(block.text, TAX_CODE_LABELS) or _line_starts_with_label(
            block.text, DOCUMENT_DATE_LABELS
        ):
            continue
        value = _find_document_number_value_in_line(block.text, DOCUMENT_NUMBER_LABELS)
        value = value or _find_next_document_number_value(blocks, index, DOCUMENT_NUMBER_LABELS)
        value = value or _find_generic_document_number(blocks, index)
        value = _clean_document_number(value)
        if value:
            return value
    return None


def _first_supplier_line(blocks: list[OcrBlock]) -> str | None:
    value = _find_labeled_value(blocks, "\n".join(block.text for block in blocks), SUPPLIER_LABELS, r"(.+)")
    if value:
        return value

    for block in blocks:
        if _supplier_fallback_candidate(block.text):
            return block.text.strip()
    return None


def _find_labeled_value(
    blocks: list[OcrBlock], text: str, labels: tuple[str, ...], value_pattern: str
) -> str | None:
    values = _find_labeled_values(blocks, text, labels, value_pattern)
    return values[0] if values else None


def _find_labeled_values(
    blocks: list[OcrBlock], text: str, labels: tuple[str, ...], value_pattern: str
) -> list[str]:
    values = []
    for index, block in enumerate(blocks):
        value = _find_labeled_value_in_line(block.text, labels, value_pattern)
        if value and value.strip() in {":", "-"}:
            value = None
        value = value or _find_next_line_value(blocks, index, block, labels, value_pattern)
        if value:
            values.append(value)
    return values


def _find_labeled_amount_values(blocks: list[OcrBlock], labels: tuple[str, ...]) -> list[str]:
    values = []
    for index, block in enumerate(blocks):
        value = _find_labeled_amount_in_line(block.text, labels)
        value = value or _find_next_line_amount(blocks, index, block, labels)
        if value:
            values.append(value)
    return values


def _find_next_line_value(
    blocks: list[OcrBlock], index: int, block: OcrBlock, labels: tuple[str, ...], value_pattern: str
) -> str | None:
    if index + 1 >= len(blocks):
        return None
    if not _line_is_label_only(block.text, labels):
        return None
    next_text = blocks[index + 1].text.strip()
    match = re.search(value_pattern, next_text, flags=REGEX_FLAGS)
    return match.group(1).strip() if match else None


def _find_next_line_amount(blocks: list[OcrBlock], index: int, block: OcrBlock, labels: tuple[str, ...]) -> str | None:
    if index + 1 >= len(blocks) or not _line_is_label_only(block.text, labels):
        return None
    next_text = blocks[index + 1].text.strip()
    if not _is_standalone_amount_value(next_text):
        return None
    match = re.search(AMOUNT_VALUE_PATTERN, next_text, flags=REGEX_FLAGS)
    return match.group(1).strip() if match else None


def _find_labeled_amount_in_line(text: str, labels: tuple[str, ...]) -> str | None:
    inline_pattern = rf"^\s*(?:{_label_regex(labels)})\s*(?::|：|\s[-–—]\s|\s+)\s*{AMOUNT_VALUE_PATTERN}"
    value = _find(inline_pattern, text)
    if value and _is_amount_value(_value_with_amount_suffix(text, value)):
        return value

    if not _line_starts_with_label(text, labels):
        return None
    separator_value = _value_after_separator(text)
    if separator_value is None or not _is_amount_value(separator_value):
        return None
    match = re.search(AMOUNT_VALUE_PATTERN, separator_value, flags=REGEX_FLAGS)
    return match.group(1).strip() if match else None


def _find_labeled_value_in_line(text: str, labels: tuple[str, ...], value_pattern: str) -> str | None:
    inline_pattern = rf"^\s*(?:{_label_regex(labels)})\s*[:\-]?\s*{value_pattern}"
    value = _find(inline_pattern, text)
    if value:
        return value

    if not _line_starts_with_label(text, labels):
        return None
    separator_value = _value_after_separator(text)
    if separator_value is None:
        return None
    match = re.search(value_pattern, separator_value, flags=REGEX_FLAGS)
    return match.group(1).strip() if match else None


def _find_document_number_value_in_line(text: str, labels: tuple[str, ...]) -> str | None:
    inline_pattern = rf"^\s*(?:{_label_regex(labels)})\s*(?::|：|\s[-–—]\s)\s*{DOCUMENT_NUMBER_VALUE_PATTERN}"
    value = _find(inline_pattern, text)
    value = _clean_document_number(value)
    if value:
        return value

    if not _line_starts_with_label(text, labels):
        return None
    separator_value = _value_after_separator(text)
    if separator_value is None:
        return None
    match = re.search(DOCUMENT_NUMBER_VALUE_PATTERN, separator_value, flags=REGEX_FLAGS)
    return _clean_document_number(match.group(1).strip()) if match else None


def _find_next_document_number_value(blocks: list[OcrBlock], index: int, labels: tuple[str, ...]) -> str | None:
    if index + 1 >= len(blocks) or not _line_is_label_only(blocks[index].text, labels):
        return None
    next_text = blocks[index + 1].text.strip()
    if _looks_like_labeled_line(next_text):
        return None
    match = re.search(DOCUMENT_NUMBER_VALUE_PATTERN, next_text, flags=REGEX_FLAGS)
    return _clean_document_number(match.group(1).strip()) if match else None


def _find_generic_document_number(blocks: list[OcrBlock], index: int) -> str | None:
    block = blocks[index]
    if not _line_is_exact_generic_document_number_label(block.text):
        return None

    separator_value = _value_after_separator(block.text)
    if separator_value:
        match = re.search(DOCUMENT_NUMBER_VALUE_PATTERN, separator_value, flags=REGEX_FLAGS)
        return _clean_document_number(match.group(1).strip()) if match else None
    return _find_next_document_number_value(blocks, index, GENERIC_DOCUMENT_NUMBER_LABELS)


def _clean_document_number(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().strip(": -")
    if not value:
        return None
    if re.fullmatch(r"\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}", value):
        return None
    if _normalize_label_text(value) in DOCUMENT_NUMBER_REJECT_VALUES:
        return None
    if not re.search(r"\d", value):
        return None
    digits = re.sub(r"\D", "", value)
    if digits and digits == re.sub(r"[\s\-\.]", "", value) and len(digits) in {10, 13}:
        return None
    return value


def _label_regex(labels: tuple[str, ...]) -> str:
    return "|".join(re.escape(label) for label in labels)


def _value_after_separator(text: str) -> str | None:
    match = re.search(r"[:：]\s*(.+?)\s*$", text)
    if match:
        value = match.group(1).strip()
        return value or None

    match = re.search(r"\s[-–—]\s*(.+?)\s*$", text)
    if match:
        value = match.group(1).strip()
        return value or None
    return None


def _line_starts_with_label(text: str, labels: tuple[str, ...]) -> bool:
    line_tokens = _normalized_label_tokens(text)
    if not line_tokens:
        return False
    return any(_label_matches_tokens(label, line_tokens, require_exact_length=False) for label in labels)


def _line_is_label_only(text: str, labels: tuple[str, ...]) -> bool:
    if re.match(rf"^\s*(?:{_label_regex(labels)})\s*[:\-]?\s*$", text, flags=REGEX_FLAGS):
        return True
    line_tokens = _normalized_label_tokens(text)
    if not line_tokens:
        return False
    return any(_label_matches_tokens(label, line_tokens, require_exact_length=True) for label in labels)


def _line_is_exact_generic_document_number_label(text: str) -> bool:
    prefix = re.split(r"[:：]", text, maxsplit=1)[0]
    return _normalize_label_text(prefix) == "so"


def _looks_like_labeled_line(text: str) -> bool:
    if not _value_after_separator(text):
        return False
    label_groups = (
        SUPPLIER_LABELS,
        TAX_CODE_LABELS,
        DOCUMENT_DATE_LABELS,
        DOCUMENT_NUMBER_LABELS,
        SUBTOTAL_LABELS,
        VAT_LABELS,
        TOTAL_LABELS,
        NOTES_LABELS,
    )
    return any(_line_starts_with_label(text, labels) for labels in label_groups)


def _label_matches_tokens(label: str, line_tokens: list[str], *, require_exact_length: bool) -> bool:
    label_tokens = _normalized_label_tokens(label)
    if not label_tokens:
        return False
    if require_exact_length and len(line_tokens) != len(label_tokens):
        return False
    if len(line_tokens) < len(label_tokens):
        return False
    if len(label_tokens) == 1:
        return line_tokens[0] == label_tokens[0]

    scores = [
        _token_similarity(label_token, line_token)
        for label_token, line_token in zip(label_tokens, line_tokens[: len(label_tokens)], strict=True)
    ]
    return min(scores) >= LABEL_WORD_MIN_SIMILARITY and _average_score(scores) >= LABEL_MIN_AVERAGE_SIMILARITY


def _token_similarity(expected: str, actual: str) -> float:
    if expected == actual:
        return 1.0
    if len(expected) <= 1 and len(actual) <= 1:
        return 0.0
    return SequenceMatcher(None, expected, actual).ratio()


def _average_score(scores: list[float]) -> float:
    return sum(scores) / len(scores) if scores else 0.0


def _normalized_label_tokens(text: str) -> list[str]:
    return _normalize_label_text(text).split()


def _normalize_label_text(text: str) -> str:
    text = text.replace("Đ", "D").replace("đ", "d")
    text = "".join(char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn")
    text = re.sub(r"['’`´]", "", text)
    text = re.sub(r"[^0-9A-Za-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _value_with_amount_suffix(text: str, value: str) -> str:
    value_index = text.find(value)
    if value_index < 0:
        return value
    return text[value_index:].strip()


def _is_amount_value(value: str) -> bool:
    value = value.strip()
    if not re.search(r"\d", value) or "%" in value:
        return False
    if re.search(CURRENCY_PATTERN, value, flags=REGEX_FLAGS):
        return True
    if re.search(r"\d{1,3}(?:[.,]\d{3})+", value):
        return True
    digits = re.sub(r"\D", "", value)
    return len(digits) >= 4


def _is_standalone_amount_value(value: str) -> bool:
    if _value_after_separator(value):
        return False
    without_currency = re.sub(CURRENCY_PATTERN, "", value, flags=REGEX_FLAGS)
    if re.search(r"[A-Za-zÀ-ỹ]", without_currency):
        return False
    return _is_amount_value(value)


def _supplier_fallback_candidate(text: str) -> bool:
    normalized = _normalize_label_text(text)
    if not normalized:
        return False
    if re.fullmatch(r"[\d\s.,]+(?:vnd)?", text.strip(), flags=REGEX_FLAGS):
        return False
    if _value_after_separator(text):
        return False
    title_phrases = ("hoa don", "bien lai", "phieu giao", "phieu xuat", "phieu nhap")
    if any(phrase in normalized for phrase in title_phrases):
        return False
    table_headers = {"mo ta", "sl", "don gia", "don vi", "thanh tien", "so luong", "hang demo", "vat"}
    if normalized in table_headers:
        return False

    non_supplier_label_groups = (
        TAX_CODE_LABELS,
        DOCUMENT_DATE_LABELS,
        DOCUMENT_NUMBER_LABELS,
        SUBTOTAL_LABELS,
        TOTAL_LABELS,
        NOTES_LABELS,
    )
    return not any(_line_starts_with_label(text, labels) for labels in non_supplier_label_groups)


def _normalize_currency(value: str) -> str:
    return "VND" if value.upper() == "VNĐ" else value.upper()


def _source_ids_for_value(value: str | None, by_text: dict[str, str]) -> list[str]:
    if not value:
        return []
    value_lower = value.lower()
    return [block_id for block_text, block_id in by_text.items() if value_lower in block_text.lower()]
