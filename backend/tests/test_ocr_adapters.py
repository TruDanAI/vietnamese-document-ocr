import builtins
import os
import sys
from types import ModuleType

import pytest

from app.config import Settings
from app.services.ocr.factory import build_ocr_adapter
from app.services.ocr.paddle_adapter import PADDLE_MKLDNN_ENV, PaddleOcrAdapter


def test_default_ocr_engine_remains_mock() -> None:
    assert Settings().ocr_engine == "mock"


def test_mock_adapter_reports_clear_metadata() -> None:
    adapter = build_ocr_adapter("mock")

    assert adapter.engine_name == "mock"
    assert adapter.model_name == "mock_synthetic"


def test_paddle_import_failure_has_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def fail_paddle_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "paddleocr":
            raise ImportError("No module named paddleocr")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fail_paddle_import)

    with pytest.raises(RuntimeError, match="PaddleOCR is not installed.*OCR_ENGINE=mock"):
        PaddleOcrAdapter()


def test_ppocrv6_engine_requires_explicit_ocr_version_api(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = ModuleType("paddleocr")

    class FakePaddleOCR:
        def __init__(self, *, lang=None):
            self.lang = lang

        def ocr(self, page_path):
            return []

    fake_module.PaddleOCR = FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    with pytest.raises(RuntimeError, match="does not expose explicit ocr_version"):
        build_ocr_adapter("ppocrv6")


def test_paddle_adapter_returns_blocks_from_paddle_result(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = ModuleType("paddleocr")

    class FakePaddleOCR:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def ocr(self, page_path):
            assert page_path == "page.png"
            return [
                {
                    "rec_texts": ["CÔNG TY TNHH DEMO OCR"],
                    "rec_scores": [0.98],
                    "rec_polys": [
                        [[10, 20], [210, 20], [210, 50], [10, 50]],
                    ],
                }
            ]

    fake_module.PaddleOCR = FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    adapter = build_ocr_adapter("paddle")
    blocks = adapter.run_page("page.png", 1)

    assert adapter.engine_name == "paddle"
    assert adapter.model_name == "paddleocr_lang_vi_auto"
    assert len(blocks) == 1
    assert blocks[0].text == "CÔNG TY TNHH DEMO OCR"
    assert blocks[0].confidence == 0.98
    assert blocks[0].bbox["x"] == 10
    assert blocks[0].bbox["width"] == 200
    assert blocks[0].bbox["polygon"] == [[10.0, 20.0], [210.0, 20.0], [210.0, 50.0], [10.0, 50.0]]


def test_paddle_adapter_returns_blocks_from_nested_paddle_2_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = ModuleType("paddleocr")

    class FakePaddleOCR:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def ocr(self, page_path):
            assert page_path == "page.png"
            return [
                [
                    [
                        [[0, 0], [10, 0], [10, 10], [0, 10]],
                        ["CÔNG TY TNHH DEMO OCR", 0.98],
                    ],
                    [
                        [[0, 20], [10, 20], [10, 30], [0, 30]],
                        ["MST 0000000000", 0.97],
                    ],
                ]
            ]

    fake_module.PaddleOCR = FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    adapter = build_ocr_adapter("paddle")
    blocks = adapter.run_page("page.png", 1)

    assert len(blocks) == 2
    assert blocks[0].text == "CÔNG TY TNHH DEMO OCR"
    assert blocks[1].text == "MST 0000000000"
    assert blocks[0].bbox["polygon"] == [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]]
    assert blocks[1].bbox["polygon"] == [[0.0, 20.0], [10.0, 20.0], [10.0, 30.0], [0.0, 30.0]]
    assert all(
        isinstance(coordinate, float)
        for block in blocks
        for point in block.bbox["polygon"]
        for coordinate in point
    )


def test_paddle_adapter_preserves_existing_mkldnn_env(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = ModuleType("paddleocr")
    monkeypatch.setenv(PADDLE_MKLDNN_ENV, "1")

    class FakePaddleOCR:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def ocr(self, page_path):
            return []

    fake_module.PaddleOCR = FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    PaddleOcrAdapter()

    assert os.environ[PADDLE_MKLDNN_ENV] == "1"


def test_ppocrv6_adapter_uses_explicit_verified_ocr_version(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = ModuleType("paddleocr")
    calls = []

    class FakePaddleOCR:
        def __init__(self, *, lang=None, ocr_version=None):
            calls.append({"lang": lang, "ocr_version": ocr_version})

        def ocr(self, page_path):
            return []

    fake_module.PaddleOCR = FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", fake_module)

    adapter = build_ocr_adapter("ppocrv6")

    assert adapter.engine_name == "ppocrv6"
    assert adapter.model_name == "PP-OCRv6_medium_det+PP-OCRv6_medium_rec"
    assert calls == [{"lang": "vi", "ocr_version": "PP-OCRv6"}]
