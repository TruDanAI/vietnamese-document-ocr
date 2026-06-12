from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentPageResponse(BaseModel):
    id: str
    document_id: str
    page_number: int
    image_path: str | None
    width: int | None
    height: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    storage_path: str
    document_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    pages: list[DocumentPageResponse] = Field(default_factory=list)


class OcrRunResponse(BaseModel):
    id: str
    document_id: str
    engine_name: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}


class OcrBlockResponse(BaseModel):
    id: str
    ocr_run_id: str
    page_id: str
    block_index: int
    text: str
    confidence: float
    bbox: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ExtractedFieldResponse(BaseModel):
    id: str
    document_id: str
    extraction_run_id: str
    field_name: str
    raw_value: str | None
    normalized_value: str | None
    confidence: float
    source_block_ids: list[str]
    is_reviewed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FieldUpdateRequest(BaseModel):
    normalized_value: str | None = None
    corrected_by: str = "reviewer"


class ExportRequest(BaseModel):
    format: str = Field(pattern="^(json|csv)$")


class ExportJobResponse(BaseModel):
    id: str
    document_id: str
    format: str
    status: str
    storage_path: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
