from __future__ import annotations

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.db.base import Base

log = logging.getLogger("farmsense.db")

def get_database_url() -> str:
    url = settings.database_url.strip()
    if not url:
        return "sqlite:///./farmsense.db"
    # Ensure postgresql+psycopg if using postgres url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = get_database_url()
is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Ensure all tables exist."""
    # Import all models to register them on Base.metadata
    import app.models.orm  # noqa: F401
    Base.metadata.create_all(bind=engine)
    log.info("Database initialized (engine: %s)", DATABASE_URL)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
