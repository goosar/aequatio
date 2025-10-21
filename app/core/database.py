from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

# Single source of truth for Base
Base = declarative_base()

# DATABASE_URL is guaranteed to be set by config validation
assert DATABASE_URL is not None, "DATABASE_URL must be configured"
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
