from app.services.ocr.base import OcrAdapter, OcrBlockResult


class MockOcrAdapter(OcrAdapter):
    engine_name = "mock"

    def run_page(self, page_path: str, page_number: int) -> list[OcrBlockResult]:
        lines = [
            "CONG TY TNHH MINH AN",
            "MST: 0312345678",
            "So chung tu: HD-2026-001",
            "Ngay: 12/06/2026",
            "Tam tinh: 1000000 VND",
            "VAT: 100000 VND",
            "Tong cong: 1100000 VND",
            "Ghi chu: Demo OCR block tu mock adapter",
        ]
        return [
            OcrBlockResult(
                text=line,
                confidence=0.98 - index * 0.02,
                bbox={"x": 40, "y": 40 + index * 34, "width": 520, "height": 26},
            )
            for index, line in enumerate(lines)
        ]
