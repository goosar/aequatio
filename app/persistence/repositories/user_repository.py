"""User repository with domain event support.

This repository follows the Repository pattern and automatically
publishes domain events to the transactional outbox when saving aggregates.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.user import User as UserEntity
from app.outbox.repository import add_outbox_event
from app.persistence.models.user import User as UserModel


class UserRepository:
    """Repository for User aggregate root.

    Responsibilities:
    - Map between domain entity (User) and persistence model (UserModel)
    - Save aggregates and publish their domain events to outbox
    - Ensure transactional consistency (entity + events in same transaction)
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def save(self, user: UserEntity) -> UserEntity:
        """Save user aggregate and publish domain events.

        This method:
        1. Maps domain entity to persistence model
        2. Inserts/updates in database
        3. Publishes all domain events to transactional outbox
        4. Clears events from aggregate
        5. Returns updated entity with database ID

        Args:
            user: User domain entity (aggregate root).

        Returns:
            Updated user entity with database ID.

        Raises:
            ValueError: If username or email already exists.

        Example:
            >>> user = User.register("john", "john@example.com", "Pass123!")
            >>> saved_user = repo.save(user)
            >>> saved_user.id  # Now populated
            123
            >>> saved_user.has_events()  # Events cleared after save
            False
        """
        try:
            # Map domain entity → persistence model
            if user.id:
                # Update existing
                user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
                if not user_model:
                    raise ValueError(f"User with id {user.id} not found")

                user_model.username = user.username
                user_model.email = user.email
                user_model.hashed_password = user.hashed_password
                user_model.is_active = user.is_active
                user_model.updated_at = user.updated_at
            else:
                # Create new
                user_model = UserModel(
                    username=user.username,
                    email=user.email,
                    hashed_password=user.hashed_password,
                    is_active=user.is_active,
                    created_at=user.created_at,
                )
                self.db.add(user_model)

            # Flush to get ID (but don't commit yet)
            self.db.flush()

            # Update entity with database ID
            if not user.id:
                user.update_event_user_id(user_model.id)

            # Publish domain events to outbox (transactional)
            for event in user.get_events():
                add_outbox_event(
                    db=self.db,
                    event_type=event.metadata.event_type,
                    payload=event.model_dump(mode="json"),
                    aggregate_type="User",
                    aggregate_id=str(user_model.id),
                )

            # Clear events from aggregate
            user.clear_events()

            # Map back to domain entity
            return self._to_entity(user_model)

        except IntegrityError as e:
            self.db.rollback()
            if "username" in str(e.orig):
                raise ValueError(f"Username '{user.username}' already exists") from e
            elif "email" in str(e.orig):
                raise ValueError(f"Email '{user.email}' already registered") from e
            raise ValueError("User save failed due to constraint violation") from e

    def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        """Find user by ID.

        Args:
            user_id: User UUID to search for.

        Returns:
            User domain entity if found, None otherwise.
        """
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(user_model) if user_model else None

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Find user by username.

        Args:
            username: Username to search for.

        Returns:
            User domain entity if found, None otherwise.
        """
        user_model = self.db.query(UserModel).filter(UserModel.username == username).first()
        return self._to_entity(user_model) if user_model else None

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Find user by email.

        Args:
            email: Email to search for.

        Returns:
            User domain entity if found, None otherwise.
        """
        user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(user_model) if user_model else None

    def username_exists(self, username: str) -> bool:
        """Check if username exists.

        Args:
            username: Username to check.

        Returns:
            True if exists, False otherwise.
        """
        return (
            self.db.query(UserModel.id).filter(UserModel.username == username).first() is not None
        )

    def email_exists(self, email: str) -> bool:
        """Check if email exists.

        Args:
            email: Email to check.

        Returns:
            True if exists, False otherwise.
        """
        return self.db.query(UserModel.id).filter(UserModel.email == email).first() is not None

    # =========================================================================
    # MAPPING (Private)
    # =========================================================================

    def _to_entity(self, model: UserModel) -> UserEntity:
        """Map persistence model to domain entity.

        Args:
            model: SQLAlchemy UserModel instance.

        Returns:
            User domain entity.
        """
        return UserEntity(
            id=model.id,
            username=model.username,
            email=model.email,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
