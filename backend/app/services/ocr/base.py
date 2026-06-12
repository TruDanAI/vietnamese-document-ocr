from dataclasses import dataclass


@dataclass(frozen=True)
class OcrBlockResult:
    text: str
    confidence: float
    bbox: dict


class OcrAdapter:
    engine_name = "base"

    def run_page(self, page_path: str, page_number: int) -> list[OcrBlockResult]:
        raise NotImplementedError
