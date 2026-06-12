from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        storage_dir=str(tmp_path / "storage"),
        ocr_engine="mock",
    )
    return TestClient(create_app(settings))


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
        files={"file": ("demo-invoice.txt", b"demo content", "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    documents = client.get("/documents")
    assert documents.status_code == 200
    assert len(documents.json()) == 1

    detail = client.get(f"/documents/{document_id}")
    assert detail.status_code == 200
    assert detail.json()["pages"][0]["page_number"] == 1

    ocr_run = client.post(f"/documents/{document_id}/ocr-runs")
    assert ocr_run.status_code == 201
    ocr_run_id = ocr_run.json()["id"]

    blocks = client.get(f"/ocr-runs/{ocr_run_id}/blocks")
    assert blocks.status_code == 200
    assert len(blocks.json()) >= 5

    fields = client.get(f"/documents/{document_id}/fields")
    assert fields.status_code == 200
    field_by_name = {field["field_name"]: field for field in fields.json()}
    assert field_by_name["tax_code"]["normalized_value"] == "0312345678"
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
