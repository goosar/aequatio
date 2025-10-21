"""Tests for UserRepository with outbox integration.

This module tests the repository layer, focusing on:
- Domain entity to persistence model mapping
- Transactional outbox event publishing
- Database operations (save, retrieve, check existence)
- Error handling and rollback scenarios

Note: The User entity generates its own UUIDs, so the repository's save()
method treats users with UUIDs as updates. To test inserts, we create
users with id=None.
"""

import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.user import User as UserEntity
from app.domain.events.schema import UserRegisteredPayload
from app.persistence.models.user import User as UserModel
from app.persistence.repositories.user_repository import UserRepository


class TestUserRepositorySaveInsert:
    """Test suite for UserRepository.save() with new users (id=None)."""

    def test_save_new_user_without_id_creates_database_record(self):
        """Test saving user with None ID creates new record."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        # Create user with None ID (insert path)
        user = UserEntity(
            id=None,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime(2025, 1, 1, 12, 0, 0),
        )

        # Mock the created model
        created_model = Mock(spec=UserModel)
        created_model.id = uuid4()
        created_model.username = user.username
        created_model.email = user.email
        created_model.hashed_password = user.hashed_password
        created_model.is_active = user.is_active
        created_model.created_at = user.created_at
        created_model.updated_at = None

        # Mock add to simulate model creation
        def mock_add(model):
            model.id = created_model.id

        db.add.side_effect = mock_add

        # Act
        result = repo.save(user)

        # Assert
        db.add.assert_called_once()
        db.flush.assert_called_once()
        assert result.id == created_model.id

    def test_save_raises_error_on_duplicate_username(self):
        """Test that duplicate username raises ValueError."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        user = UserEntity(
            id=None,
            username="existing_user",
            email="new@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )

        # Mock IntegrityError for duplicate username - orig needs to stringify to contain "username"
        orig_mock = Mock()
        orig_mock.__str__ = Mock(return_value="UNIQUE constraint failed: users.username")
        integrity_error = IntegrityError("", "", orig=orig_mock)
        db.flush.side_effect = integrity_error

        # Act & Assert
        with pytest.raises(ValueError, match="Username 'existing_user' already exists"):
            repo.save(user)

        db.rollback.assert_called_once()

    def test_save_raises_error_on_duplicate_email(self):
        """Test that duplicate email raises ValueError."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        user = UserEntity(
            id=None,
            username="new_user",
            email="existing@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )

        # Mock IntegrityError for duplicate email - orig needs to stringify to contain "email"
        orig_mock = Mock()
        orig_mock.__str__ = Mock(return_value="UNIQUE constraint failed: users.email")
        integrity_error = IntegrityError("", "", orig=orig_mock)
        db.flush.side_effect = integrity_error

        # Act & Assert
        with pytest.raises(ValueError, match="Email 'existing@example.com' already registered"):
            repo.save(user)

        db.rollback.assert_called_once()


class TestUserRepositorySaveUpdate:
    """Test suite for UserRepository.save() with existing users (id=UUID)."""

    def test_save_updates_existing_user(self):
        """Test saving existing user updates the record."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()

        user = UserEntity(
            id=user_id,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime(2025, 1, 1, 12, 0, 0),
        )

        # Mock existing user model in database
        existing_model = Mock(spec=UserModel)
        existing_model.id = user_id
        existing_model.username = "old_username"
        existing_model.email = "old@example.com"
        existing_model.hashed_password = "$2b$12$oldpassword"
        existing_model.is_active = True
        existing_model.created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
        existing_model.updated_at = None

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = existing_model
        db.query.return_value = query_mock

        # Act
        repo.save(user)

        # Assert
        db.add.assert_not_called()  # Should not add new
        db.flush.assert_called_once()
        assert existing_model.username == user.username
        assert existing_model.email == user.email

    def test_save_creates_user_when_not_found_in_database(self):
        """Test that user with UUID is created if not found in database."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()

        user = UserEntity(
            id=user_id,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime(2025, 1, 1, 12, 0, 0),
        )

        # Mock user not found in database
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        db.query.return_value = query_mock

        # Act
        repo.save(user)

        # Assert - should create new user (not error)
        db.add.assert_called_once()

    def test_save_updates_timestamp(self):
        """Test that updated_at is preserved when updating."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()
        updated_at = datetime.datetime(2025, 10, 20, 15, 30, 0)

        user = UserEntity(
            id=user_id,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime(2025, 1, 1, 12, 0, 0),
            updated_at=updated_at,
        )

        # Mock existing user
        existing_model = Mock(spec=UserModel)
        existing_model.id = user_id
        existing_model.username = user.username
        existing_model.email = user.email
        existing_model.hashed_password = user.hashed_password
        existing_model.is_active = user.is_active
        existing_model.created_at = user.created_at
        existing_model.updated_at = None

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = existing_model
        db.query.return_value = query_mock

        # Act
        repo.save(user)

        # Assert
        assert existing_model.updated_at == updated_at


class TestUserRepositoryDomainEvents:
    """Test suite for domain event publishing to outbox."""

    def test_save_publishes_domain_events_to_outbox(self):
        """Test that domain events are published when saving."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()

        # Create user with event
        user = UserEntity(
            id=user_id,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime(2025, 1, 1, 12, 0, 0),
        )

        # Add domain event
        user._raise_event(
            UserRegisteredPayload(
                user_id=user_id,
                username=user.username,
                email=user.email,
                metadata={},
            ),
            event_type="user.registered",
        )

        assert user.has_events()

        # Mock existing user
        existing_model = Mock(spec=UserModel)
        existing_model.id = user_id
        existing_model.username = user.username
        existing_model.email = user.email
        existing_model.hashed_password = user.hashed_password
        existing_model.is_active = user.is_active
        existing_model.created_at = user.created_at
        existing_model.updated_at = None

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = existing_model
        db.query.return_value = query_mock

        # Track what's added (should include outbox events)
        db.add.side_effect = lambda item: None

        # Act
        repo.save(user)

        # Assert
        assert db.add.call_count >= 1  # At least one outbox event added
        assert not user.has_events()  # Events cleared after save

    def test_save_clears_events_after_publishing(self):
        """Test that events are cleared after save."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()

        user = UserEntity(
            id=user_id,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime(2025, 1, 1, 12, 0, 0),
        )

        # Add event
        user._raise_event(
            UserRegisteredPayload(
                user_id=user_id,
                username=user.username,
                email=user.email,
                metadata={},
            ),
            event_type="user.registered",
        )

        assert user.has_events()

        # Mock existing user
        existing_model = Mock(spec=UserModel)
        existing_model.id = user_id
        existing_model.username = user.username
        existing_model.email = user.email
        existing_model.hashed_password = user.hashed_password
        existing_model.is_active = user.is_active
        existing_model.created_at = user.created_at
        existing_model.updated_at = None

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = existing_model
        db.query.return_value = query_mock

        # Act
        repo.save(user)

        # Assert
        assert not user.has_events()


class TestUserRepositoryRetrieval:
    """Test suite for UserRepository retrieval methods."""

    def test_get_by_id_returns_user_when_found(self):
        """Test get_by_id returns user entity when found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()

        # Mock database model
        user_model = Mock(spec=UserModel)
        user_model.id = user_id
        user_model.username = "john_doe"
        user_model.email = "john@example.com"
        user_model.hashed_password = "$2b$12$hashedpassword"
        user_model.is_active = True
        user_model.created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
        user_model.updated_at = None

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = user_model
        db.query.return_value = query_mock

        # Act
        result = repo.get_by_id(user_id)

        # Assert
        assert result is not None
        assert result.id == user_id
        assert result.username == "john_doe"

    def test_get_by_id_returns_none_when_not_found(self):
        """Test get_by_id returns None when user not found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        db.query.return_value = query_mock

        # Act
        result = repo.get_by_id(user_id)

        # Assert
        assert result is None

    def test_get_by_username_returns_user_when_found(self):
        """Test get_by_username returns user when found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        user_model = Mock(spec=UserModel)
        user_model.id = uuid4()
        user_model.username = "john_doe"
        user_model.email = "john@example.com"
        user_model.hashed_password = "$2b$12$hashedpassword"
        user_model.is_active = True
        user_model.created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
        user_model.updated_at = None

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = user_model
        db.query.return_value = query_mock

        # Act
        result = repo.get_by_username("john_doe")

        # Assert
        assert result is not None
        assert result.username == "john_doe"

    def test_get_by_username_returns_none_when_not_found(self):
        """Test get_by_username returns None when not found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        db.query.return_value = query_mock

        # Act
        result = repo.get_by_username("nonexistent")

        # Assert
        assert result is None

    def test_get_by_email_returns_user_when_found(self):
        """Test get_by_email returns user when found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        user_model = Mock(spec=Session)
        user_model.id = uuid4()
        user_model.username = "john_doe"
        user_model.email = "john@example.com"
        user_model.hashed_password = "$2b$12$hashedpassword"
        user_model.is_active = True
        user_model.created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
        user_model.updated_at = None

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = user_model
        db.query.return_value = query_mock

        # Act
        result = repo.get_by_email("john@example.com")

        # Assert
        assert result is not None
        assert result.email == "john@example.com"

    def test_get_by_email_returns_none_when_not_found(self):
        """Test get_by_email returns None when not found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        db.query.return_value = query_mock

        # Act
        result = repo.get_by_email("nonexistent@example.com")

        # Assert
        assert result is None


class TestUserRepositoryExistence:
    """Test suite for existence check methods."""

    def test_username_exists_returns_true_when_found(self):
        """Test username_exists returns True when found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = Mock()
        db.query.return_value = query_mock

        # Act
        result = repo.username_exists("john_doe")

        # Assert
        assert result is True

    def test_username_exists_returns_false_when_not_found(self):
        """Test username_exists returns False when not found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        db.query.return_value = query_mock

        # Act
        result = repo.username_exists("nonexistent")

        # Assert
        assert result is False

    def test_email_exists_returns_true_when_found(self):
        """Test email_exists returns True when found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = Mock()
        db.query.return_value = query_mock

        # Act
        result = repo.email_exists("john@example.com")

        # Assert
        assert result is True

    def test_email_exists_returns_false_when_not_found(self):
        """Test email_exists returns False when not found."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        db.query.return_value = query_mock

        # Act
        result = repo.email_exists("nonexistent@example.com")

        # Assert
        assert result is False


class TestUserRepositoryMapping:
    """Test suite for entity-model mapping."""

    def test_to_entity_maps_all_fields_correctly(self):
        """Test _to_entity maps all fields from model to entity."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)
        user_id = uuid4()
        created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
        updated_at = datetime.datetime(2025, 1, 15, 14, 30, 0)

        user_model = Mock(spec=UserModel)
        user_model.id = user_id
        user_model.username = "john_doe"
        user_model.email = "john@example.com"
        user_model.hashed_password = "$2b$12$hashedpassword"
        user_model.is_active = True
        user_model.created_at = created_at
        user_model.updated_at = updated_at

        # Act
        result = repo._to_entity(user_model)

        # Assert
        assert isinstance(result, UserEntity)
        assert result.id == user_id
        assert result.username == "john_doe"
        assert result.email == "john@example.com"
        assert result.is_active is True
        assert result.created_at == created_at
        assert result.updated_at == updated_at

    def test_to_entity_with_inactive_user(self):
        """Test _to_entity correctly maps inactive user."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        user_model = Mock(spec=UserModel)
        user_model.id = uuid4()
        user_model.username = "inactive_user"
        user_model.email = "inactive@example.com"
        user_model.hashed_password = "$2b$12$hashedpassword"
        user_model.is_active = False
        user_model.created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
        user_model.updated_at = datetime.datetime(2025, 1, 15, 14, 30, 0)

        # Act
        result = repo._to_entity(user_model)

        # Assert
        assert result.is_active is False
        assert result.username == "inactive_user"


class TestUserRepositoryTransactions:
    """Test suite for transaction management."""

    def test_save_rolls_back_on_integrity_error(self):
        """Test that save rolls back on integrity error."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        user = UserEntity(
            id=None,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )

        # Mock IntegrityError
        integrity_error = IntegrityError("", "", orig=Mock(args=["constraint"]))
        db.flush.side_effect = integrity_error

        # Act & Assert
        with pytest.raises(ValueError):
            repo.save(user)

        db.rollback.assert_called_once()

    def test_save_does_not_commit_transaction(self):
        """Test that save does not commit."""
        # Arrange
        db = Mock(spec=Session)
        repo = UserRepository(db)

        user = UserEntity(
            id=None,
            username="john_doe",
            email="john@example.com",
            hashed_password="$2b$12$hashedpassword",
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )

        # Mock add to simulate success
        db.add.side_effect = lambda model: setattr(model, "id", uuid4())

        # Act
        repo.save(user)

        # Assert
        db.commit.assert_not_called()

    def test_repository_initialization(self):
        """Test UserRepository initialization."""
        # Arrange
        db = Mock(spec=Session)

        # Act
        repo = UserRepository(db)

        # Assert
        assert repo.db is db
        assert isinstance(repo, UserRepository)
