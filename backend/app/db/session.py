from collections.abc import Generator

from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.models.base import Base


def build_engine(database_url: str):
    if database_url.startswith("sqlite:///"):
        parsed = urlparse(database_url)
        db_path = Path(parsed.path.lstrip("/"))
        if str(db_path) not in {":memory:", ""}:
            db_path.parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


settings = get_settings()
engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def make_session_factory(app_settings: Settings):
    app_engine = build_engine(app_settings.database_url)
    Base.metadata.create_all(bind=app_engine)
    return sessionmaker(bind=app_engine, autoflush=False, autocommit=False, future=True)
