import inspect
import os
from collections.abc import Mapping

from app.services.ocr.base import OcrAdapter, OcrBlockResult


PADDLE_LANG = "vi"
PADDLE_MKLDNN_ENV = "PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"
PPOCRV6_OCR_VERSION = "PP-OCRv6"
PPOCRV6_MODEL_NAME = "PP-OCRv6_medium_det+PP-OCRv6_medium_rec"


class PaddleOcrAdapter(OcrAdapter):
    engine_name = "paddle"
    model_name = "paddleocr_lang_vi_auto"

    def __init__(
        self,
        *,
        engine_name: str | None = None,
        model_name: str | None = None,
        ocr_kwargs: dict | None = None,
        require_ocr_version_api: bool = False,
    ) -> None:
        self.engine_name = engine_name or self.engine_name
        self.model_name = model_name or self.model_name
        ocr_kwargs = dict(ocr_kwargs or {"lang": PADDLE_LANG})

        try:
            _apply_paddle_runtime_defaults()
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Use OCR_ENGINE=mock or install PaddleOCR separately."
            ) from exc

        if require_ocr_version_api:
            _ensure_explicit_ocr_version_api(PaddleOCR)

        try:
            self._ocr = PaddleOCR(**ocr_kwargs)
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
            points = _normalize_points(points)
            if not points:
                continue
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


class PpOcrV6Adapter(PaddleOcrAdapter):
    engine_name = "ppocrv6"
    model_name = PPOCRV6_MODEL_NAME

    def __init__(self) -> None:
        super().__init__(
            engine_name=self.engine_name,
            model_name=self.model_name,
            ocr_kwargs={"lang": PADDLE_LANG, "ocr_version": PPOCRV6_OCR_VERSION},
            require_ocr_version_api=True,
        )


def _flatten_paddle_result(result):
    flattened = []
    _collect_paddle_items(result, flattened)
    return flattened


def _collect_paddle_items(value, flattened: list) -> None:
    page_mapping = _as_mapping(value)
    if page_mapping is not None:
        flattened.extend(_items_from_page_mapping(page_mapping))
        return

    sequence = _as_sequence(value)
    if sequence is None:
        return
    if _looks_like_ocr_item(sequence):
        flattened.append(sequence)
        return

    for item in sequence:
        _collect_paddle_items(item, flattened)


def _looks_like_ocr_item(item) -> bool:
    item_sequence = _as_sequence(item)
    if item_sequence is None or len(item_sequence) < 2:
        return False
    return _looks_like_polygon(item_sequence[0]) and _looks_like_text_score_pair(item_sequence[1])


def _looks_like_polygon(value) -> bool:
    points = _as_sequence(value)
    if points is None or len(points) < 2:
        return False
    return _looks_like_point(points[0]) and _looks_like_point(points[1])


def _looks_like_point(value) -> bool:
    point = _as_sequence(value)
    if point is None or len(point) < 2:
        return False
    return _coerce_float(point[0]) is not None and _coerce_float(point[1]) is not None


def _looks_like_text_score_pair(value) -> bool:
    text_score = _as_sequence(value)
    if text_score is None or len(text_score) < 2:
        return False
    return isinstance(text_score[0], str) and _coerce_float(text_score[1]) is not None


def _parse_paddle_item(item):
    item_sequence = _as_sequence(item)
    if item_sequence is None or not _looks_like_ocr_item(item_sequence):
        return None
    points = item_sequence[0]
    text_confidence = _as_sequence(item_sequence[1])
    if text_confidence is None or len(text_confidence) < 2:
        return None
    confidence = _coerce_float(text_confidence[1])
    if confidence is None:
        return None
    return points, text_confidence[0], confidence


def _as_mapping(value) -> Mapping | None:
    if isinstance(value, Mapping):
        return value
    for method_name in ("to_dict", "dict"):
        method = getattr(value, method_name, None)
        if callable(method):
            try:
                mapped = method()
            except (TypeError, ValueError):
                continue
            if isinstance(mapped, Mapping):
                return mapped
    return None


def _items_from_page_mapping(page: Mapping) -> list:
    result_page = _as_mapping(page.get("res")) if "res" in page else None
    page = result_page or page

    rec_texts = _as_sequence(page.get("rec_texts")) or []
    rec_scores = _as_sequence(page.get("rec_scores")) or []
    rec_polys = _as_sequence(page.get("rec_polys"))
    if rec_polys is None:
        rec_polys = _as_sequence(page.get("dt_polys"))
    rec_polys = rec_polys or []

    flattened = []
    for index, text in enumerate(rec_texts):
        score = rec_scores[index] if index < len(rec_scores) else 0.0
        poly = rec_polys[index] if index < len(rec_polys) else [[0, 0], [0, 0], [0, 0], [0, 0]]
        flattened.append([poly, [text, score]])
    return flattened


def _normalize_points(points) -> list[list[float]]:
    normalized = []
    point_sequence = _as_sequence(points)
    if point_sequence is None:
        return normalized

    for point in point_sequence:
        point = _as_sequence(point)
        if point is None or len(point) < 2:
            continue
        x = _coerce_float(point[0])
        y = _coerce_float(point[1])
        if x is None or y is None:
            continue
        normalized.append([x, y])
    return normalized


def _as_sequence(value) -> list | None:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (str, bytes, Mapping)):
        return None
    if isinstance(value, (list, tuple)):
        return list(value)
    return None


def _coerce_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _detect_model_name(ocr) -> str | None:
    for attribute in ("model_name", "ocr_version", "version"):
        value = getattr(ocr, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _apply_paddle_runtime_defaults() -> None:
    # Avoids a PaddlePaddle 3.3 CPU oneDNN/PIR inference crash seen in local smoke runs.
    os.environ.setdefault(PADDLE_MKLDNN_ENV, "0")


def _ensure_explicit_ocr_version_api(paddle_ocr_class) -> None:
    try:
        parameters = inspect.signature(paddle_ocr_class).parameters
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "Installed PaddleOCR package does not expose inspectable constructor "
            "metadata for explicit PP-OCRv6 selection."
        ) from exc

    if "ocr_version" not in parameters:
        raise RuntimeError(
            "Installed PaddleOCR package does not expose explicit ocr_version "
            "selection for PP-OCRv6. Use OCR_ENGINE=mock or OCR_ENGINE=paddle."
        )
