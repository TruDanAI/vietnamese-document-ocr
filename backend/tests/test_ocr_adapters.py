import builtins

import pytest

from app.config import Settings
from app.services.ocr.factory import build_ocr_adapter
from app.services.ocr.paddle_adapter import PaddleOcrAdapter


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


def test_ppocrv6_engine_is_not_faked_without_verified_api_support() -> None:
    with pytest.raises(ValueError, match="PP-OCRv6 is not enabled"):
        build_ocr_adapter("ppocrv6")
