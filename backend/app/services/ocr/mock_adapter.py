from app.services.ocr.base import OcrAdapter, OcrBlockResult


class MockOcrAdapter(OcrAdapter):
    engine_name = "mock"
    model_name = "mock_synthetic"

    def run_page(self, page_path: str, page_number: int) -> list[OcrBlockResult]:
        lines = _lines_for_path(page_path)
        return [
            OcrBlockResult(
                text=line,
                confidence=0.98 - index * 0.02,
                bbox={
                    "x": 40,
                    "y": 40 + index * 34,
                    "width": 520,
                    "height": 26,
                    "polygon": [
                        [40, 40 + index * 34],
                        [560, 40 + index * 34],
                        [560, 66 + index * 34],
                        [40, 66 + index * 34],
                    ],
                },
                page_number=page_number,
                block_index=index,
            )
            for index, line in enumerate(lines)
        ]


def _lines_for_path(page_path: str) -> list[str]:
    normalized = page_path.lower()
    if "invoice-stress-demo" in normalized:
        return [
            "HÓA ĐƠN BÁN HÀNG",
            "Đơn vị bán: CÔNG TY TNHH DEMO OCR",
            "MST: 0000000000",
            "Số hóa đơn: DEMO-INV-010",
            "Ngày: 14/06/2026",
            "Mô tả | SL | Đơn giá | Thành tiền",
            "Dịch vụ demo A | 1 | 750.000 | 750.000",
            "Dịch vụ demo B | 2 | 250.000 | 500.000",
            "Cộng tiền hàng: 1.250.000 VND",
            "Thuế GTGT: 125.000 VND",
            "Tổng thanh toán: 1.375.000 VND",
            "Ghi chú: Hóa đơn stress synthetic",
        ]
    if "invoice-demo-diacritics" in normalized:
        return [
            "HÓA ĐƠN BÁN HÀNG",
            "Don vi ban: CÔNG TY TNHH DEMO OCR",
            "MST: 0000000000",
            "So hoa don: DEMO-INV-009",
            "Ngay: 14/06/2026",
            "Cong tien hang: 1.250.000 VND",
            "Thue GTGT: 125.000 VND",
            "Tong thanh toan: 1.375.000 VND",
            "Ghi chu: Hoa don demo OCR",
        ]
    if "invoice-alt-labels" in normalized:
        return [
            "Nha cung cap: CONG TY CO PHAN NAM PHU",
            "Tax code: 0312345678",
            "Invoice No: INV/2026/88",
            "Date: 15-06-2026",
            "Subtotal 3.300.000 VND",
            "VAT 330.000 VND",
            "Total 3.630.000 VND",
            "Note: Alternate invoice labels synthetic",
        ]
    if "invoice-split-values" in normalized:
        return [
            "Don vi ban:",
            "CONG TY TNHH SAO BAC",
            "MST:",
            "0300000001",
            "So hoa don:",
            "INV-2026-014",
            "Ngay lap:",
            "05/06/2026",
            "Cong tien hang:",
            "2,500,000 VND",
            "Thue GTGT:",
            "250,000 VND",
            "Tong thanh toan:",
            "2,750,000 VND",
            "Ghi chu:",
            "Hoa don synthetic chia dong",
        ]
    if "receipt-discount" in normalized:
        return [
            "CUA HANG MINH CHAU",
            "Ma so thue: 010 000 0003",
            "So chung tu: RC-2026-15",
            "Date: 07-06-2026",
            "Tam tinh: 500.000 VND",
            "VAT: 0 VND",
            "Tong thanh toan: 450.000 VND",
            "Ghi chu - Khuyen mai synthetic",
        ]
    if "receipt-marketplace" in normalized:
        return [
            "CUA HANG HOA SEN",
            "MST: 0100000002",
            "So bien lai: BL-2026-02",
            "Ngay ban: 06/06/2026",
            "Tong tien hang: 125.000 VND",
            "VAT: 0 VND",
            "Tong cong: 125.000 VND",
            "Ghi chu: Bien lai synthetic khong VAT",
        ]
    if "receipt-demo-diacritics" in normalized:
        return [
            "BIÊN LAI BÁN HÀNG",
            "CUA HANG DEMO",
            "MST: 0000000000",
            "So bien lai: DEMO-REC-009",
            "Ngay ban: 14/06/2026",
            "Tam tinh: 320.000 VND",
            "VAT: 0 VND",
            "Tong cong: 320.000 VND",
            "Ghi chu: Bán hàng demo OCR",
        ]
    if "receipt-stress-demo" in normalized:
        return [
            "BIÊN LAI BÁN HÀNG",
            "CỬA HÀNG DEMO",
            "MST: 0000000000",
            "Số biên lai: DEMO-REC-010",
            "Ngày bán: 14/06/2026",
            "Cà phê demo: 45.000 VND",
            "Bánh demo: 35.000 VND",
            "Tạm tính: 80.000 VND",
            "VAT: 0 VND",
            "Tổng cộng: 80.000 VND",
            "Ghi chú: Biên lai stress synthetic",
        ]
    if "delivery-note-split-sender" in normalized:
        return [
            "PHIEU GIAO HANG",
            "Nguoi gui:",
            "KHO TRUNG TAM FAKE",
            "MST: 0200000004",
            "So phieu giao: PGH-2026-21",
            "Ngay giao hang: 08/06/2026",
            "Tong tien hang: 980.000 VND",
            "VAT 98.000 VND",
            "Can thanh toan: 1.078.000 VND",
            "Ghi nhan: Synthetic delivery note",
        ]
    if "delivery-note-warehouse" in normalized:
        return [
            "Kho xuat: KHO MIEN NAM SYNTHETIC",
            "So phieu xuat: PX-2026-31",
            "Ngay xuat: 09/06/2026",
            "Thanh tien: 640000 VND",
            "Tong phai tra: 640000 VND",
            "Ghi chu: Hang synthetic noi bo",
        ]
    if "delivery-note-stress-demo" in normalized:
        return [
            "PHIẾU GIAO HÀNG",
            "Người gửi: KHO DEMO",
            "MST: 0000000000",
            "Số phiếu giao: DEMO-DN-010",
            "Ngày giao hàng: 14/06/2026",
            "Hàng demo | Số lượng | Đơn vị | Thành tiền",
            "Thùng demo A | 03 | thùng | 300.000",
            "Kiện demo B | 02 | kiện | 240.000",
            "Tạm tính: 540.000 VND",
            "VAT: 54.000 VND",
            "Cần thanh toán: 594.000 VND",
            "Ghi nhận: Giao hàng stress synthetic",
        ]
    if "delivery-note-demo-diacritics" in normalized:
        return [
            "PHIẾU GIAO HÀNG",
            "Nguoi gui: KHO DEMO",
            "MST: 0000000000",
            "So phieu giao: DEMO-DN-009",
            "Ngay giao hang: 14/06/2026",
            "Tam tinh: 540.000 VND",
            "VAT: 54.000 VND",
            "Can thanh toan: 594.000 VND",
            "Ghi nhan: Giao hàng demo OCR",
        ]
    if "delivery" in normalized or "giao" in normalized:
        return [
            "Nguoi gui: KHO HANG HOA VIET",
            "MST: 2222222222",
            "So phieu: PXK-2026-77",
            "Ngay giao: 03/06/2026",
            "Thanh tien: 780.000 VND",
            "VAT: 78.000 VND",
            "Tong cong: 858.000 VND",
            "Ghi nhan: Giao hang truoc 17h",
        ]
    if "receipt" in normalized or "bien_lai" in normalized:
        return [
            "CUA HANG ANH DAO",
            "MST: 1111111111",
            "So chung tu: RC-0099",
            "Ngay: 01/05/2026",
            "Tam tinh: 250000 VND",
            "VAT: 0 VND",
            "Tong cong: 250000 VND",
            "Ghi chu: Bien lai ban le synthetic",
        ]
    return [
            "Don vi ban: CONG TY TNHH MINH AN",
            "MST: 0000000000",
            "So hoa don: HD-2026-001",
            "Ngay: 12/06/2026",
            "Cong tien hang: 1.000.000 VND",
            "Thue GTGT: 100.000 VND",
            "Tong thanh toan: 1.100.000 VND",
            "Ghi chu: Du lieu demo, khong phai thong tin that",
        ]
