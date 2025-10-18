"""User domain entity (Aggregate Root).

This module defines the User as a rich domain model that encapsulates
business logic and emits domain events. It follows DDD principles where
the entity is responsible for maintaining its invariants and publishing
events when state changes occur.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.security import hash_password, validate_password_strength
from app.domain.events.schema import Event, UserRegisteredPayload, make_event


class User(BaseModel):
    """User domain entity (Aggregate Root).

    This is a rich domain model that:
    - Encapsulates business rules and invariants
    - Emits domain events when state changes
    - Validates operations before mutating state
    - Maintains integrity without external services

    Attributes:
        id: Unique user identifier (generated on registration).
        username: Unique username (3-50 chars, alphanumeric + underscore).
        email: Unique email address.
        hashed_password: Securely hashed password.
        is_active: Whether the account is active.
        created_at: Timestamp of account creation.
        updated_at: Timestamp of last update.
        domain_events: List of uncommitted domain events.

    Example:
        >>> # Create new user
        >>> user = User.register(
        ...     username="john_doe",
        ...     email="john@example.com",
        ...     plain_password="SecurePass123!",
        ...     metadata={"ip": "192.168.1.1"}
        ... )
        >>> user.id  # UUID generated
        >>> len(user.domain_events)  # 1 event (UserRegistered)
        1
        >>> user.clear_events()  # After persisting
    """

    # Identity
    id: Optional[UUID] = None
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr

    # Security
    hashed_password: str
    is_active: bool = True

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Event sourcing
    domain_events: List[Event] = Field(default_factory=list, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "hashed_password": "$2b$12$...",
                "is_active": True,
                "created_at": "2025-10-18T10:30:00Z",
            }
        },
    }

    # =========================================================================
    # FACTORY METHODS (Static)
    # =========================================================================

    @staticmethod
    def register(
        username: str, email: str, plain_password: str, metadata: Optional[dict] = None
    ) -> "User":
        """Factory method to register a new user (Aggregate Root).

        This method:
        1. Validates business rules (password strength, reserved usernames)
        2. Hashes the password securely
        3. Creates the user entity
        4. Emits UserRegisteredPayload domain event

        Args:
            username: Desired username (3-50 chars, alphanumeric + underscore).
            email: User's email address.
            plain_password: Plaintext password (will be hashed).
            metadata: Optional metadata for the event (IP, user agent, etc.).

        Returns:
            New User instance with pending domain event.

        Raises:
            ValueError: If validation fails (weak password, reserved username).

        Example:
            >>> user = User.register(
            ...     "john_doe",
            ...     "john@example.com",
            ...     "SecurePass123!",
            ...     {"ip": "192.168.1.1"}
            ... )
            >>> user.has_events()
            True
        """
        # Business Rule 1: Reserved usernames
        reserved = {"admin", "root", "system", "api", "administrator", "mod", "moderator"}
        if username.lower() in reserved:
            raise ValueError(f"Username '{username}' is reserved")

        # Business Rule 2: Password strength
        is_valid, error_msg = validate_password_strength(plain_password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {error_msg}")

        # Hash password
        hashed_password = hash_password(plain_password)

        # Create entity
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow(),
        )

        # Emit domain event (will be committed to outbox after persistence)
        user._raise_event(
            UserRegisteredPayload(
                user_id=user.id or 0,  # Will be updated after DB insert
                username=user.username,
                email=user.email,
                metadata=metadata or {},
            ),
            event_type="user.registered",
        )

        return user

    # =========================================================================
    # COMMAND METHODS (State Mutations)
    # =========================================================================

    def deactivate(self, reason: Optional[str] = None) -> None:
        """Deactivate the user account.

        Args:
            reason: Optional reason for deactivation (for auditing).

        Raises:
            ValueError: If user is already inactive.

        Example:
            >>> user.deactivate("Policy violation")
            >>> user.is_active
            False
        """
        if not self.is_active:
            raise ValueError(f"User '{self.username}' is already inactive")

        self.is_active = False
        self.updated_at = datetime.utcnow()

        # Future: emit UserDeactivatedPayload event
        # self._raise_event(UserDeactivatedPayload(...), "user.deactivated")

    def activate(self) -> None:
        """Reactivate the user account.

        Raises:
            ValueError: If user is already active.
        """
        if self.is_active:
            raise ValueError(f"User '{self.username}' is already active")

        self.is_active = True
        self.updated_at = datetime.utcnow()

    def change_email(self, new_email: str) -> None:
        """Change user's email address.

        Args:
            new_email: New email address.

        Raises:
            ValueError: If email is the same as current.

        Example:
            >>> user.change_email("newemail@example.com")
            >>> user.email
            'newemail@example.com'
        """
        if self.email == new_email:
            raise ValueError("New email is the same as current email")

        # Store old email for future event emission
        # old_email = self.email
        self.email = new_email
        self.updated_at = datetime.utcnow()

        # Future: emit UserEmailChangedPayload event
        # self._raise_event(
        #     UserEmailChangedPayload(user_id=self.id, old_email=old_email, new_email=new_email),
        #     "user.email_changed"
        # )

    # =========================================================================
    # EVENT MANAGEMENT
    # =========================================================================

    def _raise_event(self, payload: BaseModel, event_type: str) -> None:
        """Internal method to raise a domain event.

        Args:
            payload: Event payload (Pydantic model).
            event_type: Event type identifier.
        """
        event = make_event(payload, event_type)
        self.domain_events.append(event)

    def update_event_user_id(self, user_id: UUID) -> None:
        """Update user_id in pending events after database insert.

        This is called by the repository after getting the auto-generated ID.

        Args:
            user_id: Database-generated user ID (UUID).
        """
        self.id = user_id
        for event in self.domain_events:
            if hasattr(event.payload, "user_id"):
                # Update payload immutably
                updated_payload = event.payload.model_copy(update={"user_id": user_id})
                # Replace event with updated version
                event.payload = updated_payload

    def has_events(self) -> bool:
        """Check if there are uncommitted domain events.

        Returns:
            True if events exist, False otherwise.
        """
        return len(self.domain_events) > 0

    def get_events(self) -> List[Event]:
        """Get all uncommitted domain events.

        Returns:
            List of domain events.
        """
        return self.domain_events.copy()

    def clear_events(self) -> None:
        """Clear all domain events (called after persisting to outbox).

        Example:
            >>> user = User.register(...)
            >>> repository.save(user)  # Persists events to outbox
            >>> user.clear_events()    # Clear after commit
        """
        self.domain_events.clear()

    # =========================================================================
    # QUERY METHODS (No State Mutation)
    # =========================================================================

    def can_login(self) -> bool:
        """Check if user can log in.

        Returns:
            True if user is active, False otherwise.
        """
        return self.is_active

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(id={self.id}, username='{self.username}', active={self.is_active})>"
