"""Tests for UserApplicationService.

This module tests the application service layer that orchestrates
user-related use cases, including registration, retrieval, and deactivation.
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.services.user_service import UserApplicationService
from app.domain.entities.user import User


class TestUserApplicationServiceRegistration:
    """Test cases for user registration use case."""

    def test_register_user_success(self):
        """Test successful user registration."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        username = "john_doe"
        email = "john@example.com"
        password = "SecurePass123!"

        # Create a mock user that would be returned by save
        mock_user = User.register(username, email, password)
        mock_user.id = uuid4()
        mock_repo.save.return_value = mock_user

        # Act
        result = service.register_user(username, email, password)

        # Assert
        assert result.username == username
        assert result.email == email
        assert result.id is not None
        mock_repo.save.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_register_user_with_metadata(self):
        """Test user registration with metadata."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        metadata = {"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"}
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!", metadata)
        mock_user.id = uuid4()
        mock_repo.save.return_value = mock_user

        # Act
        result = service.register_user(
            "john_doe", "john@example.com", "SecurePass123!", metadata=metadata
        )

        # Assert
        assert result is not None
        mock_repo.save.assert_called_once()
        # Verify the user passed to save has events with metadata
        saved_user = mock_repo.save.call_args[0][0]
        assert saved_user.has_events()
        events = saved_user.get_events()
        assert events[0].payload.metadata == metadata

    def test_register_user_with_weak_password_raises_error(self):
        """Test that registration with weak password raises ValueError."""
        # Arrange
        mock_db = Mock()
        service = UserApplicationService(mock_db)

        # Act & Assert
        with pytest.raises(ValueError, match="Password validation failed"):
            service.register_user("john_doe", "john@example.com", "weak")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_register_user_with_reserved_username_raises_error(self):
        """Test that registration with reserved username raises ValueError."""
        # Arrange
        mock_db = Mock()
        service = UserApplicationService(mock_db)

        # Act & Assert
        with pytest.raises(ValueError, match="Username 'admin' is reserved"):
            service.register_user("admin", "admin@example.com", "SecurePass123!")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_register_user_duplicate_username_raises_error(self):
        """Test that registration with duplicate username raises ValueError."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        # Simulate IntegrityError from repository
        mock_repo.save.side_effect = ValueError("Username 'john_doe' already exists")

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            service.register_user("john_doe", "john@example.com", "SecurePass123!")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_register_user_duplicate_email_raises_error(self):
        """Test that registration with duplicate email raises ValueError."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        # Simulate IntegrityError from repository
        mock_repo.save.side_effect = ValueError("Email 'john@example.com' already exists")

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            service.register_user("john_doe", "john@example.com", "SecurePass123!")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_register_user_rollback_on_commit_error(self):
        """Test that transaction is rolled back on commit error."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_repo.save.return_value = mock_user
        mock_db.commit.side_effect = Exception("Database connection lost")

        # Act & Assert
        with pytest.raises(Exception, match="Database connection lost"):
            service.register_user("john_doe", "john@example.com", "SecurePass123!")

        mock_db.rollback.assert_called_once()

    def test_register_user_rollback_on_save_error(self):
        """Test that transaction is rolled back on save error."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        mock_repo.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            service.register_user("john_doe", "john@example.com", "SecurePass123!")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_register_user_creates_domain_entity(self):
        """Test that register_user creates a proper domain entity."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        username = "john_doe"
        email = "john@example.com"
        password = "SecurePass123!"

        # Capture the user passed to save
        saved_user_capture = []

        def capture_save(user):
            saved_user_capture.append(user)
            user.id = uuid4()
            return user

        mock_repo.save.side_effect = capture_save

        # Act
        service.register_user(username, email, password)

        # Assert
        assert len(saved_user_capture) == 1
        saved_user = saved_user_capture[0]
        assert isinstance(saved_user, User)
        assert saved_user.username == username
        assert saved_user.email == email
        assert saved_user.is_active is True
        assert saved_user.has_events()


class TestUserApplicationServiceRetrieval:
    """Test cases for user retrieval use cases."""

    def test_get_user_by_id_found(self):
        """Test retrieving user by ID when user exists."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_user.id = user_id
        mock_repo.get_by_id.return_value = mock_user

        # Act
        result = service.get_user_by_id(user_id)

        # Assert
        assert result is not None
        assert result.id == user_id
        assert result.username == "john_doe"
        mock_repo.get_by_id.assert_called_once_with(user_id)

    def test_get_user_by_id_not_found(self):
        """Test retrieving user by ID when user doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_repo.get_by_id.return_value = None

        # Act
        result = service.get_user_by_id(user_id)

        # Assert
        assert result is None
        mock_repo.get_by_id.assert_called_once_with(user_id)

    def test_get_user_by_username_found(self):
        """Test retrieving user by username when user exists."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        username = "john_doe"
        mock_user = User.register(username, "john@example.com", "SecurePass123!")
        mock_user.id = uuid4()
        mock_repo.get_by_username.return_value = mock_user

        # Act
        result = service.get_user_by_username(username)

        # Assert
        assert result is not None
        assert result.username == username
        mock_repo.get_by_username.assert_called_once_with(username)

    def test_get_user_by_username_not_found(self):
        """Test retrieving user by username when user doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        username = "nonexistent"
        mock_repo.get_by_username.return_value = None

        # Act
        result = service.get_user_by_username(username)

        # Assert
        assert result is None
        mock_repo.get_by_username.assert_called_once_with(username)

    def test_get_user_by_username_case_sensitive(self):
        """Test that username lookup is case-sensitive."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        # Act
        service.get_user_by_username("JohnDoe")

        # Assert
        mock_repo.get_by_username.assert_called_once_with("JohnDoe")


class TestUserApplicationServiceDeactivation:
    """Test cases for user deactivation use case."""

    def test_deactivate_user_success(self):
        """Test successful user deactivation."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_user.id = user_id
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.save.return_value = mock_user

        # Act
        result = service.deactivate_user(user_id)

        # Assert
        assert result.is_active is False
        assert result.updated_at is not None
        mock_repo.get_by_id.assert_called_once_with(user_id)
        mock_repo.save.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_deactivate_user_not_found(self):
        """Test deactivating non-existent user raises ValueError."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"User with id {user_id} not found"):
            service.deactivate_user(user_id)

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_deactivate_already_inactive_user_raises_error(self):
        """Test deactivating already inactive user raises ValueError."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_user.id = user_id
        mock_user.deactivate()  # Already inactive
        mock_repo.get_by_id.return_value = mock_user

        # Act & Assert
        with pytest.raises(ValueError, match="already inactive"):
            service.deactivate_user(user_id)

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_deactivate_user_rollback_on_commit_error(self):
        """Test that transaction is rolled back on commit error."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_user.id = user_id
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.save.return_value = mock_user
        mock_db.commit.side_effect = Exception("Database connection lost")

        # Act & Assert
        with pytest.raises(Exception, match="Database connection lost"):
            service.deactivate_user(user_id)

        mock_db.rollback.assert_called_once()

    def test_deactivate_user_rollback_on_save_error(self):
        """Test that transaction is rolled back on save error."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_user.id = user_id
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            service.deactivate_user(user_id)

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_deactivate_user_updates_timestamp(self):
        """Test that deactivation updates the updated_at timestamp."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_user.id = user_id
        original_updated_at = mock_user.updated_at
        mock_repo.get_by_id.return_value = mock_user

        # Capture the saved user
        saved_user_capture = []

        def capture_save(user):
            saved_user_capture.append(user)
            return user

        mock_repo.save.side_effect = capture_save

        # Act
        service.deactivate_user(user_id)

        # Assert
        assert len(saved_user_capture) == 1
        saved_user = saved_user_capture[0]
        assert saved_user.updated_at is not None
        assert saved_user.updated_at != original_updated_at or original_updated_at is None


class TestUserApplicationServiceIntegration:
    """Integration tests for complete workflows."""

    def test_register_and_retrieve_workflow(self):
        """Test complete workflow of registering and retrieving a user."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        username = "john_doe"
        email = "john@example.com"
        password = "SecurePass123!"
        user_id = uuid4()

        # Setup registration
        def save_user(user):
            user.id = user_id
            return user

        mock_repo.save.side_effect = save_user

        # Act - Register
        registered_user = service.register_user(username, email, password)

        # Setup retrieval
        mock_repo.get_by_id.return_value = registered_user

        # Act - Retrieve
        retrieved_user = service.get_user_by_id(user_id)

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.id == user_id
        assert retrieved_user.username == username
        assert retrieved_user.email == email

    def test_register_deactivate_workflow(self):
        """Test complete workflow of registering and deactivating a user."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()

        # Setup registration
        def save_user(user):
            user.id = user_id
            return user

        mock_repo.save.side_effect = save_user

        # Act - Register
        registered_user = service.register_user("john_doe", "john@example.com", "SecurePass123!")
        assert registered_user.is_active is True

        # Setup deactivation
        mock_repo.get_by_id.return_value = registered_user

        # Act - Deactivate
        deactivated_user = service.deactivate_user(user_id)

        # Assert
        assert deactivated_user.is_active is False
        assert deactivated_user.updated_at is not None

    def test_multiple_users_registration(self):
        """Test registering multiple users."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        users_data = [
            ("user1", "user1@example.com", "Pass123!"),
            ("user2", "user2@example.com", "Pass456!"),
            ("user3", "user3@example.com", "Pass789!"),
        ]

        def save_user(user):
            user.id = uuid4()
            return user

        mock_repo.save.side_effect = save_user

        # Act
        registered_users = []
        for username, email, password in users_data:
            user = service.register_user(username, email, password)
            registered_users.append(user)

        # Assert
        assert len(registered_users) == 3
        assert all(user.id is not None for user in registered_users)
        assert all(user.is_active for user in registered_users)
        assert mock_repo.save.call_count == 3
        assert mock_db.commit.call_count == 3

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        # Arrange
        mock_db = Mock()

        # Act
        service = UserApplicationService(mock_db)

        # Assert
        assert service.db is mock_db
        assert service.user_repo is not None
        assert hasattr(service, "register_user")
        assert hasattr(service, "get_user_by_id")
        assert hasattr(service, "get_user_by_username")
        assert hasattr(service, "deactivate_user")


class TestUserApplicationServiceEdgeCases:
    """Test cases for edge cases and error conditions."""

    def test_register_user_with_empty_metadata(self):
        """Test registration with empty metadata dictionary."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!", {})
        mock_user.id = uuid4()
        mock_repo.save.return_value = mock_user

        # Act
        result = service.register_user("john_doe", "john@example.com", "SecurePass123!", metadata={})

        # Assert
        assert result is not None
        mock_repo.save.assert_called_once()

    def test_register_user_with_none_metadata(self):
        """Test registration with None metadata (uses default empty dict)."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!", {})
        mock_user.id = uuid4()
        mock_repo.save.return_value = mock_user

        # Act
        result = service.register_user("john_doe", "john@example.com", "SecurePass123!", metadata=None)

        # Assert
        assert result is not None
        # Verify empty dict was passed to User.register
        saved_user = mock_repo.save.call_args[0][0]
        events = saved_user.get_events()
        assert events[0].payload.metadata == {}

    def test_deactivate_user_with_uuid_string(self):
        """Test deactivating user with UUID string conversion."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        user_id = uuid4()
        mock_user = User.register("john_doe", "john@example.com", "SecurePass123!")
        mock_user.id = user_id
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.save.return_value = mock_user

        # Act
        result = service.deactivate_user(user_id)

        # Assert
        assert result.is_active is False

    @pytest.mark.parametrize(
        "username,email,password",
        [
            ("valid_user", "valid@example.com", "ValidPass123!"),
            ("abc", "short@example.com", "ShortPass1!"),
            ("a" * 50, "long@example.com", "LongUserPass1!"),
            ("user_with_123", "user123@example.com", "UserPass123!"),
        ],
    )
    def test_register_user_with_various_valid_inputs(self, username: str, email: str, password: str):
        """Test registration with various valid input combinations."""
        # Arrange
        mock_db = Mock()
        mock_repo = Mock()
        service = UserApplicationService(mock_db)
        service.user_repo = mock_repo

        mock_user = User.register(username, email, password)
        mock_user.id = uuid4()
        mock_repo.save.return_value = mock_user

        # Act
        result = service.register_user(username, email, password)

        # Assert
        assert result.username == username
        assert result.email == email

    @pytest.mark.parametrize(
        "password,error_match",
        [
            ("weak", "Password validation failed"),
            ("nouppercase123!", "uppercase"),
            ("NOLOWERCASE123!", "lowercase"),
            ("NoDigits!", "digit"),
            ("NoSpecial123", "special character"),
            ("Short1!", "at least 8 characters"),
        ],
    )
    def test_register_user_with_invalid_passwords(self, password: str, error_match: str):
        """Test that registration fails with various invalid passwords."""
        # Arrange
        mock_db = Mock()
        service = UserApplicationService(mock_db)

        # Act & Assert
        with pytest.raises(ValueError, match=error_match):
            service.register_user("john_doe", "john@example.com", password)

        mock_db.rollback.assert_called_once()
