import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvalSample:
    sample_id: str
    document_type: str
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
        samples.append(
            EvalSample(
                sample_id=payload["sample_id"],
                document_type=payload["document_type"],
                source_file=source_file,
                expected_file=expected_file,
                expected_fields=expected_payload["fields"],
            )
        )
    return samples
