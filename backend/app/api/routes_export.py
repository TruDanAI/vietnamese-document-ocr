from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Document, ExportJob, ExtractedField
from app.schemas.document import ExportJobResponse, ExportRequest
from app.services.export.writers import build_export_content

router = APIRouter(tags=["export"])


@router.post("/documents/{document_id}/exports", response_model=ExportJobResponse, status_code=status.HTTP_201_CREATED)
def create_export(
    document_id: str,
    payload: ExportRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ExportJob:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    fields = list(
        db.scalars(
            select(ExtractedField).where(ExtractedField.document_id == document_id).order_by(ExtractedField.field_name)
        ).all()
    )
    if not fields:
        raise HTTPException(status_code=400, detail="Document has no extracted fields to export.")

    content, extension = build_export_content(document, fields, payload.format)
    filename = f"{document.id}.{extension}"
    if isinstance(content, bytes):
        storage_path = request.app.state.storage.write_export_bytes(filename, content)
    else:
        storage_path = request.app.state.storage.write_export(filename, content)
    job = ExportJob(
        document_id=document.id,
        format=payload.format,
        status="completed",
        storage_path=storage_path,
    )
    document.status = "exported"
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/exports/{export_id}/download")
def download_export(export_id: str, db: Session = Depends(get_db)) -> FileResponse:
    job = db.get(ExportJob, export_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Export not found.")
    path = Path(job.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file is missing.")
    return FileResponse(path=path, filename=path.name)
