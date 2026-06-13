import re
from dataclasses import dataclass

from app.models import OcrBlock


REGEX_FLAGS = re.IGNORECASE | re.UNICODE

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
    subtotal = _find_labeled_amount(
        blocks,
        text,
        r"Tạm tính|Tam tinh|Cộng tiền hàng|Cong tien hang|Tổng tiền hàng|Tong tien hang|Subtotal|Tiền hàng|Tien hang|Thành tiền|Thanh tien",
    )
    vat_amount = _find_labeled_amount(blocks, text, r"VAT|Thuế GTGT|Thue GTGT")
    total_amount = _find_labeled_amount(
        blocks,
        text,
        r"Tổng thanh toán|Tong thanh toán|Tong thanh toan|Tổng cộng|Tong cong|Cần thanh toán|Can thanh toan|Tổng phải trả|Tong phai tra|Total|Thanh toán|Thanh toan",
        prefer_last=True,
    )
    currency = _normalize_currency(_find(r"\b(VND|VNĐ|USD)\b", text) or "VND")
    notes = _find_labeled_value(blocks, text, r"Ghi chú|Ghi chu|Note|Ghi nhận|Ghi nhan", r"(.+)")

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
    value = _find_labeled_value(blocks, text, r"MST|Mã số thuế|Ma so thue|Tax code", r"([0-9][0-9\s\-]{6,24}[0-9])")
    if value is None:
        return None
    normalized = re.sub(r"\D", "", value)
    return normalized if len(normalized) in {10, 13} else None


def _find_document_date(blocks: list[OcrBlock], text: str) -> str | None:
    return _find_labeled_value(
        blocks,
        text,
        r"Ngày giao hàng|Ngay giao hang|Ngày giao|Ngay giao|Ngày lập|Ngay lap|Ngày bán|Ngay ban|Ngày xuất|Ngay xuat|Ngày|Ngay|Date",
        r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    )


def _find_labeled_amount(blocks: list[OcrBlock], text: str, labels: str, *, prefer_last: bool = False) -> str | None:
    values = _find_labeled_values(blocks, text, labels, r"([0-9][0-9.,\s]*)")
    if not values:
        return None
    value = values[-1] if prefer_last else values[0]
    return re.sub(r"[^\d]", "", value)


def _find_document_number(blocks: list[OcrBlock]) -> str | None:
    explicit_labels = r"Số chứng từ|So chung tu|Số hóa đơn|So hoa don|Số biên lai|So bien lai|Số phiếu giao|So phieu giao|Số phiếu xuất|So phieu xuat|Số phiếu|So phieu|Invoice No\.?"
    explicit_pattern = rf"(?:{explicit_labels})\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9\-\/]*)"
    generic_pattern = r"^(?:Số|So)\s*[:\-]\s*([A-Za-z0-9][A-Za-z0-9\-\/]*)"
    for index, block in enumerate(blocks):
        lowered = block.text.lower()
        if "mã số thuế" in lowered or "ma so thue" in lowered or lowered.startswith("mst"):
            continue
        value = _find_next_line_value(blocks, index, block, explicit_labels, r"([A-Za-z0-9][A-Za-z0-9\-\/]*)")
        value = value or _find(explicit_pattern, block.text) or _find(generic_pattern, block.text)
        if value:
            return value
    return None


def _first_supplier_line(blocks: list[OcrBlock]) -> str | None:
    labels = r"Đơn vị bán|Don vi ban|Nhà cung cấp|Nha cung cap|Người gửi|Nguoi gui|Kho xuất|Kho xuat"
    value = _find_labeled_value(blocks, "\n".join(block.text for block in blocks), labels, r"(.+)")
    if value:
        return value

    for block in blocks:
        lowered = block.text.lower()
        if re.match(rf"^\s*(?:{labels})\b", block.text, flags=REGEX_FLAGS):
            return re.sub(r"^[^:]+:\s*", "", block.text).strip()
    ignored = (
        "phieu",
        "phiếu",
        "hoa don",
        "hóa đơn",
        "bien lai",
        "biên lai",
        "mst",
        "mã số thuế",
        "ma so thue",
        "tax code",
        "số ",
        "so ",
        "so:",
        "ngày",
        "ngay",
        "date",
        "tạm tính",
        "tam tinh",
        "subtotal",
        "vat",
        "tổng",
        "tong",
        "total",
        "ghi chú",
        "ghi chu",
        "note",
    )
    for block in blocks:
        lowered = block.text.lower()
        if not any(token in lowered for token in ignored):
            return block.text.strip()
    return None


def _find_labeled_value(blocks: list[OcrBlock], text: str, labels: str, value_pattern: str) -> str | None:
    values = _find_labeled_values(blocks, text, labels, value_pattern)
    return values[0] if values else None


def _find_labeled_values(blocks: list[OcrBlock], text: str, labels: str, value_pattern: str) -> list[str]:
    values = []
    inline_pattern = rf"(?<![A-Za-z])(?:{labels})\s*[:\-]?\s*{value_pattern}"
    for index, block in enumerate(blocks):
        value = _find(inline_pattern, block.text)
        if value and value.strip() in {":", "-"}:
            value = None
        value = value or _find_next_line_value(blocks, index, block, labels, value_pattern)
        if value:
            values.append(value)
    return values


def _find_next_line_value(
    blocks: list[OcrBlock], index: int, block: OcrBlock, labels: str, value_pattern: str
) -> str | None:
    if index + 1 >= len(blocks):
        return None
    label_only = re.match(rf"^\s*(?:{labels})\s*[:\-]?\s*$", block.text, flags=REGEX_FLAGS)
    if not label_only:
        return None
    next_text = blocks[index + 1].text.strip()
    match = re.search(value_pattern, next_text, flags=REGEX_FLAGS)
    return match.group(1).strip() if match else None


def _normalize_currency(value: str) -> str:
    return "VND" if value.upper() == "VNĐ" else value.upper()


def _source_ids_for_value(value: str | None, by_text: dict[str, str]) -> list[str]:
    if not value:
        return []
    value_lower = value.lower()
    return [block_id for block_text, block_id in by_text.items() if value_lower in block_text.lower()]
