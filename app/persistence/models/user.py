"""User persistence model.

This module defines the SQLAlchemy ORM model for users in the database.
It handles the storage and retrieval of user data including authentication
and audit information.
"""

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    """User database model.

    Represents a user entity in the database with authentication credentials
    and audit timestamps.

    Attributes:
        id: Unique identifier for the user (primary key).
        username: Unique username for login and identification.
        email: Unique email address for communication and recovery.
        hashed_password: Securely hashed password (never store plaintext).
        is_active: Flag indicating if the user account is active.
        created_at: Timestamp of user creation (auto-generated).
        updated_at: Timestamp of last update (auto-updated on modification).

    Example:
        >>> user = User(
        ...     username="john_doe",
        ...     email="john@example.com",
        ...     hashed_password="$2b$12$...",
        ...     is_active=True
        ... )
        >>> session.add(user)
        >>> session.commit()
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"))

    def __repr__(self) -> str:
        """Return string representation of the User instance.

        Returns:
            String representation showing username and active status.
        """
        return f"<User(id={self.id}, username='{self.username}', is_active={self.is_active})>"
