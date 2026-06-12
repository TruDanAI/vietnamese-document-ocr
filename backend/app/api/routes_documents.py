from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models import Document, DocumentPage, ExtractedField, ExtractionRun
from app.schemas.document import DocumentDetailResponse, DocumentResponse, ExtractedFieldResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = "business_document",
    db: Session = Depends(get_db),
) -> Document:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    storage_path = request.app.state.storage.save_upload(file.filename or "document.bin", content)
    document = Document(
        filename=storage_path.split("\\")[-1].split("/")[-1],
        original_filename=file.filename or "document.bin",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        storage_path=storage_path,
        document_type=document_type,
        status="uploaded",
    )
    db.add(document)
    db.flush()
    db.add(
        DocumentPage(
            document_id=document.id,
            page_number=1,
            image_path=storage_path,
        )
    )
    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())).all())


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)) -> Document:
    document = db.scalar(
        select(Document).options(selectinload(Document.pages)).where(Document.id == document_id)
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.get("/{document_id}/fields", response_model=list[ExtractedFieldResponse])
def get_document_fields(document_id: str, db: Session = Depends(get_db)) -> list[ExtractedField]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    latest_run = db.scalar(
        select(ExtractionRun)
        .where(ExtractionRun.document_id == document_id)
        .order_by(ExtractionRun.started_at.desc())
        .limit(1)
    )
    if latest_run is None:
        return []

    return list(
        db.scalars(
            select(ExtractedField)
            .where(ExtractedField.extraction_run_id == latest_run.id)
            .order_by(ExtractedField.field_name.asc())
        ).all()
    )
