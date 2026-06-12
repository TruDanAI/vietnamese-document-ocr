import re
from pathlib import Path
from uuid import uuid4


class LocalStorageService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.uploads_dir = root / "uploads"
        self.exports_dir = root / "exports"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> str:
        safe_name = self._safe_filename(filename or "document.bin")
        storage_name = f"{uuid4()}-{safe_name}"
        path = self.uploads_dir / storage_name
        path.write_bytes(content)
        return str(path)

    def write_export(self, filename: str, content: str) -> str:
        safe_name = self._safe_filename(filename)
        path = self.exports_dir / safe_name
        path.write_text(content, encoding="utf-8")
        return str(path)

    @staticmethod
    def _safe_filename(filename: str) -> str:
        name = Path(filename).name.strip() or "file"
        return re.sub(r"[^A-Za-z0-9._-]+", "_", name)
