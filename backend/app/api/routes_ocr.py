from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db
from app.models import Document, ExtractedField, ExtractionRun, OcrBlock, OcrRun
from app.schemas.document import OcrBlockResponse, OcrRunResponse
from app.services.extraction.rules import extract_fields
from app.services.ocr.factory import build_ocr_adapter

router = APIRouter(tags=["ocr"])


@router.post("/documents/{document_id}/ocr-runs", response_model=OcrRunResponse, status_code=status.HTTP_201_CREATED)
def run_ocr(document_id: str, request: Request, db: Session = Depends(get_db)) -> OcrRun:
    document = db.scalar(
        select(Document).options(selectinload(Document.pages)).where(Document.id == document_id)
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not document.pages:
        raise HTTPException(status_code=400, detail="Document has no page records.")

    settings = request.app.state.settings
    adapter = build_ocr_adapter(settings.ocr_engine)
    ocr_run = OcrRun(document_id=document.id, engine_name=adapter.engine_name, status="running")
    db.add(ocr_run)
    db.flush()

    try:
        block_index = 0
        for page in document.pages:
            page_path = page.image_path or document.storage_path
            for result in adapter.run_page(page_path, page.page_number):
                db.add(
                    OcrBlock(
                        ocr_run_id=ocr_run.id,
                        page_id=page.id,
                        block_index=block_index,
                        text=result.text,
                        confidence=result.confidence,
                        bbox=result.bbox,
                    )
                )
                block_index += 1
        db.flush()

        blocks = list(
            db.scalars(select(OcrBlock).where(OcrBlock.ocr_run_id == ocr_run.id).order_by(OcrBlock.block_index.asc()))
        )
        extraction_run = ExtractionRun(
            document_id=document.id,
            ocr_run_id=ocr_run.id,
            status="completed",
            finished_at=datetime.now(UTC),
        )
        db.add(extraction_run)
        db.flush()
        for field in extract_fields(blocks):
            db.add(
                ExtractedField(
                    document_id=document.id,
                    extraction_run_id=extraction_run.id,
                    field_name=field.field_name,
                    raw_value=field.raw_value,
                    normalized_value=field.normalized_value,
                    confidence=field.confidence,
                    source_block_ids=field.source_block_ids,
                )
            )

        ocr_run.status = "completed"
        ocr_run.finished_at = datetime.now(UTC)
        document.status = "extracted"
        db.commit()
        db.refresh(ocr_run)
        return ocr_run
    except Exception as exc:
        ocr_run.status = "failed"
        ocr_run.error_message = str(exc)
        ocr_run.finished_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(status_code=500, detail=f"OCR run failed: {exc}") from exc


@router.get("/ocr-runs/{ocr_run_id}/blocks", response_model=list[OcrBlockResponse])
def get_ocr_blocks(ocr_run_id: str, db: Session = Depends(get_db)) -> list[OcrBlock]:
    ocr_run = db.get(OcrRun, ocr_run_id)
    if ocr_run is None:
        raise HTTPException(status_code=404, detail="OCR run not found.")
    return list(
        db.scalars(
            select(OcrBlock)
            .options(joinedload(OcrBlock.page))
            .where(OcrBlock.ocr_run_id == ocr_run_id)
            .order_by(OcrBlock.block_index.asc())
        ).all()
    )
