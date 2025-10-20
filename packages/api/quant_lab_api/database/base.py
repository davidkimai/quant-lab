"""
Database setup with SQLAlchemy ORM.

Supports both SQLite (development) and PostgreSQL (production).
Provides session management and dependency injection for FastAPI.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool

from quant_lab_api.config import settings


# Create engine based on database URL
if settings.is_sqlite:
    # SQLite: Use single connection with check_same_thread=False for FastAPI
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL: Use connection pooling
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    Call this on application startup.
    """
    # Import models to register them with Base
    from quant_lab_api.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
