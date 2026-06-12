from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Document, ExtractedField, FieldCorrection
from app.schemas.document import ExtractedFieldResponse, FieldUpdateRequest

router = APIRouter(tags=["review"])


@router.patch("/extracted-fields/{field_id}", response_model=ExtractedFieldResponse)
def update_extracted_field(
    field_id: str,
    payload: FieldUpdateRequest,
    db: Session = Depends(get_db),
) -> ExtractedField:
    field = db.get(ExtractedField, field_id)
    if field is None:
        raise HTTPException(status_code=404, detail="Extracted field not found.")

    old_value = field.normalized_value
    field.normalized_value = payload.normalized_value
    field.is_reviewed = True
    db.add(
        FieldCorrection(
            document_id=field.document_id,
            field_id=field.id,
            old_value=old_value,
            new_value=payload.normalized_value,
            corrected_by=payload.corrected_by,
        )
    )
    db.commit()
    db.refresh(field)
    return field


@router.post("/documents/{document_id}/review/approve")
def approve_document(document_id: str, db: Session = Depends(get_db)) -> dict:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    fields = list(db.scalars(select(ExtractedField).where(ExtractedField.document_id == document_id)).all())
    if not fields:
        raise HTTPException(status_code=400, detail="Document has no extracted fields to approve.")

    for field in fields:
        field.is_reviewed = True
    document.status = "approved"
    db.commit()
    return {"ok": True, "document_id": document_id, "status": document.status}
