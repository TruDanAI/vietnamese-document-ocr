from pathlib import Path
from io import BytesIO

import fitz
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        storage_dir=str(tmp_path / "storage"),
        ocr_engine="mock",
    )
    return TestClient(create_app(settings))


def demo_png_bytes() -> bytes:
    output = BytesIO()
    image = Image.new("RGB", (900, 500), color="white")
    image.save(output, format="PNG")
    return output.getvalue()


def demo_pdf_bytes() -> bytes:
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    page.insert_text((72, 72), "CONG TY TNHH MINH AN\nMST: 0000000000")
    content = pdf.tobytes()
    pdf.close()
    return content


def test_health_starts_empty(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["documents"] == 0


def test_upload_ocr_review_approve_export_workflow(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    upload = client.post(
        "/documents/upload",
        files={"file": ("demo-invoice.png", demo_png_bytes(), "image/png")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    documents = client.get("/documents")
    assert documents.status_code == 200
    assert len(documents.json()) == 1

    detail = client.get(f"/documents/{document_id}")
    assert detail.status_code == 200
    page = detail.json()["pages"][0]
    assert page["page_number"] == 1
    assert page["width"] == 900

    page_image = client.get(f"/documents/pages/{page['id']}/image")
    assert page_image.status_code == 200
    assert page_image.headers["content-type"] == "image/png"

    ocr_run = client.post(f"/documents/{document_id}/ocr-runs")
    assert ocr_run.status_code == 201
    ocr_run_id = ocr_run.json()["id"]

    blocks = client.get(f"/ocr-runs/{ocr_run_id}/blocks")
    assert blocks.status_code == 200
    assert len(blocks.json()) >= 5
    assert blocks.json()[0]["page_number"] == 1

    latest_blocks = client.get(f"/documents/{document_id}/ocr-blocks")
    assert latest_blocks.status_code == 200
    assert len(latest_blocks.json()) == len(blocks.json())

    fields = client.get(f"/documents/{document_id}/fields")
    assert fields.status_code == 200
    field_by_name = {field["field_name"]: field for field in fields.json()}
    assert field_by_name["tax_code"]["normalized_value"] == "0000000000"
    assert field_by_name["total_amount"]["normalized_value"] == "1100000"

    supplier_id = field_by_name["supplier_name"]["id"]
    update = client.patch(
        f"/extracted-fields/{supplier_id}",
        json={"normalized_value": "CONG TY TNHH MINH AN - REVIEWED", "corrected_by": "tester"},
    )
    assert update.status_code == 200
    assert update.json()["is_reviewed"] is True
    assert update.json()["normalized_value"].endswith("REVIEWED")

    approve = client.post(f"/documents/{document_id}/review/approve")
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    json_export = client.post(f"/documents/{document_id}/exports", json={"format": "json"})
    assert json_export.status_code == 201
    assert Path(json_export.json()["storage_path"]).exists()

    csv_export = client.post(f"/documents/{document_id}/exports", json={"format": "csv"})
    assert csv_export.status_code == 201
    assert Path(csv_export.json()["storage_path"]).exists()

    xlsx_export = client.post(f"/documents/{document_id}/exports", json={"format": "xlsx"})
    assert xlsx_export.status_code == 201
    assert Path(xlsx_export.json()["storage_path"]).exists()


def test_pdf_upload_creates_rendered_page_image(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    upload = client.post(
        "/documents/upload",
        files={"file": ("demo-invoice.pdf", demo_pdf_bytes(), "application/pdf")},
    )

    assert upload.status_code == 201
    document_id = upload.json()["id"]
    detail = client.get(f"/documents/{document_id}")
    assert detail.status_code == 200
    page = detail.json()["pages"][0]
    assert page["page_number"] == 1
    assert page["width"] > 0
    assert page["height"] > 0


def test_unsupported_upload_returns_clear_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    upload = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"plain text is not a page image", "text/plain")},
    )

    assert upload.status_code == 400
    assert "Unsupported file type" in upload.json()["detail"]
