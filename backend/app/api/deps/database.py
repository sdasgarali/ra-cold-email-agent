"""Database session dependency."""
from typing import Generator
from sqlalchemy.orm import Session
from app.db.base import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
