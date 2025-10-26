"""Shared pytest fixtures for all tests."""

from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.persistence.models.expense import SQLAlchemyExpense  # noqa: F401
from app.persistence.models.outbox import OutboxEvent  # noqa: F401
from app.persistence.models.user import User as UserModel  # noqa: F401


@pytest.fixture(scope="function")
def engine():
    """Create a test database engine with tables.

    Uses a shared in-memory SQLite database with pooling disabled
    to ensure all connections use the same database instance.
    """
    # Create in-memory SQLite database with:
    # - check_same_thread=False: Allow TestClient to use across threads
    # - poolclass=StaticPool: Share the same connection across all uses
    # - connect_args: Configure SQLite behavior
    from sqlalchemy.pool import StaticPool

    test_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Critical: ensures single shared connection
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Cleanup
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test.

    This fixture:
    - Uses the engine fixture which has tables already created
    - Yields a database session
    - Rolls back after the test

    Scope: function (new session for each test)
    """
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create session
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
