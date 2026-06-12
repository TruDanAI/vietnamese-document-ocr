from app.models import OcrBlock
from app.services.extraction.rules import extract_fields


def make_blocks(lines: list[str]) -> list[OcrBlock]:
    return [
        OcrBlock(
            id=f"block-{index}",
            ocr_run_id="run-1",
            page_id="page-1",
            block_index=index,
            text=line,
            confidence=0.9,
            bbox={"x": 0, "y": index * 20, "width": 200, "height": 20},
        )
        for index, line in enumerate(lines)
    ]


def fields_from_lines(lines: list[str]) -> dict[str, str | None]:
    return {field.field_name: field.normalized_value for field in extract_fields(make_blocks(lines))}


def test_extracts_invoice_like_vietnamese_fields() -> None:
    fields = fields_from_lines(
        [
            "Đơn vị bán: CÔNG TY TNHH MINH AN",
            "Mã số thuế: 0000000000",
            "Số hóa đơn: HD-2026-001",
            "Ngày: 12/06/2026",
            "Cộng tiền hàng: 1.000.000 VND",
            "Thuế GTGT: 100.000 VND",
            "Tổng thanh toán: 1.100.000 VND",
            "Ghi chú: Hàng demo, không phải dữ liệu thật",
        ]
    )

    assert fields["supplier_name"] == "CÔNG TY TNHH MINH AN"
    assert fields["tax_code"] == "0000000000"
    assert fields["document_number"] == "HD-2026-001"
    assert fields["document_date"] == "12/06/2026"
    assert fields["subtotal"] == "1000000"
    assert fields["vat_amount"] == "100000"
    assert fields["total_amount"] == "1100000"
    assert fields["currency"] == "VND"
    assert fields["notes"] == "Hàng demo, không phải dữ liệu thật"


def test_extracts_receipt_like_fields() -> None:
    fields = fields_from_lines(
        [
            "CUA HANG ANH DAO",
            "MST: 1111111111",
            "So chung tu: RC-0099",
            "Ngay: 01/05/2026",
            "Tam tinh: 250000 VND",
            "VAT: 0 VND",
            "Tong cong: 250000 VND",
            "Ghi chu: Bien lai ban le synthetic",
        ]
    )

    assert fields["supplier_name"] == "CUA HANG ANH DAO"
    assert fields["tax_code"] == "1111111111"
    assert fields["document_number"] == "RC-0099"
    assert fields["document_date"] == "01/05/2026"
    assert fields["subtotal"] == "250000"
    assert fields["vat_amount"] == "0"
    assert fields["total_amount"] == "250000"
    assert fields["notes"] == "Bien lai ban le synthetic"


def test_extracts_delivery_note_like_fields_and_known_weak_cases() -> None:
    fields = fields_from_lines(
        [
            "Người gửi: KHO HANG HOA VIET",
            "MST: 2222222222",
            "Số phiếu: PXK-2026-77",
            "Ngày giao: 03/06/2026",
            "Tạm tính: 780.000 VND",
            "VAT: 78.000 VND",
            "Tổng cộng: 858.000 VND",
            "Ghi nhận: Giao hàng trước 17h",
        ]
    )

    assert fields["supplier_name"] == "KHO HANG HOA VIET"
    assert fields["tax_code"] == "2222222222"
    assert fields["document_number"] == "PXK-2026-77"
    assert fields["document_date"] == "03/06/2026"
    assert fields["subtotal"] == "780000"
    assert fields["vat_amount"] == "78000"
    assert fields["total_amount"] == "858000"
    assert fields["notes"] == "Giao hàng trước 17h"
