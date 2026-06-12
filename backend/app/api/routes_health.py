from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Document, OcrBlock

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    document_count = db.scalar(select(func.count(Document.id))) or 0
    ocr_block_count = db.scalar(select(func.count(OcrBlock.id))) or 0
    return {
        "ok": True,
        "documents": document_count,
        "ocr_blocks": ocr_block_count,
    }
