import re
import unicodedata
from datetime import datetime


MONEY_FIELDS = {"subtotal", "vat_amount", "total_amount"}


def normalize_value(field_name: str, value: str | None) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    if field_name in MONEY_FIELDS:
        return normalize_money(value)
    if field_name == "document_date":
        return normalize_date(value)
    if field_name == "tax_code":
        return normalize_tax_code(value)
    if field_name == "currency":
        return normalize_currency(value)
    return normalize_text(value)


def normalize_money(value: str) -> str:
    return re.sub(r"[^\d]", "", value)


def normalize_tax_code(value: str) -> str:
    return re.sub(r"[\s\-\.]", "", value)


def normalize_currency(value: str) -> str:
    normalized = value.upper().replace("VNĐ", "VND").replace("₫", "VND")
    return re.sub(r"\s+", "", normalized)


def normalize_date(value: str) -> str:
    clean = value.strip().replace(".", "/").replace("-", "/")
    for fmt in ("%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(clean, fmt).date().isoformat()
        except ValueError:
            continue
    return clean


def normalize_text(value: str) -> str:
    no_accents = "".join(
        char for char in unicodedata.normalize("NFD", value) if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", no_accents).strip().casefold()
