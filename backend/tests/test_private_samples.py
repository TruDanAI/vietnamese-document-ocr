from pathlib import Path

from PIL import Image

from app.evaluation import private_samples
from app.services.ocr.base import OcrAdapter, OcrBlockResult


class FakeOcrAdapter(OcrAdapter):
    engine_name = "fake"
    model_name = "fake_model"

    def __init__(self) -> None:
        self.page_paths: list[str] = []

    def run_page(self, page_path: str, page_number: int) -> list[OcrBlockResult]:
        self.page_paths.append(page_path)
        lines = [
            "Don vi ban: CONG TY TNHH DEMO OCR",
            "MST: 0000000000",
            "So hoa don: DEMO-INV-001",
            "Ngay: 14/06/2026",
            "Tong thanh toan: 100.000 VND",
            "RAW OCR PREVIEW SENTINEL",
        ]
        return [
            OcrBlockResult(
                text=line,
                confidence=0.95,
                bbox={"x": 0, "y": index * 20, "width": 200, "height": 20},
                page_number=page_number,
                block_index=index,
            )
            for index, line in enumerate(lines)
        ]


def _write_png(path: Path) -> None:
    image = Image.new("RGB", (20, 20), "white")
    image.save(path)


def test_private_sample_harness_exits_cleanly_for_empty_input(tmp_path: Path, capsys) -> None:
    input_dir = tmp_path / "private_samples"
    output_dir = tmp_path / "eval_reports"
    input_dir.mkdir()

    result = private_samples.run_private_sample_harness(
        engine="mock",
        input_dir=input_dir,
        output_dir=output_dir,
    )

    captured = capsys.readouterr()
    assert result.markdown_path is None
    assert result.json_path is None
    assert result.document_count == 0
    assert "No supported private sample files found" in captured.out
    assert not output_dir.exists()


def test_private_sample_discovery_supports_images_and_pdfs_only(tmp_path: Path) -> None:
    for filename in ["sample.png", "sample.jpg", "sample.jpeg", "sample.pdf", "notes.txt", "data.json"]:
        (tmp_path / filename).write_bytes(b"placeholder")

    files = private_samples.discover_private_samples(tmp_path)

    assert [path.name for path in files] == ["sample.jpeg", "sample.jpg", "sample.pdf", "sample.png"]


def test_private_sample_report_omits_raw_ocr_preview_by_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_dir = tmp_path / "private_samples"
    output_dir = tmp_path / "eval_reports"
    pages_dir = tmp_path / "pages"
    input_dir.mkdir()
    _write_png(input_dir / "anonymized-demo.png")
    adapter = FakeOcrAdapter()
    monkeypatch.setattr(private_samples, "build_ocr_adapter", lambda engine: adapter)

    result = private_samples.run_private_sample_harness(
        engine="paddle",
        input_dir=input_dir,
        output_dir=output_dir,
        pages_dir=pages_dir,
    )

    assert result.markdown_path is not None
    assert result.json_path is not None
    markdown = result.markdown_path.read_text(encoding="utf-8")
    json_text = result.json_path.read_text(encoding="utf-8")
    assert "RAW OCR PREVIEW SENTINEL" not in markdown
    assert "RAW OCR PREVIEW SENTINEL" not in json_text
    assert "ocr_preview" not in json_text
    assert output_dir in result.markdown_path.parents
    assert pages_dir.exists()


def test_private_sample_report_includes_ocr_preview_only_when_enabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_dir = tmp_path / "private_samples"
    output_dir = tmp_path / "eval_reports"
    input_dir.mkdir()
    _write_png(input_dir / "anonymized-demo.png")
    monkeypatch.setattr(private_samples, "build_ocr_adapter", lambda engine: FakeOcrAdapter())

    result = private_samples.run_private_sample_harness(
        engine="ppocrv6",
        input_dir=input_dir,
        output_dir=output_dir,
        include_ocr_preview=True,
    )

    assert result.markdown_path is not None
    assert result.json_path is not None
    markdown = result.markdown_path.read_text(encoding="utf-8")
    json_text = result.json_path.read_text(encoding="utf-8")
    assert "OCR Preview" in markdown
    assert "RAW OCR PREVIEW SENTINEL" in markdown
    assert "RAW OCR PREVIEW SENTINEL" in json_text


def test_private_sample_harness_does_not_require_expected_json(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_dir = tmp_path / "private_samples"
    output_dir = tmp_path / "eval_reports"
    input_dir.mkdir()
    _write_png(input_dir / "anonymized-no-ground-truth.png")
    monkeypatch.setattr(private_samples, "build_ocr_adapter", lambda engine: FakeOcrAdapter())

    result = private_samples.run_private_sample_harness(
        engine="mock",
        input_dir=input_dir,
        output_dir=output_dir,
    )

    assert result.document_count == 1
    assert result.markdown_path is not None
    report_text = result.json_path.read_text(encoding="utf-8") if result.json_path else ""
    assert "expected_file" not in report_text
    assert "ground_truth" not in report_text


def test_private_sample_harness_uses_injected_fake_adapter_not_real_paddle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    input_dir = tmp_path / "private_samples"
    output_dir = tmp_path / "eval_reports"
    input_dir.mkdir()
    _write_png(input_dir / "anonymized-demo.png")
    adapter = FakeOcrAdapter()
    monkeypatch.setattr(private_samples, "build_ocr_adapter", lambda engine: adapter)

    result = private_samples.run_private_sample_harness(
        engine="paddle",
        input_dir=input_dir,
        output_dir=output_dir,
    )

    assert result.document_count == 1
    assert adapter.page_paths
    assert result.report is not None
    assert result.report["engine"] == "fake"
    assert result.report["model_name"] == "fake_model"
