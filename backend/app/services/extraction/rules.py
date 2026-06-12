import re
from dataclasses import dataclass

from app.models import OcrBlock


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
    tax_code = _find(r"(?:MST|Mã số thuế|Ma so thue|Tax code)\s*[:\-]?\s*([0-9\-]{8,20})", text)
    document_number = _find_document_number(blocks)
    document_date = _find(r"(?:Ngày giao|Ngay giao|Ngày|Ngay|Date)\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})", text)
    subtotal = _find_amount(r"(?:Tạm tính|Tam tinh|Cộng tiền hàng|Cong tien hang|Subtotal|Tiền hàng|Tien hang|Thành tiền|Thanh tien)\s*[:\-]?\s*([0-9.,]+)", text)
    vat_amount = _find_amount(r"(?:VAT|Thuế GTGT|Thue GTGT)\s*[:\-]?\s*([0-9.,]+)", text)
    total_amount = _find_amount(r"(?:Tổng thanh toán|Tong thanh toán|Tong thanh toan|Tổng cộng|Tong cong|Total|Thanh toán|Thanh toan)\s*[:\-]?\s*([0-9.,]+)", text)
    currency = _find(r"\b(VND|VNĐ|USD)\b", text) or "VND"
    notes = _find(r"(?:Ghi chú|Ghi chu|Note|Ghi nhận|Ghi nhan)\s*[:\-]?\s*(.+)", text)

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
    match = re.search(pattern, text, flags=re.IGNORECASE | re.UNICODE)
    return match.group(1).strip() if match else None


def _find_amount(pattern: str, text: str) -> str | None:
    value = _find(pattern, text)
    if value is None:
        return None
    return re.sub(r"[^\d]", "", value)


def _find_document_number(blocks: list[OcrBlock]) -> str | None:
    explicit_pattern = r"(?:Số chứng từ|So chung tu|Số hóa đơn|So hoa don|Số phiếu|So phieu|Invoice No\.?)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)"
    generic_pattern = r"^(?:Số|So)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)"
    for block in blocks:
        lowered = block.text.lower()
        if "mã số thuế" in lowered or "ma so thue" in lowered or lowered.startswith("mst"):
            continue
        value = _find(explicit_pattern, block.text) or _find(generic_pattern, block.text)
        if value:
            return value
    return None


def _first_supplier_line(blocks: list[OcrBlock]) -> str | None:
    label_prefixes = (
        "đơn vị bán",
        "don vi ban",
        "nhà cung cấp",
        "nha cung cap",
        "người gửi",
        "nguoi gui",
    )
    for block in blocks:
        lowered = block.text.lower()
        for prefix in label_prefixes:
            if lowered.startswith(prefix):
                return re.sub(r"^[^:]+:\s*", "", block.text).strip()
    ignored = ("mst", "mã số thuế", "ma so thue", "số ", "so ", "so:", "ngày", "ngay", "tạm tính", "tam tinh", "vat", "tổng", "tong", "ghi chú", "ghi chu")
    for block in blocks:
        lowered = block.text.lower()
        if not any(token in lowered for token in ignored):
            return block.text.strip()
    return None


def _source_ids_for_value(value: str | None, by_text: dict[str, str]) -> list[str]:
    if not value:
        return []
    value_lower = value.lower()
    return [block_id for block_text, block_id in by_text.items() if value_lower in block_text.lower()]
