import json
from dataclasses import dataclass
from pathlib import Path


EVAL_MODE_MOCK_ONLY = "mock_only"
EVAL_MODE_REAL_OCR = "real_ocr"
VALID_EVAL_MODES = {EVAL_MODE_MOCK_ONLY, EVAL_MODE_REAL_OCR}


@dataclass(frozen=True)
class EvalSample:
    sample_id: str
    document_type: str
    eval_mode: str
    source_file: Path
    expected_file: Path
    expected_fields: dict[str, str | None]


def load_eval_samples(dataset_dir: Path) -> list[EvalSample]:
    sample_files = sorted(dataset_dir.glob("*/*.sample.json"))
    samples: list[EvalSample] = []
    for sample_file in sample_files:
        payload = json.loads(sample_file.read_text(encoding="utf-8"))
        expected_file = (sample_file.parent / payload["expected_file"]).resolve()
        source_file = (sample_file.parent / payload["source_file"]).resolve()
        expected_payload = json.loads(expected_file.read_text(encoding="utf-8"))
        eval_mode = payload.get("eval_mode", EVAL_MODE_MOCK_ONLY)
        if eval_mode not in VALID_EVAL_MODES:
            raise ValueError(
                f"Unsupported eval_mode={eval_mode!r} in {sample_file}. "
                f"Expected one of: {', '.join(sorted(VALID_EVAL_MODES))}."
            )
        samples.append(
            EvalSample(
                sample_id=payload["sample_id"],
                document_type=payload["document_type"],
                eval_mode=eval_mode,
                source_file=source_file,
                expected_file=expected_file,
                expected_fields=expected_payload["fields"],
            )
        )
    return samples
