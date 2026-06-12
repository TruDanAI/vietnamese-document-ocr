from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/reports")
def list_evaluation_reports(request: Request) -> list[dict]:
    report_dir = request.app.state.storage.eval_reports_dir
    reports = []
    for path in sorted(report_dir.glob("eval-*.*"), key=lambda item: item.stat().st_mtime, reverse=True):
        reports.append(
            {
                "filename": path.name,
                "format": path.suffix.lstrip("."),
                "size_bytes": path.stat().st_size,
                "modified_at": path.stat().st_mtime,
            }
        )
    return reports


@router.get("/reports/{filename}")
def download_evaluation_report(filename: str, request: Request) -> FileResponse:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid report filename.")
    path = request.app.state.storage.eval_reports_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Evaluation report not found.")
    media_type = "application/json" if Path(filename).suffix == ".json" else "text/markdown"
    return FileResponse(path=path, filename=filename, media_type=media_type)
