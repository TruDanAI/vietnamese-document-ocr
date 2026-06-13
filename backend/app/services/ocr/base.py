from dataclasses import dataclass


@dataclass(frozen=True)
class OcrBlockResult:
    text: str
    confidence: float
    bbox: dict
    page_number: int
    block_index: int


class OcrAdapter:
    engine_name = "base"
    model_name = "unknown"

    def run_page(self, page_path: str, page_number: int) -> list[OcrBlockResult]:
        raise NotImplementedError
