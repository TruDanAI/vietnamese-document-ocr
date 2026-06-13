from app.services.ocr.base import OcrAdapter, OcrBlockResult


class PaddleOcrAdapter(OcrAdapter):
    engine_name = "paddle"
    model_name = "paddleocr_lang_vi_auto"

    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Use OCR_ENGINE=mock or install PaddleOCR separately."
            ) from exc

        try:
            self._ocr = PaddleOCR(lang="vi")
        except Exception as exc:
            raise RuntimeError(f"PaddleOCR failed to initialize: {exc}") from exc
        self.model_name = _detect_model_name(self._ocr) or self.model_name

    def run_page(self, page_path: str, page_number: int) -> list[OcrBlockResult]:
        try:
            result = self._ocr.ocr(page_path)
        except Exception as exc:
            raise RuntimeError(f"PaddleOCR failed while reading page {page_number}: {exc}") from exc

        blocks: list[OcrBlockResult] = []
        for item in _flatten_paddle_result(result):
            parsed = _parse_paddle_item(item)
            if parsed is None:
                continue
            points, text, confidence = parsed
            xs = [float(point[0]) for point in points]
            ys = [float(point[1]) for point in points]
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
                    page_number=page_number,
                    block_index=len(blocks),
                )
            )
        return blocks


def _flatten_paddle_result(result):
    if not result:
        return []
    if isinstance(result, list) and result and _looks_like_ocr_item(result[0]):
        return result

    flattened = []
    for page in result:
        if isinstance(page, dict):
            # PaddleOCR 3.x prediction objects may serialize into dict-like shapes.
            rec_texts = page.get("rec_texts") or []
            rec_scores = page.get("rec_scores") or []
            rec_polys = page.get("rec_polys") or page.get("dt_polys") or []
            for index, text in enumerate(rec_texts):
                score = rec_scores[index] if index < len(rec_scores) else 0.0
                poly = rec_polys[index] if index < len(rec_polys) else [[0, 0], [0, 0], [0, 0], [0, 0]]
                flattened.append([poly, [text, score]])
        elif isinstance(page, list):
            flattened.extend(page)
    return flattened


def _looks_like_ocr_item(item) -> bool:
    return isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], (list, tuple))


def _parse_paddle_item(item):
    if not _looks_like_ocr_item(item):
        return None
    points = item[0]
    text_confidence = item[1]
    if len(text_confidence) < 2:
        return None
    return points, text_confidence[0], text_confidence[1]


def _detect_model_name(ocr) -> str | None:
    for attribute in ("model_name", "ocr_version", "version"):
        value = getattr(ocr, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
