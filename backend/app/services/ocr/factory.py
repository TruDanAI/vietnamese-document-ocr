from app.services.ocr.base import OcrAdapter
from app.services.ocr.mock_adapter import MockOcrAdapter
from app.services.ocr.paddle_adapter import PaddleOcrAdapter


def build_ocr_adapter(engine_name: str) -> OcrAdapter:
    normalized = engine_name.lower().strip()
    if normalized == "mock":
        return MockOcrAdapter()
    if normalized == "paddleocr":
        return PaddleOcrAdapter()
    raise ValueError(f"Unsupported OCR engine: {engine_name}")
