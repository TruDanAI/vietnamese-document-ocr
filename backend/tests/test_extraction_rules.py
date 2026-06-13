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


def test_extracts_split_invoice_label_values() -> None:
    fields = fields_from_lines(
        [
            "Don vi ban:",
            "CONG TY TNHH SAO BAC",
            "MST:",
            "0300000001",
            "So hoa don:",
            "INV-2026-014",
            "Ngay lap:",
            "05/06/2026",
            "Tong thanh toan:",
            "2,750,000 VND",
            "Ghi chu:",
            "Hoa don synthetic chia dong",
        ]
    )

    assert fields["supplier_name"] == "CONG TY TNHH SAO BAC"
    assert fields["tax_code"] == "0300000001"
    assert fields["document_number"] == "INV-2026-014"
    assert fields["document_date"] == "05/06/2026"
    assert fields["total_amount"] == "2750000"
    assert fields["notes"] == "Hoa don synthetic chia dong"


def test_extracts_receipt_variant_labels_and_spaced_tax_code() -> None:
    fields = fields_from_lines(
        [
            "CUA HANG HOA SEN",
            "Ma so thue: 010 000 0003",
            "So bien lai: BL-2026-02",
            "Ngay ban: 06/06/2026",
            "Tong tien hang: 125.000 VND",
            "Tong cong: 125.000 VND",
        ]
    )

    assert fields["tax_code"] == "0100000003"
    assert fields["document_number"] == "BL-2026-02"
    assert fields["document_date"] == "06/06/2026"
    assert fields["subtotal"] == "125000"
    assert fields["total_amount"] == "125000"


def test_extracts_delivery_variant_labels_without_total_substring_collision() -> None:
    fields = fields_from_lines(
        [
            "PHIEU GIAO HANG",
            "Nguoi gui:",
            "KHO TRUNG TAM FAKE",
            "So phieu giao: PGH-2026-21",
            "Ngay giao hang: 08/06/2026",
            "Subtotal 980.000 VND",
            "Total 1.078.000 VND",
        ]
    )

    assert fields["supplier_name"] == "KHO TRUNG TAM FAKE"
    assert fields["document_number"] == "PGH-2026-21"
    assert fields["document_date"] == "08/06/2026"
    assert fields["subtotal"] == "980000"
    assert fields["total_amount"] == "1078000"


def test_rejects_heavily_spaced_partial_tax_code() -> None:
    fields = fields_from_lines(
        [
            "CUA HANG TEST",
            "Ma so thue: 010 000 0",
            "So chung tu: RC-TEST-01",
            "Ngay: 10/06/2026",
        ]
    )

    assert fields["tax_code"] is None


def test_subtotal_without_true_total_does_not_extract_total_amount() -> None:
    fields = fields_from_lines(
        [
            "Don vi ban: CONG TY TEST",
            "MST: 0100000009",
            "So hoa don: INV-TEST-01",
            "Ngay: 10/06/2026",
            "Subtotal 980.000 VND",
        ]
    )

    assert fields["subtotal"] == "980000"
    assert fields["total_amount"] is None


def test_prefers_final_payable_total_when_multiple_total_like_amounts_exist() -> None:
    fields = fields_from_lines(
        [
            "Don vi ban: CONG TY TEST",
            "MST: 0100000010",
            "So hoa don: INV-TEST-02",
            "Ngay: 10/06/2026",
            "Tong cong: 1.000.000 VND",
            "Can thanh toan: 900.000 VND",
        ]
    )

    assert fields["total_amount"] == "900000"
