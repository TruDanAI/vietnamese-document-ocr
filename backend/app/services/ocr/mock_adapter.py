from app.services.ocr.base import OcrAdapter, OcrBlockResult


class MockOcrAdapter(OcrAdapter):
    engine_name = "mock"

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
    if "delivery" in normalized or "giao" in normalized:
        return [
            "Nguoi gui: KHO HANG HOA VIET",
            "MST: 0311112222",
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
            "MST: 0109998888",
            "So chung tu: RC-0099",
            "Ngay: 01/05/2026",
            "Tam tinh: 250000 VND",
            "VAT: 0 VND",
            "Tong cong: 250000 VND",
            "Ghi chu: Bien lai ban le synthetic",
        ]
    return [
            "Don vi ban: CONG TY TNHH MINH AN",
            "MST: 0312345678",
            "So hoa don: HD-2026-001",
            "Ngay: 12/06/2026",
            "Cong tien hang: 1.000.000 VND",
            "Thue GTGT: 100.000 VND",
            "Tong thanh toan: 1.100.000 VND",
            "Ghi chu: Du lieu demo, khong phai thong tin that",
        ]
