from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_documents import router as documents_router
from app.api.routes_evaluation import router as evaluation_router
from app.api.routes_export import router as export_router
from app.api.routes_health import router as health_router
from app.api.routes_ocr import router as ocr_router
from app.api.routes_review import router as review_router
from app.config import Settings, get_settings
from app.db import session as db_session
from app.services.storage.local import LocalStorageService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    session_factory = db_session.make_session_factory(settings)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Vietnamese business document OCR, human review, and export MVP.",
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.storage = LocalStorageService(settings.storage_path)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(ocr_router)
    app.include_router(review_router)
    app.include_router(export_router)
    app.include_router(evaluation_router)
    return app


app = create_app()
