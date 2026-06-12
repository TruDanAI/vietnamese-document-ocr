from app.services.ocr.base import OcrAdapter, OcrBlockResult


class PaddleOcrAdapter(OcrAdapter):
    engine_name = "paddleocr"

    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Use OCR_ENGINE=mock or install PaddleOCR separately."
            ) from exc

        self._ocr = PaddleOCR(lang="vi")

    def run_page(self, page_path: str, page_number: int) -> list[OcrBlockResult]:
        result = self._ocr.ocr(page_path)
        blocks: list[OcrBlockResult] = []
        for page in result or []:
            for item in page or []:
                points = item[0]
                text, confidence = item[1]
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                blocks.append(
                    OcrBlockResult(
                        text=str(text),
                        confidence=float(confidence),
                        bbox={
                            "x": min(xs),
                            "y": min(ys),
                            "width": max(xs) - min(xs),
                            "height": max(ys) - min(ys),
                            "polygon": points,
                        },
                    )
                )
        return blocks
