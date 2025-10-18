"""Application services for user operations.

Application services orchestrate use cases by coordinating domain entities,
repositories, and other services. They sit between the API layer and domain layer,
providing a clean boundary that hides infrastructure concerns.

Key differences:
- Domain Services = Business logic that doesn't belong to a single entity
- Application Services = Use case orchestration (transaction boundaries, calling repos)
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.persistence.repositories.user_repository import UserRepository


class UserApplicationService:
    """Application service for user-related use cases.

    This service encapsulates the complete use case workflow, hiding
    infrastructure details (database, transactions) from the API layer.

    Benefits:
    - API layer doesn't know about database sessions
    - Transaction boundaries are clear (one service call = one transaction)
    - Easy to test (can mock the service)
    - Can add cross-cutting concerns (logging, monitoring, caching)
    """

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.user_repo = UserRepository(db)

    def register_user(
        self, username: str, email: str, password: str, metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """Register a new user (use case).

        This method encapsulates the complete user registration workflow:
        1. Validate business rules (domain entity)
        2. Create user aggregate
        3. Persist to database with events
        4. Commit transaction

        Args:
            username: Desired username.
            email: User's email address.
            password: Plaintext password (will be hashed).
            metadata: Optional metadata for event (IP, user agent, etc.).

        Returns:
            Registered User entity with database ID.

        Raises:
            ValueError: If registration fails (weak password, duplicate, etc.).

        Example:
            >>> service = UserApplicationService(db)
            >>> user = service.register_user(
            ...     username="john_doe",
            ...     email="john@example.com",
            ...     password="SecurePass123!",
            ...     metadata={"ip": "192.168.1.1"}
            ... )
            >>> user.id
            123
        """
        try:
            # 1. Create user aggregate (domain validates business rules)
            user = User.register(
                username=username, email=email, plain_password=password, metadata=metadata or {}
            )

            # 2. Persist to database (repository handles constraints)
            saved_user = self.user_repo.save(user)

            # 3. Commit transaction atomically
            self.db.commit()

            return saved_user

        except Exception:
            # Rollback on any error
            self.db.rollback()
            raise

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID.

        Args:
            user_id: User identifier.

        Returns:
            User entity if found, None otherwise.
        """
        return self.user_repo.get_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username.

        Args:
            username: Username to search for.

        Returns:
            User entity if found, None otherwise.
        """
        return self.user_repo.get_by_username(username)

    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account (use case).

        Args:
            user_id: ID of user to deactivate.

        Returns:
            Updated user entity.

        Raises:
            ValueError: If user not found or already inactive.
        """
        try:
            # Load user aggregate
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")

            # Execute domain operation
            user.deactivate()

            # Persist changes
            saved_user = self.user_repo.save(user)
            self.db.commit()

            return saved_user

        except Exception:
            self.db.rollback()
            raise
